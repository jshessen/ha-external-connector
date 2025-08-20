"""Service router for Home Assistant External Connector integration.

This module provides a centralized service router that delegates to
integration-specific service modules for scalable service management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, ServiceCall

from .browser_mod_lwa_assistant import BrowserModLWAAssistant
from .const import DOMAIN
from .integrations.alexa.services import (
    async_setup_alexa_services,
    async_unload_alexa_services,
)
from .utils import ServiceError

if TYPE_CHECKING:
    from homeassistant.helpers.service import ServiceRegistry

_LOGGER = logging.getLogger(__name__)

# Core integration services (non-integration-specific)
SERVICE_SETUP_LWA_PROFILE = "setup_lwa_profile"
SERVICE_CHECK_BROWSER_MOD = "check_browser_mod"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up all services for the integration using modular router pattern."""
    try:
        # Set up core integration services
        await _setup_core_services(hass)

        # Set up integration-specific services
        await async_setup_alexa_services(hass)

        _LOGGER.info("All services registered successfully")

    except ServiceError as err:
        _LOGGER.error("Failed to set up services: %s", err)
        raise


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload all services for the integration."""
    try:
        # Unload core services
        await _unload_core_services(hass)

        # Unload integration-specific services
        try:
            await async_unload_alexa_services(hass)
        except Exception as integration_error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning(
                "Error unloading integration services: %s", integration_error
            )

        _LOGGER.info("All services unloaded successfully")

    except ServiceError as err:
        _LOGGER.warning("Error during service unload: %s", err)


async def _setup_core_services(hass: HomeAssistant) -> None:
    """Set up core integration services (non-integration-specific)."""

    async def handle_setup_lwa_profile(_call: ServiceCall) -> None:
        """Handle the setup_lwa_profile service call."""
        try:
            assistant = BrowserModLWAAssistant(hass)
            result = await assistant.start_lwa_setup_workflow()
            _LOGGER.info("LWA setup workflow result: %s", result)
        except ServiceError as err:
            _LOGGER.error("LWA setup workflow failed: %s", err)
            raise

    async def handle_check_browser_mod(_call: ServiceCall) -> None:
        """Handle the check_browser_mod service call."""
        try:
            assistant = BrowserModLWAAssistant(hass)
            result = await assistant.check_browser_mod_availability()
            _LOGGER.info("Browser Mod availability check result: %s", result)
        except ServiceError as err:
            _LOGGER.error("Browser Mod check failed: %s", err)
            raise

    # Register core services
    services: ServiceRegistry = hass.services
    services.async_register(
        DOMAIN,
        SERVICE_SETUP_LWA_PROFILE,
        handle_setup_lwa_profile,
    )

    services.async_register(
        DOMAIN,
        SERVICE_CHECK_BROWSER_MOD,
        handle_check_browser_mod,
    )

    _LOGGER.debug("Core services registered")


async def _unload_core_services(hass: HomeAssistant) -> None:
    """Unload core integration services."""
    services: ServiceRegistry = hass.services
    services.async_remove(DOMAIN, SERVICE_SETUP_LWA_PROFILE)
    services.async_remove(DOMAIN, SERVICE_CHECK_BROWSER_MOD)

    _LOGGER.debug("Core services unloaded")
