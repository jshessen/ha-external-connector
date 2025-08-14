"""
🎯 ALEXA SKILL SETUP API ENDPOINTS

Enhanced web API for interactive Alexa Skill definition and setup process.
Extends the existing web API architecture with comprehensive skill management.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...integrations.alexa.skill_definition_manager import (
    AlexaSkillDefinitionManager,
    SkillDefinitionRequest,
    SkillDefinitionResponse,
)
from ...integrations.alexa.console_automation import (
    AmazonDeveloperConsoleAutomator,
    ConsoleAutomationRequest,
    ConsoleAutomationResponse,
    AutomationMethod,
)
from ...utils import ValidationError

router = APIRouter(prefix="/alexa", tags=["alexa"])


class SkillValidationResult(BaseModel):
    """Model for skill validation results."""

    skill_id: str
    lambda_function: str
    overall_status: str
    checks: list[dict[str, str]]
    recommendations: list[str]


class SkillListResponse(BaseModel):
    """Model for listing skills."""

    skills: list[dict[str, str]]
    total_count: int


# Global skill manager and console automator instances
skill_manager = AlexaSkillDefinitionManager()
console_automator = AmazonDeveloperConsoleAutomator(skill_manager)


@router.post("/skills", response_model=SkillDefinitionResponse)
async def create_skill(request: SkillDefinitionRequest) -> SkillDefinitionResponse:
    """
    Create a new Alexa Smart Home Skill definition.

    This endpoint handles the complete skill creation process including:
    - Manifest generation
    - OAuth endpoint configuration
    - Setup instruction generation
    """
    try:
        return skill_manager.create_skill_definition(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}",
        ) from e


@router.get("/skills", response_model=SkillListResponse)
async def list_skills() -> SkillListResponse:
    """List all created Alexa skills."""
    skills = [
        {
            "skill_id": skill_id,
            "skill_name": manifest.skill_name,
            "status": "created",
            "lambda_endpoint": manifest.lambda_endpoint,
        }
        for skill_id, manifest in skill_manager.skills.items()
    ]

    return SkillListResponse(skills=skills, total_count=len(skills))


@router.get("/skills/{skill_id}/manifest")
async def get_skill_manifest(skill_id: str) -> dict[str, Any]:
    """Get the complete Alexa Skill manifest JSON for a specific skill."""
    try:
        return skill_manager.get_skill_manifest(skill_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/skills/{skill_id}/test-directives")
async def get_test_directives(skill_id: str) -> dict[str, Any]:
    """Generate test directives for Alexa skill testing."""
    try:
        return skill_manager.generate_test_directives(skill_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/skills/{skill_id}/validate", response_model=SkillValidationResult)
async def validate_skill(
    skill_id: str, lambda_function_name: str
) -> SkillValidationResult:
    """
    Validate that an Alexa skill is properly configured.

    Performs comprehensive validation including:
    - Lambda function configuration
    - Alexa trigger setup
    - Account linking configuration
    - OAuth endpoint testing
    """
    try:
        result = skill_manager.validate_skill_setup(skill_id, lambda_function_name)
        return SkillValidationResult(**result)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/skills/{skill_id}/export")
async def export_skill_configuration(skill_id: str, format: str = "json") -> str:
    """Export skill configuration in various formats (JSON, YAML)."""
    try:
        return skill_manager.export_configuration(skill_id, format)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/setup-wizard/steps")
async def get_alexa_setup_steps() -> list[dict[str, Any]]:
    """
    Get the Alexa skill setup wizard steps.

    This provides a structured flow for the interactive setup process.
    """
    return [
        {
            "step": 1,
            "title": "Skill Basic Information",
            "description": "Configure skill name, description, and locales",
            "fields": [
                {
                    "name": "skill_name",
                    "type": "text",
                    "required": True,
                    "label": "Skill Name",
                },
                {
                    "name": "description",
                    "type": "textarea",
                    "required": True,
                    "label": "Skill Description",
                },
                {
                    "name": "supported_locales",
                    "type": "multiselect",
                    "required": False,
                    "label": "Supported Languages",
                    "options": [
                        "en-US",
                        "en-GB",
                        "en-CA",
                        "en-AU",
                        "en-IN",
                        "de-DE",
                        "es-ES",
                        "fr-FR",
                        "it-IT",
                        "ja-JP",
                    ],
                },
            ],
            "completed": False,
        },
        {
            "step": 2,
            "title": "Lambda Function Configuration",
            "description": "Configure AWS Lambda function for the skill endpoint",
            "fields": [
                {
                    "name": "lambda_function_name",
                    "type": "text",
                    "required": True,
                    "label": "Lambda Function Name",
                },
                {
                    "name": "aws_region",
                    "type": "select",
                    "required": True,
                    "label": "AWS Region",
                    "options": [
                        "us-east-1",
                        "us-west-2",
                        "eu-west-1",
                        "ap-northeast-1",
                    ],
                },
            ],
            "completed": False,
        },
        {
            "step": 3,
            "title": "Account Linking Setup",
            "description": "Configure OAuth settings for Home Assistant integration",
            "fields": [
                {
                    "name": "home_assistant_url",
                    "type": "url",
                    "required": True,
                    "label": "Home Assistant URL",
                },
                {
                    "name": "oauth_client_id",
                    "type": "text",
                    "required": True,
                    "label": "OAuth Client ID",
                },
                {
                    "name": "enable_cloudflare",
                    "type": "checkbox",
                    "required": False,
                    "label": "Enable CloudFlare Security",
                },
                {
                    "name": "cloudflare_domain",
                    "type": "text",
                    "required": False,
                    "label": "CloudFlare Domain",
                    "conditional": {"field": "enable_cloudflare", "value": True},
                },
            ],
            "completed": False,
        },
        {
            "step": 4,
            "title": "Amazon Developer Console",
            "description": "Complete setup in Amazon Developer Console",
            "type": "instructions",
            "completed": False,
        },
        {
            "step": 5,
            "title": "Testing & Validation",
            "description": "Test the skill and validate configuration",
            "type": "validation",
            "completed": False,
        },
    ]


@router.get("/regions/compatibility")
async def check_alexa_region_compatibility() -> dict[str, Any]:
    """
    Check Alexa Smart Home compatibility for different AWS regions.

    Returns supported regions and their language capabilities.
    """
    return {
        "supported_regions": {
            "us-east-1": {
                "name": "US East (N. Virginia)",
                "languages": [
                    "English (US)",
                    "English (CA)",
                    "Portuguese (BR)",
                    "Spanish (ES)",
                    "Spanish (MX)",
                    "Spanish (US)",
                ],
                "recommended": True,
                "description": "Primary region for North American Alexa skills",
            },
            "eu-west-1": {
                "name": "Europe (Ireland)",
                "languages": [
                    "English (UK)",
                    "English (IN)",
                    "German (DE)",
                    "Spanish (ES)",
                    "French (FR)",
                    "Italian (IT)",
                ],
                "recommended": True,
                "description": "Primary region for European Alexa skills",
            },
            "us-west-2": {
                "name": "US West (Oregon)",
                "languages": ["Japanese (JP)", "English (AU)"],
                "recommended": False,
                "description": "Secondary region for specific languages",
            },
            "ap-northeast-1": {
                "name": "Asia Pacific (Tokyo)",
                "languages": ["Japanese (JP)"],
                "recommended": False,
                "description": "Japan-specific Alexa skills",
            },
        },
        "recommendations": [
            "Use us-east-1 for English (US) skills",
            "Use eu-west-1 for European languages",
            "Ensure your AWS Lambda function is in the same region as your skill",
            "Account linking OAuth endpoints must be accessible from Alexa services",
        ],
    }


@router.get("/templates/manifest")
async def get_skill_manifest_template() -> dict[str, Any]:
    """Get a template for Alexa Skill manifest configuration."""
    return {
        "manifest": {
            "publishingInformation": {
                "locales": {
                    "en-US": {
                        "name": "{{SKILL_NAME}}",
                        "summary": "{{SKILL_DESCRIPTION}}",
                        "description": "{{SKILL_DESCRIPTION}}",
                        "examplePhrases": [
                            "Alexa, turn on the lights",
                            "Alexa, set the temperature to 72 degrees",
                            "Alexa, dim the bedroom lights",
                        ],
                        "keywords": ["smart home", "home assistant", "automation"],
                    }
                },
                "isAvailableWorldwide": False,
                "testingInstructions": "Test with Home Assistant integration",
                "category": "SMART_HOME",
                "distributionCountries": ["US", "CA", "GB", "AU"],
            },
            "apis": {
                "smartHome": {
                    "endpoint": {"uri": "{{LAMBDA_ARN}}"},
                    "protocolVersion": "3",
                }
            },
            "manifestVersion": "1.0",
            "permissions": [{"name": "alexa::devices:all:notifications:write"}],
            "accountLinking": {
                "type": "AUTH_CODE",
                "authorizationUrl": "{{OAUTH_AUTHORIZATION_URL}}",
                "accessTokenUrl": "{{OAUTH_TOKEN_URL}}",
                "clientId": "{{OAUTH_CLIENT_ID}}",
                "scopes": ["smart_home"],
                "skipOnEnablement": False,
            },
        }
    }


@router.post("/skills/{skill_id}/console-automation", response_model=ConsoleAutomationResponse)
async def create_console_automation_guide(
    skill_id: str, request: ConsoleAutomationRequest
) -> ConsoleAutomationResponse:
    """
    Create Amazon Developer Console automation guide for a skill.

    This endpoint provides comprehensive automation assistance including:
    - Step-by-step manual instructions with exact values
    - Browser automation scripts (Selenium/Playwright)
    - Validation checklists for setup verification
    - Troubleshooting guidance
    """
    try:
        # Set the skill_id from the path parameter
        request.skill_id = skill_id
        return console_automator.create_automation_guide(request)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create automation guide: {str(e)}",
        ) from e


@router.get("/skills/{skill_id}/browser-automation-script")
async def get_browser_automation_script(skill_id: str) -> dict[str, str]:
    """
    Get Selenium/Playwright browser automation script for skill setup.

    Returns a complete Python script that can automate the Amazon Developer
    Console setup process using browser automation tools.
    """
    try:
        if skill_id not in skill_manager.skills:
            raise ValidationError(f"Skill not found: {skill_id}")

        skill_manifest = skill_manager.skills[skill_id]
        script_content = console_automator._generate_browser_automation_script(skill_manifest)

        return {
            "skill_id": skill_id,
            "script_type": "selenium",
            "script_content": script_content,
            "requirements": "selenium, webdriver-manager",
            "usage_instructions": "Save as .py file and run: python amazon_console_automation.py",
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/skills/{skill_id}/validate-console-setup")
async def validate_console_setup(skill_id: str) -> dict[str, Any]:
    """
    Validate that a skill is properly configured in Amazon Developer Console.

    Provides validation checklist and recommendations for verifying
    the skill setup without requiring direct API access.
    """
    try:
        return console_automator.validate_skill_setup(skill_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/skills/{skill_id}/export-manifest")
async def export_skill_manifest(skill_id: str) -> dict[str, Any]:
    """
    Export skill manifest for import into Amazon Developer Console.

    Generates a complete skill manifest that can be imported directly
    into the Amazon Developer Console.
    """
    try:
        return console_automator.generate_manifest_export(skill_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/console-automation/methods")
async def get_automation_methods() -> dict[str, Any]:
    """Get available console automation methods and their descriptions."""
    return {
        "automation_methods": {
            "guided_manual": {
                "name": "Guided Manual Setup",
                "description": "Step-by-step instructions with exact values to enter",
                "pros": [
                    "No additional software required",
                    "Works with any browser",
                    "Easy to follow and understand",
                    "Full control over each step",
                ],
                "cons": [
                    "Manual data entry required",
                    "More time-consuming",
                    "Prone to human error",
                ],
                "estimated_time": 25,
                "difficulty": "beginner",
            },
            "browser_automation": {
                "name": "Browser Automation",
                "description": "Selenium script to automate form filling",
                "pros": [
                    "Automated form filling",
                    "Faster execution",
                    "Reduced human error",
                    "Consistent results",
                ],
                "cons": [
                    "Requires Python and Selenium",
                    "May break with console updates",
                    "Still requires manual OAuth secret entry",
                ],
                "estimated_time": 10,
                "difficulty": "intermediate",
            },
            "manifest_import": {
                "name": "Manifest Import",
                "description": "Generate manifest for console import",
                "pros": [
                    "Quick skill creation",
                    "Accurate configuration",
                    "No form filling required",
                ],
                "cons": [
                    "Limited to manifest import only",
                    "Still requires manual account linking setup",
                    "Not all settings available via import",
                ],
                "estimated_time": 5,
                "difficulty": "beginner",
            },
            "hybrid": {
                "name": "Hybrid Approach",
                "description": "Combination of automation and manual steps",
                "pros": [
                    "Best of both approaches",
                    "Automation where possible",
                    "Manual control for critical steps",
                ],
                "cons": [
                    "More complex workflow",
                    "Requires understanding of both methods",
                ],
                "estimated_time": 15,
                "difficulty": "intermediate",
            },
        },
        "recommendations": {
            "first_time_users": "guided_manual",
            "experienced_users": "browser_automation",
            "quick_setup": "manifest_import",
            "production_deployment": "hybrid",
        },
    }
