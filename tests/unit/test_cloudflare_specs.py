"""
CloudFlare Specification and Configuration Tests

Tests for CloudFlare data models, specifications, and configuration validation.
These tests focus on data structure validation and business logic, not service
implementation.
"""

from ha_connector.adapters.cloudflare_manager import (
    AccessApplicationSpec,
    CloudFlareConfig,
    CloudFlareResourceResponse,
    CloudFlareResourceType,
    DNSRecordSpec,
)


class TestCloudFlareResourceTypes:
    """Test CloudFlare resource type enumeration"""

    def test_resource_type_values(self) -> None:
        """Test that resource types have expected values"""
        assert CloudFlareResourceType.ACCESS_APPLICATION == "access_application"
        assert CloudFlareResourceType.DNS_RECORD == "dns_record"

    def test_resource_type_iteration(self) -> None:
        """Test that we can iterate over resource types"""
        types = list(CloudFlareResourceType)
        assert len(types) >= 2
        assert CloudFlareResourceType.ACCESS_APPLICATION in types
        assert CloudFlareResourceType.DNS_RECORD in types


class TestCloudFlareConfig:
    """Test CloudFlare configuration model"""

    def test_config_with_api_token_and_debug(self) -> None:
        """Test config creation with API token and debug mode"""
        config = CloudFlareConfig(
            api_token="test-token",
            api_key=None,
            email=None,
            zone_id="test-zone-id",
            debug=True,
        )
        assert config.api_token == "test-token"

    def test_config_with_api_key_and_email(self) -> None:
        """Test config creation with API key and email"""
        config = CloudFlareConfig(
            api_token=None,
            api_key="test-key",
            email="test@example.com",
            zone_id="test-zone-id",
        )
        assert config.api_key == "test-key"
        assert config.email == "test@example.com"
        assert config.zone_id == "test-zone-id"
        assert config.api_token is None

    def test_config_with_debug_enabled(self) -> None:
        """Test config with debug mode enabled"""
        config = CloudFlareConfig(
            api_token="test-token",
            api_key=None,
            email=None,
            zone_id="test-zone-id",
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
            content="192.168.1.1",
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
            proxied=False,
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
        """Test creating success response"""
        response = CloudFlareResourceResponse(
            status="success", resource={"id": "123", "name": "test"}
        )
        assert response.status == "success"
        assert response.resource == {"id": "123", "name": "test"}
        assert not response.errors

    def test_error_response(self) -> None:
        """Test creating error response"""
        response = CloudFlareResourceResponse(status="error", errors=["Invalid token"])
        assert response.status == "error"
        assert response.errors == ["Invalid token"]
        assert response.resource is None
