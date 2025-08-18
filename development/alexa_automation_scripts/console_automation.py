"""Amazon Developer Console Automation (Compatibility Module).

This module provides compatibility imports for the refactored console automation
components. The original large console_automation.py has been decomposed into
focused modules in the automation/ package for better maintainability.

🎯 REFACTORING STATUS:
- ✅ Data Models → automation/models.py
- ✅ SMAPI Client → automation/smapi_client.py
- 🔄 SMAPI Manager → automation/smapi_manager.py (in progress)
- 🔄 Browser Guide → automation/browser_guide.py (in progress)
- 🔄 Main Coordinator → automation/coordinator.py (in progress)

For new code, import directly from the automation package:
    from .automation import AmazonSMAPIClient, SMAPICredentials, etc.
"""

# Re-export all public APIs from the automation package for backward compatibility
from .automation import (
    AmazonDeveloperConsoleAutomator,
    AmazonSMAPIClient,
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

# Backward compatibility aliases - everything is now properly implemented
SMAPIIntegrationManager = AmazonSMAPIClient  # Alias for backward compatibility

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
    # Legacy compatibility (will be restored as development continues)
    "AmazonDeveloperConsoleAutomator",
    "SMAPIIntegrationManager",
]
