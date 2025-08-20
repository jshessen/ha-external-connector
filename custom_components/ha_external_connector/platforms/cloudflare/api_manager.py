"""
CloudFlare Manager Adapter - Pure JSON CRUD interface over CloudFlare resources.

Modern Python implementation for CloudFlare resource management
aligned with AWS adapter pattern.
"""

# pyright: reportUnknownVariableType=false
# https://github.com/microsoft/pyright/issues/698

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Self

import httpx
from pydantic import BaseModel, Field

from ...utils import HAConnectorError, HAConnectorLogger, ValidationError

# Global instance storage for backwards compatibility
_global_managers: dict[str, CloudFlareManager] = {}


def get_cloudflare_manager() -> CloudFlareManager:
    """Get or create global CloudFlare manager instance."""
    if "default" not in _global_managers:
        _global_managers["default"] = CloudFlareManager()
    return _global_managers["default"]


class CloudFlareResourceResponse(BaseModel):
    """Response model for CloudFlare resource operations."""

    status: str
    resource: dict[str, Any] | None = None
    errors: list[str] = []


def _extract_id(resource: dict[str, Any] | None) -> str | None:
    """Safely extract 'id' from a resource dict."""
    if resource is not None:
        id_val = resource.get("id")
        if isinstance(id_val, str):
            return id_val
    return None


class CloudFlareResourceType(str, Enum):
    """Enumeration of supported CloudFlare resource types."""

    ACCESS_APPLICATION = "access_application"
    DNS_RECORD = "dns_record"
    ZONE = "zone"


# --- Base Manager ---
class CloudFlareBaseManager:
    """Base class for CloudFlare resource managers."""

    def __init__(self) -> None:
        self.logger = HAConnectorLogger(self.__class__.__name__)


class CloudFlareConfig(BaseModel):
    """CloudFlare API configuration."""

    api_token: str | None = Field(
        None, description="CloudFlare API token (recommended)"
    )
    api_key: str | None = Field(None, description="CloudFlare global API key")
    email: str | None = Field(
        None, description="CloudFlare account email (required with API key)"
    )
    zone_id: str | None = Field(None, description="CloudFlare zone ID (optional)")
    debug: bool = Field(default=False, description="Enable debug logging")


class AccessApplicationSpec(BaseModel):
    """Specification model for CloudFlare Access applications."""

    name: str = Field(..., description="Application name")
    domain: str = Field(..., description="Domain for the application")
    subdomain: str | None = Field(
        None, description="Subdomain (if different from domain)"
    )
    session_duration: str = Field(default="24h", description="Session duration")
    auto_redirect_to_identity: bool = Field(
        default=True, description="Auto redirect to identity provider"
    )
    allowed_identity_providers: list[str] = Field(
        default_factory=list, description="Allowed identity providers"
    )
    cors_headers: dict[str, Any] | None = Field(
        None, description="CORS headers configuration"
    )
    service_auth_401_redirect: bool = Field(
        default=False, description="Service auth 401 redirect"
    )
    tags: list[str] | None = Field(None, description="Application tags")


class DNSRecordSpec(BaseModel):
    """Specification model for CloudFlare DNS records."""

    zone_id: str = Field(..., description="Zone ID")
    record_type: str = Field(..., description="DNS record type (A, CNAME, etc.)")
    name: str = Field(..., description="DNS record name")
    content: str = Field(..., description="DNS record content")
    ttl: int = Field(default=1, description="TTL (1 for auto)")
    proxied: bool = Field(default=True, description="Enable CloudFlare proxy")


# --- Access Application Manager ---
class CloudFlareAccessManager(CloudFlareBaseManager):
    """Manager for CloudFlare Access applications."""

    def __init__(self, client: httpx.Client) -> None:
        super().__init__()
        self.client = client

    def create_or_update(
        self, spec: AccessApplicationSpec, account_id: str
    ) -> CloudFlareResourceResponse:
        """Create or update Access application."""
        try:
            app_data: dict[str, Any] = {
                "name": spec.name,
                "domain": spec.domain,
                "session_duration": spec.session_duration,
                "auto_redirect_to_identity": spec.auto_redirect_to_identity,
                "service_auth_401_redirect": spec.service_auth_401_redirect,
            }

            if spec.subdomain:
                app_data["domain"] = f"{spec.subdomain}.{spec.domain}"

            if spec.allowed_identity_providers:
                app_data["allowed_identity_providers"] = spec.allowed_identity_providers

            if spec.cors_headers:
                app_data["cors_headers"] = spec.cors_headers

            if spec.tags:
                app_data["tags"] = spec.tags

            response = self.client.post(
                f"/accounts/{account_id}/access/apps", json=app_data
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                errors = data.get("errors", [])
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {errors}"]
                )

            return CloudFlareResourceResponse(status="success", resource=data["result"])

        except httpx.HTTPError as exc:
            self.logger.error("HTTP error creating Access application: %s", exc)
            return CloudFlareResourceResponse(
                status="error", errors=[f"HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            self.logger.error("Failed to create Access application: %s", exc)
            return CloudFlareResourceResponse(
                status="error", errors=[f"Creation failed: {str(exc)}"]
            )

    def read(self, app_id: str, account_id: str) -> CloudFlareResourceResponse:
        """Read Access application."""
        try:
            response = self.client.get(f"/accounts/{account_id}/access/apps/{app_id}")
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {data.get('errors', [])}"]
                )

            return CloudFlareResourceResponse(status="success", resource=data["result"])

        except httpx.HTTPError as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"Read HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"Read failed: {str(exc)}"]
            )

    def delete(self, app_id: str, account_id: str) -> CloudFlareResourceResponse:
        """Delete Access application."""
        try:
            response = self.client.delete(
                f"/accounts/{account_id}/access/apps/{app_id}"
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {data.get('errors', [])}"]
                )

            return CloudFlareResourceResponse(status="success", resource=None)

        except httpx.HTTPError as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"Delete HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"Delete failed: {str(exc)}"]
            )


# --- DNS Manager ---
class CloudFlareDNSManager(CloudFlareBaseManager):
    """Manager for CloudFlare DNS records."""

    def __init__(self, client: httpx.Client) -> None:
        super().__init__()
        self.client = client

    def create_or_update(self, spec: DNSRecordSpec) -> CloudFlareResourceResponse:
        """Create or update DNS record."""
        try:
            record_data: dict[str, Any] = {
                "type": spec.record_type,
                "name": spec.name,
                "content": spec.content,
                "ttl": spec.ttl,
                "proxied": spec.proxied,
            }

            response = self.client.post(
                f"/zones/{spec.zone_id}/dns_records", json=record_data
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {data.get('errors', [])}"]
                )

            return CloudFlareResourceResponse(status="success", resource=data["result"])

        except httpx.HTTPError as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS creation HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS creation failed: {str(exc)}"]
            )

    def read(self, zone_id: str, record_id: str) -> CloudFlareResourceResponse:
        """Read DNS record."""
        try:
            response = self.client.get(f"/zones/{zone_id}/dns_records/{record_id}")
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {data.get('errors', [])}"]
                )

            return CloudFlareResourceResponse(status="success", resource=data["result"])

        except httpx.HTTPError as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS read HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS read failed: {str(exc)}"]
            )

    def delete(self, zone_id: str, record_id: str) -> CloudFlareResourceResponse:
        """Delete DNS record."""
        try:
            response = self.client.delete(f"/zones/{zone_id}/dns_records/{record_id}")
            response.raise_for_status()

            data = response.json()
            if not data.get("success", False):
                return CloudFlareResourceResponse(
                    status="error", errors=[f"API error: {data.get('errors', [])}"]
                )

            return CloudFlareResourceResponse(status="success", resource=None)

        except httpx.HTTPError as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS delete HTTP error: {str(exc)}"]
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return CloudFlareResourceResponse(
                status="error", errors=[f"DNS delete failed: {str(exc)}"]
            )


# --- Main CloudFlare Manager ---
class CloudFlareManager:
    """
    Main CloudFlare resource manager providing CRUD operations.

    This class serves as the primary interface for managing CloudFlare resources
    including Access applications, DNS records, and zones.
    """

    def __init__(self, config: CloudFlareConfig | None = None) -> None:
        self.config: CloudFlareConfig = config or self._load_config_from_env()
        self.logger: HAConnectorLogger = HAConnectorLogger("cloudflare_manager")
        self._validate_credentials()
        self._client: httpx.Client = self._create_http_client()

        # Initialize resource managers
        self.access_manager: CloudFlareAccessManager = CloudFlareAccessManager(
            self._client
        )
        self.dns_manager: CloudFlareDNSManager = CloudFlareDNSManager(self._client)

    def _load_config_from_env(self) -> CloudFlareConfig:
        """Load CloudFlare configuration from environment variables."""
        return CloudFlareConfig(
            api_token=os.getenv("CF_API_TOKEN"),
            api_key=os.getenv("CF_API_KEY"),
            email=os.getenv("CF_EMAIL"),
            zone_id=os.getenv("CF_ZONE_ID"),
            debug=os.getenv("CF_DEBUG", "false").lower() == "true",
        )

    def _validate_credentials(self) -> None:
        """Validate CloudFlare credentials."""
        if not self.config.api_token and (
            not self.config.api_key or not self.config.email
        ):
            raise HAConnectorError(
                "CloudFlare credentials not found. Set either:\n"
                "  CF_API_TOKEN=your_api_token (recommended)\n"
                "Or:\n"
                "  CF_API_KEY=your_global_api_key\n"
                "  CF_EMAIL=your_email"
            )

    def _create_http_client(self) -> httpx.Client:
        """Create HTTP client with CloudFlare authentication."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        elif self.config.api_key and self.config.email:
            headers["X-Auth-Key"] = self.config.api_key
            headers["X-Auth-Email"] = self.config.email

        return httpx.Client(
            base_url="https://api.cloudflare.com/v4",
            headers=headers,
            timeout=30.0,
        )

    def create_resource(
        self,
        resource_type: CloudFlareResourceType,
        resource_spec: dict[str, Any],
        **kwargs: Any,
    ) -> CloudFlareResourceResponse:
        """Create a resource based on type and specification."""
        try:
            if resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                access_spec = AccessApplicationSpec(**resource_spec)
                account_id = kwargs.get("account_id") or self.get_account_id()
                return self.access_manager.create_or_update(access_spec, account_id)
            if resource_type == CloudFlareResourceType.DNS_RECORD:
                dns_spec = DNSRecordSpec(**resource_spec)
                return self.dns_manager.create_or_update(dns_spec)
            return CloudFlareResourceResponse(
                status="error",
                errors=[f"Unknown resource type: {resource_type}"],
            )
        except ValidationError as exc:
            return CloudFlareResourceResponse(
                status="error",
                errors=[f"Invalid resource specification: {str(exc)}"],
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            self.logger.error("Resource creation failed for %s: %s", resource_type, exc)
            return CloudFlareResourceResponse(
                status="error", errors=[f"Resource creation failed: {str(exc)}"]
            )

    def read_resource(
        self,
        resource_type: CloudFlareResourceType,
        resource_id: str,
        **kwargs: Any,
    ) -> CloudFlareResourceResponse:
        """Read a resource's current state."""
        try:
            if resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                account_id = kwargs.get("account_id") or self.get_account_id()
                return self.access_manager.read(resource_id, account_id)
            if resource_type == CloudFlareResourceType.DNS_RECORD:
                zone_id = kwargs.get("zone_id")
                if not zone_id:
                    return CloudFlareResourceResponse(
                        status="error", errors=["zone_id required for DNS records"]
                    )
                return self.dns_manager.read(zone_id, resource_id)
            return CloudFlareResourceResponse(
                status="error",
                errors=[f"Unknown resource type: {resource_type}"],
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            self.logger.error("Resource read failed for %s: %s", resource_type, exc)
            return CloudFlareResourceResponse(
                status="error", errors=[f"Resource read failed: {str(exc)}"]
            )

    def update_resource(
        self,
        resource_type: CloudFlareResourceType,
        _resource_id: str,  # unused
        resource_spec: dict[str, Any],
        **kwargs: Any,
    ) -> CloudFlareResourceResponse:
        """Update a resource."""
        # For most resources, update is the same as create_or_update
        return self.create_resource(resource_type, resource_spec, **kwargs)

    def delete_resource(
        self,
        resource_type: CloudFlareResourceType,
        resource_id: str,
        **kwargs: Any,
    ) -> CloudFlareResourceResponse:
        """Delete a resource."""
        try:
            if resource_type == CloudFlareResourceType.ACCESS_APPLICATION:
                account_id = kwargs.get("account_id") or self.get_account_id()
                return self.access_manager.delete(resource_id, account_id)
            if resource_type == CloudFlareResourceType.DNS_RECORD:
                zone_id = kwargs.get("zone_id")
                if not zone_id:
                    return CloudFlareResourceResponse(
                        status="error", errors=["zone_id required for DNS records"]
                    )
                return self.dns_manager.delete(zone_id, resource_id)
            return CloudFlareResourceResponse(
                status="error",
                errors=[f"Unknown resource type: {resource_type}"],
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            self.logger.error("Resource deletion failed for %s: %s", resource_type, exc)
            return CloudFlareResourceResponse(
                status="error", errors=[f"Resource deletion failed: {str(exc)}"]
            )

    def get_zone_id(self, domain: str) -> str:
        """Get zone ID for a domain."""
        if self.config.zone_id:
            return self.config.zone_id

        # Extract root domain (e.g., example.com from ha.example.com)
        domain_parts = domain.split(".")
        root_domain = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else domain

        response = self._client.get("/zones", params={"name": root_domain})
        response.raise_for_status()

        data = response.json()
        if not data.get("success", False):
            raise ValidationError(f"CloudFlare API error: {data.get('errors', [])}")

        zones = data.get("result", [])
        if not zones:
            raise ValidationError(f"No zone found for domain: {root_domain}")

        zone_id = zones[0]["id"]
        if not isinstance(zone_id, str):
            raise ValidationError(f"Invalid zone ID type: {type(zone_id)}")
        return zone_id

    def get_account_id(self) -> str:
        """Get CloudFlare account ID."""
        response = self._client.get("/accounts")
        response.raise_for_status()

        data = response.json()
        if not data.get("success", False):
            raise ValidationError(f"Failed to get account ID: {data.get('errors', [])}")

        accounts = data.get("result", [])
        if not accounts:
            raise ValidationError("No CloudFlare accounts found")

        account_id = accounts[0]["id"]
        if not isinstance(account_id, str):
            raise ValidationError(f"Invalid account ID type: {type(account_id)}")
        return account_id

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if hasattr(self, "_client"):
            self._client.close()


# Legacy compatibility functions
class AccessApplicationConfig(AccessApplicationSpec):
    """Legacy alias for AccessApplicationSpec."""


def create_access_application(
    domain: str,
    application_name: str = "Home Assistant",
    lambda_url: str | None = None,
) -> dict[str, Any]:
    """Convenience function to create CloudFlare Access application."""
    with CloudFlareManager() as cf_manager:
        if lambda_url:
            # Legacy behavior - create both app and DNS
            app_spec = AccessApplicationSpec(
                name=application_name,
                domain=domain,
                subdomain=None,
                session_duration="24h",
                auto_redirect_to_identity=True,
                allowed_identity_providers=[],
                cors_headers=None,
                service_auth_401_redirect=False,
                tags=None,
            )
            app_result = cf_manager.create_resource(
                CloudFlareResourceType.ACCESS_APPLICATION, app_spec.model_dump()
            )

            if app_result.status != "success":
                raise HAConnectorError(f"Failed to create app: {app_result.errors}")

            # Create DNS record
            zone_id = cf_manager.get_zone_id(domain)
            lambda_hostname = (
                lambda_url.replace("https://", "").replace("http://", "").split("/")[0]
            )

            dns_spec = DNSRecordSpec(
                zone_id=zone_id,
                record_type="CNAME",
                name=domain,
                content=lambda_hostname,
                ttl=1,
                proxied=True,
            )

            dns_result = cf_manager.create_resource(
                CloudFlareResourceType.DNS_RECORD, dns_spec.model_dump()
            )

            if dns_result.status != "success":
                # Clean up application
                app_id = _extract_id(app_result.resource)
                if app_id is None:
                    cf_manager.logger.warning(
                        "Could not extract 'id' from app_result.resource: %s",
                        app_result.resource,
                    )
                else:
                    cf_manager.delete_resource(
                        CloudFlareResourceType.ACCESS_APPLICATION,
                        app_id,
                    )
                raise HAConnectorError(f"Failed to create DNS: {dns_result.errors}")

            return {
                "application": app_result.resource,
                "dns_record": dns_result.resource,
                "access_url": f"https://{domain}",
            }

        app_spec = AccessApplicationSpec(
            name=application_name,
            domain=domain,
            subdomain=None,
            session_duration="24h",
            auto_redirect_to_identity=True,
            allowed_identity_providers=[],
            cors_headers=None,
            service_auth_401_redirect=False,
            tags=None,
        )
        result = cf_manager.create_resource(
            CloudFlareResourceType.ACCESS_APPLICATION, app_spec.model_dump()
        )

        if result.status != "success":
            raise HAConnectorError(f"Failed to create app: {result.errors}")

        if result.resource is None:
            raise HAConnectorError("CloudFlare API did not return a resource object.")
        return result.resource
