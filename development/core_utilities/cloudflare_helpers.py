"""CloudFlare validation helper functions for configuration manager."""

from __future__ import annotations

import os
from typing import Any

from ..utils import logger

# Import CloudFlare components at module level to avoid import-outside-toplevel warnings
# Initialize as None, will be set if import succeeds
CloudFlareManager: Any = None
CloudFlareResourceType: Any = None

# Check CloudFlare availability once at module load
try:
    from ..platforms.cloudflare.api_manager import (
        CloudFlareManager,
        CloudFlareResourceType,
    )
except ImportError:
    # CloudFlare adapter not available - will be handled gracefully
    CloudFlareManager = None  # pyright: ignore
    CloudFlareResourceType = None  # pyright: ignore


def _is_cloudflare_available() -> bool:
    """Check if CloudFlare manager is available."""
    return CloudFlareManager is not None


def validate_cloudflare_domain_setup(domain: str) -> None:
    """Validate CloudFlare domain setup.

    Args:
        domain: Domain to validate CloudFlare setup for

    Raises:
        ValueError: If validation fails
    """
    logger.debug(f"Validating CloudFlare setup for domain: {domain}")

    # Basic domain format validation
    if not domain or "." not in domain:
        raise ValueError(f"Invalid domain format: {domain}")

    # Check if we have API access for validation
    cf_api_token = os.getenv("CF_API_TOKEN")
    cf_api_key = os.getenv("CF_API_KEY")

    if not cf_api_token and not cf_api_key:
        logger.info("No CloudFlare API credentials - skipping deep validation")
        return

    # Implement CloudFlare API validation using the adapter
    if not _is_cloudflare_available():
        logger.warning("CloudFlare adapter not available - skipping API validation")
        return

    _perform_cloudflare_api_validation(domain)


def _perform_cloudflare_api_validation(domain: str) -> None:
    """Perform CloudFlare API validation using the adapter.

    Args:
        domain: Domain to validate

    Raises:
        ValueError: If API validation fails
    """
    try:
        logger.debug("Performing CloudFlare API validation...")

        if not _is_cloudflare_available():
            raise ImportError("CloudFlare adapter not available")

        with CloudFlareManager() as cf_manager:
            # Test 1: Verify API credentials work by getting account info
            account_id = _validate_cloudflare_credentials(cf_manager)

            # Test 2: Verify domain zone exists and is accessible
            _validate_cloudflare_domain_zone(cf_manager, domain)

            # Test 3: Check if Access applications exist for this domain
            _check_cloudflare_access_applications(cf_manager, domain, account_id)

        logger.info(f"✅ CloudFlare API validation completed for {domain}")

    except (ImportError, AttributeError, TypeError) as e:
        logger.warning(f"CloudFlare API validation failed: {str(e)}")
        logger.info("This may indicate missing permissions or network issues")


def _validate_cloudflare_credentials(cf_manager: Any) -> str:
    """Validate CloudFlare API credentials.

    Args:
        cf_manager: CloudFlare manager instance

    Returns:
        Account ID if validation successful

    Raises:
        ValueError: If credentials are invalid
    """
    try:
        account_id: str = cf_manager.get_account_id()
        logger.debug(
            f"✅ CloudFlare API credentials valid (Account: {account_id[:8]}...)"
        )
        return account_id
    except (ValueError, ConnectionError, OSError) as e:
        raise ValueError(f"CloudFlare API credentials invalid: {e}") from e


def _validate_cloudflare_domain_zone(cf_manager: Any, domain: str) -> None:
    """Validate that domain zone exists in CloudFlare.

    Args:
        cf_manager: CloudFlare manager instance
        domain: Domain to validate

    Raises:
        ValueError: If domain zone not found
    """
    try:
        zone_id: str = cf_manager.get_zone_id(domain)
        logger.debug(f"✅ Domain zone found (Zone: {zone_id[:8]}...)")
    except (ValueError, ConnectionError, OSError) as e:
        raise ValueError(f"Domain '{domain}' not found in CloudFlare zones: {e}") from e


def _check_cloudflare_access_applications(
    cf_manager: Any, domain: str, account_id: str
) -> None:
    """Check for existing CloudFlare Access applications.

    Args:
        cf_manager: CloudFlare manager instance
        domain: Domain to check
        account_id: CloudFlare account ID
    """
    if not _is_cloudflare_available():
        return

    try:
        response = cf_manager.read_resource(
            CloudFlareResourceType.ACCESS_APPLICATION,
            resource_id="",  # Empty to list all
            account_id=account_id,
        )

        if response.status == "success" and response.resource:
            apps = response.resource.get("result", [])
            domain_apps = [app for app in apps if domain in str(app.get("domain", ""))]

            if domain_apps:
                logger.debug(
                    f"✅ Found {len(domain_apps)} Access application(s) for domain"
                )
            else:
                logger.info(f"ℹ️  No existing Access applications found for {domain}")
        else:
            logger.debug("⚠️  Could not verify Access applications (may be normal)")

    except (ValueError, ConnectionError, OSError) as e:
        # Access application check is optional - don't fail validation
        logger.debug(f"Access application check failed (non-critical): {str(e)}")
