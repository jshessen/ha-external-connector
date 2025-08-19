"""
Pytest Configuration and Shared Fixtures

Provides common fixtures and configuration for all test modules.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

# Import pytest internals for proper hook typing
from _pytest.config import Config
from _pytest.nodes import Item
from pydantic import BaseModel

from development.deployment_tools.deploy_manager import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentStrategy,
)
from development.deployment_tools.service_installer import (
    ServiceConfig,
    ServiceInstaller,
    ServiceType,
)
from development.utils.manager import (
    ConfigurationManager,
    ConfigurationState,
    InstallationScenario,
)
from tests.fixtures.test_secrets import get_deterministic_secret

# Import AWS fixtures to make them available to tests
try:
    from tests.fixtures.aws_fixtures import (  # noqa: F401
        aws_framework,
        aws_iam_role,
        aws_lambda_function,
        aws_ssm_parameter,
    )
except ImportError:
    # Graceful fallback when AWS fixtures are not available
    # Define stub functions that return None for missing AWS dependencies

    @pytest.fixture(name="aws_framework")
    def aws_framework_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None

    @pytest.fixture(name="aws_lambda_function")
    def aws_lambda_function_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None

    @pytest.fixture(name="aws_iam_role")
    def aws_iam_role_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None

    @pytest.fixture(name="aws_ssm_parameter")
    def aws_ssm_parameter_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None

    @pytest.fixture(name="mock_lambda_response")
    def mock_lambda_response_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None

    @pytest.fixture(name="mock_iam_response")
    def mock_iam_response_fallback() -> None:
        """Fallback fixture when AWS fixtures are unavailable."""
        return None


# Import CloudFlare fixtures to make them available to tests
try:
    from tests.fixtures.cloudflare_fixtures import (  # noqa: E402, F401
        cloudflare_config,
        cloudflare_environment,
        cloudflare_test_framework,
    )
except ImportError:
    # Graceful fallback when CloudFlare fixtures are not available
    @pytest.fixture(name="cloudflare_config")
    def cloudflare_config_fallback() -> None:
        """Fallback fixture when CloudFlare dependencies are unavailable."""
        return None

    @pytest.fixture(name="cloudflare_environment")
    def cloudflare_environment_fallback() -> None:
        """Fallback fixture when CloudFlare dependencies are unavailable."""
        return None

    @pytest.fixture(name="cloudflare_test_framework")
    def cloudflare_test_framework_fallback() -> None:
        """Fallback fixture when CloudFlare dependencies are unavailable."""
        return None

    cloudflare_config = cloudflare_config_fallback
    cloudflare_environment = cloudflare_environment_fallback
    cloudflare_test_framework = cloudflare_test_framework_fallback


class MockAWSResponse(BaseModel):
    """Mock AWS response structure"""

    status_code: int = 200
    response_metadata: dict[str, Any] = {}
    data: dict[str, Any] = {}


class MockCloudFlareResponse(BaseModel):
    """Mock CloudFlare response structure"""

    success: bool = True
    errors: list[str] = []
    messages: list[str] = []
    result: dict[str, Any] = {}


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str]]:
    """Mock environment variables for testing"""
    test_env = {
        "HA_BASE_URL": "https://test.homeassistant.local:8123",
        "ALEXA_SECRET": "test-alexa-secret-123",
        "CF_CLIENT_ID": "test-cf-client-id",
        "CF_CLIENT_SECRET": "test-cf-client-secret",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    }

    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def mock_config_manager() -> ConfigurationManager:
    """Create a mock configuration manager"""
    config_manager = ConfigurationManager()
    # Manually set config attributes to simulate loaded state
    config_manager.config = ConfigurationState(
        scenario=InstallationScenario.DIRECT_ALEXA,
        ha_base_url="https://test.homeassistant.local:8123",
        alexa_secret=get_deterministic_secret("alexa_secret"),
        cf_client_id="test-cf-client-id",
        cf_client_secret=get_deterministic_secret("cf_client_secret"),
        aws_region="us-east-1",
    )
    return config_manager


@pytest.fixture
def mock_service_config() -> ServiceConfig:
    """Create a mock service configuration"""
    return ServiceConfig(
        service_type=ServiceType.ALEXA,
        function_name="ha-alexa-proxy",
        source_path=tempfile.mkdtemp(prefix="alexa-source-"),
        handler="lambda_function.lambda_handler",
        runtime="python3.11",
        timeout=30,
        memory_size=256,
        description="Test Alexa proxy function",
        environment_variables={
            "HA_BASE_URL": "https://test.homeassistant.local:8123",
            "ALEXA_SECRET": "test-alexa-secret-123",
        },
        create_url=True,
        url_auth_type="NONE",
        role_arn=None,
    )


@pytest.fixture
def mock_deployment_config() -> DeploymentConfig:
    """Create a mock deployment configuration"""
    return DeploymentConfig(
        environment="dev",  # Use valid environment
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
        tags={"Environment": "dev", "Version": "1.0.0"},
    )


@pytest.fixture
def mock_aws_client() -> Mock:
    """Mock AWS client with common responses"""
    mock_client = Mock()

    # Lambda client responses
    mock_client.list_functions.return_value = {
        "Functions": [],
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    mock_client.create_function.return_value = {
        "FunctionName": "ha-alexa-proxy",
        "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:ha-alexa-proxy",
        "Runtime": "python3.11",
        "State": "Active",
        "ResponseMetadata": {"HTTPStatusCode": 201},
    }

    mock_client.update_function_code.return_value = {
        "FunctionName": "ha-alexa-proxy",
        "LastModified": "2025-01-01T00:00:00.000+0000",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    # IAM client responses
    mock_client.get_role.side_effect = mock_client.exceptions.NoSuchEntityException(
        {"Error": {"Code": "NoSuchEntity", "Message": "Role not found"}}, "GetRole"
    )

    mock_client.create_role.return_value = {
        "Role": {
            "RoleName": "ha-lambda-alexa",
            "Arn": "arn:aws:iam::123456789012:role/ha-lambda-alexa",
            "CreateDate": "2025-01-01T00:00:00Z",
        },
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    # SSM client responses
    mock_client.get_parameter.side_effect = mock_client.exceptions.ParameterNotFound(
        {"Error": {"Code": "ParameterNotFound", "Message": "Parameter not found"}},
        "GetParameter",
    )

    mock_client.put_parameter.return_value = {
        "Version": 1,
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    # CloudWatch Logs responses
    mock_client.describe_log_groups.return_value = {
        "logGroups": [],
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }

    mock_client.create_log_group.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    return mock_client


@pytest.fixture
def mock_cloudflare_client() -> Mock:
    """Mock CloudFlare client with common responses"""
    mock_client = Mock()

    # Zone responses
    mock_client.zones.list.return_value = {
        "success": True,
        "errors": [],
        "messages": [],
        "result": [],
    }

    # Access application responses
    mock_client.zero_trust.access.applications.list.return_value = {
        "success": True,
        "errors": [],
        "messages": [],
        "result": [],
    }

    # DNS record responses
    mock_client.zones.dns_records.list.return_value = {
        "success": True,
        "errors": [],
        "messages": [],
        "result": [],
    }

    return mock_client


@pytest.fixture(name="service_installer")
def mock_service_installer(
    _mock_deployment_config: DeploymentConfig,
) -> ServiceInstaller:
    """Create a mock service installer"""
    with patch("ha_connector.deployment.service_installer.boto3") as mock_boto3:
        mock_boto3.client.return_value = Mock()
        installer = ServiceInstaller(
            region="us-east-1",
            dry_run=True,
            verbose=_mock_deployment_config.verbose,
        )
        return installer


@pytest.fixture(name="deployment_manager")
def mock_deployment_manager(
    _mock_deployment_config: DeploymentConfig,
) -> DeploymentManager:
    """Create a mock deployment manager"""
    with patch("ha_connector.deployment.deploy_manager.ServiceInstaller"):
        manager = DeploymentManager(_mock_deployment_config)
        return manager


# Pytest markers for test categorization
pytest_plugins: list[str] = []


# Skip AWS tests if credentials not available
def pytest_configure(config: Config) -> None:
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "aws: mark test as requiring AWS credentials")
    config.addinivalue_line(
        "markers", "cloudflare: mark test as requiring CloudFlare credentials"
    )
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """
    Modify test items to skip tests that require missing dependencies.

    Args:
        config: The pytest configuration object (required by pytest API)
        items: List of collected test items to modify
    """
    # Suppress the unused argument warning for the required pytest hook parameter
    _ = config
    # Modify test collection to add markers based on test names and conditions
    for item in items:
        # Mark AWS tests
        if (
            "aws" in item.name.lower()
            or "lambda" in item.name.lower()
            or "iam" in item.name.lower()
        ):
            item.add_marker(pytest.mark.aws)

        # Mark CloudFlare tests
        if "cloudflare" in item.name.lower() or "cf" in item.name.lower():
            item.add_marker(pytest.mark.cloudflare)

        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "deploy" in item.name.lower() or "install" in item.name.lower():
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def cleanup_environment() -> Generator[None]:
    """Cleanup environment after each test"""
    yield
    # Any cleanup code would go here


# Explicitly re-export fixtures for pytest auto-discovery
__all__ = [
    "aws_framework",
    "aws_lambda_function",
    "aws_iam_role",
    "aws_ssm_parameter",
    "cloudflare_config",
    "cloudflare_environment",
    "cloudflare_test_framework",
]
