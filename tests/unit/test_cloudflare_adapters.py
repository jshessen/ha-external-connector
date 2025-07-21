"""
Unit Tests for CloudFlare Adapters Module

Tests CloudFlare adapter functionality including DNS, Access Applications, and Zones.
"""

from unittest.mock import Mock, patch

import pytest

from ha_connector.adapters.cloudflare_manager import (
    AccessApplicationSpec,
    CloudFlareConfig,
    CloudFlareManager,
    CloudFlareResourceResponse,
    CloudFlareResourceType,
    DNSRecordSpec,
)
from ha_connector.utils import HAConnectorError


def create_test_cloudflare_config() -> CloudFlareConfig:
    """Helper function to create test CloudFlare config"""
    return CloudFlareConfig(
        api_token="test-token",
        api_key=None,
        email=None,
        zone_id="test-zone-id",
        debug=True,
    )


class TestCloudFlareManager:
    """Test CloudFlare Manager base functionality"""

    config: CloudFlareConfig

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.config = create_test_cloudflare_config()

    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_validate_credentials")
    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_create_http_client")
    def test_init_with_valid_credentials(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test CloudFlare manager initialization with valid credentials"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        manager = CloudFlareManager(config=self.config)
        assert manager.config.api_token == "test-token"
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

    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_validate_credentials")
    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_create_http_client")
    def test_load_config_from_env(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test loading configuration from environment variables"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        with patch.dict('os.environ', {
            'CF_API_TOKEN': 'env-token',
            'CF_ZONE_ID': 'env-zone-id',
            'CF_DEBUG': 'true'
        }):
            manager = CloudFlareManager()
            assert manager.config.api_token == "env-token"
            assert manager.config.zone_id == "env-zone-id"
            assert manager.config.debug is True

    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_validate_credentials")
    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_create_http_client")
    def test_managers_initialized(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test that sub-managers are properly initialized"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        manager = CloudFlareManager(config=self.config)
        assert hasattr(manager, 'access_manager')
        assert hasattr(manager, 'dns_manager')


class TestCloudFlareResourceTypes:
    """Test CloudFlare Resource Type enumeration"""

    def test_resource_type_values(self) -> None:
        """Test that resource types have expected values"""
        assert CloudFlareResourceType.ACCESS_APPLICATION.value == "access_application"
        assert CloudFlareResourceType.DNS_RECORD.value == "dns_record"
        assert CloudFlareResourceType.ZONE.value == "zone"

    def test_resource_type_iteration(self) -> None:
        """Test that we can iterate through resource types"""
        resource_types = list(CloudFlareResourceType)
        assert CloudFlareResourceType.ACCESS_APPLICATION in resource_types
        assert CloudFlareResourceType.DNS_RECORD in resource_types
        assert CloudFlareResourceType.ZONE in resource_types


class TestCloudFlareConfig:
    """Test CloudFlare configuration model"""

    def test_config_with_api_token(self) -> None:
        """Test configuration with API token"""
        config = CloudFlareConfig(
            api_token="test-token",
            api_key=None,
            email=None,
            zone_id=None,
        )
        assert config.api_token == "test-token"
        assert config.api_key is None
        assert config.email is None
        assert config.debug is False

    def test_config_with_api_key_and_email(self) -> None:
        """Test configuration with API key and email"""
        config = CloudFlareConfig(
            api_token=None,
            api_key="test-key",
            email="test@example.com",
            zone_id=None,
        )
        assert config.api_key == "test-key"
        assert config.email == "test@example.com"
        assert config.api_token is None

    def test_config_with_debug_enabled(self) -> None:
        """Test configuration with debug enabled"""
        config = CloudFlareConfig(
            api_token="test-token",
            api_key=None,
            email=None,
            zone_id=None,
            debug=True,
        )
        assert config.debug is True


class TestAccessApplicationSpec:
    """Test Access Application specification model"""

    def test_minimal_spec(self) -> None:
        """Test creating minimal access application spec"""
        spec = AccessApplicationSpec(
            name="test-app",
            domain="example.com",
            subdomain=None,
            cors_headers=None,
            tags=None,
        )
        assert spec.name == "test-app"
        assert spec.domain == "example.com"
        assert spec.session_duration == "24h"
        assert spec.auto_redirect_to_identity is True

    def test_full_spec(self) -> None:
        """Test creating full access application spec"""
        spec = AccessApplicationSpec(
            name="test-app",
            domain="example.com",
            subdomain="app",
            session_duration="12h",
            auto_redirect_to_identity=False,
            allowed_identity_providers=["google", "github"],
            cors_headers={"Access-Control-Allow-Origin": "*"},
            service_auth_401_redirect=True,
            tags=["production", "web"],
        )
        assert spec.name == "test-app"
        assert spec.domain == "example.com"
        assert spec.subdomain == "app"
        assert spec.session_duration == "12h"
        assert spec.auto_redirect_to_identity is False
        assert spec.allowed_identity_providers == ["google", "github"]
        assert spec.service_auth_401_redirect is True
        assert spec.tags == ["production", "web"]


class TestDNSRecordSpec:
    """Test DNS Record specification model"""

    def test_minimal_dns_record(self) -> None:
        """Test creating minimal DNS record spec"""
        spec = DNSRecordSpec(
            zone_id="test-zone",
            record_type="A",
            name="test.example.com",
            content="192.168.1.1"
        )
        assert spec.zone_id == "test-zone"
        assert spec.record_type == "A"
        assert spec.name == "test.example.com"
        assert spec.content == "192.168.1.1"
        assert spec.ttl == 1
        assert spec.proxied is True

    def test_full_dns_record(self) -> None:
        """Test creating full DNS record spec"""
        spec = DNSRecordSpec(
            zone_id="test-zone",
            record_type="CNAME",
            name="www.example.com",
            content="example.com",
            ttl=300,
            proxied=False
        )
        assert spec.zone_id == "test-zone"
        assert spec.record_type == "CNAME"
        assert spec.name == "www.example.com"
        assert spec.content == "example.com"
        assert spec.ttl == 300
        assert spec.proxied is False


class TestCloudFlareResourceResponse:
    """Test CloudFlare resource response model"""

    def test_success_response(self) -> None:
        """Test successful response"""
        response = CloudFlareResourceResponse(
            status="success",
            resource={"id": "123", "name": "test"}
        )
        assert response.status == "success"
        assert response.resource == {"id": "123", "name": "test"}
        assert not response.errors

    def test_error_response(self) -> None:
        """Test error response"""
        response = CloudFlareResourceResponse(
            status="error",
            errors=["Invalid credentials", "Resource not found"]
        )
        assert response.status == "error"
        assert response.resource is None
        assert response.errors == ["Invalid credentials", "Resource not found"]


class TestCredentialValidation:
    """Test credential validation logic"""

    def test_valid_api_token(self) -> None:
        """Test validation with valid API token"""
        config = CloudFlareConfig(
            api_token="valid-token",
            api_key=None,
            email=None,
            zone_id=None,
        )
        # This would be tested via CloudFlareManager initialization
        # but we can test the config is valid
        assert config.api_token == "valid-token"

    def test_valid_api_key_email_pair(self) -> None:
        """Test validation with valid API key and email"""
        config = CloudFlareConfig(
            api_token=None,
            api_key="valid-key",
            email="test@example.com",
            zone_id=None,
        )
        assert config.api_key == "valid-key"
        assert config.email == "test@example.com"

    def test_invalid_partial_credentials(self) -> None:
        """Test validation fails with incomplete credentials"""
        config = CloudFlareConfig(
            api_token=None,
            api_key="valid-key",
            email=None,  # Missing email
            zone_id=None,
        )
        with pytest.raises(HAConnectorError):
            CloudFlareManager(config=config)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_configuration(self) -> None:
        """Test handling of invalid configuration"""
        config = CloudFlareConfig(
            api_token=None,
            api_key=None,
            email=None,
            zone_id=None,
        )  # No credentials
        with pytest.raises(HAConnectorError):
            CloudFlareManager(config=config)

    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_validate_credentials")
    @patch("ha_connector.adapters.cloudflare_manager.CloudFlareManager."
           "_create_http_client")
    def test_manager_creation_success(
        self, mock_create_client: Mock, mock_validate: Mock
    ) -> None:
        """Test successful manager creation"""
        mock_validate.return_value = None
        mock_create_client.return_value = Mock()

        config = CloudFlareConfig(
            api_token="test-token",
            api_key=None,
            email=None,
            zone_id=None,
        )
        manager = CloudFlareManager(config=config)
        assert manager.config.api_token == "test-token"
        mock_validate.assert_called_once()
        mock_create_client.assert_called_once()
