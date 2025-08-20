"""CloudFlare resource models and specifications.

This module defines Pydantic models for CloudFlare resource specifications.
These models provide type-safe configuration for CloudFlare resource creation
and management operations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CloudFlareResourceType(str, Enum):
    """Enumeration of supported CloudFlare resource types."""

    ACCESS_APPLICATION = "access_application"
    DNS_RECORD = "dns_record"
    ZONE = "zone"


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
    comment: str | None = Field(None, description="Record comment")


class ZoneSpec(BaseModel):
    """Specification model for CloudFlare zones."""

    name: str = Field(..., description="Zone name (domain)")
    jump_start: bool = Field(default=True, description="Enable jump start")
    zone_type: str = Field(default="full", description="Zone type")
    account_id: str | None = Field(None, description="Account ID")
    plan_id: str | None = Field(None, description="Plan ID")
