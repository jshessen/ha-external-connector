"""Alexa integration configuration flow."""

import logging
from typing import Any, Protocol, cast

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from custom_components.ha_external_connector.const import DOMAIN


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

    async def async_create_entry(
        self, title: str, data: dict[str, Any]
    ) -> FlowResult:  # pyright: ignore[return]
        """Create config entry."""
        ...


_LOGGER = logging.getLogger(__name__)

ALEXA_SCHEMA = vol.Schema(
    {
        vol.Required("aws_access_key_id"): str,
        vol.Required("aws_secret_access_key"): str,
        vol.Required("aws_region", default="us-east-1"): str,
        vol.Required("skill_id"): str,
        vol.Required("client_id"): str,
        vol.Required("client_secret"): str,
        vol.Optional("cloudflare_api_token"): str,
        vol.Optional("domain_name"): str,
    }
)


class AlexaConfigFlow(ConfigFlow):
    """Alexa-specific configuration flow."""

    VERSION: int = 1

    def __init__(self) -> None:
        """Initialize Alexa config flow."""
        self._main_flow_data: dict[str, Any] = {}

    @property
    def domain(self) -> str:
        """Return the domain."""
        return DOMAIN

    def set_main_flow_data(self, data: dict[str, Any]) -> None:
        """Set main flow data from the router."""
        self._main_flow_data = data

    def is_matching(self, other_flow: Any) -> bool:
        """Return if this config flow matches the config entry."""
        return (
            hasattr(other_flow, "domain")
            and getattr(other_flow, "domain", None) == DOMAIN
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Alexa integration setup."""
        errors = {}

        if user_input is not None:
            try:
                # Validate Alexa configuration
                await self._validate_alexa_input(user_input)

                # Combine main flow data with Alexa-specific data
                final_data = {
                    **self._main_flow_data,
                    "integration_type": "alexa",
                    "aws_config": {
                        "access_key_id": user_input["aws_access_key_id"],
                        "secret_access_key": user_input["aws_secret_access_key"],
                        "region": user_input["aws_region"],
                    },
                    "alexa_config": {
                        "skill_id": user_input["skill_id"],
                        "client_id": user_input["client_id"],
                        "client_secret": user_input["client_secret"],
                    },
                    "cloudflare_config": {
                        "api_token": user_input.get("cloudflare_api_token"),
                        "domain_name": user_input.get("domain_name"),
                    },
                }

                # Use protocol for method access
                flow = cast(ConfigFlowProtocol, self)
                title = (
                    f"Alexa - {self._main_flow_data.get('name', 'External Connector')}"
                )
                return await flow.async_create_entry(title=title, data=final_data)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except (ValueError, vol.Invalid) as err:
                _LOGGER.error("Validation error in Alexa setup: %s", err)
                errors["base"] = "invalid_input"
            except HomeAssistantError as err:
                _LOGGER.error("Home Assistant error in Alexa setup: %s", err)
                errors["base"] = "unknown"

        # Use protocol for method access
        flow = cast(ConfigFlowProtocol, self)
        return flow.async_show_form(
            step_id="user",
            data_schema=ALEXA_SCHEMA,
            errors=errors,
            description_placeholders={
                "setup_url": "https://developer.amazon.com/alexa/console/ask"
            },
        )

    async def _validate_alexa_input(self, data: dict[str, Any]) -> None:
        """Validate Alexa configuration input."""
        # Validate required fields
        required_fields = [
            "aws_access_key_id",
            "aws_secret_access_key",
            "skill_id",
            "client_id",
            "client_secret",
        ]
        for field in required_fields:
            if not data.get(field, "").strip():
                raise InvalidAuth(f"{field} is required")

        # TODO: Add actual AWS and Alexa API validation
        _LOGGER.debug("Alexa configuration validated successfully")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
