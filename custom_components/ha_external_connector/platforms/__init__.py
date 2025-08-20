"""Platform abstraction layer for external cloud platforms.

This module provides a unified interface for managing resources across different
cloud platforms including AWS, CloudFlare, Google Cloud, and Azure.

The platform layer provides:
- Unified CRUD operations for cloud resources
- Type-safe resource specifications using Pydantic models
- Consistent error handling and response formats
- Platform-specific optimizations while maintaining common interfaces
- Async/await support for non-blocking operations
"""

from __future__ import annotations

from .base import BasePlatform, PlatformRegistry, ResourceOperation, ResourceResponse
from .registry import get_platform, register_platform
from .services import (
    AWSService,
    CloudFlareService,
    PlatformConfig,
    PlatformService,
    PlatformType,
    platform_registry,
)

__all__ = [
    "BasePlatform",
    "PlatformRegistry",
    "ResourceOperation",
    "ResourceResponse",
    "get_platform",
    "register_platform",
    # Service compatibility layer
    "AWSService",
    "CloudFlareService",
    "PlatformConfig",
    "PlatformService",
    "PlatformType",
    "platform_registry",
]


from .aws.client import AWSPlatform
from .cloudflare.client import CloudFlarePlatform


def __getattr__(name: str) -> type[BasePlatform]:
    """Dynamic import of platform implementations."""
    if name == "AWSPlatform":
        return AWSPlatform
    if name == "CloudFlarePlatform":
        return CloudFlarePlatform
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
