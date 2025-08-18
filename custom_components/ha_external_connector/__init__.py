"""Home Assistant External Connector Integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .services import async_setup_services, async_unload_services

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ha_external_connector"
PLATFORMS: list[Platform] = []


async def async_setup(_hass: HomeAssistant, _config: dict) -> bool:
    """Set up the Home Assistant External Connector integration."""
    _LOGGER.info("Setting up Home Assistant External Connector integration")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Assistant External Connector from a config entry."""
    _LOGGER.info("Setting up config entry for Home Assistant External Connector")

    # Initialize integration data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Set up services
    await async_setup_services(hass)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading config entry for Home Assistant External Connector")

    # Unload services
    await async_unload_services(hass)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
