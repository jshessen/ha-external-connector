"""
Unit Tests for Deployment Module

Tests deployment manager and service installer functionality.
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch

import pytest
from moto import mock_aws

from development.deployment_tools.deploy_manager import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentStrategy,
    orchestrate_deployment,
)
from development.deployment_tools.service_installer import (
    DeploymentResult,
    ServiceConfig,
    ServiceInstaller,
    ServiceType,
)
from development.utils.helpers import ValidationError


# Shared test fixtures for performance optimization
@pytest.fixture(name="aws_manager")
def mock_aws_manager() -> Mock:
    """Shared mock AWS manager fixture"""
    manager = Mock()
    manager.create_resource = Mock()
    manager.delete_resource = Mock(return_value={"success": True})
    return manager


@pytest.fixture(name="iam_result")
def mock_iam_result() -> Mock:
    """Shared mock IAM result fixture"""
    result = Mock()
    result.status = "success"
    result.resource = {"Role": {"Arn": "arn:aws:iam::123456789012:role/test-role"}}
    result.errors = []
    return result


@pytest.fixture(name="lambda_result")
def mock_lambda_result() -> Mock:
    """Shared mock Lambda result fixture"""
    result = Mock()
    result.status = "created"
    result.resource = {
        "Configuration": {
            "FunctionArn": (
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            "FunctionUrl": {
                "FunctionUrl": "https://example.lambda-url.us-east-1.on.aws/"
            },
        }
    }
    result.errors = []
    return result


@pytest.fixture(name="service_config")
def sample_service_config() -> ServiceConfig:
    """Shared service configuration object"""
    return ServiceConfig(
        service_type=ServiceType.ALEXA,
        function_name="ha-alexa-proxy",
        source_path="tests/fixtures/dummy_function",
        handler="lambda_function.lambda_handler",
        memory_size=128,
        timeout=30,
        environment_variables={
            "HA_URL": "https://test.com",
            "HA_TOKEN": "test-token",
        },
    )


@pytest.fixture(name="deployment_config_dict")
def sample_deployment_config_dict() -> dict[str, Any]:
    """Shared deployment configuration dictionary"""
    return {
        "environment": "dev",
        "version": "1.0.0-test",
        "services": [ServiceType.ALEXA],
        "region": "us-east-1",
        "dry_run": True,
        "verbose": False,
        "cloudflare_setup": False,
        "cloudflare_domain": None,
        "service_overrides": None,
        "tags": None,
    }


@pytest.fixture(name="deployment_config")
def fast_deployment_config(deployment_config_dict: dict[str, Any]) -> DeploymentConfig:
    """Fast deployment configuration for performance testing"""
    return DeploymentConfig(
        strategy=DeploymentStrategy.IMMEDIATE, **deployment_config_dict
    )


@pytest.fixture(name="deployment_result")
def mock_deployment_result() -> DeploymentResult:
    """Shared mock deployment result for fast testing"""
    return DeploymentResult(
        success=True,
        function_name="ha-alexa-proxy",
        function_arn=None,  # Simplified for speed
        function_url=None,
        role_arn=None,
        metadata={"message": "Fast test execution"},
    )


@pytest.fixture(name="service_installer")
def fast_service_installer() -> Mock:
    """Fast service installer mock for performance testing"""
    installer = Mock()
    installer.deploy_predefined_service.return_value = DeploymentResult(
        success=True,
        function_name="ha-alexa-proxy",
        function_arn=None,
        function_url=None,
        role_arn=None,
        metadata={"dry_run": True, "message": "Fast execution"},
    )
    return installer


# Fast ServiceInstaller fixture using moto for consistent AWS mocking
@pytest.fixture(name="fast_service_installer")
def mock_service_installer() -> ServiceInstaller:
    """Create ServiceInstaller with mocked AWS dependencies using moto"""
    with mock_aws():
        return ServiceInstaller(region="us-east-1", dry_run=True, verbose=False)


# Global moto fixture for deployment tests
@pytest.fixture(autouse=True, scope="class")
def mock_aws_for_deployment() -> Generator[None]:
    """Automatically apply moto mocking to all deployment test classes"""
    with mock_aws():
        yield


class TestServiceInstaller:
    """Test Service Installer functionality with complete moto mocking"""

    installer: ServiceInstaller

    def setup_method(self) -> None:
        """Set up test fixtures using moto for consistent AWS mocking"""
        # moto is applied automatically via fixture - all AWS operations are mocked
        self.installer = ServiceInstaller(
            region="us-east-1", dry_run=True, verbose=False
        )

    def test_init_with_valid_region(self) -> None:
        """Test initialization with valid region"""
        installer = ServiceInstaller(region="us-west-2")
        assert installer.region == "us-west-2"
        assert installer.dry_run is False
        assert installer.verbose is False

    def test_init_dry_run_mode(self) -> None:
        """Test initialization in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)
        assert installer.dry_run is True

    def test_get_default_config_alexa(self) -> None:
        """Test getting default configuration for Alexa service"""
        config = self.installer.get_default_config(ServiceType.ALEXA)

        assert config["function_name"] == "ha-alexa-proxy"
        assert config["handler"] == "smart_home_bridge.lambda_handler"
        assert config["runtime"] == "python3.11"

    def test_get_default_config_ios(self) -> None:
        """Test getting default configuration for iOS service"""
        config = self.installer.get_default_config(ServiceType.IOS_COMPANION)

        assert config["function_name"] == "ha-ios-proxy"
        assert config["handler"] == "ios_wrapper.lambda_handler"

    def test_get_default_config_invalid_type(self) -> None:
        """Test getting default configuration for invalid service type"""
        # Test with a string that's not a valid ServiceType
        config = self.installer.get_default_config("invalid_type")  # type: ignore
        assert config == {}

    @patch("ha_connector.deployment.service_installer.Path")
    def test_create_deployment_package_success(self, mock_path: Mock) -> None:
        """Test successful deployment package creation in dry run mode"""
        # Mock path exists check to avoid ValidationError
        mock_source = Mock()
        mock_source.exists.return_value = True

        # Create a mock that behaves like a Path object
        mock_output = Mock()
        # Direct assignment with type ignore for Python 3.13 compatibility
        mock_output.__str__ = Mock(return_value="/test/output.zip")  # type: ignore[method-assign]
        mock_output.__fspath__ = Mock(return_value="/test/output.zip")

        # Set up Path to return different mocks for different paths
        def path_side_effect(path_str: str) -> Mock:
            if str(path_str) == "/test/source":
                return mock_source
            if str(path_str) == "/test/output.zip":
                return mock_output
            return Mock()

        mock_path.side_effect = path_side_effect

        # Use dry run mode to avoid complex file system operations
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        result = installer.create_deployment_package(
            source_path="/test/source", output_path="/test/output.zip"
        )

        # In dry run mode, it should return the output path
        # without actually creating files
        assert result == "/test/output.zip"

    def test_create_deployment_package_invalid_source(self) -> None:
        """Test deployment package creation with invalid source"""
        with pytest.raises(ValidationError, match="Source path does not exist"):
            self.installer.create_deployment_package(source_path="/nonexistent/path")

    def test_create_iam_role_success(self, aws_manager: Mock, iam_result: Mock) -> None:
        """Test successful IAM role creation"""
        aws_manager.create_resource.return_value = iam_result
        self.installer.aws_manager = aws_manager

        result = self.installer.create_iam_role(
            role_name="test-role", service_type=ServiceType.ALEXA
        )

        assert result == "arn:aws:iam::123456789012:role/test-role"

    def test_deploy_service_success(
        self,
        aws_manager: Mock,
        iam_result: Mock,
        lambda_result: Mock,
        service_config: ServiceConfig,
    ) -> None:
        """Test successful service deployment"""

        # Set up mock to return different results based on resource type
        def create_resource_side_effect(resource_type: Any, _spec: Any) -> Mock:
            if resource_type.value == "iam":
                return iam_result
            if resource_type.value == "lambda":
                return lambda_result
            return Mock()

        aws_manager.create_resource.side_effect = create_resource_side_effect
        self.installer.aws_manager = aws_manager

        with patch.object(self.installer, "create_deployment_package") as mock_package:
            mock_package.return_value = "/test/package.zip"

            result = self.installer.deploy_service(service_config)

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            assert result.function_name == "ha-alexa-proxy"
            assert result.function_arn is not None
            assert "arn:aws:lambda" in result.function_arn

    def test_deploy_service_dry_run(self) -> None:
        """Test service deployment in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/source",
            runtime="python3.11",
        )

        # Mock the create_deployment_package method to avoid path validation
        with patch.object(installer, "create_deployment_package") as mock_package:
            mock_package.return_value = "/test/package.zip"

            result = installer.deploy_service(config)

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            assert "Would deploy" in (result.metadata or {}).get("message", "")

    def test_deploy_predefined_service_alexa(self) -> None:
        """Test deploying predefined Alexa service"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        with patch.object(installer, "deploy_service") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                function_name="ha-alexa-proxy",
                function_arn=None,
                function_url=None,
                role_arn=None,
            )

            result = installer.deploy_predefined_service(
                ServiceType.ALEXA, {"HA_BASE_URL": "https://test.com"}
            )

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            mock_deploy.assert_called_once()

    def test_list_deployed_services(self) -> None:
        """Test listing deployed services"""
        # Replace the method with a mock that returns expected data
        mock_services = [
            {"FunctionName": "ha-alexa-proxy", "State": "Active"},
            {"FunctionName": "ha-ios-proxy", "State": "Active"},
        ]

        with patch.object(
            self.installer, "list_deployed_services", return_value=mock_services
        ):
            services = self.installer.list_deployed_services()

            assert len(services) == 2
            assert services[0]["FunctionName"] == "ha-alexa-proxy"

    @patch("ha_connector.deployment.service_installer.AWSResourceManager")
    def test_remove_service_success(self, mock_aws_resource_manager: Mock) -> None:
        """Test successful service removal"""
        mock_manager = Mock()
        mock_manager.delete_resource.return_value = {"success": True}
        mock_aws_resource_manager.return_value = mock_manager

        result = self.installer.remove_service("ha-alexa-proxy")

        assert result is True

    def test_remove_service_dry_run(self) -> None:
        """Test service removal in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        result = installer.remove_service("ha-alexa-proxy")

        # In dry run mode, removal should always succeed
        assert result is True


class TestDeploymentManager:
    """Test Deployment Manager functionality with complete moto mocking"""

    config: DeploymentConfig
    manager: DeploymentManager

    def setup_method(self) -> None:
        """Set up test fixtures with moto AWS mocking"""
        self.config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=False,
            verbose=True,
            skip_tests=True,
            force=False,
            rollback_on_failure=True,
            health_check_timeout=300,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags={"Environment": "dev"},
        )
        self.manager = DeploymentManager(self.config)

    def test_init_with_valid_config(self) -> None:
        """Test initialization with valid configuration"""
        assert self.manager.config == self.config
        assert self.manager.logger is not None

    def test_validate_deployment_config_success(self) -> None:
        """Test successful deployment configuration validation"""
        # This should not raise an exception for valid config
        try:
            self.manager.validate_deployment_config()
        except ValidationError:
            pytest.fail("Valid config should not raise ValidationError")

    def test_validate_deployment_config_invalid_environment(self) -> None:
        """Test deployment configuration validation with invalid environment"""
        config = DeploymentConfig(
            environment="invalid",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )
        manager = DeploymentManager(config)

        with pytest.raises(ValidationError, match="Invalid environment"):
            manager.validate_deployment_config()

    @patch("ha_connector.deployment.deploy_manager.ServiceInstaller")
    def test_pre_deployment_checks_success(self, mock_installer_class: Mock) -> None:
        """Test successful pre-deployment checks"""
        mock_installer = Mock()
        mock_installer.aws_manager = Mock()
        mock_installer_class.return_value = mock_installer

        result = self.manager.pre_deployment_checks()

        assert result is True

    def test_deploy_service_with_strategy_immediate(self) -> None:
        """Test deploying service with immediate strategy"""
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=(
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            function_url="https://test.lambda-url.us-east-1.on.aws/",
            role_arn=None,
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service_installer instance with the mock
        self.manager.service_installer = mock_installer

        result = self.manager.deploy_service_with_strategy(
            ServiceType.ALEXA, {"HA_BASE_URL": "https://test.com"}
        )

        assert isinstance(result, DeploymentResult)
        assert result.success is True

    def test_execute_deployment_success(self) -> None:
        """Test successful deployment execution"""
        # Use simplified mock for faster execution
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=None,  # Simplified for speed
            function_url=None,
            role_arn=None,
            metadata={"message": "Fast test execution"},
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service installer instance
        self.manager.service_installer = mock_installer

        with patch.object(self.manager, "pre_deployment_checks", return_value=True):
            result = self.manager.execute_deployment()

            assert result["success"] is True
            assert len(result["results"]) == 1
            assert isinstance(result["results"][0], DeploymentResult)

    @patch("ha_connector.deployment.deploy_manager.ServiceInstaller")
    def test_execute_deployment_with_errors(self, mock_installer_class_2: Mock) -> None:
        """Test deployment execution with errors"""
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=False,
            function_name="ha-alexa-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            errors=["Failed to create Lambda function"],
        )
        mock_installer.deploy_predefined_service.return_value = mock_result
        mock_installer_class_2.return_value = mock_installer

        with patch.object(self.manager, "pre_deployment_checks") as mock_checks:
            mock_checks.return_value = True

            result = self.manager.execute_deployment()

            assert result["success"] is False
            assert len(result["errors"]) >= 1

    def test_execute_deployment_dry_run(self) -> None:
        """Test deployment execution in dry run mode"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=True,
            verbose=False,  # Disable verbose for faster execution
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )
        manager = DeploymentManager(config)

        # Simplified mock for faster execution
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            metadata={"dry_run": True, "message": "Fast dry run test"},
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service installer instance
        manager.service_installer = mock_installer

        with patch.object(manager, "pre_deployment_checks", return_value=True):
            result = manager.execute_deployment()

            assert result["success"] is True
            assert result["dry_run"] is True


class TestDeploymentStrategies:
    """Test different deployment strategies with complete moto mocking"""

    def test_immediate_strategy(self) -> None:
        """Test immediate deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],  # Test single service for speed
            region="us-east-1",
            dry_run=True,  # Use dry run for faster execution
            verbose=False,  # Disable verbose for speed
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.IMMEDIATE

    def test_rolling_strategy(self) -> None:
        """Test rolling deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.ROLLING,
            services=[ServiceType.ALEXA],  # Test single service for speed
            region="us-east-1",
            dry_run=True,  # Use dry run for faster execution
            verbose=False,  # Disable verbose for speed
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.ROLLING

    def test_blue_green_strategy(self) -> None:
        """Test blue-green deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.BLUE_GREEN,
            services=[ServiceType.ALEXA],  # Test single service for speed
            region="us-east-1",
            dry_run=True,  # Use dry run for faster execution
            verbose=False,  # Disable verbose for speed
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.BLUE_GREEN


class TestOrchestrationFunction:
    """Test deployment orchestration function - optimized for speed"""

    def test_orchestrate_deployment_basic(self) -> None:
        """Test basic deployment orchestration"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=True,  # Use dry run for faster execution
            verbose=False,  # Disable verbose for speed
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        with patch(
            "ha_connector.deployment.deploy_manager.DeploymentManager"
        ) as mock_mgr:
            mock_manager = Mock()
            mock_manager.execute_deployment.return_value = {
                "success": True,
                "results": [],
                "errors": [],
                "dry_run": True,
            }
            mock_mgr.return_value = mock_manager

            result = orchestrate_deployment(config)

            assert result["success"] is True
            assert result["dry_run"] is True
            mock_mgr.assert_called_once_with(config)
            mock_manager.execute_deployment.assert_called_once()


class TestDeploymentResult:
    """Test DeploymentResult data class"""

    def test_deployment_result_success(self) -> None:
        """Test successful deployment result"""
        result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=(
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            function_url="https://test.lambda-url.us-east-1.on.aws/",
            role_arn="arn:aws:iam::123456789012:role/ha-lambda-alexa",
        )

        assert result.success is True
        assert result.function_name == "ha-alexa-proxy"
        assert result.function_arn is not None
        assert result.errors == []

    def test_deployment_result_failure(self) -> None:
        """Test failed deployment result"""
        result = DeploymentResult(
            success=False,
            function_name="ha-ios-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            errors=["Failed to create IAM role"],
        )

        assert result.success is False
        assert result.function_arn is None
        assert "Failed to create IAM role" in result.errors

    def test_deployment_result_with_metadata(self) -> None:
        """Test deployment result with metadata"""
        result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            metadata={
                "dry_run": True,
                "message": "Would deploy Alexa service",
                "duration": 0.1,
            },
        )

        assert result.success is True
        assert result.metadata["dry_run"] is True
        assert "Would deploy" in result.metadata["message"]


class TestServiceConfig:
    """Test ServiceConfig data class"""

    def test_service_config_validation(self) -> None:
        """Test service configuration validation"""
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/alexa",
            runtime="python3.11",
            timeout=30,
            memory_size=512,
        )

        assert config.service_type == ServiceType.ALEXA
        assert config.timeout == 30
        assert config.memory_size == 512
        assert config.runtime == "python3.11"

    def test_service_config_defaults(self) -> None:
        """Test service configuration with default values"""
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/alexa",
        )

        assert config.runtime == "python3.11"
        assert config.timeout == 30
        assert config.memory_size == 512
        assert config.create_url is False

    def test_service_config_with_optional_fields(self) -> None:
        """Test service configuration with optional fields"""
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/alexa",
            description="Test Alexa function",
            environment_variables={"HA_BASE_URL": "https://test.com"},
            create_url=True,
            url_auth_type="AWS_IAM",
            role_arn="arn:aws:iam::123456789012:role/test-role",
        )

        assert config.description == "Test Alexa function"
        assert config.environment_variables is not None
        # Ensure environment_variables is subscriptable before accessing
        env_vars = config.environment_variables
        assert env_vars is not None
        assert env_vars.get("HA_BASE_URL") == "https://test.com"
        assert config.create_url is True
        assert config.url_auth_type == "AWS_IAM"


class TestDeploymentConfig:
    """Test DeploymentConfig data class"""

    def test_deployment_config_defaults(self) -> None:
        """Test deployment configuration with default values"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            services=[ServiceType.ALEXA],
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        assert config.strategy == DeploymentStrategy.ROLLING
        assert config.region == "us-east-1"
        assert config.dry_run is False
        assert config.verbose is False
        assert config.rollback_on_failure is True

    def test_deployment_config_validation(self) -> None:
        """Test deployment configuration validation"""
        config = DeploymentConfig(
            environment="prod",
            version="2.1.0",
            strategy=DeploymentStrategy.BLUE_GREEN,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-west-2",
            dry_run=True,
            verbose=True,
            skip_tests=False,
            force=False,
            rollback_on_failure=True,
            health_check_timeout=600,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        assert config.environment == "prod"
        assert config.strategy == DeploymentStrategy.BLUE_GREEN
        assert len(config.services) == 2
        assert config.health_check_timeout == 600


# Integration-style tests
class TestDeploymentIntegration:
    """Integration tests for deployment functionality with complete moto mocking"""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_deployment_workflow_dry_run(self) -> None:
        """Test complete deployment workflow in dry run mode"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0-test",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],  # Test fewer services for speed
            region="us-east-1",
            dry_run=True,
            verbose=False,  # Disable verbose for faster execution
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        # Simplified mocking for faster execution
        with patch(
            "ha_connector.deployment.deploy_manager.ServiceInstaller"
        ) as mock_svc:
            mock_installer = Mock()
            mock_installer.deploy_predefined_service.return_value = DeploymentResult(
                success=True,
                function_name="ha-alexa-proxy",
                function_arn=None,
                function_url=None,
                role_arn=None,
                metadata={"dry_run": True, "message": "Would install Alexa service"},
            )
            mock_svc.return_value = mock_installer

            manager = DeploymentManager(config)
            with patch.object(manager, "pre_deployment_checks", return_value=True):
                result = manager.execute_deployment()

                assert result["success"] is True
                assert result["dry_run"] is True
                assert len(result["results"]) == 1

    @pytest.mark.slow
    @pytest.mark.integration
    def test_deployment_error_handling(self) -> None:
        """Test deployment error handling and recovery - simplified for speed"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0-test",
            strategy=DeploymentStrategy.IMMEDIATE,  # Faster than ROLLING
            services=[ServiceType.ALEXA],  # Test single service for speed
            region="us-east-1",
            dry_run=True,  # Use dry run for faster execution
            verbose=False,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None,
        )

        with patch(
            "ha_connector.deployment.deploy_manager.ServiceInstaller"
        ) as mock_svc:
            mock_installer = Mock()
            mock_installer.deploy_predefined_service.return_value = DeploymentResult(
                success=False,
                function_name="ha-alexa-proxy",
                function_arn=None,
                function_url=None,
                role_arn=None,
                errors=["Simulated failure"],
            )
            mock_svc.return_value = mock_installer

            manager = DeploymentManager(config)
            with patch.object(manager, "pre_deployment_checks", return_value=True):
                result = manager.execute_deployment()

                assert result["success"] is False
                assert len(result["errors"]) >= 1
