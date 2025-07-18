"""
Test CLI Commands

Comprehensive tests for all CLI commands and functionality.
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ha_connector.cli import app
from ha_connector.config import InstallationScenario
from ha_connector.deployment import ServiceType, DeploymentStrategy


class TestCLICommands:
    """Test CLI command functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.test_env = {
            "HA_BASE_URL": "https://test.example.com",
            "ALEXA_SECRET": "test-secret-123",
            "AWS_REGION": "us-east-1"
        }

    def test_version_command(self):
        """Test version command"""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.stdout

    def test_help_command(self):
        """Test help command"""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Home Assistant External Connector" in result.stdout

        # Test individual command help
        commands = ["install", "deploy", "configure", "status", "remove"]
        for command in commands:
            result = self.runner.invoke(app, [command, "--help"])
            assert result.exit_code == 0

    @patch.dict(os.environ, {"HA_BASE_URL": "https://test.example.com", "ALEXA_SECRET": "test-secret", "AWS_REGION": "us-east-1"})
    @patch("ha_connector.cli.commands.ConfigurationManager")
    @patch("ha_connector.cli.commands.DeploymentManager")
    def test_install_command_success(self, mock_deployment_manager, mock_config_manager):
        """Test successful installation"""
        # Mock configuration manager
        mock_config = Mock()
        mock_config.load_from_environment.return_value = True
        mock_config.validate_configuration.return_value = Mock(is_valid=True, errors=[])
        mock_config_manager.return_value = mock_config

        # Mock deployment manager
        mock_deployment = Mock()
        mock_deployment.execute_deployment.return_value = {
            "success": True,
            "services": [
                {
                    "function_name": "ha-alexa-proxy",
                    "success": True,
                    "function_arn": "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy",
                    "function_url": "https://test.lambda-url.us-east-1.on.aws/"
                }
            ],
            "deployment_time": 30.5,
            "strategy": "rolling",
            "environment": "prod"
        }
        mock_deployment_manager.return_value = mock_deployment

        result = self.runner.invoke(app, [
            "install",
            "direct_alexa",
            "--region", "us-east-1",
            "--environment", "prod"
        ])

        assert result.exit_code == 0
        assert "Installation completed successfully" in result.stdout
        mock_config_manager.assert_called_once()
        mock_deployment_manager.assert_called_once()

    @patch.dict(os.environ, {})
    @patch("ha_connector.cli.commands.ConfigurationManager")
    def test_install_command_invalid_scenario(self, mock_config_manager):
        """Test installation with invalid scenario"""
        result = self.runner.invoke(app, [
            "install",
            "invalid_scenario"
        ])

        assert result.exit_code == 1
        assert "Invalid scenario" in result.stdout

    @patch.dict(os.environ, {"HA_BASE_URL": "https://test.example.com"})
    @patch("ha_connector.cli.commands.ConfigurationManager")
    def test_install_command_config_validation_failure(self, mock_config_manager):
        """Test installation with configuration validation failure"""
        mock_config = Mock()
        mock_config.load_from_environment.return_value = True
        mock_config.validate_configuration.return_value = Mock(
            is_valid=False,
            errors=["Missing required environment variable: ALEXA_SECRET"]
        )
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(app, [
            "install",
            "direct_alexa"
        ])

        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stdout
        assert "ALEXA_SECRET" in result.stdout

    @patch("ha_connector.cli.commands.DeploymentManager")
    def test_deploy_command_success(self, mock_deployment_manager):
        """Test successful deployment"""
        mock_deployment = Mock()
        mock_deployment.execute_deployment.return_value = {
            "success": True,
            "services": [
                {
                    "function_name": "ha-alexa-proxy",
                    "success": True,
                    "function_arn": "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy",
                    "function_url": "https://test.lambda-url.us-east-1.on.aws/"
                }
            ],
            "deployment_time": 15.2,
            "strategy": "rolling",
            "environment": "prod"
        }
        mock_deployment_manager.return_value = mock_deployment

        result = self.runner.invoke(app, [
            "deploy",
            "alexa",
            "--strategy", "rolling"
        ])

        assert result.exit_code == 0
        assert "Deployment completed successfully" in result.stdout
        mock_deployment_manager.assert_called_once()

    def test_deploy_command_invalid_service(self):
        """Test deployment with invalid service"""
        result = self.runner.invoke(app, [
            "deploy",
            "invalid_service"
        ])

        assert result.exit_code == 1
        assert "Invalid service" in result.stdout

    def test_deploy_command_invalid_strategy(self):
        """Test deployment with invalid strategy"""
        result = self.runner.invoke(app, [
            "deploy",
            "alexa",
            "--strategy", "invalid_strategy"
        ])

        assert result.exit_code == 1
        assert "Invalid strategy" in result.stdout

    @patch("ha_connector.cli.commands.ConfigurationManager")
    def test_configure_command_validation_success(self, mock_config_manager):
        """Test configuration validation success"""
        mock_config = Mock()
        mock_config.validate_configuration.return_value = Mock(is_valid=True, errors=[])
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(app, [
            "configure",
            "--validate-only"
        ])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.stdout

    @patch("ha_connector.cli.commands.ConfigurationManager")
    def test_configure_command_validation_failure(self, mock_config_manager):
        """Test configuration validation failure"""
        mock_config = Mock()
        mock_config.validate_configuration.return_value = Mock(
            is_valid=False,
            errors=["Missing HA_BASE_URL", "Invalid AWS region"]
        )
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(app, [
            "configure",
            "--validate-only"
        ])

        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stdout
        assert "HA_BASE_URL" in result.stdout

    @patch("ha_connector.cli.commands.validate_aws_access")
    @patch("ha_connector.cli.commands.ServiceInstaller")
    def test_status_command_success(self, mock_service_installer, mock_aws_validate):
        """Test status command success"""
        mock_aws_validate.return_value = {"status": "success"}

        mock_installer = Mock()
        mock_installer.list_deployed_services.return_value = [
            {
                "name": "ha-alexa-proxy",
                "status": "Active",
                "last_modified": "2024-01-15T10:30:00Z",
                "runtime": "python3.11",
                "memory": "256MB"
            }
        ]
        mock_service_installer.return_value = mock_installer

        result = self.runner.invoke(app, [
            "status",
            "--verbose"
        ])

        assert result.exit_code == 0
        assert "AWS connectivity OK" in result.stdout
        assert "ha-alexa-proxy" in result.stdout

    @patch("ha_connector.cli.commands.validate_aws_access")
    def test_status_command_aws_failure(self, mock_aws_validate):
        """Test status command with AWS connectivity failure"""
        mock_aws_validate.return_value = {"status": "error", "message": "Access denied"}

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 1
        assert "AWS connectivity failed" in result.stdout

    @patch("ha_connector.cli.commands.ServiceInstaller")
    def test_remove_command_success(self, mock_service_installer):
        """Test remove command success"""
        mock_installer = Mock()
        mock_installer.remove_service.return_value = True
        mock_service_installer.return_value = mock_installer

        result = self.runner.invoke(app, [
            "remove",
            "alexa",
            "--force"
        ])

        assert result.exit_code == 0
        assert "Successfully removed" in result.stdout

    def test_remove_command_invalid_service(self):
        """Test remove command with invalid service"""
        result = self.runner.invoke(app, [
            "remove",
            "invalid_service",
            "--force"
        ])

        assert result.exit_code == 1
        assert "Invalid service" in result.stdout

    @patch("ha_connector.cli.commands.ServiceInstaller")
    def test_remove_command_all_services(self, mock_service_installer):
        """Test removing all services"""
        mock_installer = Mock()
        mock_installer.remove_service.return_value = True
        mock_service_installer.return_value = mock_installer

        result = self.runner.invoke(app, [
            "remove",
            "all",
            "--force"
        ])

        assert result.exit_code == 0
        # Should attempt to remove 3 services
        assert mock_installer.remove_service.call_count == 3

    def test_dry_run_mode(self):
        """Test dry-run mode doesn't make changes"""
        result = self.runner.invoke(app, [
            "install",
            "direct_alexa",
            "--dry-run"
        ])

        # Should show dry-run message
        assert "DRY RUN MODE" in result.stdout or result.exit_code != 0

    @patch("ha_connector.cli.commands.Prompt.ask")
    @patch("ha_connector.cli.commands.ConfigurationManager")
    def test_interactive_configuration(self, mock_config_manager, mock_prompt):
        """Test interactive configuration setup"""
        mock_config = Mock()
        mock_config.validate_configuration.return_value = Mock(is_valid=True, errors=[])
        mock_config.generate_secure_secret.return_value = "generated-secret-123"
        mock_config_manager.return_value = mock_config

        mock_prompt.side_effect = [
            "https://interactive.example.com",
            "us-west-2"
        ]

        result = self.runner.invoke(app, [
            "configure",
            "--interactive"
        ])

        assert result.exit_code == 0
        assert "Interactive Configuration" in result.stdout


class TestCLIHelpers:
    """Test CLI helper functions"""

    def test_get_services_for_scenario(self):
        """Test service mapping for scenarios"""
        from ha_connector.cli.commands import _get_services_for_scenario

        # Test direct Alexa
        services = _get_services_for_scenario(InstallationScenario.DIRECT_ALEXA)
        assert services == [ServiceType.ALEXA]

        # Test CloudFlare Alexa
        services = _get_services_for_scenario(InstallationScenario.CLOUDFLARE_ALEXA)
        assert ServiceType.ALEXA in services
        assert ServiceType.CLOUDFLARE_PROXY in services

        # Test CloudFlare iOS
        services = _get_services_for_scenario(InstallationScenario.CLOUDFLARE_IOS)
        assert ServiceType.IOS_COMPANION in services
        assert ServiceType.CLOUDFLARE_PROXY in services

        # Test all
        services = _get_services_for_scenario(InstallationScenario.ALL)
        assert len(services) == 3
        assert ServiceType.ALEXA in services
        assert ServiceType.IOS_COMPANION in services
        assert ServiceType.CLOUDFLARE_PROXY in services


class TestCLIIntegration:
    """Integration tests for CLI functionality"""

    def setup_method(self):
        """Set up integration test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_command_chaining(self):
        """Test that commands can be chained properly"""
        # This would test scenarios like:
        # 1. configure -> validate
        # 2. install -> status
        # 3. deploy -> status
        pass

    def test_error_handling(self):
        """Test CLI error handling"""
        # Test keyboard interrupt
        result = self.runner.invoke(app, ["install", "direct_alexa"])
        # The exact behavior depends on mocking

        # Test invalid arguments
        result = self.runner.invoke(app, ["--invalid-flag"])
        assert result.exit_code != 0

    def test_verbose_output(self):
        """Test verbose output functionality"""
        result = self.runner.invoke(app, [
            "status",
            "--verbose"
        ])
        # Should include additional details when verbose is enabled
        # Exact assertions depend on implementation


if __name__ == "__main__":
    pytest.main([__file__])
