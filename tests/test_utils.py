"""
Test Utilities and Helper Functions

Provides common utilities for testing Home Assistant External Connector.
"""

import json
import secrets
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from ha_connector.config import InstallationScenario
from ha_connector.deployment import DeploymentResult, ServiceConfig, ServiceType

# Test constants - clearly marked as test data
TEST_SECRET_PREFIX = "test-"
TEST_DOMAIN = "test.homeassistant.local"


@dataclass
class MockDeploymentResult:
    """Configuration for creating mock deployment function details."""

    function_name: str = "test-function"
    function_arn: str | None = (
        "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    )
    function_url: str | None = None
    role_arn: str | None = None


@dataclass
class MockDeploymentConfig:
    """Configuration for creating mock deployment results."""

    success: bool = True
    result: MockDeploymentResult = field(default_factory=MockDeploymentResult)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@contextmanager
def temporary_config_file(config_data: dict[str, Any]) -> Iterator[Path]:
    """Context manager for temporary configuration files with automatic cleanup."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as temp_file:
        json.dump(config_data, temp_file, indent=2)
        temp_file_path = Path(temp_file.name)

    try:
        yield temp_file_path
    finally:
        # Ensure cleanup even if test fails
        if temp_file_path.exists():
            temp_file_path.unlink()


def _generate_test_secret(service_name: str) -> str:
    """Generate a secure test secret for the given service."""
    # Use secrets module for secure random generation even in tests
    random_suffix = secrets.token_hex(8)
    return f"{TEST_SECRET_PREFIX}{service_name}-{random_suffix}"


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
    """Create a temporary configuration file for testing.

    NOTE: This function returns a path that requires manual cleanup.
    Consider using temporary_config_file() context manager for automatic cleanup.
    """
    # Use secure temporary file creation instead of mktemp
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as temp_file:
        json.dump(config_data, temp_file, indent=2)
        temp_file_path = Path(temp_file.name)

    return temp_file_path


def get_sample_config(scenario: InstallationScenario) -> dict[str, Any]:
    """Get sample configuration for testing scenarios"""
    base_config = {
        "ha_base_url": f"https://{TEST_DOMAIN}:8123",
        "aws_region": "us-east-1",
    }

    if scenario == InstallationScenario.DIRECT_ALEXA:
        base_config["alexa_secret"] = _generate_test_secret("alexa")
    elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
        base_config.update(
            {
                "alexa_secret": _generate_test_secret("alexa"),
                "cf_client_id": _generate_test_secret("cf-client"),
                "cf_client_secret": _generate_test_secret("cf-secret"),
                "cloudflare_domain": "test.example.com",
            }
        )
    elif scenario == InstallationScenario.CLOUDFLARE_IOS:
        base_config.update(
            {
                "ios_secret": _generate_test_secret("ios"),
                "cf_client_id": _generate_test_secret("cf-client"),
                "cf_client_secret": _generate_test_secret("cf-secret"),
                "cloudflare_domain": "test.example.com",
            }
        )

    return base_config


def create_mock_service_installer(dry_run: bool = True) -> Mock:
    """Create a mock service installer for testing"""
    mock_installer = Mock()

    # Mock validation
    mock_installer.validate_prerequisites.return_value = {"success": True}

    # Mock installation results
    def mock_install_service(
        service_config: ServiceConfig, _environment_vars: dict[str, Any]
    ) -> DeploymentResult:
        return DeploymentResult(
            success=True,
            function_name=service_config.function_name,
            function_arn=(
                None
                if dry_run
                else (
                    f"arn:aws:lambda:us-east-1:123456789012:"
                    f"function:{service_config.function_name}"
                )
            ),
            function_url=(
                None if dry_run else "https://test.lambda-url.us-east-1.on.aws/"
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
    def mock_remove_service(service_type: ServiceType) -> dict[str, Any]:
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

    def mock_execute_deployment() -> dict[str, Any]:
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
) -> None:
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
    config: MockDeploymentConfig | None = None,
) -> DeploymentResult:
    """Create a mock DeploymentResult object."""
    if config is None:
        config = MockDeploymentConfig()

    return DeploymentResult(
        success=config.success,
        function_name=config.result.function_name,
        function_arn=config.result.function_arn,
        function_url=config.result.function_url,
        role_arn=config.result.role_arn,
        errors=config.errors,
        warnings=config.warnings,
        metadata=config.metadata,
    )


def assert_service_config_valid(
    config: ServiceConfig, service_type: ServiceType
) -> None:
    """Assert that a service configuration is valid"""
    assert isinstance(config, ServiceConfig)
    assert config.service_type == service_type
    assert config.function_name
    assert config.handler
    assert config.runtime == "python3.11"
    assert config.timeout > 0
    assert config.memory_size >= 128


@lru_cache(maxsize=32)
def get_expected_function_name(service_type: ServiceType) -> str:
    """Get expected function name for service type.

    Cached for performance during test runs with many service configurations.
    """
    mapping = {
        ServiceType.ALEXA: "ha-alexa-proxy",
        ServiceType.IOS_COMPANION: "ha-ios-proxy",
        ServiceType.CLOUDFLARE_PROXY: "ha-cloudflare-proxy",
    }
    return mapping[service_type]


@lru_cache(maxsize=32)
def get_expected_iam_role_name(service_type: ServiceType) -> str:
    """Get expected IAM role name for service type.

    Cached for performance during test runs with many service configurations.
    """
    mapping = {
        ServiceType.ALEXA: "ha-lambda-alexa",
        ServiceType.IOS_COMPANION: "ha-lambda-ios",
        ServiceType.CLOUDFLARE_PROXY: "ha-lambda-cloudflare",
    }
    return mapping[service_type]


@lru_cache(maxsize=32)
def get_expected_ssm_path(service_type: ServiceType) -> str:
    """Get expected SSM parameter path for service type.

    Cached for performance during test runs with many service configurations.
    """
    mapping = {
        ServiceType.ALEXA: "/ha-alexa/config",
        ServiceType.IOS_COMPANION: "/ha-ios/config",
        ServiceType.CLOUDFLARE_PROXY: "/ha-cloudflare/config",
    }
    return mapping[service_type]


def cleanup_temp_files(*paths: Path) -> None:
    """Clean up temporary files created during testing"""
    for path in paths:
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
