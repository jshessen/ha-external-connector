"""CloudFlare service implementations for resource management.

This module provides async service classes for managing different types of
CloudFlare resources. Each service class handles the specific CloudFlare API
calls and resource management for its respective CloudFlare service.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field


class CloudFlareServiceResponse(BaseModel):
    """Response model for CloudFlare service operations."""

    status: str
    resource: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


class BaseCloudFlareService:
    """Base class for CloudFlare service implementations."""

    def __init__(self) -> None:
        pass


class AccessService(BaseCloudFlareService):
    """Service for managing CloudFlare Access applications.

    Provides comprehensive access management with application lifecycle,
    policy configuration, and sophisticated error handling patterns.
    """

    async def create_or_update(
        self, client: httpx.AsyncClient, spec: Any, account_id: str
    ) -> CloudFlareServiceResponse:
        """Create or update Access application.

        Args:
            client: Authenticated httpx client
            spec: Access application specification
            account_id: CloudFlare account ID

        Returns:
            Response containing application status and details
        """
        try:
            # Prepare application data from spec
            app_data = {
                "name": spec.name,
                "domain": spec.domain,
                "session_duration": getattr(spec, "session_duration", "24h"),
                "auto_redirect_to_identity": getattr(
                    spec, "auto_redirect_to_identity", True
                ),
            }

            # Add optional fields
            if hasattr(spec, "subdomain") and spec.subdomain:
                app_data["domain"] = f"{spec.subdomain}.{spec.domain}"

            if hasattr(spec, "allowed_identity_providers"):
                app_data["allowed_idps"] = spec.allowed_identity_providers

            if hasattr(spec, "cors_headers") and spec.cors_headers:
                app_data["cors_headers"] = spec.cors_headers

            if hasattr(spec, "service_auth_401_redirect"):
                app_data["service_auth_401_redirect"] = spec.service_auth_401_redirect

            # Check if application exists (by name lookup)
            existing_app = await self._find_application_by_name(
                client, spec.name, account_id
            )

            if existing_app:
                # Update existing application
                app_id = existing_app["id"]
                response = await client.put(
                    f"/accounts/{account_id}/access/apps/{app_id}", json=app_data
                )
                operation = "updated"
            else:
                # Create new application
                response = await client.post(
                    f"/accounts/{account_id}/access/apps", json=app_data
                )
                operation = "created"

            response.raise_for_status()
            data = response.json()

            if not data.get("success", False):
                errors = data.get("errors", [])
                return CloudFlareServiceResponse(
                    status="error", errors=[f"CloudFlare API error: {errors}"]
                )

            result = data["result"]
            result["operation"] = operation

            return CloudFlareServiceResponse(status="success", resource=result)

        except httpx.HTTPError as e:
            return CloudFlareServiceResponse(
                status="error",
                errors=[f"HTTP error creating Access application: {str(e)}"],
            )

    async def _find_application_by_name(
        self, client: httpx.AsyncClient, name: str, account_id: str
    ) -> dict[str, Any] | None:
        """Find Access application by name.

        Args:
            client: Authenticated httpx client
            name: Application name to search for
            account_id: CloudFlare account ID

        Returns:
            Application data if found, None otherwise
        """
        try:
            response = await client.get(f"/accounts/{account_id}/access/apps")
            response.raise_for_status()

            data = response.json()
            if data.get("success", False):
                apps = data.get("result", [])
                for app in apps:
                    if app.get("name") == name:
                        return app
            return None

        except httpx.HTTPError:
            return None

    async def read(
        self, client: httpx.AsyncClient, app_id: str, account_id: str
    ) -> CloudFlareServiceResponse:
        """Read Access application configuration.

        Args:
            client: Authenticated httpx client
            app_id: Access application ID
            account_id: CloudFlare account ID

        Returns:
            Response containing application details
        """
        try:
            response = await client.get(f"/accounts/{account_id}/access/apps/{app_id}")
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                errors = data.get("errors", [])
                return CloudFlareServiceResponse(
                    status="error", errors=[f"CloudFlare API error: {errors}"]
                )

            return CloudFlareServiceResponse(status="success", resource=data["result"])

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return CloudFlareServiceResponse(
                    status="not_found",
                    errors=[f"Access application not found: {app_id}"],
                )
            return CloudFlareServiceResponse(
                status="error",
                errors=[f"HTTP error reading Access application: {str(e)}"],
            )
        except httpx.HTTPError as e:
            return CloudFlareServiceResponse(
                status="error",
                errors=[f"HTTP error reading Access application: {str(e)}"],
            )

    async def delete(
        self, client: httpx.AsyncClient, app_id: str, account_id: str
    ) -> CloudFlareServiceResponse:
        """Delete Access application.

        Args:
            client: Authenticated httpx client
            app_id: Access application ID
            account_id: CloudFlare account ID

        Returns:
            Deletion response
        """
        try:
            response = await client.delete(
                f"/accounts/{account_id}/access/apps/{app_id}"
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                errors = data.get("errors", [])
                return CloudFlareServiceResponse(
                    status="error", errors=[f"CloudFlare API error: {errors}"]
                )

            return CloudFlareServiceResponse(
                status="success", resource={"deleted_app_id": app_id}
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return CloudFlareServiceResponse(
                    status="not_found",
                    errors=[f"Access application not found: {app_id}"],
                )
            return CloudFlareServiceResponse(
                status="error",
                errors=[f"HTTP error deleting Access application: {str(e)}"],
            )
        except httpx.HTTPError as e:
            return CloudFlareServiceResponse(
                status="error", errors=[f"Delete operation failed: {str(e)}"]
            )

    async def list_applications(
        self, client: httpx.AsyncClient, account_id: str
    ) -> CloudFlareServiceResponse:
        """List all Access applications.

        Args:
            client: Authenticated httpx client
            account_id: CloudFlare account ID

        Returns:
            Response containing list of applications
        """
        try:
            response = await client.get(f"/accounts/{account_id}/access/apps")
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                errors = data.get("errors", [])
                return CloudFlareServiceResponse(
                    status="error", errors=[f"CloudFlare API error: {errors}"]
                )

            applications = data.get("result", [])
            return CloudFlareServiceResponse(
                status="success",
                resource={"applications": applications, "count": len(applications)},
            )

        except httpx.HTTPError as e:
            return CloudFlareServiceResponse(
                status="error", errors=[f"List operation failed: {str(e)}"]
            )


class DNSService(BaseCloudFlareService):
    """Service for managing CloudFlare DNS records."""

    async def create_or_update(
        self, _client: httpx.AsyncClient, _spec: Any
    ) -> CloudFlareServiceResponse:
        """Create or update DNS record."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["DNS service implementation pending"],
        )

    async def read(
        self, _client: httpx.AsyncClient, _record_id: str, _zone_id: str
    ) -> CloudFlareServiceResponse:
        """Read DNS record."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["DNS service implementation pending"],
        )

    async def delete(
        self, _client: httpx.AsyncClient, _record_id: str, _zone_id: str
    ) -> CloudFlareServiceResponse:
        """Delete DNS record."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["DNS service implementation pending"],
        )

    async def list_records(
        self, _client: httpx.AsyncClient, _zone_id: str
    ) -> CloudFlareServiceResponse:
        """List DNS records."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["DNS service implementation pending"],
        )


class ZoneService(BaseCloudFlareService):
    """Service for managing CloudFlare zones."""

    async def create_or_update(
        self, _client: httpx.AsyncClient, _spec: Any
    ) -> CloudFlareServiceResponse:
        """Create or update zone."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["Zone service implementation pending"],
        )

    async def read(
        self, _client: httpx.AsyncClient, _zone_id: str
    ) -> CloudFlareServiceResponse:
        """Read zone configuration."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["Zone service implementation pending"],
        )

    async def delete(
        self, _client: httpx.AsyncClient, _zone_id: str
    ) -> CloudFlareServiceResponse:
        """Delete zone."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["Zone service implementation pending"],
        )

    async def list_zones(self, _client: httpx.AsyncClient) -> CloudFlareServiceResponse:
        """List zones."""
        return CloudFlareServiceResponse(
            status="not_implemented",
            errors=["Zone service implementation pending"],
        )
