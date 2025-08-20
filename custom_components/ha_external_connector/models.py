"""Shared models for HA External Connector."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(UTC)


class SecurityLevel(str, Enum):
    """Security severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityStatus(str, Enum):
    """Security check status."""

    PASSED = "passed"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    ERROR = "error"


class ValidationResult(BaseModel):
    """Result of a validation operation."""

    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class SecurityCheck(BaseModel):
    """Individual security check definition."""

    check_id: str = Field(..., description="Unique identifier for the check")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Security category")
    level: SecurityLevel = Field(..., description="Security severity level")
    enabled: bool = Field(True, description="Whether check is enabled")


class SecurityCheckResult(BaseModel):
    """Result of a security check."""

    check: SecurityCheck
    status: SecurityStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(
        default_factory=list, description="Security recommendations"
    )
    execution_time: float = Field(0.0, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=utc_now)


class SecurityPolicy(BaseModel):
    """Security policy configuration."""

    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    checks: list[SecurityCheck] = Field(
        default_factory=list, description="Security checks"
    )
    enabled_checks: list[str] = Field(
        default_factory=list, description="List of enabled check IDs"
    )
    enforcement_level: SecurityLevel = Field(
        SecurityLevel.MEDIUM, description="Policy enforcement level"
    )
    enabled: bool = Field(True, description="Whether policy is enabled")


class ComplianceRule(BaseModel):
    """Compliance rule definition."""

    rule_id: str = Field(..., description="Unique rule identifier")
    framework: str = Field(
        ..., description="Compliance framework (e.g., SOC2, ISO27001)"
    )
    title: str = Field(..., description="Rule title")
    description: str = Field(..., description="Rule description")
    severity: SecurityLevel = Field(..., description="Rule severity level")
    required_checks: list[str] = Field(
        default_factory=list, description="Required security check IDs"
    )
    validation_checks: list[str] = Field(
        default_factory=list, description="Validation check IDs for compliance"
    )


class IntegrationHealth(BaseModel):
    """Health status of an integration."""

    integration_name: str
    healthy: bool
    last_check: datetime = Field(default_factory=utc_now)
    services_status: dict[str, bool] = Field(default_factory=dict)
    error_message: str | None = None


class DeploymentStatus(str, Enum):
    """Deployment status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class DeploymentResult(BaseModel):
    """Result of a deployment operation."""

    success: bool
    status: DeploymentStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    duration_seconds: float | None = None
