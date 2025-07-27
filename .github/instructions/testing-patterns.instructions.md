---
description: "Testing patterns and best practices for HA External Connector"
applyTo: "**/test_*.py,**/tests/**/*.py,**/*_test.py"
---

# Testing Patterns

## AWS Testing with Moto (MANDATORY)

### Standard Test Setup

```python
from moto import mock_aws
import boto3
import pytest
from typing import Iterator

@pytest.fixture(name="aws_framework")
def aws_test_framework() -> Iterator[AWSTestFramework]:
    """Provide an AWS test framework instance with moto."""
    with mock_aws():
        yield AWSTestFramework()

@mock_aws
def test_lambda_deployment():
    """Test Lambda deployment using moto for realistic AWS mocking."""
    # Test implementation here
    lambda_client = boto3.client("lambda", region_name="us-east-1")
    result = lambda_client.list_functions()
    assert "Functions" in result
```

### Prohibited Patterns (DO NOT USE)

```python
# ❌ NEVER: Manual mocking of AWS services
@patch("boto3.client")
def test_bad_aws_mocking(mock_boto3):
    mock_client = MagicMock()
    # This bypasses realistic AWS behavior

# ❌ NEVER: Patching individual AWS methods
@patch("ha_connector.adapters.aws_manager.AWSLambdaManager.create_function")
def test_bad_method_patching(mock_create):
    # This breaks AWS service integration testing
```

## Fixture Design Patterns

### Dynamic Secret Generation

```python
import secrets
import pytest

@pytest.fixture(name="test_secret", scope="session")
def test_secret_fixture() -> str:
    """Generate a secure test secret for the session."""
    return f"test-secret-{secrets.token_urlsafe(16)}"

@pytest.fixture(name="test_config")
def test_config_fixture(test_secret: str) -> dict:
    """Generate test configuration with dynamic secrets."""
    return {
        "alexa_skill_id": f"amzn1.ask.skill.{secrets.token_urlsafe(22)}",
        "client_secret": test_secret,
        "verification_token": f"token-{secrets.token_urlsafe(12)}",
    }
```

### Performance-Optimized Fixtures

```python
@pytest.fixture(name="aws_clients", scope="session")
def aws_clients_fixture() -> dict:
    """Session-scoped AWS clients for performance."""
    with mock_aws():
        return {
            "lambda": boto3.client("lambda", region_name="us-east-1"),
            "iam": boto3.client("iam", region_name="us-east-1"),
            "ssm": boto3.client("ssm", region_name="us-east-1"),
        }
```

## Test Organization Standards

### Test Class Structure

```python
class TestServiceInstaller:
    """Test class following naming and organization standards."""

    def setup_method(self) -> None:
        """Setup method using moto for fast execution."""
        with mock_aws():
            self.manager = ServiceInstaller()

    def test_successful_deployment(self) -> None:
        """Test successful deployment scenario."""
        # Test implementation
        pass

    def test_deployment_failure_handling(self) -> None:
        """Test error handling in deployment."""
        # Test implementation
        pass
```

### Test Data Management

```python
@pytest.fixture(name="sample_lambda_code")
def sample_lambda_code_fixture() -> bytes:
    """Provide sample Lambda deployment package."""
    import zipfile
    import io

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr("lambda_function.py", "def lambda_handler(event, context): return {'statusCode': 200}")
    return zip_buffer.getvalue()
```

## Assertion Patterns

### AWS Resource Validation

```python
def assert_lambda_function_exists(lambda_client, function_name: str) -> None:
    """Assert that a Lambda function exists with correct configuration."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name
    assert response["Configuration"]["Runtime"] == "python3.11"
    assert response["Configuration"]["State"] == "Active"

def assert_iam_role_has_policy(iam_client, role_name: str, policy_arn: str) -> None:
    """Assert that an IAM role has the expected policy attached."""
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p["PolicyArn"] for p in response["AttachedPolicies"]]
    assert policy_arn in policy_arns
```

## Performance Requirements

- Individual test execution: < 0.5 seconds
- Full test suite: < 20 seconds total
- Use session-scoped fixtures for expensive operations
- Batch AWS operations where possible
- Clean up resources in teardown methods

## Test Documentation Standards

```python
def test_complex_deployment_scenario(aws_framework) -> None:
    """
    Test complex deployment scenario with multiple AWS resources.

    This test verifies:
    1. Lambda function creation with correct configuration
    2. IAM role and policy attachment
    3. CloudWatch log group creation
    4. Error handling for resource conflicts
    """
    # Test implementation with clear steps
    pass
```
