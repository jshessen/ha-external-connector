"""AWS test fixtures for moto integration."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import boto3
import pytest
from moto import mock_aws

if TYPE_CHECKING:
    # Import AWS client types from mypy-boto3 packages
    from mypy_boto3_iam.client import IAMClient
    from mypy_boto3_lambda.client import LambdaClient
    from mypy_boto3_ssm.client import SSMClient

# Test parameters
AWS_MANAGER_TEST_PARAMS: dict[str, Any] = {
    "test_region": "us-east-1",
    "test_account_id": "123456789012",
    "lambda_function_name": "ha-external-connector-test-function",
    "lambda_function_arn": (
        "arn:aws:lambda:us-east-1:123456789012:"
        "function:ha-external-connector-test-function"
    ),
    "iam_role_name": "ha-external-connector-test-role",
    "iam_role_arn": ("arn:aws:iam::123456789012:role/ha-external-connector-test-role"),
    "ssm_parameter_name": "/ha-external-connector/test/config",
    "lambda_timeout": 30,
    "lambda_memory_size": 128,
    "lambda_runtime": "python3.13",
    "lambda_handler": "lambda_function.lambda_handler",
    "lambda_environment_vars": {"TEST_MODE": "true", "LOG_LEVEL": "INFO"},
    "tags": {"Environment": "test", "Project": "ha-external-connector"},
}


class AWSTestFramework:
    """AWS testing framework with moto integration."""

    def __init__(self, region: str = "us-east-1") -> None:
        """Initialize the framework with a specific AWS region."""
        self.region = region

    @property
    def iam_client(self) -> IAMClient:
        """Get IAM client with explicit type annotation."""
        return boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            "iam", region_name=self.region
        )

    @property
    def lambda_client(self) -> LambdaClient:
        """Lambda client factory with proper type hints."""
        return boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            "lambda", region_name=self.region
        )

    @property
    def ssm_client(self) -> SSMClient:
        """Get SSM client with explicit type annotation."""
        return boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            "ssm", region_name=self.region
        )


def create_tags(tags_data: dict[str, Any]) -> list[dict[str, str]]:
    """Create a list of tags in the format required by AWS."""
    return [{"Key": str(key), "Value": str(value)} for key, value in tags_data.items()]


def _get_test_tags_for_ssm() -> list[dict[str, str]]:
    """Get test tags formatted for SSM."""
    return create_tags(AWS_MANAGER_TEST_PARAMS["tags"])


def _get_iam_role_config() -> dict[str, Any]:
    """Get IAM role configuration."""
    return {
        "RoleName": str(AWS_MANAGER_TEST_PARAMS["iam_role_name"]),
        "AssumeRolePolicyDocument": """{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }""",
        "Tags": create_tags(AWS_MANAGER_TEST_PARAMS["tags"]),
    }


def _get_ssm_parameter_config() -> dict[str, Any]:
    """Get SSM parameter configuration."""
    return {
        "Name": str(AWS_MANAGER_TEST_PARAMS["ssm_parameter_name"]),
        "Value": '{"test": "config"}',
        "Type": "SecureString",
        "Tags": _get_test_tags_for_ssm(),
    }


def _get_lambda_function_config() -> dict[str, Any]:
    """Get Lambda function configuration."""
    return {
        "FunctionName": str(AWS_MANAGER_TEST_PARAMS["lambda_function_name"]),
        "Runtime": str(AWS_MANAGER_TEST_PARAMS["lambda_runtime"]),
        "Role": str(AWS_MANAGER_TEST_PARAMS["iam_role_arn"]),
        "Handler": str(AWS_MANAGER_TEST_PARAMS["lambda_handler"]),
        "Code": {"ZipFile": b"fake code"},
        "Description": "Test Lambda function for HA External Connector",
        "Timeout": int(AWS_MANAGER_TEST_PARAMS["lambda_timeout"]),
        "MemorySize": int(AWS_MANAGER_TEST_PARAMS["lambda_memory_size"]),
        "Environment": {
            "Variables": dict(AWS_MANAGER_TEST_PARAMS["lambda_environment_vars"])
        },
    }


@pytest.fixture
def aws_framework() -> Iterator[AWSTestFramework]:
    """Provide an AWS test framework instance."""
    with mock_aws():
        framework = AWSTestFramework()
        yield framework


@pytest.fixture
def aws_lambda_function(aws_framework_instance: AWSTestFramework) -> dict[str, Any]:
    """Create a test Lambda function."""
    config = _get_lambda_function_config()
    response = aws_framework_instance.lambda_client.create_function(**config)
    # Convert TypedDict to regular dict for compatibility
    return dict(response)


@pytest.fixture
def aws_iam_role(aws_framework_instance: AWSTestFramework) -> dict[str, Any]:
    """Create a test IAM role."""
    config = _get_iam_role_config()
    response = aws_framework_instance.iam_client.create_role(**config)
    # Convert TypedDict to regular dict for compatibility
    return dict(response)


@pytest.fixture
def aws_ssm_parameter(aws_framework_instance: AWSTestFramework) -> dict[str, Any]:
    """Create a test SSM parameter."""
    config = _get_ssm_parameter_config()
    response = aws_framework_instance.ssm_client.put_parameter(**config)
    # Convert TypedDict to regular dict for compatibility
    return dict(response)
