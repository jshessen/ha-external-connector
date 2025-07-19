"""
Test Utilities and Helper Functions

Provides common utilities for testing Home Assistant External Connector.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from ha_connector.config import InstallationScenario
from ha_connector.deployment import DeploymentResult, ServiceConfig, ServiceType


def create_mock_aws_response(
    success: bool = True,
    data: dict[str, Any] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Create a mock AWS API response"""
    if data is None:
        data = {}

    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200 if success else 400,
            "RequestId": "mock-request-id",
        }
    }

    if success:
        response.update(data)
    else:
        response["Error"] = {
            "Code": error_code or "MockError",
            "Message": error_message or "Mock error message",
        }

    return response


def create_mock_cloudflare_response(
    success: bool = True,
    result: Any = None,
    errors: list[str] | None = None,
    messages: list[str] | None = None,
) -> dict[str, Any]:
    """Create a mock CloudFlare API response"""
    return {
        "success": success,
        "errors": errors or [],
        "messages": messages or [],
        "result": result,
    }


def create_temp_config_file(config_data: dict[str, Any]) -> Path:
    """Create a temporary configuration file for testing"""
    temp_file = Path(tempfile.mktemp(suffix=".json"))
    temp_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    return temp_file


def get_sample_config(scenario: InstallationScenario) -> dict[str, Any]:
    """Get sample configuration for testing scenarios"""
    base_config = {
        "ha_base_url": "https://test.homeassistant.local:8123",
        "aws_region": "us-east-1",
    }

    if scenario == InstallationScenario.DIRECT_ALEXA:
        base_config["alexa_secret"] = "test-alexa-secret"
    elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
        base_config.update({
            "alexa_secret": "test-alexa-secret",
            "cf_client_id": "test-cf-client-id",
            "cf_client_secret": "test-cf-client-secret",
            "cloudflare_domain": "test.example.com",
        })
    elif scenario == InstallationScenario.CLOUDFLARE_IOS:
        base_config.update({
            "ios_secret": "test-ios-secret",
            "cf_client_id": "test-cf-client-id",
            "cf_client_secret": "test-cf-client-secret",
            "cloudflare_domain": "test.example.com",
        })

    return base_config


def create_mock_service_installer(dry_run: bool = True) -> Mock:
    """Create a mock service installer for testing"""
    mock_installer = Mock()

    # Mock validation
    mock_installer.validate_prerequisites.return_value = {"success": True}

    # Mock installation results
    def mock_install_service(
        service_config, environment_vars  # pylint: disable=unused-argument
    ):
        return DeploymentResult(
            success=True,
            function_name=service_config.function_name,
            function_arn=(
                None if dry_run
                else (
                    f"arn:aws:lambda:us-east-1:123456789012:"
                    f"function:{service_config.function_name}"
                )
            ),
            function_url=(
                None if dry_run
                else "https://test.lambda-url.us-east-1.on.aws/"
            ),
            role_arn=None,
            errors=[],
            warnings=[],
            metadata={
                "service_type": service_config.service_type.value,
                "dry_run": dry_run,
                "duration": 0.5 if dry_run else 10.0,
                "message": (
                    f"{'Would install' if dry_run else 'Installed'} "
                    f"{service_config.service_type.value} service"
                ),
            },
        )

    mock_installer.install_service.side_effect = mock_install_service

    # Mock removal
    def mock_remove_service(service_type):
        return {
            "success": True,
            "service_type": service_type,
            "dry_run": dry_run,
            "message": (
                f"{'Would remove' if dry_run else 'Removed'} "
                f"{service_type.value} service"
            ),
        }

    mock_installer.remove_service.side_effect = mock_remove_service

    return mock_installer


def create_mock_deployment_manager(dry_run: bool = True) -> Mock:
    """Create a mock deployment manager for testing"""
    mock_manager = Mock()

    def mock_execute_deployment():
        return {
            "success": True,
            "results": [],
            "errors": [],
            "dry_run": dry_run,
            "duration": 5.0 if not dry_run else 1.0,
        }

    mock_manager.execute_deployment.side_effect = mock_execute_deployment
    return mock_manager


def assert_deployment_result_valid(
    result: dict[str, Any], expected_success: bool = True
):
    """Assert that a deployment result is valid"""
    assert "success" in result
    assert "results" in result
    assert "errors" in result
    assert result["success"] == expected_success

    if expected_success:
        assert len(result["errors"]) == 0
    else:
        assert len(result["errors"]) > 0


def create_mock_deployment_result(
    success: bool = True,
    function_name: str = "test-function",
    function_arn: str | None = (
        "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    ),
    function_url: str | None = None,
    role_arn: str | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Create a mock DeploymentResult object."""
    return DeploymentResult(
        success=success,
        function_name=function_name,
        function_arn=function_arn,
        function_url=function_url,
        role_arn=role_arn,
        errors=errors or [],
        warnings=warnings or [],
        metadata=metadata or {},
    )


def assert_service_config_valid(config, service_type: ServiceType):
    """Assert that a service configuration is valid"""
    assert isinstance(config, ServiceConfig)
    assert config.service_type == service_type
    assert config.function_name
    assert config.handler
    assert config.runtime == "python3.11"
    assert config.timeout > 0
    assert config.memory_size >= 128


def get_expected_function_name(service_type: ServiceType) -> str:
    """Get expected function name for service type"""
    mapping = {
        ServiceType.ALEXA: "ha-alexa-proxy",
        ServiceType.IOS_COMPANION: "ha-ios-proxy",
        ServiceType.CLOUDFLARE_PROXY: "ha-cloudflare-proxy",
    }
    return mapping[service_type]


def get_expected_iam_role_name(service_type: ServiceType) -> str:
    """Get expected IAM role name for service type"""
    mapping = {
        ServiceType.ALEXA: "ha-lambda-alexa",
        ServiceType.IOS_COMPANION: "ha-lambda-ios",
        ServiceType.CLOUDFLARE_PROXY: "ha-lambda-cloudflare",
    }
    return mapping[service_type]


def get_expected_ssm_path(service_type: ServiceType) -> str:
    """Get expected SSM parameter path for service type"""
    mapping = {
        ServiceType.ALEXA: "/ha-alexa/config",
        ServiceType.IOS_COMPANION: "/ha-ios/config",
        ServiceType.CLOUDFLARE_PROXY: "/ha-cloudflare/config",
    }
    return mapping[service_type]


def cleanup_temp_files(*paths: Path):
    """Clean up temporary files created during testing"""
    for path in paths:
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
