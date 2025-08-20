"""Common utilities for Home Assistant External Connector.

This module provides shared functionality including logging, validation,
and common helper functions used across all components.
"""

from __future__ import annotations

import logging
import re
from typing import Any, NoReturn

_LOGGER = logging.getLogger(__name__)

# Type alias for logger instances used throughout the integration
HAConnectorLogger = logging.Logger


def assert_never(value: NoReturn) -> NoReturn:
    """Assert that a code path is never reached.

    This is useful for exhaustive type checking with mypy.

    Args:
        value: Value that should never be reached

    Raises:
        AssertionError: Always, since this should never be called
    """
    raise AssertionError(f"Unhandled value: {value!r}")


def validate_string_length(
    value: str, min_length: int = 1, max_length: int = 255, field_name: str = "field"
) -> bool:
    """Validate string length constraints.

    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")

    return True


def validate_aws_arn(arn: str) -> bool:
    """Validate AWS ARN format.

    Args:
        arn: ARN string to validate

    Returns:
        True if valid ARN format

    Raises:
        ValueError: If ARN format is invalid
    """
    # Basic ARN pattern: arn:partition:service:region:account-id:resource
    arn_pattern = r"^arn:[^:]+:[^:]+:[^:]*:[^:]*:.+"

    if not re.match(arn_pattern, arn):
        raise ValueError(f"Invalid ARN format: {arn}")

    return True


def validate_domain_name(domain: str) -> bool:
    """Validate domain name format.

    Args:
        domain: Domain name to validate

    Returns:
        True if valid domain format

    Raises:
        ValueError: If domain format is invalid
    """
    # Basic domain validation
    domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"

    if not re.match(domain_pattern, domain):
        raise ValueError(f"Invalid domain format: {domain}")

    return True


def safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with dot notation support.

    Args:
        data: Dictionary to search
        key: Key to look for (supports dot notation like 'a.b.c')
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    if "." not in key:
        return data.get(key, default)

    # Handle dot notation
    keys = key.split(".")
    current = data

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default

    return current


def mask_sensitive_data(
    data: dict[str, Any], sensitive_keys: set[str]
) -> dict[str, Any]:
    """Mask sensitive data in a dictionary for logging.

    Args:
        data: Dictionary containing potential sensitive data
        sensitive_keys: Set of keys to mask

    Returns:
        Dictionary with sensitive values masked
    """
    masked = {}

    for key, value in data.items():
        if key.lower() in {k.lower() for k in sensitive_keys}:
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value, sensitive_keys)
        else:
            masked[key] = value

    return masked


def format_error_message(error: Exception, context: str | None = None) -> str:
    """Format error message with optional context.

    Args:
        error: Exception to format
        context: Optional context string

    Returns:
        Formatted error message
    """
    base_message = str(error)

    if context:
        return f"{context}: {base_message}"

    return base_message


def normalize_integration_name(name: str) -> str:
    """Normalize integration name to lowercase with underscores.

    Args:
        name: Integration name to normalize

    Returns:
        Normalized integration name
    """
    # Convert to lowercase and replace spaces/hyphens with underscores
    normalized = re.sub(r"[- ]+", "_", name.lower())
    # Remove any non-alphanumeric characters except underscores
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    # Remove duplicate underscores
    normalized = re.sub(r"_+", "_", normalized)
    # Strip leading/trailing underscores
    return normalized.strip("_")
