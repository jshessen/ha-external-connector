"""Template for integration config flows.

This template incorporates proven patterns from TEMPLATE_services.py:
- Comprehensive error handling with ServiceError for user-actionable feedback
- Safe parameter extraction using .get() methods
- Proper async/await usage for Protocol methods
- Structured exception hierarchy for different error types
- Clear validation logic with descriptive error messages

To use this template:
1. Copy this file to your integration folder
2. Replace "example" with your integration name throughout
3. Update validation logic for your specific requirements
4. Add proper connection testing in _validate_input method
5. Update data schema and error handling as needed

Benefits applied from services template:
- Enhanced error handling prevents runtime failures
- ServiceError provides user-actionable error messages
- Safe parameter access prevents KeyError exceptions
- Proper async patterns maintain type safety
- Comprehensive logging aids debugging
"""

# pylint: disable-all
# This is a template file - disable all linting

from __future__ import annotations

import logging
from typing import Any, Protocol, cast

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from custom_components.ha_external_connector.const import DOMAIN
from custom_components.ha_external_connector.utils import ServiceError


class ConfigFlowProtocol(Protocol):
    """Protocol for config flow functionality."""

    domain: str

    async def async_show_form(
        self,
        step_id: str,
        data_schema: vol.Schema | None = None,
        errors: dict[str, str] | None = None,
        description_placeholders: dict[str, str] | None = None,
    ) -> FlowResult:
        """Show form to user."""
        ...

    async def async_create_entry(self, title: str, data: dict[str, Any]) -> FlowResult:
        """Create config entry."""
        ...


_LOGGER = logging.getLogger(__name__)

# TODO: Define schema for your integration
INTEGRATION_SCHEMA = vol.Schema(
    {
        vol.Required("example_field"): str,
        vol.Optional("optional_field"): str,
    }
)


class ExampleIntegrationConfigFlow(config_entries.ConfigFlow):
    """Example integration-specific configuration flow."""

    VERSION: int = 1

    def __init__(self) -> None:
        """Initialize integration config flow."""
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
        """Handle integration setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Extract parameters safely (pattern from services template)
                example_field = user_input.get("example_field")
                if not example_field:
                    raise ServiceError("Required field 'example_field' not provided")

                # TODO: Add validation logic
                await self._validate_input(user_input)

                # Combine main flow data with integration-specific data
                final_data = {
                    **self._main_flow_data,
                    "integration_type": "example",  # Change this
                    "example_config": {
                        "example_field": example_field,
                        "optional_field": user_input.get("optional_field"),
                    },
                }

                # Use protocol for method access - await the async method
                flow = cast(ConfigFlowProtocol, self)
                name = self._main_flow_data.get("name", "External Connector")
                title = f"Example - {name}"
                return await flow.async_create_entry(title=title, data=final_data)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ServiceError as err:
                _LOGGER.error("Service validation error in example setup: %s", err)
                errors["base"] = "invalid_input"
            except (ValueError, vol.Invalid) as err:
                _LOGGER.error("Validation error in example setup: %s", err)
                errors["base"] = "invalid_input"
            except HomeAssistantError as err:
                _LOGGER.error("Home Assistant error in example setup: %s", err)
                errors["base"] = "unknown"
            except Exception as err:
                # Catch-all for unexpected errors (pattern from services template)
                _LOGGER.error("Unexpected error in example setup: %s", err)
                errors["base"] = "unknown"

        # Use protocol for method access - await the async method
        flow = cast(ConfigFlowProtocol, self)
        return await flow.async_show_form(
            step_id="user",
            data_schema=INTEGRATION_SCHEMA,
            errors=errors,
            description_placeholders={"setup_url": "https://example.com/setup"},
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> None:
        """
        Validate user input with comprehensive error handling.

        Patterns from services template:
        - Safe parameter extraction using .get()
        - Explicit validation with ServiceError for user feedback
        - Proper async exception handling
        """
        # Safe parameter extraction (pattern from services template)
        example_field = user_input.get("example_field")
        if not example_field:
            raise ServiceError("Example field is required")

        if not isinstance(example_field, str) or len(example_field.strip()) < 3:
            raise ServiceError("Example field must be at least 3 characters")

        # Optional field validation with defaults
        optional_field = user_input.get("optional_field", "")
        if optional_field and not isinstance(optional_field, str):
            raise ServiceError("Optional field must be a string")

        # TODO: Add actual connection testing here
        # Example pattern:
        # try:
        #     await test_connection(example_field)
        # except ConnectionError as err:
        #     raise CannotConnect(f"Failed to connect: {err}") from err


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
