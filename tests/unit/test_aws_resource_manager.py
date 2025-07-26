"""
High-Level AWS Resource Manager Tests

Tests for the main AWSResourceManager class that orchestrates AWS service operations.
These tests focus on manager coordination and resource routing, not individual
service implementation.
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch

import pytest

from ha_connector.adapters.aws_manager import (
    AWSIAMManager,
    AWSLambdaManager,
    AWSLogsManager,
    AWSResourceManager,
    AWSResourceResponse,
    AWSResourceType,
    AWSSSMManager,
    AWSTriggerManager,
)


# Shared test fixtures
@pytest.fixture(name="_boto3_session")
def mock_boto3_session() -> Generator[Mock, None, None]:
    """Mock boto3 session to avoid real AWS connections"""
    with patch("ha_connector.adapters.aws_manager.boto3.Session") as mock_session:
        mock_session.return_value.client.return_value = Mock()
        yield mock_session


@pytest.fixture(name="aws_manager")
def fast_aws_manager(
    _boto3_session: Mock,
) -> AWSResourceManager:
    """Fast AWS manager using mocked boto3 for performance testing"""
    return AWSResourceManager(region="us-east-1")


@pytest.fixture(name="lambda_spec")
def sample_lambda_spec() -> dict[str, str]:
    """Shared Lambda resource spec for testing"""
    return {
        "function_name": "test-function",
        "runtime": "python3.11",
        "handler": "lambda_function.lambda_handler",
        "role_arn": "arn:aws:iam::123456789012:role/test-role",
        "package_path": "/path/to/package.zip",
    }


class TestAWSResourceManager:
    """Test AWS Resource Manager orchestration functionality"""

    def test_init_with_valid_region(self, _boto3_session: Mock) -> None:
        """Test initialization with valid region"""
        manager = AWSResourceManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_init_with_different_region(self, _boto3_session: Mock) -> None:
        """Test initialization with different region"""
        manager = AWSResourceManager(region="us-west-2")
        assert manager.region == "us-west-2"

    def test_manager_instances_created(self, aws_manager: AWSResourceManager) -> None:
        """Test that sub-managers are properly initialized"""
        assert isinstance(aws_manager.lambda_manager, AWSLambdaManager)
        assert isinstance(aws_manager.iam_manager, AWSIAMManager)
        assert isinstance(aws_manager.ssm_manager, AWSSSMManager)
        assert isinstance(aws_manager.logs_manager, AWSLogsManager)
        assert isinstance(aws_manager.trigger_manager, AWSTriggerManager)

    def test_create_lambda_resource(
        self, aws_manager: AWSResourceManager, lambda_spec: dict[str, Any]
    ) -> None:
        """Test creating Lambda resource through main manager"""
        # Mock the lambda manager with a valid spec
        with patch.object(
            aws_manager.lambda_manager, "create_or_update"
        ) as mock_create:
            mock_create.return_value = AWSResourceResponse(
                status="success", resource={"function_name": "test-function"}
            )

            result = aws_manager.create_resource(AWSResourceType.LAMBDA, lambda_spec)
            assert result.status == "success"
            mock_create.assert_called_once()

    def test_read_resource(self, aws_manager: AWSResourceManager) -> None:
        """Test reading resources through main manager"""
        with patch.object(aws_manager.lambda_manager, "read") as mock_read:
            mock_read.return_value = AWSResourceResponse(
                status="success", resource={"function_name": "test-function"}
            )

            result = aws_manager.read_resource(AWSResourceType.LAMBDA, "test-function")
            assert result.status == "success"
            mock_read.assert_called_once_with("test-function")

    def test_delete_resource(self, aws_manager: AWSResourceManager) -> None:
        """Test deleting resources through main manager"""
        with patch.object(aws_manager.lambda_manager, "delete") as mock_delete:
            mock_delete.return_value = AWSResourceResponse(status="success")

            result = aws_manager.delete_resource(
                AWSResourceType.LAMBDA, "test-function"
            )
            assert result.status == "success"
            mock_delete.assert_called_once_with("test-function")

    def test_create_iam_resource(self, aws_manager: AWSResourceManager) -> None:
        """Test creating IAM resource through main manager"""
        iam_spec = {
            "resource_type": "role",
            "name": "test-role",
            "assume_role_policy": {"Version": "2012-10-17"},
            "description": "Test role",
        }

        with patch.object(aws_manager.iam_manager, "create_or_update") as mock_create:
            mock_create.return_value = AWSResourceResponse(
                status="success", resource={"role_name": "test-role"}
            )

            result = aws_manager.create_resource(AWSResourceType.IAM, iam_spec)
            assert result.status == "success"
            mock_create.assert_called_once()
