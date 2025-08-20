"""Protocol definitions for Home Assistant External Connector.

This module provides common protocol definitions used across config flows,
services, and other components to maintain type safety while working with
Home Assistant's internal APIs.
"""

from typing import Any, Protocol

from homeassistant.data_entry_flow import FlowResult


class ConfigFlowProtocol(Protocol):
    """Protocol for Home Assistant config flow operations."""

    def async_set_unique_id(self, unique_id: str) -> None:
        """Set unique ID for the config flow."""

    def _abort_if_unique_id_configured(self) -> None:
        """Abort if unique ID is already configured."""

    def async_show_form(
        self,
        step_id: str,
        data_schema: Any | None = None,
        errors: dict[str, str] | None = None,
        description_placeholders: dict[str, str] | None = None,
    ) -> FlowResult:
        """Show a form to the user."""

    def async_create_entry(self, title: str, data: dict[str, Any]) -> FlowResult:
        """Create a config entry."""


class ServiceDataProtocol(Protocol):
    """Protocol for service call data."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from service data."""


class ServiceRegistryProtocol(Protocol):
    """Protocol for service registry."""

    def async_register(self, domain: str, service: str, handler: Any) -> None:
        """Register a service."""

    def async_remove(self, domain: str, service: str) -> None:
        """Remove a service."""


class PlatformProtocol(Protocol):
    """Protocol for platform implementations."""

    @property
    def name(self) -> str:
        """Return the platform name."""
        ...

    async def async_setup(self) -> bool:
        """Set up the platform."""
        ...

    async def async_unload(self) -> bool:
        """Unload the platform."""
        ...
