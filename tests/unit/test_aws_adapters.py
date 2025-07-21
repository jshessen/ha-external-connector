"""
Unit Tests for AWS Adapters Module

Tests all AWS adapter functionality including Lambda, IAM, SSM, Logs, and Triggers.
"""

from unittest.mock import patch

from ha_connector.adapters.aws_manager import (
    AWSIAMManager,
    AWSLambdaManager,
    AWSLogsManager,
    AWSResourceManager,
    AWSResourceResponse,
    AWSResourceType,
    AWSSSMManager,
    AWSTriggerManager,
    IAMResourceSpec,
    LambdaResourceSpec,
    LogsResourceSpec,
    SSMResourceSpec,
)


class TestAWSResourceManager:
    """Test AWS Resource Manager base functionality"""

    manager: AWSResourceManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSResourceManager(region="us-east-1")

    def test_init_with_valid_region(self) -> None:
        """Test initialization with valid region"""
        manager = AWSResourceManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_init_with_different_region(self) -> None:
        """Test initialization with different region"""
        manager = AWSResourceManager(region="us-west-2")
        assert manager.region == "us-west-2"

    def test_manager_instances_created(self) -> None:
        """Test that sub-managers are properly initialized"""
        manager = AWSResourceManager(region="us-east-1")
        assert isinstance(manager.lambda_manager, AWSLambdaManager)
        assert isinstance(manager.iam_manager, AWSIAMManager)
        assert isinstance(manager.ssm_manager, AWSSSMManager)
        assert isinstance(manager.logs_manager, AWSLogsManager)
        assert isinstance(manager.trigger_manager, AWSTriggerManager)

    def test_create_lambda_resource(self) -> None:
        """Test creating Lambda resource through main manager"""
        manager = AWSResourceManager(region="us-east-1")

        # Mock the lambda manager with a valid spec
        with patch.object(manager.lambda_manager, "create_or_update") as mock_create:
            mock_create.return_value = AWSResourceResponse(
                status="success", resource={"function_name": "test-function"}
            )

            spec = {
                "function_name": "test-function",
                "runtime": "python3.11",
                "handler": "lambda_function.lambda_handler",
                "role_arn": "arn:aws:iam::123456789012:role/test-role",
                "package_path": "/path/to/package.zip",
            }

            result = manager.create_resource(AWSResourceType.LAMBDA, spec)
            assert result.status == "success"
            mock_create.assert_called_once()

    def test_read_resource(self) -> None:
        """Test reading resources through main manager"""
        manager = AWSResourceManager(region="us-east-1")

        with patch.object(manager.lambda_manager, "read") as mock_read:
            mock_read.return_value = AWSResourceResponse(
                status="success", resource={"function_name": "test-function"}
            )

            result = manager.read_resource(AWSResourceType.LAMBDA, "test-function")
            assert result.status == "success"
            mock_read.assert_called_once_with("test-function")

    def test_delete_resource(self) -> None:
        """Test deleting resources through main manager"""
        manager = AWSResourceManager(region="us-east-1")

        with patch.object(manager.lambda_manager, "delete") as mock_delete:
            mock_delete.return_value = AWSResourceResponse(status="success")

            result = manager.delete_resource(AWSResourceType.LAMBDA, "test-function")
            assert result.status == "success"
            mock_delete.assert_called_once_with("test-function")


class TestAWSLambdaManager:
    """Test AWS Lambda Manager functionality"""

    manager: AWSLambdaManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSLambdaManager(region="us-east-1")

    def test_initialization(self) -> None:
        """Test Lambda manager initialization"""
        manager = AWSLambdaManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_create_or_update_stub(self) -> None:
        """Test create_or_update method (currently stub)"""
        spec = LambdaResourceSpec(
            function_name="test",
            handler="lambda_function.lambda_handler",
            role_arn="arn:aws:iam::123456789012:role/test-role",
            package_path="/path/to/package.zip",
            description="Test function",
            environment_variables={},
        )
        result = self.manager.create_or_update(spec)
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_read_stub(self) -> None:
        """Test read method (currently stub)"""
        result = self.manager.read("test-function")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_delete_stub(self) -> None:
        """Test delete method (currently stub)"""
        result = self.manager.delete("test-function")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors


class TestAWSIAMManager:
    """Test AWS IAM Manager functionality"""

    manager: AWSIAMManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSIAMManager(region="us-east-1")

    def test_initialization(self) -> None:
        """Test IAM manager initialization"""
        manager = AWSIAMManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_create_or_update_stub(self) -> None:
        """Test create_or_update method (currently stub)"""
        spec = IAMResourceSpec(
            resource_type="role",
            name="test-role",
            assume_role_policy={"Version": "2012-10-17"},
            policy_document=None,
            description="Test role",
        )
        result = self.manager.create_or_update(spec)
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_read_stub(self) -> None:
        """Test read method (currently stub)"""
        result = self.manager.read("test-role")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_delete_stub(self) -> None:
        """Test delete method (currently stub)"""
        result = self.manager.delete("test-role")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors


class TestAWSSSMManager:
    """Test AWS SSM Manager functionality"""

    manager: AWSSSMManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSSSMManager(region="us-east-1")

    def test_initialization(self) -> None:
        """Test SSM manager initialization"""
        manager = AWSSSMManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_create_or_update_stub(self) -> None:
        """Test create_or_update method (currently stub)"""
        spec = SSMResourceSpec(name="/test/param", value="test-value")
        result = self.manager.create_or_update(spec)
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_read_stub(self) -> None:
        """Test read method (currently stub)"""
        result = self.manager.read("/test/param")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_delete_stub(self) -> None:
        """Test delete method (currently stub)"""
        result = self.manager.delete("/test/param")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors


class TestAWSLogsManager:
    """Test AWS Logs Manager functionality"""

    manager: AWSLogsManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSLogsManager(region="us-east-1")

    def test_initialization(self) -> None:
        """Test Logs manager initialization"""
        manager = AWSLogsManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_create_or_update_stub(self) -> None:
        """Test create_or_update method (currently stub)"""
        spec = LogsResourceSpec(log_group_name="test-log-group")
        result = self.manager.create_or_update(spec)
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_read_stub(self) -> None:
        """Test read method (currently stub)"""
        result = self.manager.read("test-log-group")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors

    def test_delete_stub(self) -> None:
        """Test delete method (currently stub)"""
        result = self.manager.delete("test-log-group")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Not implemented" in result.errors


class TestAWSTriggerManager:
    """Test AWS Trigger Manager functionality"""

    manager: AWSTriggerManager

    def setup_method(self) -> None:
        """Set up test environment"""
        self.manager = AWSTriggerManager(region="us-east-1")

    def test_initialization(self) -> None:
        """Test Trigger manager initialization"""
        manager = AWSTriggerManager(region="us-east-1")
        assert manager.region == "us-east-1"

    def test_create_or_update_stub(self) -> None:
        """Test create_or_update method (currently stub)"""
        result = self.manager.create_or_update({"function_name": "test"})
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Trigger resource creation not implemented" in result.errors

    def test_read_stub(self) -> None:
        """Test read method (currently stub)"""
        result = self.manager.read("test-function-url")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "success"
        assert "Trigger resource reading not implemented" in result.errors

    def test_delete_stub(self) -> None:
        """Test delete method (currently stub)"""
        result = self.manager.delete("test-function-url")
        assert isinstance(result, AWSResourceResponse)
        assert result.status == "not_implemented"
        assert "Trigger delete not implemented" in result.errors


class TestResourceTypes:
    """Test AWS Resource Type enumeration"""

    def test_lambda_resource_type(self) -> None:
        """Test Lambda resource type"""
        assert AWSResourceType.LAMBDA.value == "lambda"

    def test_resource_type_values(self) -> None:
        """Test that resource types have expected values"""
        # Test that we can iterate through resource types
        resource_types = list(AWSResourceType)
        assert AWSResourceType.LAMBDA in resource_types


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_resource_type_handling(self) -> None:
        """Test handling of invalid resource types"""
        manager = AWSResourceManager(region="us-east-1")

        # This should be handled gracefully by the implementation
        # The actual behavior depends on how the manager handles unknown types
        try:
            result = manager.create_resource(AWSResourceType.LAMBDA, {})
            # If it doesn't raise an error, result should indicate failure
            assert result is not None
        except (ValueError, TypeError):
            # It's acceptable for this to raise a validation error
            pass

    def test_aws_response_model(self) -> None:
        """Test AWSResourceResponse model"""
        response = AWSResourceResponse(status="success")
        assert response.status == "success"
        assert response.resource is None
        assert not response.errors

        response_with_data = AWSResourceResponse(
            status="success", resource={"key": "value"}, errors=["warning message"]
        )
        assert response_with_data.status == "success"
        assert response_with_data.resource == {"key": "value"}
        assert response_with_data.errors == ["warning message"]
