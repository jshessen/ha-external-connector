# Security Validation User Guide

## Quick Start

The HA External Connector Security Validation Framework provides comprehensive security analysis for AWS Lambda functions with 12 comprehensive security checks.

### Installation

```bash
# Run the demo script to see the framework in action
# (Virtual environment is automatically activated in VS Code terminal)
python scripts/demo_security.py

# Or use explicit path if needed
${workspaceFolder}/.venv/bin/python scripts/demo_security.py
```

### Basic Usage

```python
from ha_connector.security import LambdaSecurityValidator

# Initialize the validator
validator = LambdaSecurityValidator(region="us-east-1")

# Validate a Lambda function
results = validator.validate_function("my-lambda-function")

# Check results
for result in results:
    if result.status in ["fail", "error"]:
        print(f"❌ {result.check.name}: {result.message}")
    elif result.status == "warning":
        print(f"⚠️ {result.check.name}: {result.message}")
    else:
        print(f"✅ {result.check.name}: {result.message}")
```

## Security Checks Overview

The framework performs **12 comprehensive security checks**:

| Check | Level | Purpose |
|-------|-------|---------|
| Runtime Version | HIGH | Detects deprecated runtimes |
| Environment Variables | MEDIUM | Scans for sensitive data |
| Execution Role | HIGH | Validates least privilege |
| VPC Configuration | MEDIUM | Network security validation |
| Dead Letter Queue | LOW | Error handling setup |
| Reserved Concurrency | LOW | Resource limit validation |
| X-Ray Tracing | INFO | Observability configuration |
| KMS Encryption | HIGH | Data encryption validation |
| Function Timeout | MEDIUM | DoS prevention |
| Memory Allocation | LOW | Resource usage validation |
| Code Signing | HIGH | Code integrity verification |
| Layer Security | MEDIUM | Dependency source validation |

## Understanding Results

### Security Status Levels

- **✅ PASSED**: Security check completed successfully
- **⚠️ WARNING**: Potential security concern, review recommended
- **❌ FAIL**: Security issue detected, action required
- **🔥 ERROR**: Check failed to complete, investigate

### Security Levels

- **🔥 CRITICAL**: Immediate action required
- **🔴 HIGH**: Security risk, address soon
- **🟡 MEDIUM**: Moderate risk, plan remediation
- **🟢 LOW**: Minor issue, monitor
- **ℹ️ INFO**: Informational, no action needed

## Common Security Issues

### 1. Deprecated Runtime Versions

**Issue**: Function uses outdated runtime (python2.7, nodejs8.10)

**Solution**:

```python
# Update Lambda function runtime
import boto3

lambda_client = boto3.client('lambda')
lambda_client.update_function_configuration(
    FunctionName='my-function',
    Runtime='python3.11'  # Use supported runtime
)
```

### 2. Sensitive Environment Variables

**Issue**: Environment variables contain passwords, API keys, or secrets

**Solution**:

```python
# Use AWS Systems Manager Parameter Store
import boto3

ssm = boto3.client('ssm')

# Store secret in Parameter Store
ssm.put_parameter(
    Name='/myapp/api-key',
    Value='secret-api-key',
    Type='SecureString'
)

# Update Lambda to reference parameter instead of hardcoded value
lambda_client.update_function_configuration(
    FunctionName='my-function',
    Environment={
        'Variables': {
            'API_KEY_PARAM': '/myapp/api-key'  # Reference instead of value
        }
    }
)
```

### 3. Overly Permissive IAM Roles

**Issue**: Lambda execution role has excessive permissions

**Solution**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"
    }
  ]
}
```

### 4. Missing KMS Encryption

**Issue**: Function doesn't use customer-managed KMS keys

**Solution**:

```python
# Enable KMS encryption with customer-managed key
lambda_client.update_function_configuration(
    FunctionName='my-function',
    KMSKeyArn='arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
)
```

### 5. No Code Signing

**Issue**: Function doesn't use code signing for integrity

**Solution**:

```bash
# Create signing profile
aws signer put-signing-profile \\
    --profile-name my-signing-profile \\
    --platform-id AWSLambda-SHA384-ECDSA

# Create code signing config
aws lambda create-code-signing-config \\
    --allowed-publishers SigningProfileVersionArns=arn:aws:signer:us-east-1:123456789012:/signing-profiles/my-signing-profile \\
    --code-signing-policies UntrustedArtifactOnDeployment=Enforce

# Apply to function
aws lambda update-function-configuration \\
    --function-name my-function \\
    --code-signing-config-arn arn:aws:lambda:us-east-1:123456789012:code-signing-config:csc-123456789
```

## Automation Integration

### CI/CD Pipeline

```yaml
# GitHub Actions example
name: Lambda Security Validation
on: [push, pull_request]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run security validation
        run: |
          python scripts/validate_lambda_security.py \\
            --function-names my-lambda-1,my-lambda-2 \\
            --fail-on-high-severity
```

### Custom Validation Script

```python
#!/usr/bin/env python3
"""Custom Lambda security validation script"""

import sys
import argparse
from ha_connector.security import LambdaSecurityValidator, SecurityLevel, SecurityStatus

def main():
    parser = argparse.ArgumentParser(description='Validate Lambda security')
    parser.add_argument('--function-names', required=True,
                       help='Comma-separated list of function names')
    parser.add_argument('--fail-on-high-severity', action='store_true',
                       help='Fail if any HIGH severity issues found')

    args = parser.parse_args()

    validator = LambdaSecurityValidator()
    function_names = args.function_names.split(',')

    failed_functions = []

    for function_name in function_names:
        print(f"\\n🔍 Validating {function_name}...")

        try:
            results = validator.validate_function(function_name.strip())

            high_severity_failures = [
                r for r in results
                if r.check.level == SecurityLevel.HIGH
                and r.status in [SecurityStatus.FAIL, SecurityStatus.ERROR]
            ]

            if high_severity_failures and args.fail_on_high_severity:
                failed_functions.append(function_name)
                print(f"❌ {function_name}: {len(high_severity_failures)} HIGH severity issues")
                for result in high_severity_failures:
                    print(f"   - {result.check.name}: {result.message}")
            else:
                print(f"✅ {function_name}: Security validation passed")

        except Exception as e:
            print(f"🔥 {function_name}: Validation failed - {e}")
            failed_functions.append(function_name)

    if failed_functions:
        print(f"\\n❌ Security validation failed for: {', '.join(failed_functions)}")
        sys.exit(1)
    else:
        print(f"\\n✅ All {len(function_names)} functions passed security validation!")

if __name__ == "__main__":
    main()
```

## Monitoring Integration

### CloudWatch Metrics

```python
import boto3
from ha_connector.security import LambdaSecurityValidator, SecurityStatus

def publish_security_metrics():
    """Publish security validation metrics to CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')
    validator = LambdaSecurityValidator()

    # Get list of Lambda functions
    lambda_client = boto3.client('lambda')
    functions = lambda_client.list_functions()['Functions']

    total_functions = len(functions)
    compliant_functions = 0

    for function in functions:
        results = validator.validate_function(function['FunctionName'])

        # Check if function is compliant (no FAIL or ERROR status)
        is_compliant = all(
            result.status not in [SecurityStatus.FAIL, SecurityStatus.ERROR]
            for result in results
        )

        if is_compliant:
            compliant_functions += 1

    # Publish metrics
    cloudwatch.put_metric_data(
        Namespace='Lambda/Security',
        MetricData=[
            {
                'MetricName': 'TotalFunctions',
                'Value': total_functions,
                'Unit': 'Count'
            },
            {
                'MetricName': 'CompliantFunctions',
                'Value': compliant_functions,
                'Unit': 'Count'
            },
            {
                'MetricName': 'CompliancePercentage',
                'Value': (compliant_functions / total_functions) * 100,
                'Unit': 'Percent'
            }
        ]
    )
```

## Best Practices

### 1. Regular Validation

- Run security validation on every deployment
- Schedule weekly comprehensive scans
- Set up alerts for security violations

### 2. Policy Enforcement

- Fail CI/CD pipelines on HIGH severity issues
- Require security review for WARNING status items
- Document approved exceptions

### 3. Remediation Workflow

1. **Immediate**: Address CRITICAL and HIGH severity issues
2. **Weekly**: Review and plan MEDIUM severity fixes
3. **Monthly**: Evaluate LOW severity and INFO items
4. **Quarterly**: Review and update security policies

### 4. Documentation

- Maintain inventory of all Lambda functions
- Document security exceptions and approvals
- Keep remediation procedures up to date

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are configured
2. **Permissions**: Validator needs `lambda:GetFunction` and `iam:ListAttachedRolePolicies`
3. **Region**: Specify correct AWS region for your functions
4. **Function Names**: Use exact function names or ARNs

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now validation will show detailed debug information
validator = LambdaSecurityValidator()
results = validator.validate_function("my-function")
```

## Support

For issues or questions:

- Check the [API Documentation](../api/security_validation_api.md)
- Review [Common Issues](../troubleshooting/common_issues.md)
- See [Examples](../examples/) for more use cases
