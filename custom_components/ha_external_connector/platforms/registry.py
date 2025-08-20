"""Platform registry and management utilities.

This module provides centralized platform registration and retrieval functionality.
It maintains a global registry of platform instances and provides factory functions
for creating and configuring platforms.
"""

from __future__ import annotations

from typing import Any

from .aws.client import AWSPlatform
from .base import BasePlatform, PlatformRegistry
from .cloudflare.client import CloudFlarePlatform

# Global platform registry instance
_registry = PlatformRegistry()


def register_platform(platform: BasePlatform) -> None:
    """Register a platform instance in the global registry.

    Args:
        platform: Platform instance to register
    """
    _registry.register(platform)


def get_platform(name: str) -> BasePlatform | None:
    """Get a platform by name from the global registry.

    Args:
        name: Platform name (e.g., "aws", "cloudflare")

    Returns:
        Platform instance or None if not found
    """
    return _registry.get(name)


def list_platforms() -> list[str]:
    """List all registered platform names.

    Returns:
        List of platform names
    """
    return _registry.list_platforms()


def unregister_platform(name: str) -> bool:
    """Unregister a platform from the global registry.

    Args:
        name: Platform name to unregister

    Returns:
        True if platform was unregistered, False if not found
    """
    return _registry.unregister(name)


def create_platform(name: str, config: dict[str, Any] | None = None) -> BasePlatform:
    """Factory function to create and register a platform.

    Args:
        name: Platform name (e.g., "aws", "cloudflare")
        config: Platform-specific configuration

    Returns:
        Created platform instance

    Raises:
        ValueError: If platform type is not supported
    """
    # Create platform implementations
    if name == "aws":
        platform = AWSPlatform(config=config)
    elif name == "cloudflare":
        platform = CloudFlarePlatform(config=config)
    else:
        supported_platforms = ["aws", "cloudflare"]
        raise ValueError(
            f"Unsupported platform: {name}. "
            f"Supported platforms: {', '.join(supported_platforms)}"
        )

    # Register the created platform
    register_platform(platform)
    return platform


def get_or_create_platform(
    name: str, config: dict[str, Any] | None = None
) -> BasePlatform:
    """Get an existing platform or create it if it doesn't exist.

    Args:
        name: Platform name (e.g., "aws", "cloudflare")
        config: Platform-specific configuration (used only if creating)

    Returns:
        Platform instance
    """
    platform = get_platform(name)
    if platform is None:
        platform = create_platform(name, config)
    return platform
