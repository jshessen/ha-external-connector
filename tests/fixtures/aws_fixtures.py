"""Unified AWS testing framework and fixtures."""

import secrets
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from ha_connector.adapters.aws_manager import AWSResourceResponse


class AWSTestFramework:
    """Unified framework for AWS service testing."""

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region
        self.mock_session = self._create_mock_session()
        self.lambda_client = self._create_mock_lambda_client()
        self.iam_client = self._create_mock_iam_client()
        self.ssm_client = self._create_mock_ssm_client()

    def _create_mock_session(self) -> MagicMock:
        """Create a mock boto3 session."""
        mock_session = MagicMock()
        mock_session.region_name = self.region

        def client_factory(  # pylint: disable=unused-argument
            service_name: str, **kwargs: Any  # noqa: ARG002
        ) -> Mock:
            if service_name == "lambda":
                return self.lambda_client
            if service_name == "iam":
                return self.iam_client
            if service_name == "ssm":
                return self.ssm_client
            return Mock()

        mock_session.client.side_effect = client_factory
        return mock_session

    def _create_mock_lambda_client(self) -> Mock:
        """Create a mock Lambda client with realistic responses."""
        mock_client = Mock()

        # Configure Lambda responses
        mock_client.list_functions.return_value = {
            "Functions": [],
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        function_arn = (
            f"arn:aws:lambda:{self.region}:123456789012:function:ha-test-function"
        )
        mock_client.create_function.return_value = {
            "FunctionName": "ha-test-function",
            "FunctionArn": function_arn,
            "Runtime": "python3.11",
            "State": "Active",
            "ResponseMetadata": {"HTTPStatusCode": 201},
        }

        mock_client.update_function_code.return_value = {
            "FunctionName": "ha-test-function",
            "LastModified": "2025-01-01T00:00:00.000+0000",
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        return mock_client

    def _create_mock_iam_client(self) -> Mock:
        """Create a mock IAM client with realistic responses."""
        mock_client = Mock()

        # Configure IAM responses
        mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException(
            {"Error": {"Code": "NoSuchEntity", "Message": "Role not found"}}, "GetRole"
        )

        mock_client.create_role.return_value = {
            "Role": {
                "RoleName": "ha-test-role",
                "Arn": "arn:aws:iam::123456789012:role/ha-test-role",
                "CreateDate": "2025-01-01T00:00:00Z",
            },
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        return mock_client

    def _create_mock_ssm_client(self) -> Mock:
        """Create a mock SSM client with realistic responses."""
        mock_client = Mock()

        # Configure SSM responses
        param_not_found = mock_client.exceptions.ParameterNotFound(
            {"Error": {"Code": "ParameterNotFound", "Message": "Parameter not found"}},
            "GetParameter",
        )
        mock_client.get_parameter.side_effect = param_not_found

        mock_client.put_parameter.return_value = {
            "Version": 1,
            "ResponseMetadata": {"HTTPStatusCode": 200},
        }

        return mock_client

    def _get_client(self, service_name: str) -> Mock:
        """Get a mock client for the specified service."""
        return self.mock_session.client(service_name)

    def create_stub_response(self, success: bool = True) -> AWSResourceResponse:
        """Create a stub AWS resource response for testing."""
        if success:
            return AWSResourceResponse(
                status="success",
                resource={"message": "Test operation successful"},
                errors=[],
            )
        return AWSResourceResponse(
            status="not_implemented", resource=None, errors=["Not implemented"]
        )


class DummyManager:
    """Dummy AWS manager for testing framework validation."""

    def __init__(self, region: str):
        self.region = region
        self.session = None

    def create_or_update(self, spec: Any) -> AWSResourceResponse:  # noqa: ARG002
        """Stub implementation that returns not_implemented response."""
        # pylint: disable=unused-argument
        return AWSResourceResponse(
            status="not_implemented", resource=None, errors=["Not implemented"]
        )

    def delete(self, resource_id: str) -> AWSResourceResponse:  # noqa: ARG002
        """Stub implementation that returns not_implemented response."""
        # pylint: disable=unused-argument
        return AWSResourceResponse(
            status="not_implemented", resource=None, errors=["Not implemented"]
        )


# Test parameters for parameterized tests across AWS managers
AWS_MANAGER_TEST_PARAMS = [
    (DummyManager, dict, {"key": "value", "test_param": "test_value"}),
]


@pytest.fixture(scope="session")
def aws_test_framework() -> Generator[AWSTestFramework, None, None]:
    """Session-scoped AWS test framework fixture."""
    framework = AWSTestFramework()
    yield framework


@pytest.fixture(scope="function", name="boto3_session")
def boto3_session_fixture(  # pylint: disable=redefined-outer-name
    aws_test_framework: AWSTestFramework,
) -> MagicMock:
    """Function-scoped boto3 session fixture."""
    return aws_test_framework.mock_session


@pytest.fixture(scope="function")
def aws_environment() -> Generator[dict[str, str], None, None]:
    """AWS environment variables for testing."""
    # Generate secure test credentials
    access_key = f"AKIA{secrets.token_hex(8).upper()}"
    secret_key = secrets.token_urlsafe(32)

    env_vars = {
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_DEFAULT_REGION": "us-east-1",
    }

    yield env_vars


@pytest.fixture(scope="function", name="mock_lambda_client")
def mock_lambda_client_fixture(  # pylint: disable=redefined-outer-name
    aws_test_framework: AWSTestFramework,
) -> Mock:
    """Function-scoped Lambda client fixture."""
    return aws_test_framework.lambda_client


@pytest.fixture(scope="function", name="mock_iam_client")
def mock_iam_client_fixture(  # pylint: disable=redefined-outer-name
    aws_test_framework: AWSTestFramework,
) -> Mock:
    """Function-scoped IAM client fixture."""
    return aws_test_framework.iam_client


@pytest.fixture(scope="function", name="mock_ssm_client")
def mock_ssm_client_fixture(  # pylint: disable=redefined-outer-name
    aws_test_framework: AWSTestFramework,
) -> Mock:
    """Function-scoped SSM client fixture."""
    return aws_test_framework.ssm_client
