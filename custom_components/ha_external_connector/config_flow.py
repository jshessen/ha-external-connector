"""Config flow for Home Assistant External Connector integration."""

from __future__ import annotations

import logging
from typing import Any, Protocol, cast

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .integrations.alexa.config_flow import AlexaConfigFlow


class ConfigFlowProtocol(Protocol):
    """Protocol for config flow functionality."""

    domain: str

    async def async_show_form(
        self,
        step_id: str,
        data_schema: vol.Schema | None = None,
        errors: dict[str, str] | None = None,
        description_placeholders: dict[str, str] | None = None,
    ) -> FlowResult:  # type: ignore[return]
        """Show form to user."""
        ...

    async def async_create_entry(self, title: str, data: dict[str, Any]) -> FlowResult:  # type: ignore[return]
        """Create config entry."""
        ...


_LOGGER = logging.getLogger(__name__)

INTEGRATION_TYPES = {
    "alexa": "Alexa Smart Home",
    "google": "Google Assistant (Future)",
    "ios": "iOS Companion (Future)",
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("integration_type"): vol.In(INTEGRATION_TYPES),
        vol.Required("name", default="External Connector"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Home Assistant External Connector."""

    VERSION: int = 1

    @property
    def domain(self) -> str:
        """Return the domain."""
        return DOMAIN

    def __init__(self) -> None:
        """Initialize config flow."""
        self._selected_integration: str | None = None
        self._user_input: dict[str, Any] = {}

    def is_matching(self, other_flow: Any) -> bool:
        """Return if this config flow matches the config entry."""
        return (
            hasattr(other_flow, "domain")
            and getattr(other_flow, "domain", None) == DOMAIN
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - integration selection."""
        errors = {}

        if user_input is not None:
            try:
                integration_type = user_input["integration_type"]
                self._selected_integration = integration_type
                self._user_input.update(user_input)

                # Route to appropriate integration setup
                if integration_type == "alexa":
                    return await self._delegate_to_alexa_config()
                if integration_type in ["google", "ios"]:
                    errors["base"] = "not_implemented"
                else:
                    errors["base"] = "invalid_integration"

            except (ValueError, vol.Invalid) as err:
                _LOGGER.error("Validation error in user step: %s", err)
                errors["base"] = "invalid_input"
            except HomeAssistantError as err:
                _LOGGER.error("Home Assistant error in user step: %s", err)
                errors["base"] = "unknown"

        # Use protocol for method access
        flow = cast(ConfigFlowProtocol, self)
        return flow.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "integrations": ", ".join(INTEGRATION_TYPES.values())
            },
        )

    async def _delegate_to_alexa_config(self) -> FlowResult:
        """Delegate to Alexa-specific configuration flow."""
        try:
            # Create Alexa config flow instance and start it
            alexa_flow = AlexaConfigFlow()
            # Pass the main flow data to the Alexa flow
            alexa_flow.set_main_flow_data(self._user_input)
            return await alexa_flow.async_step_user()
        except ImportError as e:
            _LOGGER.error("Failed to import Alexa config flow: %s", e)
            errors = {"base": "alexa_import_failed"}
        except (OSError, HomeAssistantError) as e:
            _LOGGER.error("Error setting up Alexa integration: %s", e)
            errors = {"base": "alexa_setup_failed"}

        # If delegation failed, show error on main form
        flow = cast(ConfigFlowProtocol, self)
        return flow.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "integrations": ", ".join(INTEGRATION_TYPES.values())
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
