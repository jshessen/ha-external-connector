"""Unified CloudFlare framework tests.

This module replaces the repetitive test classes across CloudFlare manager
test files with a single parameterized test suite, reducing code duplication
and ensuring consistent testing patterns.
"""

from typing import Any
from unittest.mock import Mock

import httpx
import pytest

from development.platforms.cloudflare.api_manager import CloudFlareResourceResponse
from tests.fixtures.cloudflare_fixtures import (
    CLOUDFLARE_MANAGER_TEST_PARAMS,
    CloudFlareTestFramework,
)


class TestCloudFlareManagerFramework:
    """Unified test class for all CloudFlare managers.

    This replaces individual test classes for each CloudFlare manager with
    a single parameterized approach, reducing duplication while maintaining
    comprehensive coverage.
    """

    @pytest.mark.parametrize(
        "manager_class,spec_class,test_spec", CLOUDFLARE_MANAGER_TEST_PARAMS
    )
    def test_manager_initialization(  # pylint: disable=unused-argument
        self,
        cloudflare_test_framework: CloudFlareTestFramework,
        manager_class: type,
        spec_class: type,
        test_spec: dict[str, Any],
    ) -> None:
        """Test initialization for all CloudFlare managers.

        Args:
            cloudflare_test_framework: CloudFlare testing infrastructure
            manager_class: CloudFlare manager class to test
            spec_class: Specification class for the manager (unused)
            test_spec: Test specification data (unused)
        """
        # Create manager instance using framework
        manager = cloudflare_test_framework.create_manager_with_mock_client(
            manager_class
        )

        # Verify manager is properly initialized
        assert manager is not None
        assert hasattr(manager, "client")
        assert isinstance(manager.client, Mock)

    @pytest.mark.parametrize(
        "manager_class,spec_class,test_spec", CLOUDFLARE_MANAGER_TEST_PARAMS
    )
    def test_create_or_update_operation(
        self,
        cloudflare_test_framework: CloudFlareTestFramework,
        manager_class: type,
        spec_class: type,
        test_spec: dict[str, Any],
    ) -> None:
        """Test create_or_update operations for all CloudFlare managers.

        Args:
            cloudflare_test_framework: CloudFlare testing infrastructure
            manager_class: CloudFlare manager class to test
            spec_class: Specification class for the manager
            test_spec: Test specification data
        """
        # Create manager instance
        manager = cloudflare_test_framework.create_manager_with_mock_client(
            manager_class
        )

        # Create specification object
        spec = spec_class(**test_spec)

        # Test create_or_update operation
        if hasattr(manager, "create_or_update"):
            # For managers that need account_id (AccessManager)
            if "Access" in manager_class.__name__:
                result = manager.create_or_update(spec, "test-account-id")
            else:
                result = manager.create_or_update(spec)

            # Verify response
            assert isinstance(result, CloudFlareResourceResponse)
            assert result.status == "success"
            assert result.resource is not None

            # Verify HTTP client was called
            manager.client.post.assert_called()

    @pytest.mark.parametrize(
        "manager_class,spec_class,test_spec", CLOUDFLARE_MANAGER_TEST_PARAMS
    )
    def test_error_handling(
        self,
        cloudflare_test_framework: CloudFlareTestFramework,
        manager_class: type,
        spec_class: type,
        test_spec: dict[str, Any],
    ) -> None:
        """Test error handling for all CloudFlare managers.

        Args:
            cloudflare_test_framework: CloudFlare testing infrastructure
            manager_class: CloudFlare manager class to test
            spec_class: Specification class for the manager
            test_spec: Test specification data
        """
        # Create manager instance
        manager = cloudflare_test_framework.create_manager_with_mock_client(
            manager_class
        )

        # Configure client to raise HTTP error
        manager.client.post.side_effect = httpx.HTTPError("Network error")

        # Create specification object
        spec = spec_class(**test_spec)

        # Test error handling
        if hasattr(manager, "create_or_update"):
            # For managers that need account_id (AccessManager)
            if "Access" in manager_class.__name__:
                result = manager.create_or_update(spec, "test-account-id")
            else:
                result = manager.create_or_update(spec)

            # Verify error response
            assert isinstance(result, CloudFlareResourceResponse)
            assert result.status == "error"
            assert len(result.errors) > 0
            assert any("error" in error.lower() for error in result.errors)


class TestCloudFlareTestFramework:
    """Test the CloudFlare test framework itself."""

    def test_framework_initialization(
        self, cloudflare_test_framework: CloudFlareTestFramework
    ) -> None:
        """Test CloudFlare test framework initialization."""
        assert cloudflare_test_framework.zone_id == "test-zone-id"
        assert cloudflare_test_framework.config is not None
        assert cloudflare_test_framework.mock_client is not None

        # Test config properties
        assert cloudflare_test_framework.config.zone_id == "test-zone-id"
        assert cloudflare_test_framework.config.debug is True
        # Check api_token safely
        api_token = cloudflare_test_framework.config.api_token
        assert api_token is not None
        assert api_token.startswith("test-token-")

    def test_mock_client_configuration(
        self, cloudflare_test_framework: CloudFlareTestFramework
    ) -> None:
        """Test mock client is properly configured."""
        client = cloudflare_test_framework.mock_client

        # Test that all HTTP methods are mocked
        assert hasattr(client, "post")
        assert hasattr(client, "get")
        assert hasattr(client, "put")
        assert hasattr(client, "delete")

        # Test default responses are configured
        assert client.post.return_value is not None
        assert client.get.return_value is not None

    def test_stub_response_creation(self) -> None:
        """Test stub response creation."""
        # Test success response
        success_response = CloudFlareResourceResponse(
            status="success", resource={"id": "test-id", "message": "Test successful"}
        )
        assert success_response.status == "success"
        assert success_response.resource is not None
        assert isinstance(success_response.resource, dict)
        # Check for id key using get method to avoid pylint membership test warning
        resource = success_response.resource
        assert resource.get("id") is not None
        assert not success_response.errors

        # Test failure response
        failure_response = CloudFlareResourceResponse(
            status="error", errors=["Test operation failed"]
        )
        assert failure_response.status == "error"
        assert failure_response.resource is None
        assert len(failure_response.errors) > 0

    def test_cloudflare_config_fixture(self, cloudflare_config: Any) -> None:
        """Test CloudFlare config fixture."""
        assert cloudflare_config.zone_id == "test-zone-id"
        assert cloudflare_config.debug is True
        # Check api_token safely
        api_token = cloudflare_config.api_token
        assert api_token is not None
        assert api_token.startswith("test-token-")

    def test_mock_client_fixture(self, mock_cloudflare_client: Mock) -> None:
        """Test mock CloudFlare client fixture."""
        assert isinstance(mock_cloudflare_client, Mock)
        assert hasattr(mock_cloudflare_client, "post")
        assert hasattr(mock_cloudflare_client, "get")

    def test_environment_fixture(self, cloudflare_environment: dict[str, str]) -> None:
        """Test CloudFlare environment fixture."""
        assert cloudflare_environment["CF_ZONE_ID"] == "test-zone-id"
        assert cloudflare_environment["CF_DEBUG"] == "true"
        # Check api_token safely
        api_token = cloudflare_environment["CF_API_TOKEN"]
        assert api_token.startswith("test-token-")
