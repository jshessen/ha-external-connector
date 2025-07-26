"""
Security Models

Data models for security validation, compliance checking, and reporting.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC datetime with timezone awareness"""
    return datetime.now(UTC)


class SecurityLevel(str, Enum):
    """Security severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityStatus(str, Enum):
    """Security check status"""

    PASSED = "passed"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    ERROR = "error"


class SecurityCheck(BaseModel):
    """Individual security check definition"""

    check_id: str = Field(..., description="Unique identifier for the check")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Security category")
    level: SecurityLevel = Field(..., description="Security severity level")
    enabled: bool = Field(True, description="Whether check is enabled")
    required_permissions: list[str] = Field(
        default_factory=list, description="Required AWS permissions"
    )


class SecurityCheckResult(BaseModel):
    """Result of a security check"""

    check: SecurityCheck = Field(..., description="The security check")
    status: SecurityStatus = Field(..., description="Check result status")
    message: str = Field(..., description="Result message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Remediation recommendations"
    )
    execution_time: float = Field(0.0, description="Check execution time in seconds")
    timestamp: datetime = Field(
        default_factory=_utc_now, description="Check execution timestamp"
    )


class SecurityPolicy(BaseModel):
    """Security policy configuration"""

    policy_id: str = Field(..., description="Policy identifier")
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    version: str = Field("1.0", description="Policy version")
    enabled_checks: list[str] = Field(
        default_factory=list, description="List of enabled check IDs"
    )
    enforcement_level: SecurityLevel = Field(
        SecurityLevel.MEDIUM, description="Enforcement level"
    )
    exceptions: dict[str, list[str]] = Field(
        default_factory=dict, description="Policy exceptions by resource type"
    )


class ComplianceRule(BaseModel):
    """Compliance rule definition"""

    rule_id: str = Field(..., description="Rule identifier")
    framework: str = Field(..., description="Compliance framework (e.g., SOC2)")
    control_id: str = Field(..., description="Control identifier")
    requirement: str = Field(..., description="Compliance requirement")
    validation_checks: list[str] = Field(
        ..., description="Security checks that validate this rule"
    )
    mandatory: bool = Field(True, description="Whether rule is mandatory")


class SecurityReport(BaseModel):
    """Comprehensive security report"""

    report_id: str = Field(..., description="Report identifier")
    timestamp: datetime = Field(
        default_factory=_utc_now, description="Report generation time"
    )
    scope: dict[str, Any] = Field(
        ..., description="Report scope (resources, regions, etc.)"
    )
    policy: SecurityPolicy = Field(..., description="Applied security policy")
    check_results: list[SecurityCheckResult] = Field(
        ..., description="Individual check results"
    )
    summary: dict[str, Any] = Field(
        default_factory=dict, description="Report summary statistics"
    )
    compliance_status: dict[str, Any] = Field(
        default_factory=dict, description="Compliance framework status"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Overall recommendations"
    )

    @property
    def total_checks(self) -> int:
        """Total number of checks performed"""
        return len(self.check_results)

    @property
    def passed_checks(self) -> int:
        """Number of checks that passed"""
        return len([r for r in self.check_results if r.status == SecurityStatus.PASSED])

    @property
    def failed_checks(self) -> int:
        """Number of checks that failed"""
        return len([r for r in self.check_results if r.status == SecurityStatus.FAIL])

    @property
    def critical_issues(self) -> int:
        """Number of critical security issues"""
        return len(
            [
                r
                for r in self.check_results
                if r.status == SecurityStatus.FAIL
                and r.check.level == SecurityLevel.CRITICAL
            ]
        )

    @property
    def overall_status(self) -> SecurityStatus:
        """Overall security status"""
        if self.critical_issues > 0:
            return SecurityStatus.FAIL
        if self.failed_checks > 0:
            return SecurityStatus.WARNING
        return SecurityStatus.PASSED
