"""
🚀 Browser Mod LWA Demo - Simplified Prototype

Proof-of-concept demonstration of Browser Mod integration for LWA Security
Profile creation within Home Assistant ecosystem.

This prototype shows how Browser Mod can replace external Selenium automation
for HACS-compatible deployment.
"""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound

_LOGGER = logging.getLogger(__name__)


class BrowserModLWADemo:
    """Simplified Browser Mod LWA demonstration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize Browser Mod LWA Demo."""
        self.hass: HomeAssistant = hass

    async def check_browser_mod_available(self) -> bool:
        """Check if Browser Mod is available."""
        try:
            services = (
                self.hass.services.async_services()
            )  # pyright: ignore[reportUnknownMemberType]
            browser_mod_services = services.get(
                "browser_mod", {}
            )  # pyright: ignore[reportUnknownMemberType]
            return "browser_mod" in services and "popup" in browser_mod_services
        except (ServiceNotFound, RuntimeError) as e:
            _LOGGER.error("Error checking Browser Mod: %s", str(e))
            return False

    async def demonstrate_lwa_workflow(self) -> bool:
        """Demonstrate the Browser Mod LWA workflow."""
        _LOGGER.info("Starting Browser Mod LWA workflow demonstration")

        try:
            # Step 1: Show welcome popup
            await self._show_welcome_popup()

            # Step 2: Show navigation guidance
            await self._show_navigation_guidance()

            # Step 3: Show credential collection form
            await self._show_credential_form()

            return True

        except HomeAssistantError as e:
            _LOGGER.error("LWA workflow demonstration failed: %s", str(e))
            return False

    async def _show_welcome_popup(self) -> None:
        """Show welcome popup."""
        content = """
# 🚀 Browser Mod LWA Assistant

This demonstrates how Browser Mod can replace Selenium automation for
LWA Security Profile creation in a HACS-compatible way.

## Key Benefits:
- **No external dependencies** (Chrome driver, Selenium server)
- **Uses existing browser** connected to Home Assistant
- **Native HA integration** with service calls
- **Container deployment friendly**

## Next Steps:
1. Navigate to Amazon Developer Console
2. Follow step-by-step guidance
3. Collect credentials securely
        """

        await self._call_browser_mod_service(
            "popup",
            {
                "title": "🔐 LWA Security Profile Assistant",
                "content": content,
                "size": "wide",
                "right_button": "Continue",
                "left_button": "Cancel",
            },
        )

    async def _show_navigation_guidance(self) -> None:
        """Show navigation guidance."""
        await self._call_browser_mod_service(
            "notification",
            {"message": "🌐 Navigate to Amazon Developer Console", "duration": 3000},
        )

    async def _show_credential_form(self) -> None:
        """Show credential collection form."""
        form_fields = [
            {
                "name": "client_id",
                "required": True,
                "selector": {"text": {"type": "password"}},
            },
            {
                "name": "client_secret",
                "required": True,
                "selector": {"text": {"type": "password"}},
            },
        ]

        await self._call_browser_mod_service(
            "popup",
            {
                "title": "🔑 Enter LWA Credentials",
                "content": form_fields,
                "size": "normal",
                "right_button": "Save",
                "left_button": "Cancel",
            },
        )

    async def _call_browser_mod_service(
        self, service_name: str, service_data: dict[str, Any]
    ) -> None:
        """Call Browser Mod service with error handling."""
        try:
            await self.hass.services.async_call(  # pyright: ignore[reportUnknownMemberType]
                "browser_mod", service_name, service_data, blocking=True
            )
        except ServiceNotFound as e:
            _LOGGER.error("Browser Mod service not found: %s", service_name)
            msg = f"Browser Mod service '{service_name}' not available"
            raise RuntimeError(msg) from e
        except Exception as e:
            _LOGGER.error("Browser Mod service call failed: %s", str(e))
            msg = f"Failed to call browser_mod.{service_name}: {e}"
            raise RuntimeError(msg) from e


async def demo_browser_mod_integration(hass: HomeAssistant) -> None:
    """Demo function to test Browser Mod integration."""
    demo = BrowserModLWADemo(hass)

    # Check if Browser Mod is available
    if not await demo.check_browser_mod_available():
        print("❌ Browser Mod not available")
        return

    print("✅ Browser Mod available - starting demo")

    # Run the demonstration
    success = await demo.demonstrate_lwa_workflow()
    if success:
        print("🚀 Browser Mod LWA workflow demonstration completed")
    else:
        print("❌ Demo failed - check Home Assistant logs")
