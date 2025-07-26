"""
Dynamic Test Secret Generation

This module provides secure generation of test secrets that avoid hardcoded values
while maintaining appropriate lengths and formats for different use cases.
"""

import secrets
import string
from typing import Literal, TypedDict


class SecretConfig(TypedDict):
    """Configuration for test secret generation."""

    prefix: str
    min_len: int


def generate_test_secret(
    secret_type: Literal[
        "alexa", "client", "token", "generic"
    ] = "generic",  # nosec B107
    min_length: int = 8,
    custom_length: int | None = None,
) -> str:
    """
    Generate a test secret dynamically to avoid hardcoded values.

    Args:
        secret_type: Type of secret to generate (affects prefix and length)
        min_length: Minimum length for the secret
        custom_length: Override with specific length

    Returns:
        Dynamically generated test secret
    """
    # Define type-specific configurations
    configs: dict[str, SecretConfig] = {
        "alexa": {"prefix": "test-alexa-", "min_len": 32},
        "client": {"prefix": "test-client-", "min_len": 16},
        "token": {"prefix": "test-token-", "min_len": 20},
        "generic": {"prefix": "test-", "min_len": min_length},
    }

    config = configs[secret_type]
    target_length = (
        custom_length
        if custom_length is not None
        else max(config["min_len"], min_length)
    )
    prefix = config["prefix"]

    # Calculate remaining length after prefix
    remaining_length = max(target_length - len(prefix), 4)  # Minimum random part

    # Generate cryptographically secure random string
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(remaining_length))

    return f"{prefix}{random_part}"


def generate_test_short_secret() -> str:
    """Generate a short test secret for validation testing."""
    return generate_test_secret("generic", min_length=5, custom_length=5)


def generate_test_env_token() -> str:
    """Generate an environment-style test token."""
    return generate_test_secret("token", custom_length=32)


# Commonly used test secret generators
def alexa_test_secret() -> str:
    """Generate a test Alexa secret (32+ chars)."""
    return generate_test_secret("alexa")


def client_test_secret() -> str:
    """Generate a test client secret."""
    return generate_test_secret("client")


def api_test_token() -> str:
    """Generate a test API token."""
    return generate_test_secret("token")


# For backward compatibility and specific test cases
TEST_DOMAIN = "test.homeassistant.local"
TEST_URL_BASE = f"https://{TEST_DOMAIN}:8123"
TEST_REGION = "us-east-1"
