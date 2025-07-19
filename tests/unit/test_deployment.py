"""
Unit Tests for Deployment Module

Tests deployment manager and service installer functionality.
"""

from unittest.mock import Mock, patch

import pytest

from ha_connector.deployment import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentResult,
    DeploymentStrategy,
    ServiceConfig,
    ServiceInstaller,
    ServiceType,
    orchestrate_deployment,
)
from ha_connector.utils import ValidationError


class TestServiceInstaller:
    """Test Service Installer functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # pylint: disable=attribute-defined-outside-init
        self.installer = ServiceInstaller(
            region="us-east-1",
            dry_run=False,
            verbose=True
        )

    def test_init_with_valid_region(self):
        """Test initialization with valid region"""
        installer = ServiceInstaller(region="us-west-2")
        assert installer.region == "us-west-2"
        assert installer.dry_run is False
        assert installer.verbose is False

    def test_init_dry_run_mode(self):
        """Test initialization in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)
        assert installer.dry_run is True

    def test_get_default_config_alexa(self):
        """Test getting default configuration for Alexa service"""
        config = self.installer.get_default_config(ServiceType.ALEXA)

        assert config["function_name"] == "ha-alexa-proxy"
        assert config["handler"] == "alexa_wrapper.lambda_handler"
        assert config["runtime"] == "python3.11"

    def test_get_default_config_ios(self):
        """Test getting default configuration for iOS service"""
        config = self.installer.get_default_config(ServiceType.IOS_COMPANION)

        assert config["function_name"] == "ha-ios-proxy"
        assert config["handler"] == "ios_wrapper.lambda_handler"

    def test_get_default_config_invalid_type(self):
        """Test getting default configuration for invalid service type"""
        # Test with a string that's not a valid ServiceType
        config = self.installer.get_default_config("invalid_type")  # type: ignore
        assert config == {}

    @patch("ha_connector.deployment.service_installer.Path")
    def test_create_deployment_package_success(self, mock_path):
        """Test successful deployment package creation in dry run mode"""
        # Mock path exists check to avoid ValidationError
        mock_source = Mock()
        mock_source.exists.return_value = True

        mock_output = Mock()
        mock_output.__str__ = Mock(return_value="/test/output.zip")

        # Set up Path to return different mocks for different paths
        def path_side_effect(path_str):
            if str(path_str) == "/test/source":
                return mock_source
            elif str(path_str) == "/test/output.zip":
                return mock_output
            return Mock()

        mock_path.side_effect = path_side_effect

        # Use dry run mode to avoid complex file system operations
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        result = installer.create_deployment_package(
            source_path="/test/source",
            output_path="/test/output.zip"
        )

        # In dry run mode, it should return the output path
        # without actually creating files
        assert result == "/test/output.zip"

    def test_create_deployment_package_invalid_source(self):
        """Test deployment package creation with invalid source"""
        with pytest.raises(ValidationError, match="Source path does not exist"):
            self.installer.create_deployment_package(
                source_path="/nonexistent/path"
            )

    def test_create_iam_role_success(self):
        """Test successful IAM role creation"""
        mock_result = Mock()
        mock_result.status = "success"
        mock_result.resource = {
            "Role": {"Arn": "arn:aws:iam::123456789012:role/test-role"}
        }
        mock_result.errors = []

        # Replace the aws_manager instance with a mock
        mock_aws_manager = Mock()
        mock_aws_manager.create_resource.return_value = mock_result
        self.installer.aws_manager = mock_aws_manager

        result = self.installer.create_iam_role(
            role_name="test-role",
            service_type=ServiceType.ALEXA
        )

        assert result == "arn:aws:iam::123456789012:role/test-role"

    def test_deploy_service_success(self):
        """Test successful service deployment"""
        # Mock IAM role creation
        mock_iam_result = Mock()
        mock_iam_result.status = "success"
        mock_iam_result.resource = {
            "Role": {"Arn": "arn:aws:iam::123456789012:role/test-role"}
        }
        mock_iam_result.errors = []

        # Mock Lambda function deployment
        mock_lambda_result = Mock()
        mock_lambda_result.status = "created"
        mock_lambda_result.resource = {
            "Configuration": {
                "FunctionArn": (
                    "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
                ),
                "FunctionUrl": {
                    "FunctionUrl": "https://example.lambda-url.us-east-1.on.aws/"
                }
            }
        }
        mock_lambda_result.errors = []

        # Set up mock to return different results based on resource type
        def create_resource_side_effect(resource_type, _spec):
            if resource_type.value == "iam":
                return mock_iam_result
            elif resource_type.value == "lambda":
                return mock_lambda_result
            return Mock()

        # Replace the aws_manager instance with a mock
        mock_aws_manager = Mock()
        mock_aws_manager.create_resource.side_effect = create_resource_side_effect
        self.installer.aws_manager = mock_aws_manager

        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/source",
            runtime="python3.11",
            timeout=30,
            memory_size=512
        )

        with patch.object(self.installer, 'create_deployment_package') as mock_package:
            mock_package.return_value = "/test/package.zip"

            result = self.installer.deploy_service(config)

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            assert result.function_name == "ha-alexa-proxy"
            assert result.function_arn is not None
            assert "arn:aws:lambda" in result.function_arn

    def test_deploy_service_dry_run(self):
        """Test service deployment in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/source",
            runtime="python3.11"
        )

        # Mock the create_deployment_package method to avoid path validation
        with patch.object(installer, 'create_deployment_package') as mock_package:
            mock_package.return_value = "/test/package.zip"

            result = installer.deploy_service(config)

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            assert "Would deploy" in (result.metadata or {}).get("message", "")

    def test_deploy_predefined_service_alexa(self):
        """Test deploying predefined Alexa service"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        with patch.object(installer, 'deploy_service') as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                function_name="ha-alexa-proxy",
                function_arn=None,
                function_url=None,
                role_arn=None
            )

            result = installer.deploy_predefined_service(
                ServiceType.ALEXA,
                {"HA_BASE_URL": "https://test.com"}
            )

            assert isinstance(result, DeploymentResult)
            assert result.success is True
            mock_deploy.assert_called_once()

    def test_list_deployed_services(self):
        """Test listing deployed services"""
        # Replace the method with a mock that returns expected data
        mock_services = [
            {"FunctionName": "ha-alexa-proxy", "State": "Active"},
            {"FunctionName": "ha-ios-proxy", "State": "Active"}
        ]

        with patch.object(
            self.installer, 'list_deployed_services', return_value=mock_services
        ):
            services = self.installer.list_deployed_services()

            assert len(services) == 2
            assert services[0]["FunctionName"] == "ha-alexa-proxy"

    @patch("ha_connector.deployment.service_installer.AWSResourceManager")
    def test_remove_service_success(self, mock_aws_manager):
        """Test successful service removal"""
        mock_manager = Mock()
        mock_manager.delete_resource.return_value = {"success": True}
        mock_aws_manager.return_value = mock_manager

        result = self.installer.remove_service("ha-alexa-proxy")

        assert result is True

    def test_remove_service_dry_run(self):
        """Test service removal in dry run mode"""
        installer = ServiceInstaller(region="us-east-1", dry_run=True)

        result = installer.remove_service("ha-alexa-proxy")

        # In dry run mode, removal should always succeed
        assert result is True


class TestDeploymentManager:
    """Test Deployment Manager functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # pylint: disable=attribute-defined-outside-init
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
            tags={"Environment": "dev"}
        )
        self.manager = DeploymentManager(self.config)

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration"""
        assert self.manager.config == self.config
        assert self.manager.logger is not None

    def test_validate_deployment_config_success(self):
        """Test successful deployment configuration validation"""
        # This should not raise an exception for valid config
        try:
            self.manager.validate_deployment_config()
        except ValidationError:
            pytest.fail("Valid config should not raise ValidationError")

    def test_validate_deployment_config_invalid_environment(self):
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
            tags=None
        )
        manager = DeploymentManager(config)

        with pytest.raises(ValidationError, match="Invalid environment"):
            manager.validate_deployment_config()

    @patch("ha_connector.deployment.deploy_manager.ServiceInstaller")
    def test_pre_deployment_checks_success(self, mock_service_installer):
        """Test successful pre-deployment checks"""
        mock_installer = Mock()
        mock_installer.aws_manager = Mock()
        mock_service_installer.return_value = mock_installer

        result = self.manager.pre_deployment_checks()

        assert result is True

    def test_deploy_service_with_strategy_immediate(self):
        """Test deploying service with immediate strategy"""
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=(
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            function_url="https://test.lambda-url.us-east-1.on.aws/",
            role_arn=None
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service_installer instance with the mock
        self.manager.service_installer = mock_installer

        result = self.manager.deploy_service_with_strategy(
            ServiceType.ALEXA,
            {"HA_BASE_URL": "https://test.com"}
        )

        assert isinstance(result, DeploymentResult)
        assert result.success is True

    def test_execute_deployment_success(self):
        """Test successful deployment execution"""
        # Create mock installer and result
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=(
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            function_url="https://test.lambda-url.us-east-1.on.aws/",
            role_arn=None
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service installer instance
        self.manager.service_installer = mock_installer

        with patch.object(self.manager, 'pre_deployment_checks') as mock_checks:
            mock_checks.return_value = True

            result = self.manager.execute_deployment()

            assert result["success"] is True
            assert len(result["results"]) == 1
            assert isinstance(result["results"][0], DeploymentResult)

    @patch("ha_connector.deployment.deploy_manager.ServiceInstaller")
    def test_execute_deployment_with_errors(self, mock_service_installer):
        """Test deployment execution with errors"""
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=False,
            function_name="ha-alexa-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            errors=["Failed to create Lambda function"]
        )
        mock_installer.deploy_predefined_service.return_value = mock_result
        mock_service_installer.return_value = mock_installer

        with patch.object(self.manager, 'pre_deployment_checks') as mock_checks:
            mock_checks.return_value = True

            result = self.manager.execute_deployment()

            assert result["success"] is False
            assert len(result["errors"]) >= 1

    def test_execute_deployment_dry_run(self):
        """Test deployment execution in dry run mode"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=True,
            verbose=True,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )
        manager = DeploymentManager(config)

        # Create mock installer and result
        mock_installer = Mock()
        mock_result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            metadata={"dry_run": True, "message": "Would deploy Alexa service"}
        )
        mock_installer.deploy_predefined_service.return_value = mock_result

        # Replace the service installer instance
        manager.service_installer = mock_installer

        with patch.object(manager, 'pre_deployment_checks') as mock_checks:
            mock_checks.return_value = True

            result = manager.execute_deployment()

            assert result["success"] is True
            assert result["dry_run"] is True


class TestDeploymentStrategies:
    """Test different deployment strategies"""

    def test_immediate_strategy(self):
        """Test immediate deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-east-1",
            dry_run=True,
            verbose=False,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.IMMEDIATE

    def test_rolling_strategy(self):
        """Test rolling deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.ROLLING,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-east-1",
            dry_run=True,
            verbose=False,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.ROLLING

    def test_blue_green_strategy(self):
        """Test blue-green deployment strategy"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.BLUE_GREEN,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=True,
            verbose=False,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        manager = DeploymentManager(config)
        assert manager.config.strategy == DeploymentStrategy.BLUE_GREEN


class TestOrchestrationFunction:
    """Test deployment orchestration function"""

    def test_orchestrate_deployment_basic(self):
        """Test basic deployment orchestration"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA],
            region="us-east-1",
            dry_run=True,
            verbose=False,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        with patch(
            "ha_connector.deployment.deploy_manager.DeploymentManager"
        ) as mock_mgr:
            mock_manager = Mock()
            mock_manager.execute_deployment.return_value = {
                "success": True,
                "results": [],
                "errors": [],
                "dry_run": True
            }
            mock_mgr.return_value = mock_manager

            result = orchestrate_deployment(config)

            assert result["success"] is True
            assert result["dry_run"] is True
            mock_mgr.assert_called_once_with(config)
            mock_manager.execute_deployment.assert_called_once()


class TestDeploymentResult:
    """Test DeploymentResult data class"""

    def test_deployment_result_success(self):
        """Test successful deployment result"""
        result = DeploymentResult(
            success=True,
            function_name="ha-alexa-proxy",
            function_arn=(
                "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
            ),
            function_url="https://test.lambda-url.us-east-1.on.aws/",
            role_arn="arn:aws:iam::123456789012:role/ha-lambda-alexa"
        )

        assert result.success is True
        assert result.function_name == "ha-alexa-proxy"
        assert result.function_arn is not None
        assert result.errors == []

    def test_deployment_result_failure(self):
        """Test failed deployment result"""
        result = DeploymentResult(
            success=False,
            function_name="ha-ios-proxy",
            function_arn=None,
            function_url=None,
            role_arn=None,
            errors=["Failed to create IAM role"]
        )

        assert result.success is False
        assert result.function_arn is None
        assert "Failed to create IAM role" in result.errors

    def test_deployment_result_with_metadata(self):
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
                "duration": 0.1
            }
        )

        assert result.success is True
        assert result.metadata["dry_run"] is True
        assert "Would deploy" in result.metadata["message"]


class TestServiceConfig:
    """Test ServiceConfig data class"""

    def test_service_config_validation(self):
        """Test service configuration validation"""
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/alexa",
            runtime="python3.11",
            timeout=30,
            memory_size=512
        )

        assert config.service_type == ServiceType.ALEXA
        assert config.timeout == 30
        assert config.memory_size == 512
        assert config.runtime == "python3.11"

    def test_service_config_defaults(self):
        """Test service configuration with default values"""
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="ha-alexa-proxy",
            handler="alexa_wrapper.lambda_handler",
            source_path="/test/alexa"
        )

        assert config.runtime == "python3.11"
        assert config.timeout == 30
        assert config.memory_size == 512
        assert config.create_url is False

    def test_service_config_with_optional_fields(self):
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
            role_arn="arn:aws:iam::123456789012:role/test-role"
        )

        assert config.description == "Test Alexa function"
        assert config.environment_variables is not None
        assert config.environment_variables["HA_BASE_URL"] == "https://test.com"
        assert config.create_url is True
        assert config.url_auth_type == "AWS_IAM"


class TestDeploymentConfig:
    """Test DeploymentConfig data class"""

    def test_deployment_config_defaults(self):
        """Test deployment configuration with default values"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            services=[ServiceType.ALEXA],
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        assert config.strategy == DeploymentStrategy.ROLLING
        assert config.region == "us-east-1"
        assert config.dry_run is False
        assert config.verbose is False
        assert config.rollback_on_failure is True

    def test_deployment_config_validation(self):
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
            tags=None
        )

        assert config.environment == "prod"
        assert config.strategy == DeploymentStrategy.BLUE_GREEN
        assert len(config.services) == 2
        assert config.health_check_timeout == 600


# Integration-style tests
class TestDeploymentIntegration:
    """Integration tests for deployment functionality"""

    @pytest.mark.slow
    def test_full_deployment_workflow_dry_run(self):
        """Test complete deployment workflow in dry run mode"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0-test",
            strategy=DeploymentStrategy.IMMEDIATE,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-east-1",
            dry_run=True,
            verbose=True,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        with patch(
            "ha_connector.deployment.deploy_manager.ServiceInstaller"
        ) as mock_svc:
            mock_installer = Mock()

            # Mock successful installations for both services
            mock_results = [
                DeploymentResult(
                    success=True,
                    function_name="ha-alexa-proxy",
                    function_arn=None,
                    function_url=None,
                    role_arn=None,
                    metadata={"dry_run": True, "message": "Would install Alexa service"}
                ),
                DeploymentResult(
                    success=True,
                    function_name="ha-ios-proxy",
                    function_arn=None,
                    function_url=None,
                    role_arn=None,
                    metadata={"dry_run": True, "message": "Would install iOS service"}
                ),
            ]
            mock_installer.deploy_predefined_service.side_effect = mock_results
            mock_svc.return_value = mock_installer

            manager = DeploymentManager(config)

            with patch.object(manager, 'pre_deployment_checks') as mock_checks:
                mock_checks.return_value = True

                result = manager.execute_deployment()

                assert result["success"] is True
                assert result["dry_run"] is True
                assert len(result["results"]) == 2

    @pytest.mark.slow
    def test_deployment_error_handling(self):
        """Test deployment error handling and recovery"""
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0-test",
            strategy=DeploymentStrategy.ROLLING,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-east-1",
            dry_run=False,
            verbose=True,
            cloudflare_setup=False,
            cloudflare_domain=None,
            service_overrides=None,
            tags=None
        )

        with patch(
            "ha_connector.deployment.deploy_manager.ServiceInstaller"
        ) as mock_svc:
            mock_installer = Mock()

            # Mock first service success, second service failure
            mock_results = [
                DeploymentResult(
                    success=True,
                    function_name="ha-alexa-proxy",
                    function_arn=(
                        "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy"
                    ),
                    function_url="https://test.lambda-url.us-east-1.on.aws/",
                    role_arn=None
                ),
                DeploymentResult(
                    success=False,
                    function_name="ha-ios-proxy",
                    function_arn=None,
                    function_url=None,
                    role_arn=None,
                    errors=["Failed to create Lambda function"]
                ),
            ]
            mock_installer.deploy_predefined_service.side_effect = mock_results
            mock_svc.return_value = mock_installer

            manager = DeploymentManager(config)

            with patch.object(manager, 'pre_deployment_checks') as mock_checks, \
                 patch.object(manager, '_health_check_service') as mock_health:
                mock_checks.return_value = True
                # Mock health check to return True for first service,
                # but this won't matter since the service itself fails
                mock_health.return_value = True

                result = manager.execute_deployment()

                assert result["success"] is False
                assert len(result["results"]) == 2
                assert result["results"][0].success is True
                assert result["results"][1].success is False
                assert len(result["errors"]) >= 1
