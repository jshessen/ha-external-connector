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

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..utils import HAConnectorLogger, ValidationError

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


@dataclass
class SkillManifest:
    """Alexa Skill Manifest configuration."""

    skill_name: str
    description: str
    example_phrases: list[str] = field(default_factory=list)
    supported_locales: list[str] = field(default_factory=lambda: ["en-US"])
    interfaces: list[SkillInterface] = field(
        default_factory=lambda: [SkillInterface.SMART_HOME]
    )
    lambda_endpoint: str = ""
    account_linking_required: bool = True
    oauth_client_id: str = ""
    oauth_authorization_url: str = ""
    oauth_access_token_url: str = ""
    oauth_scopes: list[str] = field(default_factory=lambda: ["smart_home"])

    def to_manifest_json(self) -> dict[str, Any]:
        """Generate the complete Alexa Skill manifest JSON."""
        manifest = {
            "manifest": {
                "publishingInformation": {
                    "locales": {
                        locale: {
                            "name": self.skill_name,
                            "summary": self.description,
                            "description": self.description,
                            "examplePhrases": self.example_phrases
                            or [
                                "Alexa, turn on the lights",
                                "Alexa, set the temperature to 72 degrees",
                                "Alexa, dim the bedroom lights",
                            ],
                            "keywords": ["smart home", "home assistant", "automation"],
                            "smallIconUri": "",
                            "largeIconUri": "",
                        }
                        for locale in self.supported_locales
                    },
                    "isAvailableWorldwide": False,
                    "testingInstructions": "Test with Home Assistant integration",
                    "category": "SMART_HOME",
                    "distributionCountries": ["US", "CA", "GB", "AU"],
                },
                "apis": {
                    "smartHome": {
                        "endpoint": {"uri": self.lambda_endpoint},
                        "protocolVersion": "3",
                    }
                },
                "manifestVersion": "1.0",
                "permissions": [{"name": "alexa::devices:all:notifications:write"}],
            }
        }

        # Add account linking if required
        if self.account_linking_required:
            manifest["manifest"]["apis"]["smartHome"]["accountLinkingRequired"] = True
            manifest["manifest"]["accountLinking"] = {
                "type": "AUTH_CODE",
                "authorizationUrl": self.oauth_authorization_url,
                "accessTokenUrl": self.oauth_access_token_url,
                "clientId": self.oauth_client_id,
                "scopes": self.oauth_scopes,
                "skipOnEnablement": False,
            }

        return manifest


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
        logger.info("🎯 Creating Alexa Skill definition: %s", request.skill_name)

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

        # Create skill manifest
        manifest = SkillManifest(
            skill_name=request.skill_name,
            description=request.description,
            supported_locales=request.supported_locales,
            lambda_endpoint=f"arn:aws:lambda:{self.aws_region}:{{ACCOUNT_ID}}:function:{request.lambda_function_name}",
            oauth_client_id=request.oauth_client_id,
            oauth_authorization_url=oauth_endpoints["authorization_url"],
            oauth_access_token_url=oauth_endpoints["token_url"],
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
            f"3. Enter skill name: '{manifest.skill_name}'",
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
            f"1. Authorization URL: {manifest.oauth_authorization_url}",
            f"2. Access Token URL: {manifest.oauth_access_token_url}",
            f"3. Client ID: {manifest.oauth_client_id}",
            "4. Client Secret: [Copy from CloudFlare Access or OAuth provider]",
            f"5. Scopes: {', '.join(manifest.oauth_scopes)}",
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
        logger.info("🔍 Validating Alexa skill setup: %s", skill_id)

        validation_results = {
            "skill_id": skill_id,
            "lambda_function": lambda_function_name,
            "checks": [],
            "overall_status": "pending",
            "recommendations": [],
        }

        # TODO: Implement actual validation checks:
        # - Verify Lambda function exists and has Alexa trigger
        # - Check skill exists in Amazon Developer Console
        # - Validate account linking configuration
        # - Test OAuth endpoints
        # - Verify Home Assistant integration

        validation_results["checks"] = [
            {
                "name": "Lambda Function Exists",
                "status": "pending",
                "message": "Not yet implemented",
            },
            {
                "name": "Alexa Trigger Configured",
                "status": "pending",
                "message": "Not yet implemented",
            },
            {
                "name": "Account Linking Setup",
                "status": "pending",
                "message": "Not yet implemented",
            },
            {
                "name": "OAuth Endpoints",
                "status": "pending",
                "message": "Not yet implemented",
            },
            {
                "name": "Home Assistant Integration",
                "status": "pending",
                "message": "Not yet implemented",
            },
        ]

        validation_results["recommendations"] = [
            "Complete Lambda deployment using ha-external-connector CLI",
            "Configure Alexa Smart Home trigger in AWS Lambda console",
            "Set up account linking in Amazon Developer Console",
            "Test OAuth flow and device discovery",
        ]

        return validation_results

    def export_configuration(self, skill_id: str, format: str = "json") -> str:
        """Export skill configuration in various formats."""
        if skill_id not in self.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        skill = self.skills[skill_id]

        if format == "json":
            return json.dumps(skill.to_manifest_json(), indent=2)
        elif format == "yaml":
            # TODO: Implement YAML export
            raise ValidationError("YAML export not yet implemented")
        else:
            raise ValidationError(f"Unsupported export format: {format}")
