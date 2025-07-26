"""
High-Level CloudFlare Manager Tests

Tests for the main CloudFlareManager class that orchestrates CloudFlare service
operations. These tests focus on manager coordination and configuration, not
individual service implementation.
"""

import os
from unittest.mock import Mock, patch

import pytest

from ha_connector.adapters.cloudflare_manager import CloudFlareConfig, CloudFlareManager
from ha_connector.utils import HAConnectorError
from tests.fixtures.test_secrets import get_deterministic_secret


def create_test_cloudflare_config() -> CloudFlareConfig:
    """Create a valid CloudFlare config for testing."""
    return CloudFlareConfig(
        api_token=get_deterministic_secret("api_token"),
        api_key=get_deterministic_secret("api_token"),
        email="test@example.com",
        zone_id="test-zone-id",
        debug=True,
    )


class TestCloudFlareManager:
    """Test CloudFlare Manager orchestration functionality"""

    config: CloudFlareConfig

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.config = create_test_cloudflare_config()

    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_validate_credentials"
    )
    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_create_http_client"
    )
    def test_init_with_valid_credentials(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test CloudFlare manager initialization with valid credentials"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        manager = CloudFlareManager(config=self.config)
        expected_token = get_deterministic_secret("api_token")
        assert manager.config.api_token == expected_token
        assert manager.config.zone_id == "test-zone-id"
        assert manager.config.debug is True

    def test_init_with_missing_credentials(self) -> None:
        """Test CloudFlare manager initialization with missing credentials"""
        config = CloudFlareConfig(
            api_token=None,
            api_key=None,
            email=None,
            zone_id=None,
        )
        with pytest.raises(HAConnectorError):
            CloudFlareManager(config=config)

    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_validate_credentials"
    )
    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_create_http_client"
    )
    def test_load_config_from_env(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test loading configuration from environment variables"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        with patch.dict(
            os.environ,
            {
                "CF_API_TOKEN": get_deterministic_secret("api_token"),
                "CF_ZONE_ID": "env-zone-id",
                "CF_DEBUG": "true",
            },
        ):
            manager = CloudFlareManager()
            expected_env_token = get_deterministic_secret("api_token")
            assert manager.config.api_token == expected_env_token
            assert manager.config.zone_id == "env-zone-id"
            assert manager.config.debug is True

    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_validate_credentials"
    )
    @patch(
        "ha_connector.adapters.cloudflare_manager.CloudFlareManager."
        "_create_http_client"
    )
    def test_managers_initialized(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test that sub-managers are properly initialized"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        manager = CloudFlareManager(config=self.config)
        assert hasattr(manager, "access_manager")
        assert hasattr(manager, "dns_manager")
