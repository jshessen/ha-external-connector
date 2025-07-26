# Security Validation API Documentation

## Overview

The HA External Connector Security Validation Framework provides comprehensive security analysis for AWS Lambda functions, IAM policies, and compliance checking. This framework extends far beyond basic security validation with structured data models, detailed reporting, and enterprise-grade compliance checking.

## Architecture

```tree
Security Framework
├── Lambda Security Validator    # 12 comprehensive security checks
├── Policy Validator            # IAM policy structure validation
├── Compliance Checker          # SOC2 & AWS Well-Architected
└── Security Reporter           # Comprehensive reporting
```

## Core Classes

### LambdaSecurityValidator

Main class for validating AWS Lambda function security configurations.

#### Initialization

```python
from ha_connector.security import LambdaSecurityValidator

# Initialize validator for specific region
validator = LambdaSecurityValidator(region="us-east-1")
```

#### Primary Method: validate_function

```python
def validate_function(self, function_name: str) -> list[SecurityCheckResult]:
    """
    Validate security configuration of a Lambda function

    Args:
        function_name: Name or ARN of the Lambda function

    Returns:
        List of security check results with detailed findings

    Raises:
        ClientError: When AWS API calls fail
    """
```

**Example Usage:**

```python
# Validate a Lambda function
results = validator.validate_function("my-lambda-function")

# Process results
for result in results:
    print(f"Check: {result.check.name}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    if result.recommendations:
        print(f"Recommendations: {result.recommendations}")
```

## Security Checks

The validator performs **12 comprehensive security checks**:

### 1. Runtime Version Validation

- **ID**: `lambda_runtime_version`
- **Level**: HIGH
- **Purpose**: Ensures Lambda uses supported runtime versions
- **Checks**: Detects deprecated runtimes (python2.7, nodejs8.10, etc.)

### 2. Environment Variables Security

- **ID**: `lambda_env_vars_security`
- **Level**: MEDIUM
- **Purpose**: Detects potentially sensitive data in environment variables
- **Patterns**: password, secret, key, token, credential, api_key

### 3. Execution Role Permissions

- **ID**: `lambda_execution_role`
- **Level**: HIGH
- **Purpose**: Validates IAM role follows least privilege principle
- **Checks**: Overly permissive policies, risky managed policies

### 4. VPC Configuration

- **ID**: `lambda_vpc_config`
- **Level**: MEDIUM
- **Purpose**: Validates VPC security configuration
- **Checks**: Subnet configuration, security group setup

### 5. Dead Letter Queue Configuration

- **ID**: `lambda_dead_letter_queue`
- **Level**: LOW
- **Purpose**: Ensures proper error handling
- **Checks**: DLQ presence and configuration

### 6. Reserved Concurrency

- **ID**: `lambda_reserved_concurrency`
- **Level**: LOW
- **Purpose**: Validates concurrency limits for cost/security control
- **Checks**: Concurrency limit configuration

### 7. X-Ray Tracing Configuration

- **ID**: `lambda_tracing_config`
- **Level**: INFO
- **Purpose**: Ensures proper observability
- **Checks**: Tracing mode (Active vs PassThrough)

### 8. KMS Encryption Configuration

- **ID**: `lambda_kms_encryption`
- **Level**: HIGH
- **Purpose**: Validates encryption for sensitive data
- **Checks**: Customer-managed vs AWS-managed keys

### 9. Function Timeout Security

- **ID**: `lambda_timeout_security`
- **Level**: MEDIUM
- **Purpose**: Prevents DoS and reliability issues
- **Checks**: Timeout limits (too high/too low)

### 10. Memory Allocation Security

- **ID**: `lambda_memory_allocation`
- **Level**: LOW
- **Purpose**: Resource usage validation
- **Checks**: Memory allocation appropriateness

### 11. Code Signing Validation

- **ID**: `lambda_code_signing`
- **Level**: HIGH
- **Purpose**: Ensures code integrity
- **Checks**: Code signing configuration presence

### 12. Layer Security Analysis

- **ID**: `lambda_layer_security`
- **Level**: MEDIUM
- **Purpose**: Validates trusted dependency sources
- **Checks**: External layers, layer count limits

## Data Models

### SecurityCheck

```python
@dataclass
class SecurityCheck:
    check_id: str           # Unique identifier
    name: str              # Human-readable name
    description: str       # Detailed description
    category: str          # Security category
    level: SecurityLevel   # Severity level
    enabled: bool          # Whether check is enabled
```

### SecurityCheckResult

```python
@dataclass
class SecurityCheckResult:
    check: SecurityCheck           # The security check performed
    status: SecurityStatus         # PASSED, WARNING, FAIL, ERROR
    message: str                   # Result message
    details: dict[str, Any] | None # Additional details
    recommendations: list[str] | None  # Security recommendations
    execution_time: float          # Time taken for check
```

### Enums

```python
class SecurityLevel(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"
```

## Error Handling

The validator handles AWS API errors gracefully:

```python
try:
    results = validator.validate_function("non-existent-function")
except ClientError as e:
    print(f"AWS API Error: {e}")
```

Error scenarios automatically generate SecurityCheckResult with:

- Status: `ERROR`
- Appropriate error messages
- Zero execution time

## Performance

- **Concurrent Checks**: All security checks run independently
- **Efficient AWS API Usage**: Minimal API calls with proper caching
- **Fast Execution**: Typical validation completes in <2 seconds
- **Memory Efficient**: Minimal memory footprint

## Integration Examples

### CI/CD Pipeline Integration

```python
def validate_lambda_security(function_names: list[str]) -> bool:
    """Validate multiple Lambda functions in CI/CD"""
    validator = LambdaSecurityValidator()

    failed_checks = []
    for function_name in function_names:
        results = validator.validate_function(function_name)

        for result in results:
            if result.status in [SecurityStatus.FAIL, SecurityStatus.ERROR]:
                failed_checks.append(f"{function_name}: {result.message}")

    if failed_checks:
        print("Security validation failed:")
        for failure in failed_checks:
            print(f"  - {failure}")
        return False

    print("All security checks passed!")
    return True
```

### Custom Security Policies

```python
def validate_with_custom_policy(function_name: str) -> dict[str, Any]:
    """Validate with custom security requirements"""
    validator = LambdaSecurityValidator()
    results = validator.validate_function(function_name)

    # Custom policy: Fail if any HIGH level checks fail
    high_severity_failures = [
        result for result in results
        if result.check.level == SecurityLevel.HIGH
        and result.status == SecurityStatus.FAIL
    ]

    return {
        "function_name": function_name,
        "total_checks": len(results),
        "high_severity_failures": len(high_severity_failures),
        "compliant": len(high_severity_failures) == 0,
        "details": results
    }
```

## Best Practices

1. **Regular Validation**: Run security validation on deployment and schedule regular checks
2. **Automation Integration**: Integrate with CI/CD pipelines for automated security validation
3. **Custom Thresholds**: Define organization-specific security thresholds
4. **Monitoring Integration**: Send results to monitoring systems for alerting
5. **Documentation**: Document security exceptions and approval processes

## Security Framework Benefits

- **Comprehensive Coverage**: 12 security checks covering all major Lambda security aspects
- **Structured Results**: Consistent data models for easy integration
- **Actionable Recommendations**: Specific guidance for remediation
- **Performance Optimized**: Fast execution suitable for CI/CD integration
- **Extensible Architecture**: Easy to add custom security checks
- **Enterprise Ready**: SOC2 and AWS Well-Architected compliance integration

## Related Documentation

- [Security Validation User Guide](../guides/security_validation_guide.md)
- [Compliance Framework Integration](../guides/compliance_integration.md)
- [CI/CD Integration Examples](../guides/cicd_integration.md)
- [Custom Security Policies](../guides/custom_security_policies.md)
