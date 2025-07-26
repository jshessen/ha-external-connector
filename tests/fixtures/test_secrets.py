"""
Test Secret Generators

Provides secure random generators for test secrets to avoid hardcoded values
that trigger Bandit B105/B106 warnings while maintaining test reproducibility.
"""

import secrets
import string
from typing import Any


def generate_test_secret(prefix: str = "test", length: int = 32) -> str:
    """Generate a random test secret with a clear test prefix.

    Args:
        prefix: Prefix to clearly mark as test data (default: "test")
        length: Total length of the secret (default: 32)

    Returns:
        A random string clearly marked as test data
    """
    if length <= len(prefix) + 1:
        raise ValueError(
            f"Length must be greater than prefix length + 1 ({len(prefix) + 1})"
        )

    # Generate random suffix
    suffix_length = length - len(prefix) - 1  # -1 for the dash
    alphabet = string.ascii_letters + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(suffix_length))

    return f"{prefix}-{suffix}"


def generate_alexa_secret() -> str:
    """Generate a test Alexa secret (32+ chars as required by validation)."""
    return generate_test_secret("test-alexa-secret", 35)


def generate_cf_client_secret() -> str:
    """Generate a test CloudFlare client secret."""
    return generate_test_secret("test-cf-client", 24)


def generate_api_token() -> str:
    """Generate a test API token."""
    return generate_test_secret("test-token", 20)


def generate_short_secret() -> str:
    """Generate an intentionally short secret for validation testing."""
    return "short"  # This is intentionally hardcoded for validation tests


# Pre-generated deterministic secrets for tests that need consistency
# These are still clearly test data but deterministic for assertion purposes
DETERMINISTIC_TEST_SECRETS: dict[str, Any] = {
    "alexa_secret": "test-alexa-deterministic-secret-for-assertions-32chars",
    "cf_client_secret": "test-cf-deterministic-secret",
    "api_token": "test-deterministic-token",
    "original_secret": "test-original-deterministic",
    "modified_secret": "test-modified-deterministic",
    "short_secret": "short",
}


def get_deterministic_secret(key: str) -> str:
    """Get a deterministic test secret for tests that need consistent values.

    Args:
        key: The key for the secret type

    Returns:
        A deterministic test secret value

    Raises:
        KeyError: If the key is not found
    """
    if key not in DETERMINISTIC_TEST_SECRETS:
        raise KeyError(
            f"Unknown deterministic secret key: {key}. "
            f"Available: {list(DETERMINISTIC_TEST_SECRETS.keys())}"
        )

    return str(DETERMINISTIC_TEST_SECRETS[key])
