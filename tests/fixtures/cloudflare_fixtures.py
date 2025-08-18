"""Unified CloudFlare testing framework and fixtures."""

import unittest.mock
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock

import pytest
from ha_connector.platforms.cloudflare.api_manager import (
    AccessApplicationSpec,
    CloudFlareAccessManager,
    CloudFlareConfig,
    CloudFlareDNSManager,
    DNSRecordSpec,
)


class CloudFlareTestFramework:
    """Unified framework for CloudFlare service testing."""

    def __init__(self, zone_id: str = "test-zone-id") -> None:
        self.zone_id = zone_id
        self.config = self._create_test_config()
        self.mock_client = self._setup_mock_client()

    def _create_test_config(self) -> CloudFlareConfig:
        return CloudFlareConfig(
            api_token="test-token-" + "x" * 32,
            api_key=None,
            email=None,
            zone_id=self.zone_id,
            debug=True,
        )

    def _setup_mock_client(self) -> Mock:
        mock_client = Mock()
        mock_success_response = Mock()
        mock_success_response.json.return_value = {
            "success": True,
            "result": {"id": "test-resource-id", "status": "created"},
        }
        mock_success_response.raise_for_status.return_value = None
        mock_success_response.status_code = 200

        mock_client.post.return_value = mock_success_response
        mock_client.put.return_value = mock_success_response
        mock_client.patch.return_value = mock_success_response
        mock_client.delete.return_value = mock_success_response
        mock_client.get.return_value = mock_success_response

        return mock_client

    def create_manager_with_mock_client(self, manager_class: type) -> Any:
        if manager_class in [CloudFlareAccessManager, CloudFlareDNSManager]:
            return manager_class(self.mock_client)
        raise ValueError(f"Unknown manager class: {manager_class}")


CLOUDFLARE_MANAGER_TEST_PARAMS = [
    (
        CloudFlareAccessManager,
        AccessApplicationSpec,
        {
            "name": "Test Access App",
            "domain": "example.com",
            "subdomain": "app",
            "session_duration": "24h",
        },
    ),
    (
        CloudFlareDNSManager,
        DNSRecordSpec,
        {
            "zone_id": "test-zone-id",
            "record_type": "A",
            "name": "test.example.com",
            "content": "192.168.1.1",
            "ttl": 3600,
            "proxied": False,
        },
    ),
]


@pytest.fixture(scope="session")
def cloudflare_test_framework() -> Generator[CloudFlareTestFramework]:
    framework = CloudFlareTestFramework()
    yield framework


@pytest.fixture(scope="function")
def cloudflare_config() -> CloudFlareConfig:
    return CloudFlareConfig(
        api_token="test-token-" + "x" * 32,
        api_key=None,
        email=None,
        zone_id="test-zone-id",
        debug=True,
    )


@pytest.fixture(scope="function")
def mock_cloudflare_client() -> Generator[Mock]:
    framework = CloudFlareTestFramework()
    yield framework.mock_client


@pytest.fixture(scope="function")
def cloudflare_environment() -> Generator[dict[str, str]]:
    env_vars = {
        "CF_API_TOKEN": "test-token-" + "x" * 32,
        "CF_ZONE_ID": "test-zone-id",
        "CF_DEBUG": "true",
    }

    with unittest.mock.patch.dict("os.environ", env_vars):
        yield env_vars
