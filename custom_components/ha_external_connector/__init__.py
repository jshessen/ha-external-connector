"""Home Assistant External Connector Integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .integrations.alexa.services import async_setup_alexa_services
from .platforms import (
    AWSService,
    CloudFlareService,
    PlatformConfig,
    PlatformType,
    platform_registry,
)
from .platforms.security import (
    APIKeyValidator,
    AuthMethod,
    OAuth2Validator,
    SecurityConfig,
    security_manager,
)
from .services import async_setup_services

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup(
    hass: HomeAssistant, config: dict  # pylint: disable=unused-argument
) -> bool:
    """Set up the Home Assistant External Connector integration."""
    _LOGGER.info("Setting up Home Assistant External Connector integration")

    # Initialize platform registry
    await _initialize_platform_services()

    # Set up global services
    await async_setup_services(hass)
    await async_setup_alexa_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Assistant External Connector from a config entry."""
    _LOGGER.info("Setting up config entry for Home Assistant External Connector")

    # Initialize integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Initialize platform services based on config entry
    await _setup_entry_platforms(entry)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading config entry for Home Assistant External Connector")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _initialize_platform_services() -> None:
    """Initialize platform services."""
    # Register security validators
    oauth2_config = SecurityConfig(
        auth_method=AuthMethod.OAUTH2,
        credentials={},
    )
    api_key_config = SecurityConfig(
        auth_method=AuthMethod.API_KEY,
        credentials={},
    )

    security_manager.register_validator(
        AuthMethod.OAUTH2, OAuth2Validator(oauth2_config)
    )
    security_manager.register_validator(
        AuthMethod.API_KEY, APIKeyValidator(api_key_config)
    )

    _LOGGER.info("Platform services initialized")


async def _setup_entry_platforms(entry: ConfigEntry) -> None:
    """Set up platform services for a config entry."""
    try:
        integration_type = entry.data.get("integration_type")

        if integration_type == "alexa":
            # Set up AWS platform service
            aws_config_data = entry.data.get("aws_config", {})
            if aws_config_data:
                aws_config = PlatformConfig(
                    platform_type=PlatformType.AWS,
                    credentials=aws_config_data,
                    region=aws_config_data.get("region", "us-east-1"),
                )
                aws_service = AWSService(aws_config)
                platform_registry.register_service(PlatformType.AWS, aws_service)
                await aws_service.initialize()

            # Set up CloudFlare platform service if configured
            cloudflare_config_data = entry.data.get("cloudflare_config", {})
            if cloudflare_config_data.get("api_token"):
                cloudflare_config = PlatformConfig(
                    platform_type=PlatformType.CLOUDFLARE,
                    credentials=cloudflare_config_data,
                )
                cloudflare_service = CloudFlareService(cloudflare_config)
                platform_registry.register_service(
                    PlatformType.CLOUDFLARE, cloudflare_service
                )
                await cloudflare_service.initialize()

        _LOGGER.info("Entry platforms configured for %s", integration_type)

    except Exception as err:  # pylint: disable=broad-exception-caught
        # Broad exception catching is acceptable in HA component setup for robustness
        _LOGGER.error("Error setting up entry platforms: %s", err)
