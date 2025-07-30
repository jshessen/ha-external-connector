"""
AWS Lambda function security validation and compliance checking.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from .models import SecurityCheck, SecurityCheckResult, SecurityLevel, SecurityStatus

if TYPE_CHECKING:
    from types_boto3_iam.client import IAMClient
    from types_boto3_lambda.client import LambdaClient

logger = logging.getLogger(__name__)


class LambdaSecurityValidator:
    """Validates AWS Lambda function security configurations"""

    def __init__(
        self,
        region: str = "us-east-1",
        lambda_client: LambdaClient | None = None,
        iam_client: IAMClient | None = None,
    ) -> None:
        """Initialize the Lambda Security Validator.

        Args:
            region: AWS region for client initialization.
            lambda_client: Optional Lambda client for dependency injection.
            iam_client: Optional IAM client for dependency injection.
        """
        self.region = region
        # Support dependency injection for better testability
        self._lambda_client: LambdaClient = (
            lambda_client
            or boto3.client(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                "lambda"
            )
        )
        self._iam_client: IAMClient = (
            iam_client
            or boto3.client(  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
                "iam"
            )
        )

    @property
    def lambda_client(self) -> LambdaClient:
        """Get the Lambda client."""
        return self._lambda_client

    @property
    def iam_client(self) -> IAMClient:
        """Get the IAM client."""
        return self._iam_client

    def validate_function(self, function_name: str) -> list[SecurityCheckResult]:
        """Validate security configuration of a Lambda function"""
        results: list[SecurityCheckResult] = []

        try:
            # Get function configuration
            function_config = self._get_function_config(function_name)
            if not function_config:
                return [
                    self._create_error_result(
                        "function_exists",
                        f"Failed to retrieve configuration for function: "
                        f"{function_name}",
                    )
                ]

            # Run security checks
            results.extend(self._check_runtime_version(function_config))
            results.extend(self._check_environment_variables(function_config))
            results.extend(self._check_execution_role(function_config))
            results.extend(self._check_vpc_configuration(function_config))
            results.extend(self._check_dead_letter_queue(function_config))
            results.extend(self._check_reserved_concurrency(function_config))
            results.extend(self._check_tracing_config(function_config))

            # Additional security checks
            results.extend(self._check_kms_encryption(function_config))
            results.extend(self._check_function_timeout(function_config))
            results.extend(self._check_memory_allocation(function_config))
            results.extend(self._check_code_signing(function_config))
            results.extend(self._check_layer_security(function_config))
            results.extend(
                self._check_configuration_management_security(function_config)
            )
            results.extend(self._check_cloudflare_integration_security(function_config))
            results.extend(self._check_rate_limiting_configuration(function_config))

        except ClientError as e:
            logger.error("Error validating function %s: %s", function_name, e)
            results.append(
                self._create_error_result(
                    "validation_error", f"Validation failed: {str(e)}"
                )
            )

        return results

    def _get_function_config(self, function_name: str) -> dict[str, Any] | None:
        """Get Lambda function configuration"""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            config = response.get("Configuration", {})
            return dict(config) if config else None
        except ClientError as e:
            logger.error("Failed to get function config: %s", e)
            return None

    def _check_runtime_version(
        self, function_config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check if Lambda function uses a supported runtime version."""
        start_time = time.time()

        check = SecurityCheck(
            check_id="lambda_runtime_version",
            name="Lambda Runtime Version",
            description="Ensure Lambda function uses supported runtime version",
            category="Runtime Security",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        runtime = function_config.get("Runtime", "")
        if not runtime:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.FAIL,
                    message="Function has no runtime specified",
                    execution_time=time.time() - start_time,
                )
            ]

        # List of deprecated runtimes to check against
        deprecated_runtimes = [
            "python2.7",
            "python3.6",
            "python3.7",
            "nodejs8.10",
            "nodejs10.x",
            "dotnetcore2.1",
            "go1.x",
        ]

        if runtime in deprecated_runtimes:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.FAIL,
                    message=f"Function uses deprecated runtime: {runtime}",
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"Function uses supported runtime: {runtime}",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_environment_variables(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check for sensitive data in environment variables"""
        start_time = time.time()
        env_vars = config.get("Environment", {}).get("Variables", {})

        check = SecurityCheck(
            check_id="lambda_env_vars_security",
            name="Environment Variables Security",
            description="Check for potentially sensitive data in environment variables",
            category="Data Protection",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        sensitive_patterns = [
            "password",
            "passwd",
            "secret",
            "key",
            "token",
            "credential",
            "auth",
            "api_key",
            "access_key",
            "client_secret",
            "oauth_secret",
            "cloudflare_token",
            "cf_token",
            "bearer_token",
        ]

        issues: list[str] = []
        for var_name, var_value in env_vars.items():
            var_lower = var_name.lower()
            if (
                any(pattern in var_lower for pattern in sensitive_patterns)
                and var_value
                and len(var_value) > 10  # Likely actual secret
            ):
                issues.append(f"Variable '{var_name}' may contain sensitive data")

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=(
                        f"Found {len(issues)} potentially sensitive "
                        "environment variables"
                    ),
                    details={"issues": issues},
                    recommendations=[
                        "Use AWS Systems Manager Parameter Store for secrets",
                        "Use AWS Secrets Manager for database credentials",
                        "Encrypt sensitive environment variables",
                        "Remove hardcoded secrets from environment variables",
                        "Consider using CloudFlare Access for additional security",
                        "Implement proper secret rotation mechanisms",
                        "Use IAM roles instead of hardcoded credentials",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="No sensitive data detected in environment variables",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_execution_role(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check Lambda execution role permissions"""
        start_time = time.time()
        role_arn = config.get("Role", "")

        check = SecurityCheck(
            check_id="lambda_execution_role",
            name="Execution Role Permissions",
            description=(
                "Validate Lambda execution role follows least privilege principle"
            ),
            category="IAM Security",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        if not role_arn:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.FAIL,
                    message="No execution role configured",
                    execution_time=time.time() - start_time,
                )
            ]

        try:
            # Extract role name from ARN
            role_name = role_arn.split("/")[-1]

            # Get role policies
            attached_policies = self._get_role_policies(role_name)

            # Check for overly permissive policies
            risky_policies = self._check_for_risky_policies(attached_policies)

            if risky_policies:
                return [
                    SecurityCheckResult(
                        check=check,
                        status=SecurityStatus.WARNING,
                        message=(
                            f"Found {len(risky_policies)} potentially risky policies"
                        ),
                        details={"risky_policies": risky_policies},
                        recommendations=[
                            "Review and scope down overly permissive policies",
                            "Use resource-specific ARNs where possible",
                            "Remove unused permissions",
                            "Apply principle of least privilege",
                        ],
                        execution_time=time.time() - start_time,
                    )
                ]

            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.PASSED,
                    message=(
                        "Execution role appears to follow least privilege principle"
                    ),
                    execution_time=time.time() - start_time,
                )
            ]

        except ClientError as e:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.ERROR,
                    message=f"Failed to validate execution role: {str(e)}",
                    execution_time=time.time() - start_time,
                )
            ]

    def _get_role_policies(self, role_name: str) -> list[dict[str, Any]]:
        """Get all policies attached to a role"""
        policies: list[dict[str, Any]] = []

        try:
            # Get attached managed policies
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in response.get("AttachedPolicies", []):
                policies.append(
                    {
                        "type": "managed",
                        "name": policy.get("PolicyName", ""),
                        "arn": policy.get("PolicyArn", ""),
                    }
                )

            # Get inline policies
            inline_response = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in inline_response.get("PolicyNames", []):
                policies.append(
                    {"type": "inline", "name": policy_name, "role": role_name}
                )

        except ClientError as e:
            logger.error("Failed to get role policies: %s", e)

        return policies

    def _check_for_risky_policies(self, policies: list[dict[str, Any]]) -> list[str]:
        """Check for overly permissive policies"""
        risky_policies: list[str] = []

        # Known risky managed policies
        risky_managed_policies = [
            "arn:aws:iam::aws:policy/PowerUserAccess",
            "arn:aws:iam::aws:policy/IAMFullAccess",
            "arn:aws:iam::aws:policy/AdministratorAccess",
        ]

        for policy in policies:
            if policy["type"] == "managed" and policy["arn"] in risky_managed_policies:
                risky_policies.append(f"Risky managed policy: {policy['name']}")
            # NOTE: Inline policy analysis could be added here to check policy documents

        return risky_policies

    def _check_vpc_configuration(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check VPC configuration for security best practices"""
        start_time = time.time()
        vpc_config = config.get("VpcConfig", {})

        check = SecurityCheck(
            check_id="lambda_vpc_config",
            name="VPC Configuration",
            description="Validate Lambda VPC configuration security",
            category="Network Security",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        if not vpc_config or not vpc_config.get("SubnetIds"):
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="Function not configured with VPC (may not be required)",
                    recommendations=[
                        (
                            "Consider VPC configuration if function accesses "
                            "private resources"
                        ),
                        "Ensure function doesn't need VPC isolation",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        # Check if function has both subnets and security groups
        subnet_ids = vpc_config.get("SubnetIds", [])
        security_group_ids = vpc_config.get("SecurityGroupIds", [])

        issues: list[str] = []
        if not subnet_ids:
            issues.append("No subnets configured")
        if not security_group_ids:
            issues.append("No security groups configured")

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.FAIL,
                    message="VPC configuration incomplete",
                    details={"issues": issues},
                    recommendations=[
                        "Configure appropriate subnets for function",
                        "Attach security groups with minimal required access",
                        "Ensure subnets have appropriate route tables",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="VPC configuration appears correct",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_dead_letter_queue(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check dead letter queue configuration"""
        start_time = time.time()
        dlq_config = config.get("DeadLetterConfig", {})

        check = SecurityCheck(
            check_id="lambda_dead_letter_queue",
            name="Dead Letter Queue Configuration",
            description="Ensure proper error handling with DLQ configuration",
            category="Reliability",
            level=SecurityLevel.LOW,
            enabled=True,
        )

        if not dlq_config or not dlq_config.get("TargetArn"):
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="No dead letter queue configured",
                    recommendations=[
                        "Consider configuring DLQ for better error handling",
                        "Use SQS or SNS for dead letter destinations",
                        "Monitor failed invocations",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Dead letter queue configured",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_reserved_concurrency(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check reserved concurrency configuration"""
        start_time = time.time()
        reserved_concurrency = config.get("ReservedConcurrencyExecutions")

        check = SecurityCheck(
            check_id="lambda_reserved_concurrency",
            name="Reserved Concurrency",
            description="Check concurrency limits for cost and security control",
            category="Resource Management",
            level=SecurityLevel.LOW,
            enabled=True,
        )

        if reserved_concurrency is None:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="No reserved concurrency limit set",
                    recommendations=[
                        "Consider setting concurrency limits to control costs",
                        "Prevent function from consuming all account concurrency",
                        "Set appropriate limits based on expected load",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"Reserved concurrency set to {reserved_concurrency}",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_tracing_config(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check AWS X-Ray tracing configuration"""
        start_time = time.time()
        tracing_config = config.get("TracingConfig", {})

        check = SecurityCheck(
            check_id="lambda_tracing_config",
            name="X-Ray Tracing Configuration",
            description="Ensure proper observability with X-Ray tracing",
            category="Monitoring",
            level=SecurityLevel.INFO,
            enabled=True,
        )

        mode = tracing_config.get("Mode", "PassThrough")

        if mode == "PassThrough":
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="X-Ray tracing not actively enabled",
                    recommendations=[
                        "Enable Active tracing for better observability",
                        "Monitor function performance and errors",
                        "Use tracing data for security analysis",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"X-Ray tracing enabled with mode: {mode}",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_kms_encryption(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check KMS encryption configuration for environment variables"""
        start_time = time.time()
        kms_key_arn = config.get("KMSKeyArn")

        check = SecurityCheck(
            check_id="lambda_kms_encryption",
            name="KMS Encryption Configuration",
            description="Ensure Lambda function uses KMS encryption for sensitive data",
            category="Data Protection",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        if not kms_key_arn:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="No KMS key configured for encryption",
                    recommendations=[
                        "Configure KMS encryption for environment variables",
                        "Use customer-managed KMS keys for better control",
                        "Enable encryption for sensitive function data",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        # Check if using AWS managed key vs customer managed key
        if "aws/lambda" in kms_key_arn:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="Using AWS managed KMS key",
                    recommendations=[
                        "Consider using customer-managed KMS keys",
                        "Customer-managed keys provide better access control",
                        "Enable key rotation for customer-managed keys",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Customer-managed KMS key configured",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_function_timeout(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check function timeout configuration for security"""
        start_time = time.time()
        timeout = config.get("Timeout", 3)  # Default is 3 seconds

        check = SecurityCheck(
            check_id="lambda_timeout_security",
            name="Function Timeout Security",
            description="Validate function timeout is within secure limits",
            category="Resource Management",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        # Check for excessively long timeouts (potential DoS risk)
        if timeout > 600:  # 10 minutes
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"Function timeout is very high: {timeout} seconds",
                    recommendations=[
                        "Review if such long timeout is necessary",
                        "Consider breaking down long-running tasks",
                        "Use asynchronous processing for long operations",
                        "Monitor for timeout-related security issues",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        # Check for very short timeouts that might cause reliability issues
        if timeout < 5:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"Function timeout is quite short: {timeout} seconds",
                    recommendations=[
                        "Ensure timeout is sufficient for normal operation",
                        "Monitor for timeout errors in CloudWatch",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"Function timeout is reasonable: {timeout} seconds",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_memory_allocation(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check memory allocation for security considerations"""
        start_time = time.time()
        memory_size = config.get("MemorySize", 128)  # Default is 128 MB

        check = SecurityCheck(
            check_id="lambda_memory_allocation",
            name="Memory Allocation Security",
            description="Validate memory allocation is appropriate and secure",
            category="Resource Management",
            level=SecurityLevel.LOW,
            enabled=True,
        )

        # Check for excessive memory allocation
        if memory_size > 3008:  # Maximum is 10,240 MB but 3008 is quite high
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"High memory allocation: {memory_size} MB",
                    recommendations=[
                        "Review if high memory allocation is necessary",
                        "Monitor memory usage to prevent resource abuse",
                        "Consider cost implications of high memory allocation",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        # Check for very low memory that might cause issues
        if memory_size < 128:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"Low memory allocation: {memory_size} MB",
                    recommendations=[
                        "Ensure memory is sufficient for secure operation",
                        "Monitor for out-of-memory errors",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"Memory allocation is appropriate: {memory_size} MB",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_code_signing(self, config: dict[str, Any]) -> list[SecurityCheckResult]:
        """Check code signing configuration"""
        start_time = time.time()
        code_signing_config = config.get("CodeSigningConfigArn")

        check = SecurityCheck(
            check_id="lambda_code_signing",
            name="Code Signing Configuration",
            description="Validate Lambda function uses code signing for integrity",
            category="Code Integrity",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        if not code_signing_config:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="No code signing configuration found",
                    recommendations=[
                        "Enable code signing for production functions",
                        "Use AWS Signer to sign deployment packages",
                        "Implement code integrity verification",
                        "Prevent deployment of unsigned code",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Code signing configuration enabled",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_layer_security(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check Lambda layers for security issues"""
        start_time = time.time()
        layers = config.get("Layers", [])

        check = SecurityCheck(
            check_id="lambda_layer_security",
            name="Lambda Layer Security",
            description="Validate Lambda layers are from trusted sources",
            category="Dependency Security",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        if not layers:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.PASSED,
                    message="No layers configured",
                    execution_time=time.time() - start_time,
                )
            ]

        issues: list[str] = []
        layer_count = len(layers)

        # Check for excessive number of layers
        if layer_count > 5:
            issues.append(f"High number of layers: {layer_count}")

        # Check for public layers (potential security risk)
        for layer in layers:
            layer_arn = layer.get("Arn", "")
            if ":layer:" in layer_arn:
                # Extract account ID from ARN
                arn_parts = layer_arn.split(":")
                if len(arn_parts) >= 5:
                    account_id = arn_parts[4]
                    # Check if it's not the same account (external layer)
                    current_config_arn = config.get("FunctionArn", "")
                    if current_config_arn:
                        current_account = current_config_arn.split(":")[4]
                        if account_id != current_account:
                            issues.append(f"External layer detected: {layer_arn}")

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"Found {len(issues)} layer security concerns",
                    details={"issues": issues},
                    recommendations=[
                        "Review all layers for necessity and trust",
                        "Use layers from your own account when possible",
                        "Regularly audit layer dependencies",
                        "Monitor layer versions for security updates",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=f"All {layer_count} layers appear secure",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_configuration_management_security(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check configuration management and environment variable security patterns"""
        start_time = time.time()
        env_vars = config.get("Environment", {}).get("Variables", {})

        check = SecurityCheck(
            check_id="lambda_config_management_security",
            name="Configuration Management Security",
            description=(
                "Validate secure configuration management patterns "
                "and environment variable usage"
            ),
            category="Configuration Security",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        issues: list[str] = []
        recommendations: list[str] = []

        # Check for proper configuration hierarchies (env vars + SSM)
        config_vars = [
            var
            for var in env_vars
            if any(
                pattern in var.upper()
                for pattern in ["CONFIG", "CACHE", "TTL", "TIMEOUT", "REGION", "TABLE"]
            )
        ]

        if not config_vars:
            issues.append("No configuration management environment variables detected")
            recommendations.extend(
                [
                    "Implement configuration hierarchy (env vars + SSM)",
                    "Use environment variables for non-sensitive configuration",
                    "Consider using configuration management service pattern",
                ]
            )

        # Check for CloudFlare integration patterns
        cf_vars = [
            var
            for var in env_vars
            if any(
                pattern in var.upper()
                for pattern in ["CLOUDFLARE", "CF_", "CDN", "PROXY"]
            )
        ]

        if cf_vars:
            recommendations.append(
                "Ensure CloudFlare credentials use secure storage (SSM/Secrets Manager)"
            )

        # Check for rate limiting configurations
        rate_limit_vars = [
            var
            for var in env_vars
            if any(
                pattern in var.upper()
                for pattern in ["RATE_LIMIT", "MAX_REQUESTS", "REQUEST_SIZE", "TIMEOUT"]
            )
        ]

        if rate_limit_vars:
            # This is good - rate limiting is configured
            pass
        else:
            issues.append("No rate limiting configuration detected")
            recommendations.extend(
                [
                    "Implement request rate limiting for security",
                    "Configure maximum request size limits",
                    "Set appropriate timeout values",
                ]
            )

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=(
                        f"Configuration management security issues detected: "
                        f"{len(issues)} issues"
                    ),
                    details={"issues": issues},
                    recommendations=recommendations,
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="Configuration management security patterns appear appropriate",
                execution_time=time.time() - start_time,
            )
        ]

    def _check_cloudflare_integration_security(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check CloudFlare integration security patterns"""
        start_time = time.time()
        env_vars = config.get("Environment", {}).get("Variables", {})

        check = SecurityCheck(
            check_id="lambda_cloudflare_security",
            name="CloudFlare Integration Security",
            description="Validate CloudFlare integration security and header handling",
            category="Network Security",
            level=SecurityLevel.MEDIUM,
            enabled=True,
        )

        # Check for CloudFlare-related environment variables
        cf_vars = [
            var
            for var in env_vars
            if any(
                pattern in var.upper()
                for pattern in ["CLOUDFLARE", "CF_", "CDN", "PROXY", "BYPASS"]
            )
        ]

        if not cf_vars:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message="No CloudFlare integration detected",
                    recommendations=[
                        "Consider CloudFlare Access for additional security layer",
                        "Use CloudFlare for DDoS protection and rate limiting",
                    ],
                    execution_time=time.time() - start_time,
                )
            ]

        issues: list[str] = []
        recommendations: list[str] = []

        # Check for potential security issues with CloudFlare integration
        for var_name, var_value in env_vars.items():
            if (
                any(pattern in var_name.upper() for pattern in ["CLOUDFLARE", "CF_"])
                and var_value
                and len(var_value) > 10  # Likely contains sensitive data
            ):
                issues.append(
                    f"CloudFlare credential '{var_name}' may contain sensitive data"
                )

        if issues:
            recommendations.extend(
                [
                    "Move CloudFlare credentials to AWS Secrets Manager",
                    "Use IAM roles for CloudFlare API access when possible",
                    "Implement proper secret rotation for CloudFlare tokens",
                    "Validate CloudFlare Access headers for bypass protection",
                ]
            )

            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=(
                        f"CloudFlare integration security issues: "
                        f"{len(issues)} issues"
                    ),
                    details={"issues": issues},
                    recommendations=recommendations,
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message="CloudFlare integration security appears appropriate",
                recommendations=[
                    "Ensure CloudFlare Access headers are properly validated",
                    "Monitor CloudFlare bypass attempts in logs",
                ],
                execution_time=time.time() - start_time,
            )
        ]

    def _check_rate_limiting_configuration(
        self, config: dict[str, Any]
    ) -> list[SecurityCheckResult]:
        """Check rate limiting and request validation configuration"""
        start_time = time.time()
        env_vars = config.get("Environment", {}).get("Variables", {})

        check = SecurityCheck(
            check_id="lambda_rate_limiting_security",
            name="Rate Limiting Security Configuration",
            description="Validate rate limiting and request size controls for security",
            category="Request Security",
            level=SecurityLevel.HIGH,
            enabled=True,
        )

        issues: list[str] = []
        recommendations: list[str] = []

        # Check for rate limiting environment variables
        rate_limit_vars = {
            "MAX_REQUEST_SIZE": env_vars.get(
                "MAX_REQUEST_SIZE_BYTES", env_vars.get("MAX_REQUEST_SIZE")
            ),
            "RATE_LIMIT_WINDOW": env_vars.get("RATE_LIMIT_WINDOW_SECONDS"),
            "MAX_REQUESTS_PER_MINUTE": env_vars.get("MAX_REQUESTS_PER_MINUTE"),
            "REQUEST_TIMEOUT": env_vars.get("REQUEST_TIMEOUT_SECONDS"),
            "MAX_RETRIES": env_vars.get("MAX_RETRIES"),
        }

        configured_limits = {k: v for k, v in rate_limit_vars.items() if v is not None}

        if not configured_limits:
            issues.append("No rate limiting configuration detected")
            recommendations.extend(
                [
                    "Implement request rate limiting to prevent abuse",
                    "Configure maximum request size limits (e.g., 8KB-64KB)",
                    "Set request timeout values (e.g., 30 seconds)",
                    "Implement retry limits for resilience",
                ]
            )
        else:
            # Validate configured values for security best practices
            max_request_size = configured_limits.get("MAX_REQUEST_SIZE")
            if max_request_size:
                try:
                    size_bytes = int(max_request_size)
                    if size_bytes > 1024 * 1024:  # 1MB
                        issues.append(
                            f"Maximum request size is very large: {size_bytes} bytes"
                        )
                        recommendations.append(
                            "Consider reducing maximum request size for security"
                        )
                except ValueError:
                    issues.append("Invalid MAX_REQUEST_SIZE value")

            max_requests = configured_limits.get("MAX_REQUESTS_PER_MINUTE")
            if max_requests:
                try:
                    requests_per_min = int(max_requests)
                    if requests_per_min > 1000:
                        issues.append(
                            f"Rate limit is very high: {requests_per_min} req/min"
                        )
                        recommendations.append(
                            "Consider tightening rate limits for security"
                        )
                except ValueError:
                    issues.append("Invalid MAX_REQUESTS_PER_MINUTE value")

        if issues:
            return [
                SecurityCheckResult(
                    check=check,
                    status=SecurityStatus.WARNING,
                    message=f"Rate limiting security issues: {len(issues)} issues",
                    details={
                        "issues": issues,
                        "configured_limits": list(configured_limits.keys()),
                    },
                    recommendations=recommendations,
                    execution_time=time.time() - start_time,
                )
            ]

        return [
            SecurityCheckResult(
                check=check,
                status=SecurityStatus.PASSED,
                message=(
                    f"Rate limiting security properly configured with "
                    f"{len(configured_limits)} controls"
                ),
                execution_time=time.time() - start_time,
            )
        ]

    def _create_error_result(self, check_id: str, message: str) -> SecurityCheckResult:
        """Create an error result for failed validations"""
        check = SecurityCheck(
            check_id=check_id,
            name="Validation Error",
            description="Security validation encountered an error",
            category="Validation",
            level=SecurityLevel.CRITICAL,
            enabled=True,
        )

        return SecurityCheckResult(
            check=check,
            status=SecurityStatus.ERROR,
            message=message,
            execution_time=0.0,
        )
