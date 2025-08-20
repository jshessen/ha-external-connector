"""Alexa integration services."""

# pylint: disable=fixme  # TODO comments are intentional for future development

import logging
from typing import Any, Protocol, cast

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from custom_components.ha_external_connector.const import DOMAIN
from custom_components.ha_external_connector.platforms import (
    PlatformType,
    platform_registry,
)


class ServiceDataProtocol(Protocol):
    """Protocol for service call data."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from service data."""
        ...


class ServiceRegistryProtocol(Protocol):
    """Protocol for service registry."""

    def async_register(self, domain: str, service: str, handler: Any) -> None:
        """Register a service."""
        ...


_LOGGER = logging.getLogger(__name__)


async def async_setup_alexa_services(hass: HomeAssistant) -> None:
    """Set up Alexa integration services."""

    # Access the services registry through getattr to avoid unknown type issues
    services_obj = getattr(hass, "services", None)
    if services_obj is None:
        _LOGGER.error("Services registry not available")
        return

    services = cast(ServiceRegistryProtocol, services_obj)

    async def deploy_lambda_functions(_call: ServiceCall) -> None:
        """Deploy Alexa Lambda functions to AWS."""
        try:
            aws_service = platform_registry.get_service(PlatformType.AWS)
            if not aws_service:
                _LOGGER.error("AWS service not available")
                return

            # TODO: Implement Lambda deployment logic
            _LOGGER.info("Deploying Alexa Lambda functions")

        except (HomeAssistantError, RuntimeError) as err:
            _LOGGER.error("Failed to deploy Lambda functions: %s", err)

    async def update_skill_configuration(call: ServiceCall) -> None:
        """Update Alexa skill configuration."""
        try:
            # Extract skill_id safely from service call data
            call_data = getattr(call, "data", {})
            data = cast(ServiceDataProtocol, call_data)
            skill_id: str | None = data.get("skill_id")
            if not skill_id:
                _LOGGER.error("Skill ID required for configuration update")
                return

            # TODO: Implement skill configuration update
            _LOGGER.info("Updating skill configuration for %s", skill_id)

        except HomeAssistantError as err:
            _LOGGER.error("Failed to update skill configuration: %s", err)

    async def sync_devices(_call: ServiceCall) -> None:
        """Sync Home Assistant devices with Alexa."""
        try:
            # TODO: Implement device synchronization
            _LOGGER.info("Syncing devices with Alexa")

        except RuntimeError as err:
            _LOGGER.error("Failed to sync devices: %s", err)

    async def test_skill_connectivity(_call: ServiceCall) -> None:
        """Test Alexa skill connectivity."""
        try:
            # TODO: Implement connectivity test
            _LOGGER.info("Testing Alexa skill connectivity")

        except HomeAssistantError as err:
            _LOGGER.error("Connectivity test failed: %s", err)

    # Register services
    services.async_register(DOMAIN, "alexa_deploy_lambda", deploy_lambda_functions)

    services.async_register(DOMAIN, "alexa_update_skill", update_skill_configuration)

    services.async_register(DOMAIN, "alexa_sync_devices", sync_devices)

    services.async_register(DOMAIN, "alexa_test_connectivity", test_skill_connectivity)


async def async_unload_alexa_services(hass: HomeAssistant) -> None:
    """Unload Alexa integration services."""
    # Access the services registry through getattr to avoid unknown type issues
    services_obj = getattr(hass, "services", None)
    if services_obj is None:
        _LOGGER.warning("Services registry not available during unload")
        return

    # Remove registered services
    service_names = [
        "alexa_deploy_lambda",
        "alexa_update_skill",
        "alexa_sync_devices",
        "alexa_test_connectivity",
    ]

    for service_name in service_names:
        try:
            if hasattr(services_obj, "async_remove"):
                await services_obj.async_remove(DOMAIN, service_name)
            _LOGGER.debug("Removed Alexa service: %s", service_name)
        except Exception as service_error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning(
                "Error removing Alexa service %s: %s", service_name, service_error
            )
