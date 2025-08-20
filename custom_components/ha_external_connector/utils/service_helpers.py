"""Service utilities for Home Assistant External Connector.

This module provides common utilities and patterns for service registration
and management across all integrations.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any, cast

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .exceptions import ServiceError
from .protocols import ServiceDataProtocol, ServiceRegistryProtocol

_LOGGER = logging.getLogger(__name__)


def get_service_registry(hass: HomeAssistant) -> ServiceRegistryProtocol:
    """Get the Home Assistant service registry with type safety.

    Args:
        hass: Home Assistant instance

    Returns:
        Service registry protocol

    Raises:
        ServiceError: If service registry is not available
    """
    services_obj = getattr(hass, "services", None)
    if services_obj is None:
        raise ServiceError("Services registry not available")

    return cast(ServiceRegistryProtocol, services_obj)


def get_service_data(call: ServiceCall) -> ServiceDataProtocol:
    """Get service call data with type safety.

    Args:
        call: Service call object

    Returns:
        Service data protocol
    """
    call_data = getattr(call, "data", {})
    return cast(ServiceDataProtocol, call_data)


def safe_register_service(
    hass: HomeAssistant,
    domain: str,
    service: str,
    handler: Callable[[ServiceCall], Any],
) -> bool:
    """Safely register a service with error handling.

    Args:
        hass: Home Assistant instance
        domain: Domain to register service under
        service: Service name
        handler: Service handler function

    Returns:
        True if registration successful

    Raises:
        ServiceError: If registration fails
    """
    try:
        services = get_service_registry(hass)
        services.async_register(domain, service, handler)
        _LOGGER.debug("Registered service: %s.%s", domain, service)
        return True
    except HomeAssistantError as err:
        raise ServiceError(f"Failed to register service {domain}.{service}") from err


def safe_unregister_service(hass: HomeAssistant, domain: str, service: str) -> bool:
    """Safely unregister a service with error handling.

    Args:
        hass: Home Assistant instance
        domain: Domain of the service
        service: Service name

    Returns:
        True if unregistration successful
    """
    try:
        services = get_service_registry(hass)
        services.async_remove(domain, service)
        _LOGGER.debug("Unregistered service: %s.%s", domain, service)
        return True
    except HomeAssistantError as err:
        _LOGGER.warning("Failed to unregister service %s.%s: %s", domain, service, err)
        return False


def extract_service_param(
    call: ServiceCall, param_name: str, required: bool = True, default: Any = None
) -> Any:
    """Extract parameter from service call data safely.

    Args:
        call: Service call object
        param_name: Name of parameter to extract
        required: Whether parameter is required
        default: Default value if parameter not found

    Returns:
        Parameter value

    Raises:
        ServiceError: If required parameter is missing
    """
    data = get_service_data(call)
    value = data.get(param_name, default)

    if required and value is None:
        raise ServiceError(f"Required parameter '{param_name}' not provided")

    return value


def validate_service_permissions(
    call: ServiceCall, required_permissions: list[str]
) -> None:
    """Validate that service call has required permissions.

    Args:
        call: Service call object
        required_permissions: List of required permissions

    Raises:
        ServiceError: If permissions are insufficient
    """
    # TODO: Implement permission checking based on Home Assistant's auth system
    # For now, this is a placeholder for future implementation
    _LOGGER.debug(
        "Permission validation requested for %s (permissions: %s)",
        call,
        required_permissions,
    )


def create_service_response(
    status: str = "success",
    message: str = "",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standardized service response.

    Args:
        status: Response status (success, error, warning)
        message: Response message
        data: Optional response data

    Returns:
        Standardized service response dictionary
    """
    response: dict[str, Any] = {
        "status": status,
        "message": message,
    }

    if data is not None:
        response["data"] = data

    return response


def handle_service_error(
    error: Exception, service_name: str, context: str = ""
) -> dict[str, Any]:
    """Handle service errors with standardized response.

    Args:
        error: Exception that occurred
        service_name: Name of the service
        context: Optional context for the error

    Returns:
        Error response dictionary
    """
    error_message = str(error)
    if context:
        error_message = f"{context}: {error_message}"

    _LOGGER.error("Service error in %s: %s", service_name, error_message)

    return create_service_response(
        status="error",
        message=error_message,
        data={"service": service_name, "error_type": type(error).__name__},
    )


def mask_sensitive_data(
    data: dict[str, Any], sensitive_keys: set[str]
) -> dict[str, Any]:
    """Mask sensitive values in a dictionary for logging."""
    masked = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def log_service_call(call: ServiceCall, service_name: str) -> None:
    """Log service call for debugging purposes.

    Args:
        call: Service call object
        service_name: Name of the service
    """
    # Mask sensitive data before logging
    sensitive_keys = {"password", "token", "key", "secret", "credential"}
    data = get_service_data(call)
    masked_data = mask_sensitive_data({str(k): data[k] for k in data}, sensitive_keys)

    _LOGGER.debug(
        "Service call: %s with data: %s",
        service_name,
        masked_data,
    )


async def async_call_service_with_retry(
    hass: HomeAssistant,
    domain: str,
    service: str,
    service_data: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> Any:
    """Call a service with retry logic.

    Args:
        hass: Home Assistant instance
        domain: Service domain
        service: Service name
        service_data: Service call data
        max_retries: Maximum number of retries

    Returns:
        Service call result

    Raises:
        ServiceError: If service call fails after retries
    """
    for attempt in range(max_retries + 1):
        try:
            return await hass.services.async_call(
                domain,
                service,
                service_data,
                blocking=True,
            )
        except HomeAssistantError as err:
            if attempt == max_retries:
                raise ServiceError(
                    f"Service call {domain}.{service} failed after "
                    f"{max_retries} retries"
                ) from err

            wait_time = 2**attempt  # Exponential backoff
            _LOGGER.warning(
                "Service call %s.%s failed (attempt %d/%d), retrying in %d seconds: %s",
                domain,
                service,
                attempt + 1,
                max_retries + 1,
                wait_time,
                err,
            )
            await asyncio.sleep(wait_time)

    # Should never reach here due to the raise in the loop
    raise ServiceError(f"Unexpected error in service call {domain}.{service}")
