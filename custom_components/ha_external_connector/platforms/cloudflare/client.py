"""CloudFlare Platform Client - Modern async implementation.

This module provides a unified CloudFlare platform client that integrates the
sophisticated resource management capabilities from the development implementation
with the new platform abstraction layer.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from ..base import BasePlatform, ResourceOperation, ResourceResponse
from .models import (
    AccessApplicationSpec,
    CloudFlareResourceType,
    DNSRecordSpec,
    ZoneSpec,
)
from .services import AccessService, DNSService, ZoneService


class CloudFlareConfig(BaseModel):
    """Configuration object for CloudFlare authentication and settings.

    Groups related authentication parameters to reduce class complexity.
    """

    api_token: str | None = Field(default=None, description="CloudFlare API token")
    api_key: str | None = Field(default=None, description="CloudFlare API key")
    email: str | None = Field(default=None, description="CloudFlare account email")
    zone_id: str | None = Field(default=None, description="Default zone ID")


# Import the sophisticated CloudFlare manager for backwards compatibility
try:
    from ....development.platforms.cloudflare.api_manager import (
        CloudFlareManager as LegacyCloudFlareManager,
    )
    from ....development.platforms.cloudflare.api_manager import (
        get_cloudflare_manager,
    )
except ImportError:
    # Fallback if development module is not available
    LegacyCloudFlareManager = None
    get_cloudflare_manager = None


class CloudFlarePlatform(BasePlatform):
    """Modern CloudFlare platform implementation.

    This class provides a unified interface for CloudFlare resource management,
    integrating the sophisticated capabilities from the development implementation
    with the new async platform abstraction layer.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize CloudFlare platform.

        Args:
            config: CloudFlare configuration including API token, email, etc.
        """
        super().__init__("cloudflare", config)

        # CloudFlare configuration - grouped into config object
        self.config = CloudFlareConfig(**(config or {}))

        # Initialize HTTP client
        self._client = None

        # Initialize services
        self.access_service = AccessService()
        self.dns_service = DNSService()
        self.zone_service = ZoneService()

        # Legacy compatibility
        self._legacy_manager = None
        if LegacyCloudFlareManager:
            self._legacy_manager = get_cloudflare_manager()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with CloudFlare headers."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}

            if self.config.api_token:
                headers["Authorization"] = f"Bearer {self.config.api_token}"
            elif self.config.api_key and self.config.email:
                headers["X-Auth-Email"] = self.config.email
                headers["X-Auth-Key"] = self.config.api_key

            self._client = httpx.AsyncClient(
                base_url="https://api.cloudflare.com/client/v4",
                headers=headers,
                timeout=30.0,
            )

        return self._client

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def create_resource(
        self,
        resource_type: str,
        resource_spec: Any,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Create a new CloudFlare resource.

        Args:
            resource_type: Type of CloudFlare resource to create
            resource_spec: Resource specification (Pydantic model)
            **kwargs: Additional CloudFlare-specific parameters

        Returns:
            ResourceResponse with creation result
        """
        try:
            # Convert string to enum
            cf_resource_type = CloudFlareResourceType(resource_type)

            # Route to appropriate service
            if cf_resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                result = await self.access_service.create_or_update(
                    self.client,
                    AccessApplicationSpec.model_validate(resource_spec),
                    kwargs.get("account_id", ""),
                )
            elif cf_resource_type == CloudFlareResourceType.DNS_RECORD:
                result = await self.dns_service.create_or_update(
                    self.client, DNSRecordSpec.model_validate(resource_spec)
                )
            elif cf_resource_type == CloudFlareResourceType.ZONE:
                result = await self.zone_service.create_or_update(
                    self.client, ZoneSpec.model_validate(resource_spec)
                )
            else:
                return ResourceResponse(
                    operation=ResourceOperation.CREATE,
                    status="error",
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            # Convert service response to platform response
            return ResourceResponse(
                operation=ResourceOperation.CREATE,
                status=result.status,
                resource=result.resource,
                resource_id=result.resource.get("id") if result.resource else None,
                errors=result.errors,
                metadata={"cloudflare_zone_id": self.config.zone_id},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.CREATE,
                status="error",
                errors=[f"Invalid resource type: {e}"],
            )

    async def read_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Read an existing CloudFlare resource.

        Args:
            resource_type: Type of CloudFlare resource to read
            resource_id: CloudFlare resource identifier
            **kwargs: Additional CloudFlare-specific parameters

        Returns:
            ResourceResponse with resource data
        """
        try:
            cf_resource_type = CloudFlareResourceType(resource_type)

            # Route to appropriate service
            if cf_resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                result = await self.access_service.read(
                    self.client, resource_id, kwargs.get("account_id", "")
                )
            elif cf_resource_type == CloudFlareResourceType.DNS_RECORD:
                result = await self.dns_service.read(
                    self.client,
                    resource_id,
                    kwargs.get("zone_id", self.config.zone_id or ""),
                )
            elif cf_resource_type == CloudFlareResourceType.ZONE:
                result = await self.zone_service.read(self.client, resource_id)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.READ,
                    status="error",
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.READ,
                status=result.status,
                resource=result.resource,
                resource_id=resource_id,
                errors=result.errors,
                metadata={"cloudflare_zone_id": self.config.zone_id},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.READ,
                status="error",
                errors=[f"Invalid resource type: {e}"],
            )
        except httpx.HTTPError as e:
            return ResourceResponse(
                operation=ResourceOperation.READ,
                status="error",
                errors=[f"Resource read failed: {e}"],
            )

    async def update_resource(
        self,
        resource_type: str,
        resource_id: str,
        resource_spec: Any,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Update an existing CloudFlare resource.

        Args:
            resource_type: Type of CloudFlare resource to update
            resource_id: CloudFlare resource identifier
            resource_spec: Updated resource specification
            **kwargs: Additional CloudFlare-specific parameters

        Returns:
            ResourceResponse with update result
        """
        # For most CloudFlare resources, update is the same as create_or_update
        return await self.create_resource(resource_type, resource_spec, **kwargs)

    async def delete_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Delete an existing CloudFlare resource.

        Args:
            resource_type: Type of CloudFlare resource to delete
            resource_id: CloudFlare resource identifier
            **kwargs: Additional CloudFlare-specific parameters

        Returns:
            ResourceResponse with deletion result
        """
        try:
            cf_resource_type = CloudFlareResourceType(resource_type)

            # Route to appropriate service
            if cf_resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                result = await self.access_service.delete(
                    self.client, resource_id, kwargs.get("account_id", "")
                )
            elif cf_resource_type == CloudFlareResourceType.DNS_RECORD:
                result = await self.dns_service.delete(
                    self.client,
                    resource_id,
                    kwargs.get("zone_id", self.config.zone_id or ""),
                )
            elif cf_resource_type == CloudFlareResourceType.ZONE:
                result = await self.zone_service.delete(self.client, resource_id)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.DELETE,
                    status="error",
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status=result.status,
                resource=result.resource,
                resource_id=resource_id,
                errors=result.errors,
                metadata={"cloudflare_zone_id": self.config.zone_id},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status="error",
                errors=[f"Invalid resource type: {e}"],
            )
        except httpx.HTTPError as e:
            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status="error",
                errors=[f"Resource deletion failed: {e}"],
            )

    async def list_resources(
        self,
        resource_type: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """List CloudFlare resources of a given type.

        Args:
            resource_type: Type of CloudFlare resources to list
            **kwargs: Additional CloudFlare-specific parameters

        Returns:
            ResourceResponse with list of resources
        """
        try:
            cf_resource_type = CloudFlareResourceType(resource_type)

            # Route to appropriate service
            if cf_resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                result = await self.access_service.list_applications(
                    self.client, kwargs.get("account_id", "")
                )
            elif cf_resource_type == CloudFlareResourceType.DNS_RECORD:
                result = await self.dns_service.list_records(
                    self.client, kwargs.get("zone_id", self.config.zone_id or "")
                )
            elif cf_resource_type == CloudFlareResourceType.ZONE:
                result = await self.zone_service.list_zones(self.client)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.LIST,
                    status="error",
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status=result.status,
                resource=result.resource,
                errors=result.errors,
                metadata={
                    "cloudflare_zone_id": self.config.zone_id,
                    "resource_count": (len(result.resource) if result.resource else 0),
                },
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status="error",
                errors=[f"Invalid resource type: {e}"],
            )
        except httpx.HTTPError as e:
            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status="error",
                errors=[f"Resource listing failed: {e}"],
            )

    async def validate_access(self) -> ResourceResponse:
        """Validate CloudFlare access and credentials.

        Returns:
            ResourceResponse with validation result
        """
        try:
            # Test API access by getting user info
            response = await self.client.get("/user")

            if response.status_code == 200:
                user_data = response.json()
                return ResourceResponse(
                    operation=ResourceOperation.VALIDATE,
                    status="success",
                    resource=user_data.get("result", {}),
                    metadata={"cloudflare_zone_id": self.config.zone_id},
                )
            return ResourceResponse(
                operation=ResourceOperation.VALIDATE,
                status="error",
                errors=[f"CloudFlare API access failed: {response.status_code}"],
                metadata={"cloudflare_zone_id": self.config.zone_id},
            )

        except httpx.HTTPError as e:
            return ResourceResponse(
                operation=ResourceOperation.VALIDATE,
                status="error",
                errors=[f"CloudFlare access validation failed: {e}"],
                metadata={"cloudflare_zone_id": self.config.zone_id},
            )
