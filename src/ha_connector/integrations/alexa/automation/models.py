"""Data models and enums for Amazon Developer Console automation.

This module contains all the data structures, enums, and Pydantic models
used throughout the console automation system.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


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
    INVALID_TOKEN = "INVALID_ACCESS_TOKEN"  # nosec B105
    TOKEN_EXPIRED = "ACCESS_TOKEN_EXPIRED"  # nosec B105
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"

    # Skill Management Errors
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_ALREADY_EXISTS = "SKILL_ALREADY_EXISTS"
    INVALID_SKILL_DATA = "INVALID_SKILL_DATA"
    SKILL_IN_REVIEW = "SKILL_IN_REVIEW"

    # Validation Errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    MANIFEST_INVALID = "MANIFEST_INVALID"
    ENDPOINT_UNREACHABLE = "ENDPOINT_UNREACHABLE"

    # Rate Limiting
    RATE_LIMITED = "THROTTLED_REQUEST"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Server Errors
    INTERNAL_ERROR = "INTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "REQUEST_TIMEOUT"


@dataclass
class SMAPICredentials:
    """Amazon SMAPI OAuth 2.0 credentials container.

    Manages OAuth tokens, refresh tokens, and authentication state for
    secure communication with Amazon's Skill Management API.
    """

    client_id: str
    client_secret: str
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None
    refresh_expires_at: int | None = None
    scope: str = "alexa::ask:skills:readwrite alexa::ask:models:readwrite"

    def is_access_token_valid(self) -> bool:
        """Check if access token is valid and not expired."""
        if not self.access_token or not self.expires_at:
            return False
        return time.time() < self.expires_at

    def is_refresh_token_valid(self) -> bool:
        """Check if refresh token is valid and not expired."""
        if not self.refresh_token or not self.refresh_expires_at:
            return False
        return time.time() < self.refresh_expires_at


class ConsoleFormField(BaseModel):
    """Configuration for Amazon Developer Console form field automation.

    Defines field selectors, input types, and validation patterns for
    browser automation and guided setup workflows.
    """

    field_name: str = Field(description="Logical name for the form field")
    selector: str = Field(description="CSS/XPath selector for the field")
    field_type: str = Field(description="Field type: text, select, checkbox, radio")
    required: bool = Field(default=True, description="Whether field is required")
    validation_pattern: str | None = Field(
        default=None, description="Regex pattern for field validation"
    )
    placeholder_text: str | None = Field(
        default=None, description="Placeholder text for the field"
    )
    help_text: str | None = Field(
        default=None, description="Help text for field guidance"
    )


class ConsoleSetupStepDetails(BaseModel):
    """Detailed configuration for Amazon Developer Console setup steps.

    Provides comprehensive guidance, automation scripts, and validation
    criteria for each step in the skill deployment workflow.
    """

    step: ConsoleSetupStep = Field(description="Setup step identifier")
    form_fields: Annotated[
        list[ConsoleFormField],
        Field(default_factory=list, description="Form fields configuration"),
    ]
    validation_selectors: list[str] = Field(
        default_factory=list, description="CSS selectors for validation"
    )
    success_indicators: list[str] = Field(
        default_factory=list, description="Success indicators"
    )
    browser_script: str | None = Field(
        default=None, description="Browser automation script"
    )


class SkillValidationResult(BaseModel):
    """Result container for Amazon Alexa skill validation operations.

    Encapsulates validation status, error reporting, and remediation guidance
    for comprehensive skill quality assurance.
    """

    validation_id: str = Field(description="Unique validation operation identifier")
    status: str = Field(
        description="Current validation status (IN_PROGRESS, SUCCESSFUL, FAILED)"
    )
    result: dict[str, Any] | None = Field(
        default=None, description="Detailed validation results and findings"
    )
    error_count: int = Field(default=0, description="Number of validation errors found")
    warning_count: int = Field(
        default=0, description="Number of validation warnings found"
    )
    started_at: str | None = Field(
        default=None, description="Validation start timestamp"
    )
    completed_at: str | None = Field(
        default=None, description="Validation completion timestamp"
    )


class SkillCertificationResult(BaseModel):
    """Result container for Amazon Alexa skill certification status.

    Tracks certification workflow progress, approval status, and
    publication readiness for marketplace distribution.
    """

    certification_id: str | None = Field(
        default=None, description="Unique certification process identifier"
    )
    status: str = Field(
        description="Certification status (IN_PROGRESS, CERTIFIED, FAILED, WITHDRAWN)"
    )
    estimated_completion: str | None = Field(
        default=None, description="Estimated certification completion date"
    )
    review_notes: list[str] = Field(
        default_factory=list, description="Certification review feedback and notes"
    )
    distribution_countries: list[str] = Field(
        default_factory=list, description="Countries approved for skill distribution"
    )
    submitted_at: str | None = Field(
        default=None, description="Certification submission timestamp"
    )


class ConsoleAutomationRequest(BaseModel):
    """Request configuration for Amazon Developer Console automation operations.

    Encapsulates automation preferences, skill specifications, and deployment
    requirements for streamlined console operations.
    """

    automation_method: AutomationMethod = Field(
        default=AutomationMethod.SMAPI_AUTOMATION,
        description="Preferred automation approach for console operations",
    )
    skill_manifest: dict[str, Any] = Field(
        description="Complete Alexa skill manifest and configuration"
    )
    deployment_stage: SkillDeploymentStage = Field(
        default=SkillDeploymentStage.DEVELOPMENT,
        description="Target deployment stage for skill operations",
    )
    enable_validation: bool = Field(
        default=True, description="Enable automated skill validation"
    )
    enable_certification: bool = Field(
        default=False, description="Enable automated certification submission"
    )
    browser_automation_config: dict[str, Any] = Field(
        default_factory=dict, description="Browser automation configuration options"
    )


class ManualStepModel(BaseModel):
    """Pydantic model for manual step instructions in automation responses."""

    step_id: str
    description: str
    url: str
    additional_info: dict[str, Any] = Field(default_factory=dict)


class ConsoleAutomationResponse(BaseModel):
    """Response container for Amazon Developer Console automation results.

    Provides comprehensive feedback, success indicators, and troubleshooting
    guidance for console automation operations.
    """

    success: bool = Field(description="Overall automation operation success status")
    skill_id: str | None = Field(default=None, description="Created/updated skill ID")
    automation_method_used: AutomationMethod = Field(
        description="Actual automation method employed"
    )
    validation_results: Annotated[
        list[SkillValidationResult],
        Field(default_factory=list, description="Skill validation operation results"),
    ]
    manual_steps: Annotated[
        list[ManualStepModel],
        Field(
            default_factory=list,
            description="Manual completion steps (for guided automation)",
        ),
    ]
    browser_script: str | None = Field(
        default=None, description="Generated browser automation script (if applicable)"
    )
    error_messages: list[str] = Field(
        default_factory=list, description="Error messages and troubleshooting guidance"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for optimization and best practices",
    )
