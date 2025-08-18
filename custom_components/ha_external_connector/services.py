"""Services for Home Assistant External Connector integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .browser_mod_lwa_assistant import BrowserModLWAAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_SETUP_LWA_PROFILE = "setup_lwa_profile"
SERVICE_CHECK_BROWSER_MOD = "check_browser_mod"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the integration."""

    async def handle_setup_lwa_profile(_call: ServiceCall) -> None:
        """Handle the setup_lwa_profile service call."""
        assistant = BrowserModLWAAssistant(hass)
        result = await assistant.start_lwa_setup_workflow()
        _LOGGER.info("LWA setup workflow result: %s", result)

    async def handle_check_browser_mod(_call: ServiceCall) -> None:
        """Handle the check_browser_mod service call."""
        assistant = BrowserModLWAAssistant(hass)
        result = await assistant.check_browser_mod_availability()
        _LOGGER.info("Browser Mod availability check result: %s", result)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SETUP_LWA_PROFILE,
        handle_setup_lwa_profile,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CHECK_BROWSER_MOD,
        handle_check_browser_mod,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for the integration."""
    hass.services.async_remove(DOMAIN, SERVICE_SETUP_LWA_PROFILE)
    hass.services.async_remove(DOMAIN, SERVICE_CHECK_BROWSER_MOD)
