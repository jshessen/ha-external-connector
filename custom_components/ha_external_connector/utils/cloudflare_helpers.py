"""CloudFlare-specific helper utilities.

This module provides common CloudFlare utilities and patterns used across
CloudFlare platform services and integrations.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from .common import mask_sensitive_data
from .exceptions import CloudFlareError

_LOGGER = logging.getLogger(__name__)

# CloudFlare API base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

# Common CloudFlare error codes
CF_AUTHENTICATION_ERROR = 10000
CF_AUTHORIZATION_ERROR = 10001
CF_FORBIDDEN = 10003
CF_NOT_FOUND = 10007
CF_RATE_LIMITED = 10013
CF_INTERNAL_ERROR = 10014


def handle_cloudflare_error(response: httpx.Response, context: str = "") -> None:
    """Handle CloudFlare API error responses.

    Args:
        response: The HTTP response from CloudFlare API
        context: Optional context for the error

    Raises:
        CloudFlareError: Converted CloudFlare error with appropriate message
    """
    try:
        error_data = response.json()
    except ValueError:
        error_data = {"errors": [{"message": response.text}]}

    errors = error_data.get("errors", [])
    if not errors:
        errors = [{"message": f"HTTP {response.status_code}"}]

    error_messages: list[str] = []
    for error in errors:
        code = error.get("code", "unknown")
        message = error.get("message", "Unknown error")
        error_messages.append(f"[{code}] {message}")

    full_message = "; ".join(error_messages)
    if context:
        full_message = f"{context}: {full_message}"

    _LOGGER.error("CloudFlare Error: %s", full_message)

    # Handle specific error codes
    first_error_code = errors[0].get("code") if errors else None

    if first_error_code in [CF_AUTHENTICATION_ERROR, CF_AUTHORIZATION_ERROR]:
        raise CloudFlareError(f"Authentication failed: {full_message}")
    if first_error_code == CF_FORBIDDEN:
        raise CloudFlareError(f"Access forbidden: {full_message}")
    if first_error_code == CF_NOT_FOUND:
        raise CloudFlareError(f"Resource not found: {full_message}")
    if first_error_code == CF_RATE_LIMITED:
        raise CloudFlareError(f"Rate limit exceeded: {full_message}")
    if first_error_code == CF_INTERNAL_ERROR:
        raise CloudFlareError(f"CloudFlare internal error: {full_message}")
    raise CloudFlareError(f"CloudFlare API error: {full_message}")


def validate_cloudflare_zone_id(zone_id: str) -> bool:
    """Validate CloudFlare zone ID format.

    Args:
        zone_id: Zone ID to validate

    Returns:
        True if valid format

    Raises:
        ValueError: If zone ID format is invalid
    """
    if not zone_id:
        raise ValueError("Zone ID cannot be empty")

    # CloudFlare zone IDs are 32-character hex strings
    if len(zone_id) != 32:
        raise ValueError(f"Invalid zone ID length: {len(zone_id)} (expected 32)")

    if not all(c in "0123456789abcdef" for c in zone_id.lower()):
        raise ValueError("Zone ID must contain only hexadecimal characters")

    return True


def validate_cloudflare_account_id(account_id: str) -> bool:
    """Validate CloudFlare account ID format.

    Args:
        account_id: Account ID to validate

    Returns:
        True if valid format

    Raises:
        ValueError: If account ID format is invalid
    """
    if not account_id:
        raise ValueError("Account ID cannot be empty")

    # CloudFlare account IDs are 32-character hex strings
    if len(account_id) != 32:
        raise ValueError(f"Invalid account ID length: {len(account_id)} (expected 32)")

    if not all(c in "0123456789abcdef" for c in account_id.lower()):
        raise ValueError("Account ID must contain only hexadecimal characters")

    return True


def build_cloudflare_url(endpoint: str, **params: str) -> str:
    """Build CloudFlare API URL with parameters.

    Args:
        endpoint: API endpoint path
        **params: URL parameters to include

    Returns:
        Complete CloudFlare API URL
    """
    url = f"{CLOUDFLARE_API_BASE}/{endpoint.lstrip('/')}"

    if params:
        param_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{param_string}"

    return url


def create_cloudflare_headers(api_token: str) -> dict[str, str]:
    """Create headers for CloudFlare API requests.

    Args:
        api_token: CloudFlare API token

    Returns:
        Dictionary of HTTP headers
    """
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "User-Agent": "HomeAssistant-ExternalConnector/1.0",
    }


def sanitize_dns_name(name: str) -> str:
    """Sanitize a name for DNS record usage.

    Args:
        name: Name to sanitize

    Returns:
        Sanitized name suitable for DNS records.
    """
    # Convert to lowercase
    sanitized = name.lower()
    # Replace invalid characters with hyphens
    sanitized = re.sub(r"[^a-z0-9-._]", "-", sanitized)
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)
    # Strip leading/trailing hyphens and dots
    sanitized = sanitized.strip("-.")
    return sanitized or "unnamed-record"


def mask_cloudflare_credentials(data: dict[str, Any]) -> dict[str, Any]:
    """Mask CloudFlare credentials in data for logging.

    Args:
        data: Dictionary potentially containing CloudFlare credentials

    Returns:
        Dictionary with credentials masked
    """
    cf_sensitive_keys = {
        "api_token",
        "api_key",
        "email",
        "global_api_key",
        "origin_ca_key",
        "token",
        "key",
        "secret",
        "password",
    }

    return mask_sensitive_data(data, cf_sensitive_keys)


def extract_cloudflare_result(response_data: dict[str, Any]) -> Any:
    """Extract result data from CloudFlare API response.

    Args:
        response_data: CloudFlare API response data

    Returns:
        The result data or None if not found
    """
    if not isinstance(response_data, dict):
        return None

    if not response_data.get("success", False):
        return None

    return response_data.get("result")


def is_cloudflare_success(response_data: dict[str, Any]) -> bool:
    """Check if CloudFlare API response indicates success.

    Args:
        response_data: CloudFlare API response data

    Returns:
        True if the response indicates success
    """
    if not isinstance(response_data, dict):
        return False

    return response_data.get("success", False) is True
