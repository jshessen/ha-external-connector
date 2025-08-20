"""Utilities package for Home Assistant External Connector.

This package provides centralized utilities, protocols, and common functionality
used across all integrations and platforms in the custom component.
"""

from .common import (
    HAConnectorLogger,
    assert_never,
    format_error_message,
    mask_sensitive_data,
    normalize_integration_name,
    safe_get,
    validate_aws_arn,
    validate_domain_name,
    validate_string_length,
)
from .exceptions import (
    AlexaError,
    AuthenticationError,
    AWSError,
    CloudFlareError,
    ConfigurationError,
    ExternalConnectorError,
    HAConnectorError,
    PlatformError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceError,
    ValidationError,
)
from .protocols import (
    ConfigFlowProtocol,
    PlatformProtocol,
    ServiceDataProtocol,
    ServiceRegistryProtocol,
)

__all__ = [
    # Common utilities
    "HAConnectorLogger",
    "assert_never",
    "format_error_message",
    "mask_sensitive_data",
    "normalize_integration_name",
    "safe_get",
    "validate_aws_arn",
    "validate_domain_name",
    "validate_string_length",
    # Exception classes
    "AlexaError",
    "AuthenticationError",
    "AWSError",
    "CloudFlareError",
    "ConfigurationError",
    "ExternalConnectorError",
    "HAConnectorError",
    "PlatformError",
    "ResourceConflictError",
    "ResourceNotFoundError",
    "ServiceError",
    "ValidationError",
    # Protocol definitions
    "ConfigFlowProtocol",
    "PlatformProtocol",
    "ServiceDataProtocol",
    "ServiceRegistryProtocol",
]
