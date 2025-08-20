"""Base platform abstraction layer.

This module defines the core abstractions for platform resource management.
All platform implementations must inherit from BasePlatform and implement
the required CRUD operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResourceOperation(str, Enum):
    """Enumeration of supported resource operations."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    VALIDATE = "validate"


class ResourceResponse(BaseModel):
    """Standard response format for all platform operations."""

    operation: ResourceOperation
    status: str = Field(..., description="Operation status: success, error, pending")
    resource: dict[str, Any] | None = Field(None, description="Resource data")
    resource_id: str | None = Field(None, description="Unique resource identifier")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BasePlatform(ABC):
    """Abstract base class for all platform implementations.

    This class defines the interface that all platform implementations must provide.
    Each platform (AWS, CloudFlare, Google Cloud, Azure) must implement these methods
    to provide unified resource management capabilities.
    """

    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        """Initialize the platform.

        Args:
            name: Platform name (e.g., "aws", "cloudflare")
            config: Platform-specific configuration
        """
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def create_resource(
        self,
        resource_type: str,
        resource_spec: BaseModel,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Create a new resource.

        Args:
            resource_type: Type of resource to create
            resource_spec: Resource specification
            **kwargs: Additional platform-specific parameters

        Returns:
            ResourceResponse with creation result
        """

    @abstractmethod
    async def read_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Read an existing resource.

        Args:
            resource_type: Type of resource to read
            resource_id: Unique resource identifier
            **kwargs: Additional platform-specific parameters

        Returns:
            ResourceResponse with resource data
        """

    @abstractmethod
    async def update_resource(
        self,
        resource_type: str,
        resource_id: str,
        resource_spec: BaseModel,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Update an existing resource.

        Args:
            resource_type: Type of resource to update
            resource_id: Unique resource identifier
            resource_spec: Updated resource specification
            **kwargs: Additional platform-specific parameters

        Returns:
            ResourceResponse with update result
        """

    @abstractmethod
    async def delete_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Delete an existing resource.

        Args:
            resource_type: Type of resource to delete
            resource_id: Unique resource identifier
            **kwargs: Additional platform-specific parameters

        Returns:
            ResourceResponse with deletion result
        """

    @abstractmethod
    async def list_resources(
        self,
        resource_type: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """List resources of a given type.

        Args:
            resource_type: Type of resources to list
            **kwargs: Additional platform-specific parameters

        Returns:
            ResourceResponse with list of resources
        """

    @abstractmethod
    async def validate_access(self) -> ResourceResponse:
        """Validate platform access and credentials.

        Returns:
            ResourceResponse with validation result
        """

    async def health_check(self) -> ResourceResponse:
        """Perform a health check on the platform.

        Returns:
            ResourceResponse with health status
        """
        return await self.validate_access()


class PlatformRegistry:
    """Registry for managing available platforms.

    This class provides a centralized registry for platform instances,
    allowing for dynamic platform loading and management.
    """

    def __init__(self) -> None:
        self._platforms: dict[str, BasePlatform] = {}

    def register(self, platform: BasePlatform) -> None:
        """Register a platform instance.

        Args:
            platform: Platform instance to register
        """
        self._platforms[platform.name] = platform

    def get(self, name: str) -> BasePlatform | None:
        """Get a registered platform by name.

        Args:
            name: Platform name

        Returns:
            Platform instance or None if not found
        """
        return self._platforms.get(name)

    def list_platforms(self) -> list[str]:
        """List all registered platform names.

        Returns:
            List of platform names
        """
        return list(self._platforms.keys())

    def unregister(self, name: str) -> bool:
        """Unregister a platform.

        Args:
            name: Platform name to unregister

        Returns:
            True if platform was unregistered, False if not found
        """
        if name in self._platforms:
            del self._platforms[name]
            return True
        return False
