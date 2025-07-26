"""
Security Validation Framework

This module provides comprehensive security validation for AWS Lambda deployments,
configuration validation, and compliance checking for the Home Assistant
External Connector.

Enhanced beyond the bash version with detailed reporting, policy validation,
and integrated security scanning capabilities.
"""

from .lambda_validator import LambdaSecurityValidator
from .models import (
    ComplianceRule,
    SecurityCheck,
    SecurityCheckResult,
    SecurityLevel,
    SecurityPolicy,
    SecurityReport,
    SecurityStatus,
)
from .policy_validator import (
    ComplianceChecker,
    SecurityPolicyValidator,
    SecurityReporter,
)

__all__ = [
    # Core Models
    "SecurityCheck",
    "SecurityCheckResult",
    "SecurityPolicy",
    "SecurityReport",
    "ComplianceRule",
    "SecurityLevel",
    "SecurityStatus",
    # Validators
    "LambdaSecurityValidator",
    "SecurityPolicyValidator",
    "ComplianceChecker",
    "SecurityReporter",
]
