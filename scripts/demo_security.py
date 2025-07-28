#!/usr/bin/env python3
"""
Security Validation Demo

Demonstrates the Phase 5.2 Security Validation Framework capabilities.
"""

import sys
from pathlib import Path

from ha_connector.security import (
    ComplianceChecker,
    SecurityCheckResult,
    SecurityLevel,
    SecurityPolicy,
    SecurityPolicyValidator,
    SecurityReporter,
)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_security_validation() -> None:
    """Demonstrate security validation capabilities"""
    print("🔒 HA External Connector - Security Validation Framework Demo")
    print("=" * 60)

    # Initialize validators and show capabilities
    _initialize_and_show_validators()

    # Demo individual features
    _demo_policy_validation()
    _demo_compliance_checking()
    _demo_reporting()
    _show_framework_capabilities()
    _show_next_steps()


def _initialize_and_show_validators() -> tuple[
    SecurityPolicyValidator, ComplianceChecker, SecurityReporter
]:
    """Initialize validators and show enhanced Lambda capabilities"""
    # Initialize validators
    policy_validator = SecurityPolicyValidator()
    compliance_checker = ComplianceChecker()
    reporter = SecurityReporter()

    print("✅ Security validators initialized")
    print("   - Lambda Security Validator (12 comprehensive security checks)")
    print("     • Original: Runtime, Environment, Role, VPC, DLQ, Concurrency, Tracing")
    print("     • Enhanced: KMS Encryption, Timeout, Memory, Code Signing, Layers")
    print("   - Policy Validator")
    print("   - Compliance Checker (SOC2, AWS Well-Architected)")
    print("   - Security Reporter")
    print()

    # Demo enhanced Lambda security capabilities
    print("🛡️ Enhanced Lambda Security Validation Features:")
    print("   ✅ KMS Encryption Check - Validates customer-managed keys")
    print("   ✅ Function Timeout Security - Prevents DoS and reliability issues")
    print("   ✅ Memory Allocation Security - Resource usage validation")
    print("   ✅ Code Signing Validation - Ensures code integrity")
    print("   ✅ Layer Security Analysis - Validates trusted sources")
    print("   📈 Total: 12 security checks (7 original + 5 new)")
    print()

    return policy_validator, compliance_checker, reporter


def _demo_policy_validation() -> None:
    """Demonstrate policy validation capabilities"""
    policy_validator = SecurityPolicyValidator()

    print("📋 Testing Policy Validation...")
    test_policy = SecurityPolicy(
        policy_id="demo_policy",
        name="Demo Security Policy",
        description="Test policy for demonstration",
        version="1.0",
        enabled_checks=["lambda_runtime_version", "lambda_env_vars_security"],
        enforcement_level=SecurityLevel.MEDIUM,
    )

    policy_results = policy_validator.validate_policy(test_policy)
    print(f"   - Policy structure validation: {len(policy_results)} checks")
    for result in policy_results:
        status_icon = "✅" if result.status.value == "passed" else "⚠️"
        print(f"     {status_icon} {result.check.name}: {result.message}")
    print()


def _demo_compliance_checking() -> None:
    """Demonstrate compliance framework capabilities"""
    compliance_checker = ComplianceChecker()

    print("📊 Testing Compliance Framework...")
    # Create properly typed empty results list for demonstration
    dummy_results: list[SecurityCheckResult] = []  # In real usage, from Lambda

    soc2_compliance = compliance_checker.check_compliance("soc2", dummy_results)
    print(f"   - SOC2 compliance: {soc2_compliance['total_rules']} rules defined")

    wa_compliance = compliance_checker.check_compliance(
        "aws_well_architected", dummy_results
    )
    print(f"   - AWS Well-Architected: {wa_compliance['total_rules']} rules defined")
    print()


def _demo_reporting() -> None:
    """Demonstrate security reporting capabilities"""
    reporter = SecurityReporter()
    policy_validator = SecurityPolicyValidator()

    # Generate sample policy results for reporting demo
    test_policy = SecurityPolicy(
        policy_id="demo_policy",
        name="Demo Security Policy",
        description="Test policy for demonstration",
        version="1.0",
        enabled_checks=["lambda_runtime_version", "lambda_env_vars_security"],
        enforcement_level=SecurityLevel.MEDIUM,
    )
    policy_results = policy_validator.validate_policy(test_policy)

    print("📈 Testing Security Reporting...")
    summary = reporter.generate_summary_report(policy_results)
    print("   - Summary report generated")
    print(f"     • Total checks: {summary['summary']['total_checks']}")
    print(f"     • Pass rate: {summary['summary']['pass_rate']}%")
    print(f"     • Overall status: {summary['overall_status']}")
    print()


def _show_framework_capabilities() -> None:
    """Display comprehensive framework capabilities"""
    print("🚀 Framework Capabilities:")
    print("   ✅ Lambda security validation (12+ comprehensive security checks)")
    print("     • Runtime version validation")
    print("     • Environment variable security scanning")
    print("     • IAM role permission analysis")
    print("     • VPC configuration validation")
    print("     • KMS encryption verification")
    print("     • Function timeout security limits")
    print("     • Memory allocation validation")
    print("     • Code signing integrity checks")
    print("     • Layer dependency security analysis")
    print("   ✅ Policy structure validation")
    print("   ✅ Compliance framework integration (SOC2, AWS Well-Architected)")
    print("   ✅ Comprehensive security reporting")
    print("   ✅ Structured data models with Pydantic")
    print("   ✅ Enhanced beyond bash version capabilities")
    print()


def _show_next_steps() -> None:
    """Display recommended next steps for users"""
    print("💡 Next Steps:")
    print("   • Add AWS credentials for live Lambda function validation")
    print("   • Customize security policies for your environment")
    print("   • Integrate with CI/CD pipeline for automated security checks")
    print("   • Extend with additional compliance frameworks")


if __name__ == "__main__":
    try:
        demo_security_validation()
    except (ImportError, ModuleNotFoundError) as e:
        print(f"❌ Demo failed - Missing dependency: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Demo failed with unexpected error: {e}")
        sys.exit(1)
