"""
Security Policy Validator

Policy validation and compliance checking for security configurations.
"""

import logging
from typing import Any

from .models import (
    ComplianceRule,
    SecurityCheck,
    SecurityCheckResult,
    SecurityLevel,
    SecurityPolicy,
    SecurityStatus,
)

logger = logging.getLogger(__name__)


class SecurityPolicyValidator:
    """Validates security policies and configurations"""

    def __init__(self) -> None:
        """Initialize the security policy validator"""
        self.default_policies = self._load_default_policies()

    def validate_policy(self, policy: SecurityPolicy) -> list[SecurityCheckResult]:
        """Validate a security policy configuration"""
        results: list[SecurityCheckResult] = []

        # Check policy structure
        results.extend(self._check_policy_structure(policy))

        # Check policy completeness
        results.extend(self._check_policy_completeness(policy))

        # Check enforcement levels
        results.extend(self._check_enforcement_levels(policy))

        return results

    def _check_policy_structure(
        self, policy: SecurityPolicy
    ) -> list[SecurityCheckResult]:
        """Check basic policy structure and required fields"""
        check = SecurityCheck(
            check_id="policy_structure",
            name="Policy Structure Validation",
            description="Validate policy has required fields and structure",
            category="Policy Validation",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        issues: list[str] = []

        if not policy.policy_id:
            issues.append("Policy ID is required")
        if not policy.name:
            issues.append("Policy name is required")
        if not policy.description:
            issues.append("Policy description is required")
        if not policy.enabled_checks:
            issues.append("Policy must specify enabled checks")

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.FAIL,
                    message=f"Policy structure validation failed: {len(issues)} issues",
                    details={"issues": issues},
                    recommendations=[
                        "Provide all required policy fields",
                        "Ensure policy has meaningful description",
                        "Specify which security checks to enable",
                    ],
                    execution_time=0.1,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Policy structure is valid",
                execution_time=0.1,
            )
        ]

    def _check_policy_completeness(
        self, policy: SecurityPolicy
    ) -> list[SecurityCheckResult]:
        """Check if policy covers essential security areas"""
        check = SecurityCheck(
            check_id="policy_completeness",
            name="Policy Completeness Check",
            description="Ensure policy covers essential security categories",
            category="Policy Validation",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        essential_categories = {
            "Runtime Security",
            "Data Protection",
            "IAM Security",
            "Network Security",
        }

        # Get categories from the policy's enabled checks
        covered_categories: set[str] = set()
        for check_id in policy.enabled_checks:
            # This is a simplified mapping - in a real implementation,
            # you'd look up the actual check definitions
            if "runtime" in check_id.lower():
                covered_categories.add("Runtime Security")
            elif "env" in check_id.lower() or "data" in check_id.lower():
                covered_categories.add("Data Protection")
            elif "role" in check_id.lower() or "iam" in check_id.lower():
                covered_categories.add("IAM Security")
            elif "vpc" in check_id.lower() or "network" in check_id.lower():
                covered_categories.add("Network Security")

        missing_categories = essential_categories - covered_categories

        if missing_categories:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=(
                        f"Policy missing {len(missing_categories)} essential categories"
                    ),
                    details={"missing_categories": list(missing_categories)},
                    recommendations=[
                        "Add checks for missing security categories",
                        "Review security requirements for completeness",
                        "Consider enabling recommended security checks",
                    ],
                    execution_time=0.2,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Policy covers all essential security categories",
                execution_time=0.2,
            )
        ]

    def _check_enforcement_levels(
        self, policy: SecurityPolicy
    ) -> list[SecurityCheckResult]:
        """Check policy enforcement levels are appropriate"""
        check = SecurityCheck(
            check_id="policy_enforcement",
            name="Policy Enforcement Level Check",
            description="Validate policy enforcement levels are appropriate",
            category="Policy Validation",
            level=SecurityLevel.LOW,
            enabled=True,
        )

        if policy.enforcement_level == SecurityLevel.INFO:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="Policy enforcement level is set to INFO only",
                    recommendations=[
                        "Consider increasing enforcement level for production",
                        "Review security requirements",
                        "Enable stricter policy enforcement",
                    ],
                    execution_time=0.1,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"Policy enforcement level: {policy.enforcement_level}",
                execution_time=0.1,
            )
        ]

    def _load_default_policies(self) -> dict[str, SecurityPolicy]:
        """Load default security policies"""
        return {
            "default": SecurityPolicy(
                policy_id="default_security_policy",
                name="Default Security Policy",
                description="Standard security policy for Lambda functions",
                version="1.0",
                enabled_checks=[
                    "lambda_runtime_version",
                    "lambda_env_vars_security",
                    "lambda_execution_role",
                    "lambda_vpc_config",
                ],
                enforcement_level=SecurityLevel.MEDIUM,
            )
        }


class ComplianceChecker:
    """Checks compliance against security frameworks"""

    def __init__(self) -> None:
        """Initialize the compliance checker"""
        self.frameworks = self._load_compliance_frameworks()

    def check_compliance(
        self, framework: str, check_results: list[SecurityCheckResult]
    ) -> dict[str, Any]:
        """Check compliance against a specific framework"""
        if framework not in self.frameworks:
            return {"error": f"Unknown compliance framework: {framework}"}

        rules = self.frameworks[framework]
        compliance_status: dict[str, dict[str, Any]] = {}

        for rule in rules:
            rule_status = self._check_rule_compliance(rule, check_results)
            compliance_status[rule.rule_id] = rule_status

        # Count compliant rules with proper type checking
        compliant_count = 0
        for status_dict in compliance_status.values():
            compliant_value = status_dict.get("compliant")
            if compliant_value is True:
                compliant_count += 1

        return {
            "framework": framework,
            "total_rules": len(rules),
            "compliant_rules": compliant_count,
            "rule_status": compliance_status,
        }

    def _check_rule_compliance(
        self, rule: ComplianceRule, check_results: list[SecurityCheckResult]
    ) -> dict[str, Any]:
        """Check if a specific compliance rule is satisfied"""
        relevant_results = [
            result
            for result in check_results
            if result.check.check_id in rule.validation_checks
        ]

        if not relevant_results:
            return {
                "compliant": False,
                "reason": "No validation checks performed for this rule",
                "status": "not_checked",
            }

        # Rule is compliant if all relevant checks pass
        failed_checks = [
            result
            for result in relevant_results
            if result.status == SecurityStatus.FAIL
        ]

        if failed_checks:
            return {
                "compliant": False,
                "reason": f"Failed checks: {[r.check.name for r in failed_checks]}",
                "status": "non_compliant",
                "failed_checks": len(failed_checks),
            }

        return {
            "compliant": True,
            "reason": "All validation checks passed",
            "status": "compliant",
            "checked_items": len(relevant_results),
        }

    def _load_compliance_frameworks(self) -> dict[str, list[ComplianceRule]]:
        """Load compliance framework definitions"""
        return {
            "soc2": [
                ComplianceRule(
                    rule_id="soc2_cc6_1",
                    framework="SOC2",
                    control_id="CC6.1",
                    requirement="System uses encryption to protect data",
                    validation_checks=["lambda_env_vars_security"],
                    mandatory=True,
                ),
                ComplianceRule(
                    rule_id="soc2_cc6_2",
                    framework="SOC2",
                    control_id="CC6.2",
                    requirement="System uses secure communication protocols",
                    validation_checks=["lambda_vpc_config"],
                    mandatory=True,
                ),
            ],
            "aws_well_architected": [
                ComplianceRule(
                    rule_id="wa_sec_01",
                    framework="AWS Well-Architected",
                    control_id="SEC.01",
                    requirement="Implement strong identity foundation",
                    validation_checks=["lambda_execution_role"],
                    mandatory=True,
                ),
                ComplianceRule(
                    rule_id="wa_sec_02",
                    framework="AWS Well-Architected",
                    control_id="SEC.02",
                    requirement="Apply security at all layers",
                    validation_checks=[
                        "lambda_runtime_version",
                        "lambda_vpc_config",
                        "lambda_env_vars_security",
                    ],
                    mandatory=True,
                ),
            ],
        }


class SecurityReporter:
    """Generates comprehensive security reports"""

    def __init__(self) -> None:
        """Initialize the security reporter"""

    def generate_summary_report(
        self, check_results: list[SecurityCheckResult]
    ) -> dict[str, Any]:
        """Generate a summary security report"""
        if not check_results:
            return {"error": "No check results provided"}

        total_checks = len(check_results)
        passed_checks = len(
            [r for r in check_results if r.status == SecurityStatus.PASSED]
        )
        failed_checks = len(
            [r for r in check_results if r.status == SecurityStatus.FAIL]
        )
        warning_checks = len(
            [r for r in check_results if r.status == SecurityStatus.WARNING]
        )

        # Count by severity
        critical_issues = len(
            [
                r
                for r in check_results
                if r.status == SecurityStatus.FAIL
                and r.check.level == SecurityLevel.CRITICAL
            ]
        )
        high_issues = len(
            [
                r
                for r in check_results
                if r.status == SecurityStatus.FAIL
                and r.check.level == SecurityLevel.HIGH
            ]
        )

        return {
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "warnings": warning_checks,
                "pass_rate": round((passed_checks / total_checks) * 100, 2),
            },
            "severity_breakdown": {
                "critical": critical_issues,
                "high": high_issues,
                "total_failures": failed_checks,
            },
            "overall_status": self._determine_overall_status(check_results),
            "recommendations": self._generate_recommendations(check_results),
        }

    def _determine_overall_status(
        self, check_results: list[SecurityCheckResult]
    ) -> str:
        """Determine overall security status"""
        critical_failures = any(
            r.status == SecurityStatus.FAIL and r.check.level == SecurityLevel.CRITICAL
            for r in check_results
        )

        if critical_failures:
            return "CRITICAL"

        high_failures = any(
            r.status == SecurityStatus.FAIL and r.check.level == SecurityLevel.HIGH
            for r in check_results
        )

        if high_failures:
            return "HIGH_RISK"

        failures = any(r.status == SecurityStatus.FAIL for r in check_results)

        if failures:
            return "MEDIUM_RISK"

        warnings = any(r.status == SecurityStatus.WARNING for r in check_results)

        if warnings:
            return "LOW_RISK"

        return "SECURE"

    def _generate_recommendations(
        self, check_results: list[SecurityCheckResult]
    ) -> list[str]:
        """Generate top recommendations based on results"""
        failed_results = [r for r in check_results if r.status == SecurityStatus.FAIL]

        # Sort by severity (critical first)
        failed_results.sort(
            key=lambda x: {
                SecurityLevel.CRITICAL: 0,
                SecurityLevel.HIGH: 1,
                SecurityLevel.MEDIUM: 2,
                SecurityLevel.LOW: 3,
            }.get(x.check.level, 4)
        )

        recommendations: list[str] = []
        for result in failed_results[:5]:  # Top 5 issues
            if result.recommendations:
                # Add top 2 recommendations per issue
                for rec in result.recommendations[:2]:
                    recommendations.append(rec)

        return recommendations[:10]  # Maximum 10 recommendations
