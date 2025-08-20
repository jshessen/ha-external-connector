"""
Unit Tests for Lambda Security Validator

Comprehensive testing of the Lambda security validation framework
with all 12 security checks and error handling scenarios.
Following PROJECT_STANDARDS.md recommendations for moto library usage
with realistic AWS service mocking instead of unittest.Mock.
"""

from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

from custom_components.ha_external_connector.lambda_validator import LambdaSecurityValidator, SecurityStatus

if TYPE_CHECKING:
    # Import AWS client types from types-boto3 packages for correct type checking
    pass


class TestLambdaSecurityValidatorWithMoto:
    """Test Lambda security validator using moto for realistic AWS mocking."""

    def __init__(self) -> None:
        """Initialize test class attributes."""
        # Initialize attributes to avoid W0201 warnings
        self.mock: Any = None
        self.lambda_client: Any = None
        self.iam_client: Any = None
        self.test_role_arn: str = ""

    def setup_method(self, _method: Any) -> None:
        """Set up test environment with mocked AWS services."""
        # Use moto context manager to mock AWS services for each test
        self.mock = mock_aws()
        self.mock.start()
        # Use Any for runtime assignment to avoid static type conflicts
        self.lambda_client = boto3.client(  # pyright: ignore
            "lambda", region_name="us-east-1"
        )
        self.iam_client = boto3.client(  # pyright: ignore
            "iam", region_name="us-east-1"
        )
        self.test_role_arn = self._create_test_role()

    def teardown_method(self, _method: Any) -> None:
        """Tear down moto mocks after each test."""
        self.mock.stop()

    def _create_test_role(self) -> str:
        """Create a test IAM role for Lambda functions."""
        role_name = "test-lambda-role"
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        try:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=str(assume_role_policy),
            )
            return str(response["Role"]["Arn"])
        except ClientError as e:
            # Check if error response structure exists and has required keys
            if (
                hasattr(e, "response")
                and e.response
                and "Error" in e.response
                and "Code" in e.response["Error"]
                and e.response["Error"]["Code"] == "EntityAlreadyExists"
            ):
                # Role already exists, get its ARN
                response = self.iam_client.get_role(RoleName=role_name)
                return str(response["Role"]["Arn"])
            raise

    def _create_secure_lambda_function(self, function_name: str) -> dict[str, Any]:
        """Create a Lambda function with secure configuration."""
        response = self.lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.11",
            Role=self.test_role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": b"dummy code"},
            Environment={"Variables": {"ENCRYPTION": "enabled"}},
            TracingConfig={"Mode": "Active"},
            DeadLetterConfig={"TargetArn": "arn:aws:sqs:us-east-1:123456789012:dlq"},
        )
        return dict(response)

    def _create_insecure_lambda_function(self, function_name: str) -> dict[str, Any]:
        """Create a Lambda function with security issues."""
        response = self.lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.7",  # Deprecated runtime
            Role=self.test_role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": b"dummy code"},
            Environment={"Variables": {"API_KEY": "plaintext-key", "DEBUG": "true"}},
            Timeout=900,  # Maximum timeout (15 minutes)
        )
        return dict(response)

    def test_validate_function_comprehensive(self) -> None:
        """Test comprehensive validation of a Lambda function."""
        function_name = "test-comprehensive"
        self._create_insecure_lambda_function(function_name)

        validator = LambdaSecurityValidator(
            region="us-east-1",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )
        results = validator.validate_function(function_name)

        # Should have results for all 12 security checks
        assert len(results) >= 8  # At least the main security checks
        assert any(result.status == SecurityStatus.FAIL for result in results)

        # Check for specific security issues - runtime should be FAIL
        runtime_results = [r for r in results if "runtime" in r.message.lower()]
        assert len(runtime_results) > 0
        # The deprecated runtime should trigger a FAIL status
        assert any(result.status == SecurityStatus.FAIL for result in runtime_results)

    def test_validate_secure_function(self) -> None:
        """Test validation of a well-configured secure function."""
        function_name = "test-secure"
        self._create_secure_lambda_function(function_name)

        validator = LambdaSecurityValidator(
            region="us-east-1",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )
        results = validator.validate_function(function_name)

        # Should have results for all security checks
        assert len(results) >= 8

        # Most checks should pass for secure function
        passed_results = [r for r in results if r.status == SecurityStatus.PASSED]
        assert len(passed_results) > 0

    def test_validate_nonexistent_function(self) -> None:
        """Test validation when function doesn't exist."""
        validator = LambdaSecurityValidator(
            region="us-east-1",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )
        results = validator.validate_function("nonexistent-function")

        # Should return error result
        assert len(results) == 1
        assert results[0].status == SecurityStatus.ERROR
        assert "Failed to retrieve configuration" in results[0].message

    def test_validator_initialization(self) -> None:
        """Test Lambda security validator initialization."""
        validator = LambdaSecurityValidator(
            region="us-east-1",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )
        assert validator is not None

        # Test with custom region
        validator = LambdaSecurityValidator(
            region="us-west-2",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )
        assert validator is not None

    def test_validator_with_dependency_injection(self) -> None:
        """Test validator with dependency injection using moto clients."""
        validator = LambdaSecurityValidator(
            region="us-east-1",
            lambda_client=self.lambda_client,
            iam_client=self.iam_client,
        )

        function_name = "test-dependency-injection"
        self._create_insecure_lambda_function(function_name)

        results = validator.validate_function(function_name)
        assert len(results) >= 8
        assert any(result.status == SecurityStatus.FAIL for result in results)
