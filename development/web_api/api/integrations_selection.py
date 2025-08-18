"""
🎯 ENHANCED INTEGRATION SELECTION API

API endpoints for the interactive integration selection system.
Extends the existing integrations API with advanced selection, dependency resolution,
and configuration guidance capabilities.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from ...integrations.selection_manager import (
    IntegrationSelectionRequest,
    IntegrationSelectionResponse,
    IntegrationType,
    InteractiveIntegrationSelector,
)
from ...utils import ValidationError

router = APIRouter(prefix="/integrations/selection", tags=["integration-selection"])

# Global integration selector instance
selector = InteractiveIntegrationSelector()


@router.get("/available")
async def get_available_integrations() -> list[dict[str, Any]]:
    """Get all available integrations with their details and requirements."""
    integrations = selector.get_available_integrations()

    return [
        {
            "integration_type": integration.integration_type,
            "name": integration.name,
            "description": integration.description,
            "long_description": integration.long_description,
            "requirements": {
                "aws_services": integration.requirements.aws_services,
                "home_assistant_version": (
                    integration.requirements.home_assistant_version
                ),
                "requires_domain": integration.requirements.requires_domain,
                "requires_oauth": integration.requirements.requires_oauth,
                "estimated_setup_time": integration.requirements.estimated_setup_time,
                "complexity_level": integration.requirements.complexity_level,
            },
            "dependencies": list(integration.dependencies),
            "conflicts": list(integration.conflicts),
            "optional_enhancements": list(integration.optional_enhancements),
            "lambda_functions": integration.lambda_functions,
            "status": integration.status,
        }
        for integration in integrations
    ]


@router.post("/select", response_model=IntegrationSelectionResponse)
async def select_integrations(
    request: IntegrationSelectionRequest,
) -> IntegrationSelectionResponse:
    """
    Process integration selection with dependency resolution and conflict detection.

    This endpoint handles the complete integration selection workflow:
    - Automatic dependency resolution
    - Conflict detection and reporting
    - Setup time estimation
    - Configuration step generation
    """
    try:
        return selector.select_integrations(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/suggestions")
async def get_integration_suggestions(
    primary_goal: str = "alexa",
) -> list[dict[str, Any]]:
    """
    Get suggested integration combinations based on user goals.

    Args:
        primary_goal: Primary integration goal (alexa, ios, mobile, complete)

    Returns:
        List of suggested integration combinations with pros/cons
    """
    try:
        return selector.suggest_integration_combinations(primary_goal)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}",
        ) from e


@router.get("/details/{integration_type}")
async def get_integration_details(integration_type: IntegrationType) -> dict[str, Any]:
    """Get detailed information about a specific integration."""
    try:
        integration = selector.get_integration_details(integration_type)

        return {
            "integration_type": integration.integration_type,
            "name": integration.name,
            "description": integration.description,
            "long_description": integration.long_description,
            "requirements": {
                "aws_services": integration.requirements.aws_services,
                "home_assistant_version": (
                    integration.requirements.home_assistant_version
                ),
                "requires_domain": integration.requirements.requires_domain,
                "requires_oauth": integration.requirements.requires_oauth,
                "estimated_setup_time": integration.requirements.estimated_setup_time,
                "complexity_level": integration.requirements.complexity_level,
            },
            "dependencies": list(integration.dependencies),
            "conflicts": list(integration.conflicts),
            "optional_enhancements": list(integration.optional_enhancements),
            "lambda_functions": integration.lambda_functions,
            "status": integration.status,
            "configuration": integration.configuration,
        }
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_type}",
        ) from e


@router.get("/compatibility-matrix")
async def get_compatibility_matrix() -> dict[str, Any]:
    """
    Get compatibility matrix showing conflicts and dependencies between integrations.

    Returns a matrix format useful for building interactive selection UIs.
    """
    integrations = selector.get_available_integrations()
    matrix = {}

    for integration in integrations:
        integration_type = integration.integration_type
        matrix[integration_type] = {
            "name": integration.name,
            "dependencies": list(integration.dependencies),
            "conflicts": list(integration.conflicts),
            "optional_enhancements": list(integration.optional_enhancements),
            "complexity": integration.requirements.complexity_level,
            "estimated_time": integration.requirements.estimated_setup_time,
        }

    return {
        "matrix": matrix,
        "legend": {
            "dependencies": "Required integrations that will be automatically included",
            "conflicts": "Incompatible integrations that cannot be selected together",
            "optional_enhancements": "Recommended additional integrations",
            "complexity": "Setup complexity level (beginner/intermediate/advanced)",
            "estimated_time": "Estimated setup time in minutes",
        },
    }


@router.get("/wizard/steps")
async def get_selection_wizard_steps() -> list[dict[str, Any]]:
    """
    Get the integration selection wizard steps.

    This provides a structured flow for the interactive selection process.
    """
    return [
        {
            "step": 1,
            "title": "Define Your Goals",
            "description": (
                "What do you want to achieve with Home Assistant external "
                "integrations?"
            ),
            "type": "goal_selection",
            "options": [
                {
                    "value": "alexa",
                    "label": "Voice Control with Alexa",
                    "description": (
                        "Enable Alexa Smart Home voice commands for your devices"
                    ),
                    "icon": "🗣️",
                },
                {
                    "value": "ios",
                    "label": "iOS Companion Access",
                    "description": "Secure external access for Home Assistant iOS app",
                    "icon": "📱",
                },
                {
                    "value": "security",
                    "label": "Enhanced Security",
                    "description": "Add CloudFlare Access security layers",
                    "icon": "🔒",
                },
                {
                    "value": "performance",
                    "label": "Performance Optimization",
                    "description": "Optimize for fastest response times",
                    "icon": "⚡",
                },
                {
                    "value": "complete",
                    "label": "Complete Integration Suite",
                    "description": "All features with maximum capabilities",
                    "icon": "🚀",
                },
            ],
        },
        {
            "step": 2,
            "title": "Review Suggestions",
            "description": (
                "Based on your goals, here are the recommended integration "
                "combinations"
            ),
            "type": "suggestion_review",
            "dynamic_content": True,
        },
        {
            "step": 3,
            "title": "Customize Selection",
            "description": (
                "Fine-tune your integration selection and resolve any conflicts"
            ),
            "type": "integration_selection",
            "features": [
                "dependency_resolution",
                "conflict_detection",
                "complexity_analysis",
                "time_estimation",
            ],
        },
        {
            "step": 4,
            "title": "Configuration Preview",
            "description": (
                "Review the setup steps and requirements for your selected "
                "integrations"
            ),
            "type": "configuration_preview",
            "includes": [
                "aws_services_required",
                "lambda_functions_needed",
                "domain_requirements",
                "estimated_total_time",
                "complexity_assessment",
            ],
        },
        {
            "step": 5,
            "title": "Begin Setup",
            "description": "Start the automated deployment and configuration process",
            "type": "setup_initiation",
            "actions": [
                "validate_prerequisites",
                "initialize_configuration",
                "begin_deployment",
            ],
        },
    ]
