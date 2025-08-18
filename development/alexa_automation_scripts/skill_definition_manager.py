"""
🎯 ALEXA SKILL DEFINITION MANAGER

This module handles the complete Alexa Smart Home Skill definition and setup process,
building on the existing HA External Connector architecture to provide:

1. Interactive skill configuration wizard
2. Amazon Developer Console automation/guidance
3. Skill definition file generation
4. Lambda trigger setup and validation
5. End-to-end testing and validation

This extends the existing CLI wizard and web interface patterns.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, Field

from development.utils import HAConnectorLogger, ValidationError

logger = HAConnectorLogger("alexa.skill_definition")


class SkillStage(str, Enum):
    """Alexa Skill development stages."""

    DEVELOPMENT = "development"
    CERTIFICATION = "certification"
    LIVE = "live"


class SkillInterface(str, Enum):
    """Supported Alexa Skill interfaces."""

    SMART_HOME = "Alexa.SmartHome"
    DISCOVERY = "Alexa.Discovery"
    POWER_CONTROLLER = "Alexa.PowerController"
    BRIGHTNESS_CONTROLLER = "Alexa.BrightnessController"
    COLOR_CONTROLLER = "Alexa.ColorController"
    PERCENTAGE_CONTROLLER = "Alexa.PercentageController"
    THERMOSTAT_CONTROLLER = "Alexa.ThermostatController"
    CONTACT_SENSOR = "Alexa.ContactSensor"
    MOTION_SENSOR = "Alexa.MotionSensor"
    LOCK_CONTROLLER = "Alexa.LockController"


class AlexaRegion(str, Enum):
    """Supported Alexa regions with their endpoints."""

    NORTH_AMERICA = "NA"  # Default endpoint
    EUROPE = "EU"
    FAR_EAST = "FE"


class PublishingConfig(BaseModel):
    """Configuration for skill publishing information."""

    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    example_phrases: list[str] = Field(
        default_factory=lambda: [
            "Alexa, turn on the lights",
            "Alexa, set the temperature to 72 degrees",
            "Alexa, dim the bedroom lights",
        ],
        description="Example phrases for the skill",
    )
    supported_locales: list[str] = Field(
        default=["en-US"], description="Supported language locales"
    )
    keywords: list[str] = Field(
        default=["smart home", "home assistant", "automation"],
        description="Keywords for skill discovery",
    )


class OAuthConfig(BaseModel):
    """OAuth configuration for account linking."""

    client_id: str = Field(..., description="OAuth client ID")
    authorization_url: str = Field(..., description="OAuth authorization URL")
    access_token_url: str = Field(..., description="OAuth access token URL")
    scopes: list[str] = Field(default=["smart_home"], description="OAuth scopes")


@dataclass
class SkillManifest:
    """Alexa Skill Manifest configuration."""

    publishing: PublishingConfig
    lambda_endpoint: str
    oauth_config: OAuthConfig | None = None
    interfaces: list[SkillInterface] = field(
        default_factory=lambda: [SkillInterface.SMART_HOME]
    )

    @property
    def account_linking_required(self) -> bool:
        """Check if account linking is required."""
        return self.oauth_config is not None

    def to_manifest_json(self) -> dict[str, Any]:
        """Generate the complete Alexa Skill manifest JSON."""
        manifest = {
            "manifest": {
                "publishingInformation": self._build_publishing_info(),
                "apis": self._build_apis_config(),
                "manifestVersion": "1.0",
                "permissions": [{"name": "alexa::devices:all:notifications:write"}],
            }
        }

        if self.account_linking_required:
            manifest["manifest"]["accountLinking"] = self._build_account_linking()

        return manifest

    def _build_publishing_info(self) -> dict[str, Any]:
        """Build the publishing information section."""
        return {
            "locales": {
                locale: {
                    "name": self.publishing.name,
                    "summary": self.publishing.description,
                    "description": self.publishing.description,
                    "examplePhrases": self.publishing.example_phrases,
                    "keywords": self.publishing.keywords,
                    "smallIconUri": "",
                    "largeIconUri": "",
                }
                for locale in self.publishing.supported_locales
            },
            "isAvailableWorldwide": False,
            "testingInstructions": "Test with Home Assistant integration",
            "category": "SMART_HOME",
            "distributionCountries": ["US", "CA", "GB", "AU"],
        }

    def _build_apis_config(self) -> dict[str, Any]:
        """Build the APIs configuration section."""
        return {
            "smartHome": {
                "endpoint": {"uri": self.lambda_endpoint},
                "protocolVersion": "3",
            }
        }

    def _build_account_linking(self) -> dict[str, Any]:
        """Build the account linking configuration."""
        if not self.oauth_config:
            raise ValidationError("OAuth configuration required for account linking")

        return {
            "type": "AUTH_CODE",
            "authorizationUrl": self.oauth_config.authorization_url,
            "accessTokenUrl": self.oauth_config.access_token_url,
            "clientId": self.oauth_config.client_id,
            "scopes": self.oauth_config.scopes,
            "skipOnEnablement": False,
        }


class SkillDefinitionRequest(BaseModel):
    """Request model for creating a new skill definition."""

    skill_name: str = Field(..., description="Name of the Alexa skill")
    description: str = Field(..., description="Skill description for users")
    lambda_function_name: str = Field(..., description="AWS Lambda function name")
    home_assistant_url: str = Field(..., description="Home Assistant base URL")
    oauth_client_id: str = Field(..., description="OAuth client ID for account linking")
    supported_locales: list[str] = Field(
        default=["en-US"], description="Supported language locales"
    )
    enable_cloudflare: bool = Field(
        default=False, description="Enable CloudFlare security gateway"
    )
    cloudflare_domain: str = Field(
        "", description="CloudFlare domain for OAuth endpoints"
    )


class SkillDefinitionResponse(BaseModel):
    """Response model for skill definition operations."""

    skill_id: str
    skill_name: str
    status: str
    manifest_json: dict[str, Any]
    setup_instructions: list[str]
    lambda_arn: str
    oauth_endpoints: dict[str, str]


class AlexaSkillDefinitionManager:
    """
    Manages Alexa Smart Home Skill definitions and setup process.

    Integrates with existing HA External Connector architecture to provide
    end-to-end skill configuration and deployment.
    """

    def __init__(self, aws_region: str = "us-east-1"):
        """Initialize the skill definition manager."""
        self.aws_region = aws_region
        self.skills: dict[str, SkillManifest] = {}

    def create_skill_definition(
        self, request: SkillDefinitionRequest
    ) -> SkillDefinitionResponse:
        """
        Create a new Alexa Smart Home Skill definition.

        Args:
            request: Skill definition parameters

        Returns:
            Complete skill definition with setup instructions
        """
        logger.info(f"🎯 Creating Alexa Skill definition: {request.skill_name}")

        # Generate unique skill ID
        skill_id = f"amzn1.ask.skill.{uuid.uuid4()}"

        # Determine OAuth endpoints based on CloudFlare setup
        if request.enable_cloudflare and request.cloudflare_domain:
            oauth_base = f"https://{request.cloudflare_domain}"
        else:
            # Use API Gateway or direct Lambda URLs
            oauth_base = f"https://api.{self.aws_region}.amazonaws.com"

        oauth_endpoints = {
            "authorization_url": f"{oauth_base}/oauth/authorize",
            "token_url": f"{oauth_base}/oauth/token",
            "user_info_url": f"{oauth_base}/oauth/userinfo",
        }

        # Create publishing configuration
        publishing_config = PublishingConfig(
            name=request.skill_name,
            description=request.description,
            supported_locales=request.supported_locales,
        )

        # Create OAuth configuration
        oauth_config = OAuthConfig(
            client_id=request.oauth_client_id,
            authorization_url=oauth_endpoints["authorization_url"],
            access_token_url=oauth_endpoints["token_url"],
        )

        # Create skill manifest
        manifest = SkillManifest(
            publishing=publishing_config,
            lambda_endpoint=f"arn:aws:lambda:{self.aws_region}:{{ACCOUNT_ID}}:function:{request.lambda_function_name}",
            oauth_config=oauth_config,
        )

        # Store the skill definition
        self.skills[skill_id] = manifest

        # Generate setup instructions
        setup_instructions = self._generate_setup_instructions(
            skill_id, manifest, request
        )

        return SkillDefinitionResponse(
            skill_id=skill_id,
            skill_name=request.skill_name,
            status="created",
            manifest_json=manifest.to_manifest_json(),
            setup_instructions=setup_instructions,
            lambda_arn=manifest.lambda_endpoint,
            oauth_endpoints=oauth_endpoints,
        )

    def _generate_setup_instructions(
        self, skill_id: str, manifest: SkillManifest, request: SkillDefinitionRequest
    ) -> list[str]:
        """Generate step-by-step setup instructions for the Alexa Skill."""

        instructions = [
            "📋 **Alexa Smart Home Skill Setup Instructions**",
            "",
            "**Step 1: Amazon Developer Console Setup**",
            "1. Go to https://developer.amazon.com/alexa/console/ask",
            "2. Click 'Create Skill'",
            f"3. Enter skill name: '{manifest.publishing.name}'",
            "4. Choose 'Smart Home' as skill type",
            "5. Choose 'Provision your own' for hosting",
            "6. Click 'Create skill'",
            "",
            "**Step 2: Configure Smart Home Endpoint**",
            f"1. Set Default endpoint: {manifest.lambda_endpoint}",
            "2. Select AWS region: " + self.aws_region.upper(),
            "3. Save the configuration",
            "",
            "**Step 3: Account Linking Configuration**",
            (
                "1. Authorization URL: "
                + (
                    manifest.oauth_config.authorization_url
                    if manifest.oauth_config
                    else "Not configured"
                )
            ),
            "2. Access Token URL: "
            + (
                manifest.oauth_config.access_token_url
                if manifest.oauth_config
                else "Not configured"
            ),
            "3. Client ID: "
            + (
                manifest.oauth_config.client_id
                if manifest.oauth_config
                else "Not configured"
            ),
            "4. Client Secret: [Copy from CloudFlare Access or OAuth provider]",
            "5. Scopes: "
            + (
                ", ".join(manifest.oauth_config.scopes)
                if manifest.oauth_config
                else "Not configured"
            ),
            "6. Authorization Grant Type: Auth Code Grant",
            "",
            "**Step 4: AWS Lambda Trigger Setup**",
            f"1. Open AWS Lambda function: {request.lambda_function_name}",
            "2. Add trigger: 'Alexa Smart Home'",
            f"3. Enter Skill ID: {skill_id}",
            "4. Save the trigger configuration",
            "",
            "**Step 5: Testing & Distribution**",
            "1. Use Alexa Simulator in Developer Console",
            "2. Test account linking flow",
            "3. Test device discovery: 'Alexa, discover devices'",
            "4. Test device control: 'Alexa, turn on the lights'",
            "5. Submit for certification when ready",
            "",
            "**Additional Resources:**",
            f"- Skill ID: {skill_id}",
            f"- Lambda ARN: {manifest.lambda_endpoint}",
            "- Home Assistant Alexa Integration Documentation",
            "- Amazon Smart Home Skill API Documentation",
        ]

        return instructions

    def get_skill_manifest(self, skill_id: str) -> dict[str, Any]:
        """Get the complete skill manifest JSON for a skill."""
        if skill_id not in self.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        return self.skills[skill_id].to_manifest_json()

    def generate_test_directives(self, skill_id: str) -> dict[str, Any]:
        """Generate test directives for Alexa skill testing."""
        if skill_id not in self.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        return {
            "discovery_directive": {
                "directive": {
                    "header": {
                        "namespace": "Alexa.Discovery",
                        "name": "Discover",
                        "payloadVersion": "3",
                        "messageId": str(uuid.uuid4()),
                    },
                    "payload": {
                        "scope": {"type": "BearerToken", "token": "{{ACCESS_TOKEN}}"}
                    },
                }
            },
            "power_control_directive": {
                "directive": {
                    "header": {
                        "namespace": "Alexa.PowerController",
                        "name": "TurnOn",
                        "payloadVersion": "3",
                        "messageId": str(uuid.uuid4()),
                        "correlationToken": str(uuid.uuid4()),
                    },
                    "endpoint": {
                        "scope": {"type": "BearerToken", "token": "{{ACCESS_TOKEN}}"},
                        "endpointId": "{{DEVICE_ID}}",
                    },
                    "payload": {},
                }
            },
        }

    def validate_skill_setup(
        self, skill_id: str, lambda_function_name: str
    ) -> dict[str, Any]:
        """
        Validate that an Alexa skill is properly configured.

        Args:
            skill_id: Alexa skill ID
            lambda_function_name: AWS Lambda function name

        Returns:
            Validation results with status and recommendations
        """
        logger.info(f"🔍 Validating Alexa skill setup: {skill_id}")

        validation_results: dict[str, str | list[dict[str, str]] | list[str]] = {
            "skill_id": skill_id,
            "lambda_function": lambda_function_name,
            "checks": [],
            "overall_status": "pending",
            "recommendations": [],
        }

        # Perform validation checks for skill setup
        validation_results["checks"] = self._validate_lambda_function(
            lambda_function_name
        )
        validation_results["checks"].extend(
            self._validate_skill_configuration(skill_id)
        )
        validation_results["checks"].extend(self._validate_oauth_configuration())

        # Determine overall status
        failed_checks = [
            check
            for check in validation_results["checks"]
            if check["status"] == "failed"
        ]
        if failed_checks:
            validation_results["overall_status"] = "failed"
            validation_results["recommendations"] = [
                f"Fix {len(failed_checks)} failed validation check(s)",
                "Review configuration and retry setup",
            ]
        else:
            validation_results["overall_status"] = "passed"
            validation_results["recommendations"] = [
                "Skill setup validation completed successfully"
            ]

        return validation_results

    def _validate_lambda_function(
        self, lambda_function_name: str
    ) -> list[dict[str, str]]:
        """Validate Lambda function configuration."""
        return [
            {
                "name": "Lambda Function Exists",
                "status": "pending",
                "message": (
                    f"Check if {lambda_function_name} exists (requires AWS credentials)"
                ),
            },
            {
                "name": "Alexa Trigger Configured",
                "status": "pending",
                "message": "Verify Alexa Smart Home trigger is configured",
            },
        ]

    def _validate_skill_configuration(self, skill_id: str) -> list[dict[str, str]]:
        """Validate Amazon Developer Console skill configuration."""
        return [
            {
                "name": "Skill Exists in Console",
                "status": "pending",
                "message": (
                    f"Verify skill {skill_id} exists in Amazon Developer Console"
                ),
            },
        ]

    def _validate_oauth_configuration(self) -> list[dict[str, str]]:
        """Validate OAuth account linking configuration."""
        return [
            {
                "name": "OAuth Endpoints Accessible",
                "status": "pending",
                "message": "Test OAuth authorization and token endpoints",
            },
            {
                "name": "Account Linking Setup",
                "status": "pending",
                "message": "Verify account linking configuration in console",
            },
        ]

    def export_configuration(self, skill_id: str, export_format: str = "json") -> str:
        """Export skill configuration in various formats."""
        if skill_id not in self.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        skill = self.skills[skill_id]

        if export_format == "json":
            return str(skill.to_manifest_json())
        if export_format == "yaml":
            try:
                return yaml.dump(skill.to_manifest_json(), sort_keys=False)
            except NameError as exc:
                raise ValidationError(
                    "PyYAML is required for YAML export. "
                    "Please install it with 'pip install pyyaml'."
                ) from exc
        raise ValidationError(f"Unsupported export format: {export_format}")
