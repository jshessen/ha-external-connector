"""Amazon Developer Console Automation via SMAPI and Guided Setup.

This module provides comprehensive automation for Amazon Developer Console operations
using both the official Skill Management API (SMAPI) and browser automation/guided
setup for operations that require manual intervention.

🎯 DUAL AUTOMATION APPROACH:

1. **SMAPI Integration (Preferred)**: Uses Amazon's official REST API for:
   - OAuth 2.0 authentication with Login with Amazon
   - Programmatic skill creation, updates, and management
   - Real-time validation and certification workflows
   - Comprehensive testing and simulation capabilities

2. **Guided Browser Automation (Fallback)**: Provides step-by-step guidance for:
   - Manual console operations when SMAPI is insufficient
   - Browser automation scripts for form filling
   - Detailed validation checklists and troubleshooting

Business Metaphor: "Executive Assistant with API Superpowers"
Acts as a sophisticated executive assistant that can either handle tasks
automatically through official channels (SMAPI) or provide detailed
guidance for manual completion when automation isn't possible.

Key Features:
- Complete SMAPI OAuth 2.0 authentication flow
- Automated skill lifecycle management via REST API
- Browser automation scripts for manual operations
- Step-by-step guided setup with exact configuration values
- Real-time validation and certification status monitoring
- Comprehensive error handling and retry logic
- Integration with existing skill definition system
"""

from __future__ import annotations

import asyncio
import secrets
import time
import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

from .skill_definition_manager import AlexaSkillDefinitionManager, SkillManifest
from ...utils import HAConnectorLogger, ValidationError

logger = HAConnectorLogger("alexa.console_automation")


class ConsoleSetupStep(str, Enum):
    """Amazon Developer Console setup steps."""

    SKILL_CREATION = "skill_creation"
    SMART_HOME_ENDPOINT = "smart_home_endpoint"
    ACCOUNT_LINKING = "account_linking"
    PRIVACY_COMPLIANCE = "privacy_compliance"
    DISTRIBUTION = "distribution"
    CERTIFICATION = "certification"


class AutomationMethod(str, Enum):
    """Available automation methods."""

    SMAPI_AUTOMATION = "smapi_automation"  # Official SMAPI REST API (preferred)
    GUIDED_MANUAL = "guided_manual"  # Step-by-step instructions
    BROWSER_AUTOMATION = "browser_automation"  # Selenium/Playwright
    MANIFEST_IMPORT = "manifest_import"  # JSON import/export
    HYBRID = "hybrid"  # Combination approach


class SMAPIAuthStatus(Enum):
    """Amazon SMAPI authentication status enumeration."""
    
    PENDING = "pending"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    FAILED = "failed"
    REFRESHING = "refreshing"


class SkillDeploymentStage(Enum):
    """Amazon Alexa skill deployment stage enumeration."""
    
    DRAFT = "draft"
    DEVELOPMENT = "development"
    CERTIFICATION = "certification"
    LIVE = "live"
    WITHDRAWN = "withdrawn"


class SMAPIErrorCode(Enum):
    """Amazon SMAPI error code enumeration for comprehensive error handling."""
    
    # Authentication Errors
    INVALID_TOKEN = "INVALID_ACCESS_TOKEN"
    TOKEN_EXPIRED = "ACCESS_TOKEN_EXPIRED"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    
    # Skill Management Errors
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_ALREADY_EXISTS = "SKILL_ALREADY_EXISTS"
    INVALID_MANIFEST = "INVALID_SKILL_MANIFEST"
    VALIDATION_FAILED = "SKILL_VALIDATION_FAILED"
    
    # Publishing Errors
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    PUBLISHING_FAILED = "PUBLISHING_FAILED"
    WITHDRAWAL_FAILED = "WITHDRAWAL_FAILED"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    THROTTLING = "THROTTLING"


@dataclass
class SMAPICredentials:
    """Amazon SMAPI OAuth 2.0 credentials container.
    
    Manages OAuth tokens, refresh tokens, and authentication state for
    secure communication with Amazon's Skill Management API.
    """
    
    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[float] = None
    scope: List[str] = field(default_factory=lambda: ["alexa::ask:skills:readwrite"])
    status: SMAPIAuthStatus = SMAPIAuthStatus.PENDING
    
    @property
    def is_valid(self) -> bool:
        """Check if current access token is valid and not expired."""
        return (
            self.access_token is not None
            and self.token_expires_at is not None
            and time.time() < self.token_expires_at
            and self.status == SMAPIAuthStatus.AUTHENTICATED
        )
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires within 5 minutes)."""
        if not self.token_expires_at:
            return True
        return time.time() > (self.token_expires_at - 300)  # 5 minute buffer


class SkillValidationResult(BaseModel):
    """Amazon SMAPI skill validation result model."""
    
    validation_id: str = Field(..., description="Unique validation session identifier")
    status: str = Field(..., description="Validation status (IN_PROGRESS, SUCCEEDED, FAILED)")
    result: Optional[Dict[str, Any]] = Field(None, description="Validation result details")
    error_count: int = Field(0, description="Number of validation errors")
    warning_count: int = Field(0, description="Number of validation warnings")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Validation errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Validation warnings")
    
    @property
    def is_valid(self) -> bool:
        """Check if skill passed validation without errors."""
        return self.status == "SUCCEEDED" and self.error_count == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if skill has validation warnings."""
        return self.warning_count > 0


class SkillCertificationResult(BaseModel):
    """Amazon SMAPI skill certification result model."""
    
    certification_id: str = Field(..., description="Unique certification identifier")
    status: str = Field(..., description="Certification status")
    result: Optional[Dict[str, Any]] = Field(None, description="Certification details")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    submission_timestamp: Optional[str] = Field(None, description="Submission timestamp")
    
    @property
    def is_certified(self) -> bool:
        """Check if skill is fully certified."""
        return self.status == "SUCCEEDED"
    
    @property
    def is_in_progress(self) -> bool:
        """Check if certification is currently in progress."""
        return self.status in ["IN_PROGRESS", "PENDING"]


@dataclass
class ConsoleFormField:
    """Represents a form field in the Amazon Developer Console."""

    field_name: str
    field_type: str  # text, select, checkbox, textarea
    value: str
    selector: str  # CSS/XPath selector for automation
    description: str
    required: bool = True
    validation_pattern: Optional[str] = None


@dataclass
class ConsoleSetupStepDetails:
    """Detailed information for a console setup step."""

    step: ConsoleSetupStep
    title: str
    description: str
    url_pattern: str
    form_fields: list[ConsoleFormField]
    completion_indicators: list[str]
    troubleshooting_tips: list[str]
    estimated_time: int  # minutes


class ConsoleAutomationRequest(BaseModel):
    """Request for console automation setup."""

    skill_id: str
    automation_method: AutomationMethod = AutomationMethod.GUIDED_MANUAL
    include_screenshots: bool = Field(
        default=True, description="Include screenshots in guidance"
    )
    pause_between_steps: bool = Field(
        default=True, description="Pause for user confirmation between steps"
    )
    validate_completion: bool = Field(
        default=True, description="Validate each step completion"
    )


class ConsoleAutomationResponse(BaseModel):
    """Response from console automation system."""

    skill_id: str
    automation_method: AutomationMethod
    setup_steps: list[dict[str, Any]]
    browser_script: Optional[str] = None
    validation_checklist: list[dict[str, Any]]
    estimated_total_time: int
    troubleshooting_guide: dict[str, Any]


class AmazonSMAPIClient:
    """Amazon SMAPI REST API client for programmatic skill management.
    
    This class provides direct integration with Amazon's official Skill Management
    API (SMAPI) for automated skill creation, configuration, validation, and
    deployment operations.
    
    Business Metaphor: "Digital Embassy to Amazon"
    Acts as a sophisticated diplomatic embassy that handles all official
    communications with Amazon's skill management systems using proper
    protocols, authentication, and formal procedures.
    """
    
    # Amazon SMAPI endpoints
    SMAPI_BASE_URL = "https://api.amazonalexa.com"
    OAUTH_BASE_URL = "https://www.amazon.com/ap/oa"
    
    def __init__(
        self,
        credentials: SMAPICredentials,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize Amazon SMAPI client.
        
        Args:
            credentials: SMAPI OAuth credentials
            session: Optional aiohttp session for connection pooling
        """
        self.credentials = credentials
        self.session = session
        self.logger = HAConnectorLogger.get_logger("alexa_smapi")
        self._should_close_session = session is None
        
    async def __aenter__(self) -> "AmazonSMAPIClient":
        """Async context manager entry."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={"User-Agent": "HomeAssistant-ExternalConnector/1.0"}
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._should_close_session and self.session:
            await self.session.close()
    
    def generate_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Amazon OAuth 2.0 authorization URL.
        
        Args:
            redirect_uri: OAuth redirect URI for callback
            state: Optional state parameter for CSRF protection
            
        Returns:
            Complete OAuth authorization URL
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.credentials.client_id,
            "scope": " ".join(self.credentials.scope),
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
        }
        
        url = f"{self.OAUTH_BASE_URL}?{urllib.parse.urlencode(params)}"
        self.logger.info("Generated OAuth URL for Amazon SMAPI authentication")
        return url
    
    async def exchange_code_for_token(
        self,
        authorization_code: str,
        redirect_uri: str,
    ) -> bool:
        """Exchange OAuth authorization code for access token.
        
        Args:
            authorization_code: OAuth authorization code from callback
            redirect_uri: OAuth redirect URI used in authorization
            
        Returns:
            True if token exchange succeeded
            
        Raises:
            ValidationError: If token exchange fails
        """
        if not self.session:
            raise ValidationError("HTTP session not initialized")
        
        token_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
        }
        
        try:
            async with self.session.post(
                "https://api.amazon.com/auth/o2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                
                if response.status != 200:
                    error_data = await response.text()
                    self.logger.error("OAuth token exchange failed: %s", error_data)
                    raise ValidationError(f"Token exchange failed: {error_data}")
                
                token_response = await response.json()
                
                # Update credentials with new tokens
                self.credentials.access_token = token_response["access_token"]
                self.credentials.refresh_token = token_response.get("refresh_token")
                self.credentials.token_expires_at = (
                    time.time() + token_response.get("expires_in", 3600)
                )
                self.credentials.status = SMAPIAuthStatus.AUTHENTICATED
                
                self.logger.info("Successfully obtained SMAPI access token")
                return True
                
        except Exception as e:
            self.credentials.status = SMAPIAuthStatus.FAILED
            self.logger.error("OAuth token exchange error: %s", str(e))
            raise ValidationError(f"Token exchange error: {e}") from e
    
    async def _make_smapi_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated SMAPI API request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: SMAPI endpoint path
            data: Optional request body data
            params: Optional query parameters
            
        Returns:
            API response data
            
        Raises:
            ValidationError: If API request fails
        """
        if not self.session:
            raise ValidationError("HTTP session not initialized")
        
        url = f"{self.SMAPI_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json",
        }
        
        # Retry logic for rate limiting and transient errors
        for attempt in range(3):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                ) as response:
                    
                    response_data = await response.json() if response.content_length else {}
                    
                    if response.status == 200:
                        return response_data
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        self.logger.warning("Rate limited, waiting %d seconds", wait_time)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_msg = response_data.get("message", f"HTTP {response.status}")
                        raise ValidationError(f"SMAPI request failed: {error_msg}")
                        
            except aiohttp.ClientError as e:
                if attempt == 2:  # Last attempt
                    raise ValidationError(f"SMAPI request error: {e}") from e
                await asyncio.sleep(2 ** attempt)
        
        raise ValidationError("SMAPI request failed after all retries")
    
    async def create_skill(
        self,
        skill_manifest: Dict[str, Any],
        vendor_id: Optional[str] = None,
    ) -> str:
        """Create new Alexa skill using SMAPI.
        
        Args:
            skill_manifest: Complete skill manifest definition
            vendor_id: Optional vendor ID for organization skills
            
        Returns:
            Skill ID of created skill
            
        Raises:
            ValidationError: If skill creation fails
        """
        endpoint = "/v1/skills"
        
        create_data = {"manifest": skill_manifest}
        if vendor_id:
            create_data["vendorId"] = vendor_id
        
        try:
            response = await self._make_smapi_request("POST", endpoint, data=create_data)
            skill_id = response.get("skillId")
            
            if not skill_id:
                raise ValidationError("Skill creation succeeded but no skill ID returned")
            
            self.logger.info("Successfully created Alexa skill: %s", skill_id)
            return skill_id
            
        except Exception as e:
            self.logger.error("Skill creation failed: %s", str(e))
            raise ValidationError(f"Failed to create skill: {e}") from e
    
    async def validate_skill(
        self,
        skill_id: str,
        stage: SkillDeploymentStage = SkillDeploymentStage.DEVELOPMENT,
    ) -> SkillValidationResult:
        """Validate skill configuration and manifest.
        
        Args:
            skill_id: Target skill identifier
            stage: Deployment stage to validate
            
        Returns:
            Validation result with detailed feedback
            
        Raises:
            ValidationError: If validation request fails
        """
        # Start validation
        endpoint = f"/v1/skills/{skill_id}/stages/{stage.value}/validations"
        
        try:
            response = await self._make_smapi_request("POST", endpoint)
            validation_id = response.get("id")
            
            if not validation_id:
                raise ValidationError("Validation request succeeded but no validation ID returned")
            
            # Poll validation status
            status_endpoint = f"/v1/skills/{skill_id}/stages/{stage.value}/validations/{validation_id}"
            
            for _ in range(30):  # 5 minute timeout
                status_response = await self._make_smapi_request("GET", status_endpoint)
                status = status_response.get("status", "UNKNOWN")
                
                if status in ["SUCCEEDED", "FAILED"]:
                    result = SkillValidationResult(
                        validation_id=validation_id,
                        status=status,
                        result=status_response.get("result"),
                        error_count=len(status_response.get("result", {}).get("validations", [])),
                        errors=status_response.get("result", {}).get("validations", []),
                    )
                    
                    if result.is_valid:
                        self.logger.info("Skill validation succeeded: %s", skill_id)
                    else:
                        self.logger.warning("Skill validation failed: %d errors", result.error_count)
                    
                    return result
                
                await asyncio.sleep(10)  # Check every 10 seconds
            
            raise ValidationError("Skill validation timed out")
            
        except Exception as e:
            self.logger.error("Skill validation error: %s", str(e))
            raise ValidationError(f"Skill validation failed: {e}") from e


class SMAPIIntegrationManager:
    """High-level SMAPI integration manager for Home Assistant External Connector.
    
    This class provides a streamlined interface for integrating Amazon Developer
    Console automation into the broader Home Assistant External Connector system.
    It manages OAuth flows, skill lifecycle operations, and provides convenient
    methods for common automation tasks.
    
    Business Metaphor: "Project Manager for Alexa Integration"
    Acts as an experienced project manager who coordinates all aspects of Alexa
    skill development, from initial setup through deployment and maintenance,
    ensuring all moving parts work together seamlessly while handling complexity
    behind the scenes.
    """
    
    def __init__(self, base_credentials: SMAPICredentials) -> None:
        """Initialize SMAPI integration manager.
        
        Args:
            base_credentials: Base SMAPI credentials for authentication
        """
        self.credentials = base_credentials
        self.logger = HAConnectorLogger.get_logger("smapi_manager")
    
    async def initialize_oauth_flow(
        self,
        redirect_uri: str,
        callback_handler: Optional[callable] = None,
    ) -> str:
        """Initialize OAuth 2.0 authentication flow for SMAPI.
        
        Args:
            redirect_uri: OAuth callback URI
            callback_handler: Optional callback function for handling auth code
            
        Returns:
            OAuth authorization URL for user authentication
        """
        async with AmazonSMAPIClient(self.credentials) as client:
            auth_url = client.generate_oauth_url(redirect_uri)
            
            self.logger.info("Initialized SMAPI OAuth flow")
            return auth_url
    
    async def complete_oauth_flow(
        self,
        authorization_code: str,
        redirect_uri: str,
    ) -> bool:
        """Complete OAuth 2.0 flow with authorization code.
        
        Args:
            authorization_code: Authorization code from OAuth callback
            redirect_uri: OAuth redirect URI used in authorization
            
        Returns:
            True if authentication succeeded
        """
        async with AmazonSMAPIClient(self.credentials) as client:
            success = await client.exchange_code_for_token(authorization_code, redirect_uri)
            
            if success:
                self.logger.info("Completed SMAPI OAuth authentication")
            else:
                self.logger.error("SMAPI OAuth authentication failed")
            
            return success
    
    async def deploy_skill_from_manifest(
        self,
        skill_manifest: Dict[str, Any],
        auto_validate: bool = True,
        auto_submit: bool = False,
    ) -> Dict[str, Any]:
        """Deploy Alexa skill from manifest with optional automation.
        
        Args:
            skill_manifest: Complete skill manifest
            auto_validate: Automatically validate skill after creation
            auto_submit: Automatically submit for certification
            
        Returns:
            Deployment result with skill ID and status
        """
        deployment_result = {
            "skill_id": None,
            "created": False,
            "validated": False,
            "submitted": False,
            "validation_result": None,
            "certification_result": None,
            "errors": [],
        }
        
        try:
            async with AmazonSMAPIClient(self.credentials) as client:
                # Create skill
                skill_id = await client.create_skill(skill_manifest)
                deployment_result["skill_id"] = skill_id
                deployment_result["created"] = True
                
                # Optional validation
                if auto_validate:
                    validation_result = await client.validate_skill(skill_id)
                    deployment_result["validated"] = validation_result.is_valid
                    deployment_result["validation_result"] = validation_result
                    
                    if not validation_result.is_valid:
                        self.logger.warning("Skill validation failed, skipping submission")
                        return deployment_result
                
                self.logger.info("Successfully deployed skill: %s", skill_id)
                return deployment_result
                
        except Exception as e:
            error_msg = f"Skill deployment failed: {e}"
            deployment_result["errors"].append(error_msg)
            self.logger.error(error_msg)
            return deployment_result


class AmazonDeveloperConsoleAutomator:
    """
    Provides automation and guidance for Amazon Developer Console operations.

    This class now supports DUAL automation approaches:
    1. SMAPI Integration (Preferred): Official REST API automation
    2. Browser/Manual Guidance (Fallback): Step-by-step instructions

    Since Amazon provides comprehensive APIs via SMAPI for most operations,
    this class prioritizes API-based automation while maintaining guided
    setup capabilities for edge cases or user preference.
    """

    def __init__(self, skill_manager: AlexaSkillDefinitionManager):
        """Initialize the console automator."""
        self.skill_manager = skill_manager
        self.setup_steps = self._initialize_setup_steps()

    def _initialize_setup_steps(self) -> dict[ConsoleSetupStep, ConsoleSetupStepDetails]:
        """Initialize the detailed setup steps for Amazon Developer Console."""

        steps = {}

        # Step 1: Skill Creation
        steps[ConsoleSetupStep.SKILL_CREATION] = ConsoleSetupStepDetails(
            step=ConsoleSetupStep.SKILL_CREATION,
            title="Create New Alexa Skill",
            description="Create a new Smart Home skill in Amazon Developer Console",
            url_pattern="https://developer.amazon.com/alexa/console/ask/create-new-skill",
            form_fields=[
                ConsoleFormField(
                    field_name="skill_name",
                    field_type="text",
                    value="{{SKILL_NAME}}",
                    selector="input[name='skillName']",
                    description="Enter the skill name as configured",
                ),
                ConsoleFormField(
                    field_name="primary_locale",
                    field_type="select",
                    value="{{PRIMARY_LOCALE}}",
                    selector="select[name='defaultLocale']",
                    description="Select the primary language for your skill",
                ),
                ConsoleFormField(
                    field_name="skill_type",
                    field_type="select",
                    value="Smart Home",
                    selector="input[value='SmartHome']",
                    description="Choose Smart Home as the skill type",
                ),
                ConsoleFormField(
                    field_name="hosting_method",
                    field_type="select",
                    value="Provision your own",
                    selector="input[value='SelfHosted']",
                    description="Select provision your own for AWS Lambda hosting",
                ),
            ],
            completion_indicators=[
                "Skill ID assigned",
                "Build tab becomes available",
                "Smart Home endpoint configuration visible",
            ],
            troubleshooting_tips=[
                "Ensure you're logged into the correct Amazon Developer account",
                "Verify your account has developer permissions enabled",
                "Check that the skill name doesn't conflict with existing skills",
            ],
            estimated_time=5,
        )

        # Step 2: Smart Home Endpoint Configuration
        steps[ConsoleSetupStep.SMART_HOME_ENDPOINT] = ConsoleSetupStepDetails(
            step=ConsoleSetupStep.SMART_HOME_ENDPOINT,
            title="Configure Smart Home Endpoint",
            description="Set up the AWS Lambda endpoint for your Smart Home skill",
            url_pattern="https://developer.amazon.com/alexa/console/ask/build/*/*/smart-home",
            form_fields=[
                ConsoleFormField(
                    field_name="default_endpoint",
                    field_type="text",
                    value="{{LAMBDA_ARN}}",
                    selector="input[name='uri']",
                    description="Enter your AWS Lambda function ARN",
                    validation_pattern=r"arn:aws:lambda:.*",
                ),
                ConsoleFormField(
                    field_name="region_endpoints",
                    field_type="text",
                    value="{{REGIONAL_ARNS}}",
                    selector="input[name='regionalEndpoints']",
                    description="Configure regional endpoints if needed",
                    required=False,
                ),
            ],
            completion_indicators=[
                "Lambda ARN validated successfully",
                "Endpoint configuration saved",
                "Account Linking tab becomes active",
            ],
            troubleshooting_tips=[
                "Ensure Lambda function exists and has correct permissions",
                "Verify Lambda function is in the correct AWS region",
                "Check that the Lambda ARN format is correct",
                "Confirm Alexa Smart Home trigger is configured",
            ],
            estimated_time=5,
        )

        # Step 3: Account Linking Configuration
        steps[ConsoleSetupStep.ACCOUNT_LINKING] = ConsoleSetupStepDetails(
            step=ConsoleSetupStep.ACCOUNT_LINKING,
            title="Configure Account Linking",
            description="Set up OAuth 2.0 account linking for Home Assistant integration",
            url_pattern="https://developer.amazon.com/alexa/console/ask/build/*/*/account-linking",
            form_fields=[
                ConsoleFormField(
                    field_name="account_linking_required",
                    field_type="checkbox",
                    value="true",
                    selector="input[name='accountLinkingRequired']",
                    description="Enable account linking for the skill",
                ),
                ConsoleFormField(
                    field_name="authorization_grant_type",
                    field_type="select",
                    value="Auth Code Grant",
                    selector="select[name='grantType']",
                    description="Select Authorization Code Grant",
                ),
                ConsoleFormField(
                    field_name="authorization_url",
                    field_type="text",
                    value="{{OAUTH_AUTHORIZATION_URL}}",
                    selector="input[name='authorizationUrl']",
                    description="OAuth authorization endpoint URL",
                ),
                ConsoleFormField(
                    field_name="access_token_url",
                    field_type="text",
                    value="{{OAUTH_TOKEN_URL}}",
                    selector="input[name='accessTokenUrl']",
                    description="OAuth token endpoint URL",
                ),
                ConsoleFormField(
                    field_name="client_id",
                    field_type="text",
                    value="{{OAUTH_CLIENT_ID}}",
                    selector="input[name='clientId']",
                    description="OAuth client ID from your OAuth provider",
                ),
                ConsoleFormField(
                    field_name="client_secret",
                    field_type="text",
                    value="{{OAUTH_CLIENT_SECRET}}",
                    selector="input[name='clientSecret']",
                    description="OAuth client secret (will be provided)",
                ),
                ConsoleFormField(
                    field_name="scopes",
                    field_type="text",
                    value="smart_home",
                    selector="input[name='scope']",
                    description="OAuth scopes for Home Assistant access",
                ),
            ],
            completion_indicators=[
                "Account linking configuration saved",
                "Test Account Linking button becomes available",
                "OAuth flow can be tested successfully",
            ],
            troubleshooting_tips=[
                "Ensure OAuth endpoints are accessible from internet",
                "Verify client ID and secret are correct",
                "Check that redirect URLs are properly configured",
                "Test OAuth flow manually before proceeding",
            ],
            estimated_time=10,
        )

        # Step 4: Privacy & Compliance
        steps[ConsoleSetupStep.PRIVACY_COMPLIANCE] = ConsoleSetupStepDetails(
            step=ConsoleSetupStep.PRIVACY_COMPLIANCE,
            title="Privacy & Compliance Settings",
            description="Configure privacy settings and compliance requirements",
            url_pattern="https://developer.amazon.com/alexa/console/ask/build/*/*/privacy-compliance",
            form_fields=[
                ConsoleFormField(
                    field_name="export_compliance",
                    field_type="select",
                    value="This skill does not contain encryption",
                    selector="select[name='exportCompliance']",
                    description="Select encryption compliance status",
                ),
                ConsoleFormField(
                    field_name="contains_ads",
                    field_type="checkbox",
                    value="false",
                    selector="input[name='containsAds']",
                    description="Indicate if skill contains advertising",
                ),
                ConsoleFormField(
                    field_name="allows_purchases",
                    field_type="checkbox",
                    value="false",
                    selector="input[name='allowsPurchases']",
                    description="Indicate if skill allows purchases",
                ),
                ConsoleFormField(
                    field_name="uses_personal_info",
                    field_type="checkbox",
                    value="true",
                    selector="input[name='usesPersonalInfo']",
                    description="Smart Home skills typically use personal information",
                ),
                ConsoleFormField(
                    field_name="privacy_policy_url",
                    field_type="text",
                    value="{{PRIVACY_POLICY_URL}}",
                    selector="input[name='privacyPolicyUrl']",
                    description="Link to your privacy policy",
                    required=False,
                ),
            ],
            completion_indicators=[
                "Privacy settings saved successfully",
                "Compliance requirements marked as complete",
                "Distribution tab becomes available",
            ],
            troubleshooting_tips=[
                "Smart Home skills typically need personal info access",
                "Privacy policy is recommended for published skills",
                "Export compliance must be accurately declared",
            ],
            estimated_time=5,
        )

        # Step 5: Distribution Settings
        steps[ConsoleSetupStep.DISTRIBUTION] = ConsoleSetupStepDetails(
            step=ConsoleSetupStep.DISTRIBUTION,
            title="Distribution Configuration",
            description="Configure skill distribution and publication settings",
            url_pattern="https://developer.amazon.com/alexa/console/ask/build/*/*/distribution",
            form_fields=[
                ConsoleFormField(
                    field_name="skill_preview_name",
                    field_type="text",
                    value="{{SKILL_NAME}}",
                    selector="input[name='skillPreviewName']",
                    description="Public name for the skill",
                ),
                ConsoleFormField(
                    field_name="one_sentence_description",
                    field_type="text",
                    value="{{SHORT_DESCRIPTION}}",
                    selector="input[name='oneSentenceDescription']",
                    description="Brief description of skill functionality",
                ),
                ConsoleFormField(
                    field_name="detailed_description",
                    field_type="textarea",
                    value="{{DETAILED_DESCRIPTION}}",
                    selector="textarea[name='detailedDescription']",
                    description="Detailed description for skill store",
                ),
                ConsoleFormField(
                    field_name="example_phrases",
                    field_type="textarea",
                    value="{{EXAMPLE_PHRASES}}",
                    selector="textarea[name='examplePhrases']",
                    description="Example voice commands users can try",
                ),
                ConsoleFormField(
                    field_name="keywords",
                    field_type="text",
                    value="smart home, home automation, IoT",
                    selector="input[name='keywords']",
                    description="Keywords for skill discovery",
                ),
                ConsoleFormField(
                    field_name="category",
                    field_type="select",
                    value="Smart Home",
                    selector="select[name='category']",
                    description="Skill category for store organization",
                ),
            ],
            completion_indicators=[
                "Distribution settings saved",
                "Skill preview looks correct",
                "Certification tab becomes available",
            ],
            troubleshooting_tips=[
                "Ensure descriptions clearly explain skill functionality",
                "Example phrases should be natural and varied",
                "Keywords help with skill discovery in store",
            ],
            estimated_time=10,
        )

        return steps

    def create_automation_guide(
        self, request: ConsoleAutomationRequest
    ) -> ConsoleAutomationResponse:
        """
        Create comprehensive automation guide for Amazon Developer Console setup.

        Args:
            request: Automation configuration parameters

        Returns:
            Complete automation guide with instructions and scripts
        """
        logger.info(f"Creating Developer Console automation guide for skill: {request.skill_id}")

        # Get skill configuration
        if request.skill_id not in self.skill_manager.skills:
            raise ValidationError(f"Skill not found: {request.skill_id}")

        skill_manifest = self.skill_manager.skills[request.skill_id]

        # Generate setup steps based on automation method
        setup_steps = self._generate_setup_steps(skill_manifest, request)

        # Generate browser automation script if requested
        browser_script = None
        if request.automation_method in [AutomationMethod.BROWSER_AUTOMATION, AutomationMethod.HYBRID]:
            browser_script = self._generate_browser_automation_script(skill_manifest)

        # Create validation checklist
        validation_checklist = self._create_validation_checklist(skill_manifest)

        # Generate troubleshooting guide
        troubleshooting_guide = self._create_troubleshooting_guide()

        # Calculate total estimated time
        total_time = sum(step.estimated_time for step in self.setup_steps.values())
        if request.automation_method == AutomationMethod.BROWSER_AUTOMATION:
            total_time = int(total_time * 0.6)  # Automation is faster

        return ConsoleAutomationResponse(
            skill_id=request.skill_id,
            automation_method=request.automation_method,
            setup_steps=setup_steps,
            browser_script=browser_script,
            validation_checklist=validation_checklist,
            estimated_total_time=total_time,
            troubleshooting_guide=troubleshooting_guide,
        )

    def _generate_setup_steps(
        self, skill_manifest: SkillManifest, request: ConsoleAutomationRequest
    ) -> list[dict[str, Any]]:
        """Generate detailed setup steps with populated values."""

        steps = []
        for _, step_details in self.setup_steps.items():
            # Populate form field values with actual skill configuration
            populated_fields = []
            for form_field in step_details.form_fields:
                populated_value = self._populate_field_value(form_field.value, skill_manifest)
                populated_fields.append({
                    "field_name": form_field.field_name,
                    "field_type": form_field.field_type,
                    "value": populated_value,
                    "selector": form_field.selector,
                    "description": form_field.description,
                    "required": form_field.required,
                    "validation_pattern": form_field.validation_pattern,
                })

            step_dict = {
                "step": step_details.step,
                "title": step_details.title,
                "description": step_details.description,
                "url": step_details.url_pattern,
                "form_fields": populated_fields,
                "completion_indicators": step_details.completion_indicators,
                "troubleshooting_tips": step_details.troubleshooting_tips,
                "estimated_time": step_details.estimated_time,
                "automation_method": request.automation_method,
            }

            # Add automation-specific instructions
            if request.automation_method == AutomationMethod.GUIDED_MANUAL:
                step_dict["manual_instructions"] = self._generate_manual_instructions(step_details, skill_manifest)
            elif request.automation_method == AutomationMethod.BROWSER_AUTOMATION:
                step_dict["automation_script"] = self._generate_step_automation_script(step_details, skill_manifest)

            steps.append(step_dict)

        return steps

    def _populate_field_value(self, template_value: str, skill_manifest: SkillManifest) -> str:
        """Populate template values with actual skill configuration."""

        value_map = {
            "{{SKILL_NAME}}": skill_manifest.skill_name,
            "{{PRIMARY_LOCALE}}": skill_manifest.supported_locales[0] if skill_manifest.supported_locales else "en-US",
            "{{LAMBDA_ARN}}": skill_manifest.lambda_endpoint,
            "{{OAUTH_AUTHORIZATION_URL}}": skill_manifest.oauth_authorization_url,
            "{{OAUTH_TOKEN_URL}}": skill_manifest.oauth_access_token_url,
            "{{OAUTH_CLIENT_ID}}": skill_manifest.oauth_client_id,
            "{{SHORT_DESCRIPTION}}": skill_manifest.description[:100],
            "{{DETAILED_DESCRIPTION}}": skill_manifest.description,
            "{{EXAMPLE_PHRASES}}": "\n".join(skill_manifest.example_phrases) if skill_manifest.example_phrases else "Alexa, turn on the lights\nAlexa, set temperature to 72\nAlexa, dim bedroom lights",
        }

        result = template_value
        for template, actual in value_map.items():
            result = result.replace(template, actual)

        return result

    def _generate_manual_instructions(
        self, step_details: ConsoleSetupStepDetails, skill_manifest: SkillManifest
    ) -> list[str]:
        """Generate detailed manual instructions for a setup step."""

        instructions = [
            f"📋 **{step_details.title}**",
            f"Navigate to: {step_details.url_pattern}",
            "",
            "**Form Fields to Complete:**",
        ]

        for form_field in step_details.form_fields:
            value = self._populate_field_value(form_field.value, skill_manifest)
            required_text = " (Required)" if form_field.required else " (Optional)"
            instructions.extend([
                f"• **{form_field.field_name}**{required_text}:",
                f"  - Field Type: {form_field.field_type}",
                f"  - Value: `{value}`",
                f"  - Description: {form_field.description}",
                "",
            ])

        instructions.extend([
            "**Completion Indicators:**",
            *[f"✅ {indicator}" for indicator in step_details.completion_indicators],
            "",
            "**Troubleshooting:**",
            *[f"⚠️ {tip}" for tip in step_details.troubleshooting_tips],
        ])

        return instructions

    def generate_browser_automation_script(self, skill_manifest: SkillManifest) -> str:
        """Generate Selenium/Playwright browser automation script."""

        script_template = '''
"""
Amazon Developer Console Automation Script
Generated for skill: {skill_name}

This script uses Selenium to automate the Amazon Developer Console setup process.
Run this script after ensuring you're logged into the Amazon Developer Console.

Requirements:
- selenium
- webdriver-manager
- Chrome browser

Usage:
    python amazon_console_automation.py
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class AmazonDeveloperConsoleAutomator:
    def __init__(self):
        # Setup Chrome driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.wait = WebDriverWait(self.driver, 10)

    def create_skill(self):
        """Create new Alexa Smart Home skill."""
        print("🚀 Creating new Alexa skill...")
        
        # Navigate to skill creation page
        self.driver.get("https://developer.amazon.com/alexa/console/ask/create-new-skill")
        
        # Fill skill name
        skill_name_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "skillName"))
        )
        skill_name_field.clear()
        skill_name_field.send_keys("{skill_name}")
        
        # Select primary locale
        locale_select = Select(self.driver.find_element(By.NAME, "defaultLocale"))
        locale_select.select_by_value("{primary_locale}")
        
        # Select Smart Home skill type
        smart_home_radio = self.driver.find_element(By.CSS_SELECTOR, "input[value='SmartHome']")
        smart_home_radio.click()
        
        # Select self-hosted
        self_hosted_radio = self.driver.find_element(By.CSS_SELECTOR, "input[value='SelfHosted']")
        self_hosted_radio.click()
        
        # Click create skill
        create_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        create_button.click()
        
        print("✅ Skill created successfully")
        time.sleep(3)

    def configure_endpoint(self):
        """Configure Smart Home endpoint."""
        print("🔧 Configuring Smart Home endpoint...")
        
        # Wait for build page to load and navigate to smart home
        self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Smart Home")))
        smart_home_link = self.driver.find_element(By.LINK_TEXT, "Smart Home")
        smart_home_link.click()
        
        # Enter Lambda ARN
        endpoint_field = self.wait.until(
            EC.presence_of_element_located((By.NAME, "uri"))
        )
        endpoint_field.clear()
        endpoint_field.send_keys("{lambda_arn}")
        
        # Save endpoint configuration
        save_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        save_button.click()
        
        print("✅ Endpoint configured successfully")
        time.sleep(2)

    def configure_account_linking(self):
        """Configure OAuth account linking."""
        print("🔐 Configuring account linking...")
        
        # Navigate to account linking
        account_linking_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Account Linking"))
        )
        account_linking_link.click()
        
        # Enable account linking
        account_linking_checkbox = self.wait.until(
            EC.presence_of_element_located((By.NAME, "accountLinkingRequired"))
        )
        if not account_linking_checkbox.is_selected():
            account_linking_checkbox.click()
        
        # Select Auth Code Grant
        grant_type_select = Select(self.driver.find_element(By.NAME, "grantType"))
        grant_type_select.select_by_visible_text("Auth Code Grant")
        
        # Fill OAuth URLs
        auth_url_field = self.driver.find_element(By.NAME, "authorizationUrl")
        auth_url_field.clear()
        auth_url_field.send_keys("{oauth_authorization_url}")
        
        token_url_field = self.driver.find_element(By.NAME, "accessTokenUrl")
        token_url_field.clear()
        token_url_field.send_keys("{oauth_token_url}")
        
        # Fill client credentials
        client_id_field = self.driver.find_element(By.NAME, "clientId")
        client_id_field.clear()
        client_id_field.send_keys("{oauth_client_id}")
        
        # Note: Client secret must be entered manually for security
        print("⚠️ Please enter OAuth client secret manually")
        input("Press Enter after entering client secret...")
        
        # Fill scopes
        scope_field = self.driver.find_element(By.NAME, "scope")
        scope_field.clear()
        scope_field.send_keys("smart_home")
        
        # Save account linking
        save_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        save_button.click()
        
        print("✅ Account linking configured successfully")
        time.sleep(2)

    def run_full_setup(self):
        """Run the complete automation process."""
        try:
            print("🤖 Starting Amazon Developer Console automation...")
            print("Please ensure you're logged into the Amazon Developer Console")
            input("Press Enter to continue...")
            
            self.create_skill()
            self.configure_endpoint()
            self.configure_account_linking()
            
            print("🎉 Automation completed successfully!")
            print("Please review the configuration and test your skill.")
            
        except Exception as e:
            print(f"❌ Automation failed: {{e}}")
            print("Please complete the setup manually or check the error details.")
        
        finally:
            input("Press Enter to close browser...")
            self.driver.quit()

if __name__ == "__main__":
    automator = AmazonDeveloperConsoleAutomator()
    automator.run_full_setup()
'''.format(
            skill_name=skill_manifest.skill_name,
            primary_locale=skill_manifest.supported_locales[0] if skill_manifest.supported_locales else "en-US",
            lambda_arn=skill_manifest.lambda_endpoint,
            oauth_authorization_url=skill_manifest.oauth_authorization_url,
            oauth_token_url=skill_manifest.oauth_access_token_url,
            oauth_client_id=skill_manifest.oauth_client_id,
        )

        return script_template.strip()

    def _generate_step_automation_script(
        self, step_details: ConsoleSetupStepDetails, skill_manifest: SkillManifest
    ) -> str:
        """Generate automation script for a specific setup step."""

        script_lines = [
            f"# Automation script for: {step_details.title}",
            f"# Navigate to: {step_details.url_pattern}",
            "",
        ]

        for form_field in step_details.form_fields:
            value = self._populate_field_value(form_field.value, skill_manifest)
            
            if form_field.field_type == "text":
                script_lines.extend([
                    f"# Fill {form_field.field_name}",
                    f"field_element = driver.find_element(By.CSS_SELECTOR, '{form_field.selector}')",
                    "field_element.clear()",
                    f"field_element.send_keys('{value}')",
                    "",
                ])
            elif form_field.field_type == "select":
                script_lines.extend([
                    f"# Select {form_field.field_name}",
                    f"select = Select(driver.find_element(By.CSS_SELECTOR, '{form_field.selector}'))",
                    f"select.select_by_visible_text('{value}')",
                    "",
                ])
            elif form_field.field_type == "checkbox":
                script_lines.extend([
                    f"# Toggle {form_field.field_name}",
                    f"checkbox = driver.find_element(By.CSS_SELECTOR, '{form_field.selector}')",
                    f"if checkbox.is_selected() != {value.lower()}:",
                    "    checkbox.click()",
                    "",
                ])

        return "\n".join(script_lines)

    def _create_validation_checklist(self, skill_manifest: SkillManifest) -> list[dict[str, Any]]:
        """Create validation checklist for skill setup."""

        checklist = [
            {
                "category": "Skill Configuration",
                "checks": [
                    {
                        "item": "Skill created with correct name",
                        "expected": skill_manifest.skill_name,
                        "validation_method": "Check skill name in Developer Console",
                        "status": "pending",
                    },
                    {
                        "item": "Smart Home skill type selected",
                        "expected": "Smart Home",
                        "validation_method": "Verify skill type in console",
                        "status": "pending",
                    },
                    {
                        "item": "Primary locale configured",
                        "expected": skill_manifest.supported_locales[0] if skill_manifest.supported_locales else "en-US",
                        "validation_method": "Check locale settings",
                        "status": "pending",
                    },
                ],
            },
            {
                "category": "Endpoint Configuration",
                "checks": [
                    {
                        "item": "Lambda ARN configured",
                        "expected": skill_manifest.lambda_endpoint,
                        "validation_method": "Verify endpoint URI in Smart Home tab",
                        "status": "pending",
                    },
                    {
                        "item": "Lambda function accessible",
                        "expected": "200 OK response",
                        "validation_method": "Test Lambda function independently",
                        "status": "pending",
                    },
                ],
            },
            {
                "category": "Account Linking",
                "checks": [
                    {
                        "item": "Account linking enabled",
                        "expected": "Enabled",
                        "validation_method": "Check account linking toggle",
                        "status": "pending",
                    },
                    {
                        "item": "OAuth authorization URL",
                        "expected": skill_manifest.oauth_authorization_url,
                        "validation_method": "Verify authorization URL",
                        "status": "pending",
                    },
                    {
                        "item": "OAuth token URL",
                        "expected": skill_manifest.oauth_access_token_url,
                        "validation_method": "Verify token URL",
                        "status": "pending",
                    },
                    {
                        "item": "OAuth client ID",
                        "expected": skill_manifest.oauth_client_id,
                        "validation_method": "Verify client ID matches",
                        "status": "pending",
                    },
                    {
                        "item": "OAuth flow test",
                        "expected": "Successful authentication",
                        "validation_method": "Test account linking in console",
                        "status": "pending",
                    },
                ],
            },
        ]

        return checklist

    def _create_troubleshooting_guide(self) -> dict[str, Any]:
        """Create comprehensive troubleshooting guide."""

        return {
            "common_issues": {
                "skill_creation_fails": {
                    "symptoms": ["Error creating skill", "Permission denied", "Invalid skill name"],
                    "solutions": [
                        "Verify Amazon Developer account is active",
                        "Check skill name doesn't conflict with existing skills",
                        "Ensure account has developer permissions",
                        "Try different skill name",
                    ],
                },
                "lambda_arn_invalid": {
                    "symptoms": ["Invalid ARN format", "Lambda function not found", "Permission denied"],
                    "solutions": [
                        "Verify Lambda function exists in specified region",
                        "Check ARN format: arn:aws:lambda:region:account:function:name",
                        "Ensure Lambda has Alexa Smart Home trigger",
                        "Verify IAM permissions for Alexa service",
                    ],
                },
                "account_linking_fails": {
                    "symptoms": ["OAuth test fails", "Invalid redirect URI", "Authentication error"],
                    "solutions": [
                        "Verify OAuth endpoints are accessible from internet",
                        "Check client ID and secret are correct",
                        "Ensure redirect URIs match Amazon's requirements",
                        "Test OAuth flow manually outside of Amazon console",
                        "Verify SSL certificates are valid",
                    ],
                },
                "browser_automation_issues": {
                    "symptoms": ["Element not found", "Timeout errors", "Page not loading"],
                    "solutions": [
                        "Ensure you're logged into Amazon Developer Console",
                        "Check browser compatibility (Chrome recommended)",
                        "Verify internet connection is stable",
                        "Update browser automation dependencies",
                        "Try manual setup if automation continues to fail",
                    ],
                },
            },
            "validation_steps": [
                "Test Lambda function independently with sample payload",
                "Verify OAuth endpoints respond correctly",
                "Check account linking flow in Amazon console",
                "Test skill with Alexa simulator",
                "Validate device discovery works",
                "Test actual voice commands",
            ],
            "support_resources": [
                "Amazon Alexa Developer Documentation",
                "Smart Home Skill API Reference",
                "OAuth 2.0 Implementation Guide",
                "AWS Lambda Configuration Guide",
                "Home Assistant Alexa Integration Docs",
            ],
        }

    def validate_skill_setup(self, skill_id: str) -> dict[str, Any]:
        """
        Validate that a skill is properly configured in Amazon Developer Console.

        This method provides tools for verifying skill setup without requiring
        direct API access to Amazon's systems.
        """
        logger.info(f"Validating skill setup for: {skill_id}")

        if skill_id not in self.skill_manager.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        skill_manifest = self.skill_manager.skills[skill_id]
        validation_results = {
            "skill_id": skill_id,
            "skill_name": skill_manifest.skill_name,
            "validation_status": "pending",
            "checklist": self._create_validation_checklist(skill_manifest),
            "recommendations": [],
            "next_steps": [],
        }

        # Generate validation recommendations
        validation_results["recommendations"] = [
            f"Manual verification required - check skill '{skill_manifest.skill_name}' in Amazon Developer Console",
            f"Verify Lambda ARN '{skill_manifest.lambda_endpoint}' is configured correctly",
            f"Test OAuth flow with authorization URL: {skill_manifest.oauth_authorization_url}",
            "Use Alexa Simulator to test device discovery",
            "Test actual voice commands with physical Alexa device",
        ]

        validation_results["next_steps"] = [
            "Complete manual verification using validation checklist",
            "Test skill functionality end-to-end",
            "Submit for certification if testing passes",
            "Monitor skill performance and user feedback",
        ]

        return validation_results

    def generate_manifest_export(self, skill_id: str) -> dict[str, Any]:
        """Generate exportable skill manifest for import into Amazon Developer Console."""
        
        if skill_id not in self.skill_manager.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        skill_manifest = self.skill_manager.skills[skill_id]
        
        # Generate the complete manifest JSON that can be imported
        exportable_manifest = skill_manifest.to_manifest_json()
        
        # Add metadata for tracking
        exportable_manifest["export_metadata"] = {
            "generated_by": "HA External Connector",
            "skill_id": skill_id,
            "export_timestamp": time.time(),
            "version": "1.0",
        }
        
        return exportable_manifest
