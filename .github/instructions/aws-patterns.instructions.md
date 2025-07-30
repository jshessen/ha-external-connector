---
description: "AWS-specific coding patterns and best practices for HA External Connector"
applyTo: "**/aws_*.py,**/adapters/**/*.py,**/infrastructure/**/*.py"
---

# AWS Coding Patterns

## Lambda Function Architecture Patterns

### Transfer Block System for Shared Lambda Code

**INTENTIONAL DUPLICATE CODE MANAGEMENT:**

Lambda functions in this project use strategic code duplication with transfer blocks for optimal performance and deployment independence.

**Key Files:**

- `src/ha_connector/integrations/alexa/lambda_functions/oauth_gateway.py` (authentication)
- `src/ha_connector/integrations/alexa/lambda_functions/smart_home_bridge.py` (voice commands)

**Transfer Block Pattern:**

```python
# ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
# ║                    🚀 TRANSFER-READY CODE 🚀                ║
# ║ 📋 PURPOSE: Speed-optimized configuration for <500ms response ║
# ║ 🔄 STATUS: Ready for duplication across Lambda functions     ║
# ╚═══════════════════════════════════════════════════════════╝

def load_standardized_configuration(...):
    # Shared performance-critical code
    pass

# ╭─────────────────── TRANSFER BLOCK END ───────────────────╮
```

**Synchronization Rules:**

1. **DO NOT** eliminate duplicate code between these Lambda functions
2. **DO** copy transfer blocks when updating shared functionality
3. **DO** customize service-specific prefixes (`oauth_` → `bridge_`)
4. **DO** test both functions after synchronization

## Client Creation Patterns

### Preferred Pattern with Dependency Injection

```python
from typing import TYPE_CHECKING
import boto3

if TYPE_CHECKING:
    from types_boto3_lambda.client import LambdaClient
    from types_boto3_iam.client import IAMClient

class AWSManager:
    def __init__(
        self,
        region: str = "us-east-1",
        lambda_client: Optional["LambdaClient"] = None,
        iam_client: Optional["IAMClient"] = None,
    ) -> None:
        self.region = region
        self._lambda_client = lambda_client
        self._iam_client = iam_client

    @property
    def lambda_client(self) -> "LambdaClient":
        if self._lambda_client is None:
            self._lambda_client = boto3.client("lambda", region_name=self.region)  # pyright: ignore
        return self._lambda_client
```

### Error Handling Patterns

```python
from botocore.exceptions import ClientError
import logging

def handle_aws_operation(operation_name: str, aws_operation: callable) -> dict:
    """Standard AWS operation error handling pattern."""
    try:
        result = aws_operation()
        logging.info(f"{operation_name} completed successfully")
        return {"status": "success", "result": result}
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logging.error(f"{operation_name} failed: {error_code} - {error_message}")
        return {"status": "error", "error_code": error_code, "message": error_message}
    except Exception as e:
        logging.error(f"{operation_name} unexpected error: {str(e)}")
        return {"status": "error", "error_code": "UnexpectedError", "message": str(e)}
```

## Resource Management Patterns

### Lambda Function Configuration

```python
def get_lambda_config() -> dict:
    """Standard Lambda function configuration."""
    return {
        "Runtime": "python3.11",
        "Timeout": 30,
        "MemorySize": 256,
        "Environment": {"Variables": {}},
        "DeadLetterConfig": {"TargetArn": ""},
        "TracingConfig": {"Mode": "Active"},
    }
```

### IAM Policy Patterns

```python
def create_minimal_lambda_policy(function_name: str) -> dict:
    """Create minimal IAM policy for Lambda function."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": f"arn:aws:logs:*:*:log-group:/aws/lambda/{function_name}*",
            }
        ],
    }
```

## Naming Conventions

- Lambda functions: `ha-external-{service}-{environment}`
- IAM roles: `ha-external-{service}-role`
- IAM policies: `ha-external-{service}-policy`
- Log groups: `/aws/lambda/ha-external-{service}-{environment}`

## Resource Tagging Standards

```python
def get_standard_tags(service: str, environment: str = "development") -> dict:
    """Standard resource tags for all AWS resources."""
    return {
        "Project": "ha-external-connector",
        "Service": service,
        "Environment": environment,
        "ManagedBy": "ha-external-connector",
        "CreatedBy": "automation",
    }
```

## Security Best Practices

- Always use least privilege IAM policies
- Enable CloudTrail logging for all API calls
- Use AWS Secrets Manager for sensitive configuration
- Implement resource-based policies where applicable
- Enable VPC endpoints for private communication
