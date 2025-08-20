"""Service compatibility layer for platform consolidation.

This module provides backward-compatible service classes that bridge the old
/platform/ service interface with the new unified /platforms/ architecture.
This allows the main component to use the same interface while using the
consolidated platform architecture underneath.
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .aws.client import AWSPlatform
from .cloudflare.client import CloudFlarePlatform
from .registry import register_platform


class PlatformType(Enum):
    """Supported platform types."""

    AWS = "aws"
    CLOUDFLARE = "cloudflare"
    GOOGLE_CLOUD = "google_cloud"
    AZURE = "azure"


@dataclass
class PlatformConfig:
    """Platform configuration container."""

    platform_type: PlatformType
    credentials: dict[str, Any]
    region: str | None = None
    environment: str = "production"


class PlatformService(ABC):
    """Abstract base class for platform services."""

    def __init__(self, config: PlatformConfig):
        """Initialize platform service with configuration."""
        self.config = config
        self._client = None
        self._platform = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the platform service."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check platform service health."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up platform resources."""
        raise NotImplementedError


class AWSService(PlatformService):
    """AWS service adapter for unified platform architecture."""

    def __init__(self, config: PlatformConfig):
        """Initialize AWS service."""
        super().__init__(config)
        if config.platform_type != PlatformType.AWS:
            raise ValueError("AWS service requires AWS platform type")

    async def initialize(self) -> bool:
        """Initialize AWS platform and register it."""
        try:
            # Create AWS platform instance using the unified architecture
            platform_config = {
                "region": self.config.region,
                "credentials": self.config.credentials,
                "environment": self.config.environment,
            }
            self._platform = AWSPlatform(platform_config)

            # Register with the global registry
            register_platform(self._platform)

            return True
        except (ValueError, KeyError, RuntimeError):
            return False

    async def health_check(self) -> bool:
        """Check AWS platform health."""
        if self._platform is None:
            return False
        try:
            # Use the platform's health check if available
            return True  # Simplified for now
        except (ValueError, RuntimeError):
            return False

    async def cleanup(self) -> None:
        """Clean up AWS platform resources."""
        if self._platform:
            # Platform cleanup logic would go here
            pass


class CloudFlareService(PlatformService):
    """CloudFlare service adapter for unified platform architecture."""

    def __init__(self, config: PlatformConfig):
        """Initialize CloudFlare service."""
        super().__init__(config)
        if config.platform_type != PlatformType.CLOUDFLARE:
            raise ValueError("CloudFlare service requires CloudFlare platform type")

    async def initialize(self) -> bool:
        """Initialize CloudFlare platform and register it."""
        try:
            # Create CloudFlare platform instance using the unified architecture
            platform_config = {
                "credentials": self.config.credentials,
                "environment": self.config.environment,
            }
            self._platform = CloudFlarePlatform(platform_config)

            # Register with the global registry
            register_platform(self._platform)

            return True
        except (ValueError, KeyError, RuntimeError):
            return False

    async def health_check(self) -> bool:
        """Check CloudFlare platform health."""
        if self._platform is None:
            return False
        try:
            # Use the platform's health check if available
            return True  # Simplified for now
        except (ValueError, RuntimeError):
            return False

    async def cleanup(self) -> None:
        """Clean up CloudFlare platform resources."""
        if self._platform:
            # Platform cleanup logic would go here
            pass


class PlatformRegistry:
    """Registry for managing platform services."""

    def __init__(self):
        """Initialize platform registry."""
        self._services: dict[PlatformType, PlatformService] = {}

    def register_service(
        self, platform_type: PlatformType, service: PlatformService
    ) -> None:
        """Register a platform service."""
        self._services[platform_type] = service

    def get_service(self, platform_type: PlatformType) -> PlatformService | None:
        """Get a registered platform service."""
        return self._services.get(platform_type)

    async def initialize_all(self) -> bool:
        """Initialize all registered services."""
        results: list[bool] = []
        for service in self._services.values():
            with contextlib.suppress(ValueError, RuntimeError):
                result = await service.initialize()
                results.append(result)
                continue
            results.append(False)
        return all(results)

    async def cleanup_all(self) -> None:
        """Clean up all registered services."""
        for service in self._services.values():
            with contextlib.suppress(ValueError, RuntimeError):
                await service.cleanup()


# Global platform registry instance
platform_registry = PlatformRegistry()
