"""CloudFlare validation helper functions for configuration manager."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Import CloudFlare components at module level to avoid import-outside-toplevel warnings
CLOUDFLARE_RESOURCE_TYPE: Any = None

# Module-level flag for CloudFlare platform availability
_CLOUDFLARE_AVAILABLE = False

try:
    from .client import CloudFlarePlatform

    _CLOUDFLARE_AVAILABLE = True
    # This would need to be imported from models if needed
    CLOUDFLARE_RESOURCE_TYPE = None
except ImportError:
    _CLOUDFLARE_AVAILABLE = False
    CLOUDFLARE_RESOURCE_TYPE = None


def _is_cloudflare_available() -> bool:
    """Check if CloudFlare manager is available."""
    return _CLOUDFLARE_AVAILABLE


def _get_cloudflare_platform_instance():
    """Get a CloudFlare platform instance.

    Returns:
        CloudFlare platform instance

    Raises:
        ImportError: If CloudFlare platform is not available
    """
    if not _CLOUDFLARE_AVAILABLE:
        raise ImportError("CloudFlare adapter not available")

    return CloudFlarePlatform()


def validate_cloudflare_setup(domain: str) -> None:
    """Validate CloudFlare setup for a given domain.

    Args:
        domain: Domain to validate CloudFlare setup for

    Raises:
        ValueError: If validation fails
    """
    logger.debug("Validating CloudFlare setup for domain: %s", domain)

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

        # Get CloudFlare platform instance
        cf_manager = _get_cloudflare_platform_instance()
        try:
            # Test 1: Verify API credentials work by getting account info
            account_id = _validate_cloudflare_credentials(cf_manager)

            # Test 2: Verify domain zone exists and is accessible
            _validate_cloudflare_domain_zone(cf_manager, domain)

            # Test 3: Check if Access applications exist for this domain
            _check_cloudflare_access_applications(cf_manager, domain, account_id)
        finally:
            # Clean up if needed (CloudFlarePlatform doesn't need explicit cleanup)
            pass

        logger.info("✅ CloudFlare API validation completed for %s", domain)

    except (ImportError, AttributeError, TypeError) as e:
        logger.warning("CloudFlare API validation failed: %s", str(e))
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
            "✅ CloudFlare API credentials valid (Account: %s...)", account_id[:8]
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
        logger.debug("✅ Domain zone found (Zone: %s...)", zone_id[:8])
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
            CLOUDFLARE_RESOURCE_TYPE.ACCESS_APPLICATION,
            resource_id="",  # Empty to list all
            account_id=account_id,
        )

        if response.status == "success" and response.resource:
            apps = response.resource.get("result", [])
            domain_apps = [app for app in apps if domain in str(app.get("domain", ""))]

            if domain_apps:
                logger.debug(
                    "✅ Found %d Access application(s) for domain", len(domain_apps)
                )
            else:
                logger.info("ℹ️  No existing Access applications found for %s", domain)
        else:
            logger.debug("⚠️  Could not verify Access applications (may be normal)")

    except (ValueError, ConnectionError, OSError) as e:
        # Access application check is optional - don't fail validation
        logger.debug("Access application check failed (non-critical): %s", str(e))
