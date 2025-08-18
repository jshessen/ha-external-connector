#!/usr/bin/env python3
"""
🧪 LWA Security Profile Automation Demo

This script demonstrates the browser automation capabilities for LWA Security
Profile creation, showing the integration between SMAPITokenHelper and the new
browser automation component.

Usage:
    python scripts/demo_lwa_automation.py [--headless]
"""

import argparse
import sys
from pathlib import Path

from custom_components.ha_external_connector.integrations.alexa.lwa_security_profile_automation import (
    LWASecurityProfileAutomation,
    automate_security_profile_creation,
)
from custom_components.ha_external_connector.utils import HAConnectorLogger

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_lwa_automation(headless: bool = False) -> None:
    """Demo the LWA Security Profile automation capabilities."""
    logger = HAConnectorLogger(__name__)

    logger.info("🚀 Starting LWA Security Profile Automation Demo")
    logger.info(f"Headless mode: {headless}")

    # Method 1: Direct class usage
    logger.info("\n📋 Method 1: Direct class usage")
    try:
        with LWASecurityProfileAutomation(headless=headless) as automation:
            logger.info("✅ Browser automation initialized successfully")

            # Get browser status information
            browser_status = automation.get_browser_status()
            logger.info(f"🌐 Browser status: {browser_status['status']}")
            logger.info(f"🔧 Browser state: {browser_status.get('browser', 'unknown')}")
            if "current_url" in browser_status:
                logger.info(f"📍 Current URL: {browser_status['current_url']}")

            # Take a screenshot to verify browser is working
            if automation.take_screenshot("lwa_demo_init.png"):
                logger.info("📸 Screenshot saved: lwa_demo_init.png")

            # Demo navigation to LWA console using public method
            if automation.navigate_to_lwa_console():
                logger.info("✅ Successfully navigated to LWA Console")

                # Get updated browser status
                browser_status = automation.get_browser_status()
                logger.info(
                    f"📍 Current URL: {browser_status.get('current_url', 'unknown')}"
                )

                # Take another screenshot
                if automation.take_screenshot("lwa_demo_console.png"):
                    logger.info("📸 Screenshot saved: lwa_demo_console.png")

    except (RuntimeError, ValueError) as e:
        logger.error(f"❌ Direct class usage failed: {str(e)}")

    # Method 2: Integration function usage (recommended for SMAPITokenHelper)
    logger.info("\n📋 Method 2: Integration function usage")
    try:
        # This is the function that SMAPITokenHelper calls
        result = automate_security_profile_creation(headless=headless)

        if result:
            logger.info("✅ Integration function completed")
            logger.info(f"Result keys: {list(result.keys()) if result else 'None'}")
        else:
            logger.info("⚠️ Integration function returned None (expected in demo)")

    except (RuntimeError, ValueError) as e:
        logger.error(f"❌ Integration function failed: {str(e)}")

    logger.info("\n🎯 Demo completed!")
    logger.info("💡 To see the automation in action:")
    logger.info(
        "   1. Run: python -m ha_connector.integrations.alexa.smapi_token_helper"
    )
    logger.info(
        "   2. When prompted for Security Profile creation, choose 'Yes' for automation"
    )
    logger.info(
        "   3. Watch the browser automatically fill forms while you stay in control!"
    )


def main() -> None:
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Demo LWA Security Profile Automation")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no GUI)",
    )

    args = parser.parse_args()

    try:
        demo_lwa_automation(headless=args.headless)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except (RuntimeError, ValueError) as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
