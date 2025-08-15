"""Amazon Developer Console automation package.

This package provides comprehensive automation capabilities for Amazon Developer Console
operations through multiple approaches: SMAPI API integration, browser automation,
and guided manual workflows.
"""

from .coordinator import AmazonDeveloperConsoleAutomator
from .models import (
    AutomationMethod,
    ConsoleAutomationRequest,
    ConsoleAutomationResponse,
    ConsoleFormField,
    ConsoleSetupStep,
    ConsoleSetupStepDetails,
    SkillCertificationResult,
    SkillDeploymentStage,
    SkillValidationResult,
    SMAPIAuthStatus,
    SMAPICredentials,
    SMAPIErrorCode,
)
from .smapi_client import AmazonSMAPIClient

__all__ = [
    "AmazonDeveloperConsoleAutomator",
    "AmazonSMAPIClient",
    "AutomationMethod",
    "ConsoleAutomationRequest",
    "ConsoleAutomationResponse",
    "ConsoleFormField",
    "ConsoleSetupStep",
    "ConsoleSetupStepDetails",
    "SMAPIAuthStatus",
    "SMAPICredentials",
    "SMAPIErrorCode",
    "SkillCertificationResult",
    "SkillDeploymentStage",
    "SkillValidationResult",
]
