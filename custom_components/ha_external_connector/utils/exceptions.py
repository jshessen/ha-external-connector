"""Custom exception definitions for Home Assistant External Connector.

This module provides a hierarchy of custom exceptions used throughout
the integration for better error handling and debugging.
"""

from homeassistant.exceptions import HomeAssistantError


class ExternalConnectorError(HomeAssistantError):
    """Base exception for External Connector integration."""


# Alias for backwards compatibility
HAConnectorError = ExternalConnectorError


class PlatformError(ExternalConnectorError):
    """Exception raised by platform operations."""


class ServiceError(ExternalConnectorError):
    """Exception raised by service operations."""


class ConfigurationError(ExternalConnectorError):
    """Exception raised by configuration issues."""


class ValidationError(ExternalConnectorError):
    """Exception raised by validation failures."""


class AWSError(PlatformError):
    """Exception raised by AWS platform operations."""


class CloudFlareError(PlatformError):
    """Exception raised by CloudFlare platform operations."""


class AlexaError(ServiceError):
    """Exception raised by Alexa integration operations."""


class AuthenticationError(ExternalConnectorError):
    """Exception raised by authentication failures."""


class ResourceNotFoundError(ExternalConnectorError):
    """Exception raised when a resource is not found."""


class ResourceConflictError(ExternalConnectorError):
    """Exception raised when a resource conflict occurs."""
