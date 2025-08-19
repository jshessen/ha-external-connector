#!/usr/bin/env python3
"""
Local testing script for HACS-restructured HA External Connector integration.

This script sets up a minimal Home Assistant test environment to validate our
Browser Mod integration works correctly in the HACS structure.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add our custom component to Python path
PROJECT_ROOT = Path(__file__).parent.parent
CUSTOM_COMPONENTS_PATH = PROJECT_ROOT / "custom_components"
sys.path.insert(0, str(CUSTOM_COMPONENTS_PATH))

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


# Import integration modules at the top-level to avoid "Import outside toplevel" errors
try:
    from custom_components.ha_external_connector import DOMAIN, PLATFORMS
    from custom_components.ha_external_connector.browser_mod_lwa_assistant import (
        BrowserModLWAAssistant,
    )
    from custom_components.ha_external_connector.config_flow import ConfigFlow
    from custom_components.ha_external_connector.const import DOMAIN as CONST_DOMAIN

    _INTEGRATION_IMPORT_ERROR = None
except ImportError as e:
    DOMAIN = None
    PLATFORMS = None
    CONST_DOMAIN = None
    BrowserModLWAAssistant = None
    ConfigFlow = None
    _INTEGRATION_IMPORT_ERROR = e


async def test_integration_import():
    """Test that our integration can be imported correctly."""
    if _INTEGRATION_IMPORT_ERROR is not None:
        _LOGGER.error("❌ Import failed: %s", _INTEGRATION_IMPORT_ERROR)
        return False

    _LOGGER.info("✅ All integration modules imported successfully")
    _LOGGER.info("✅ Domain: %s", DOMAIN)
    _LOGGER.info("✅ Platforms: %s", PLATFORMS)
    _LOGGER.info("✅ Const Domain: %s", CONST_DOMAIN)

    return True


async def test_browser_mod_assistant_init():
    """Test that BrowserModLWAAssistant can be initialized."""
    try:
        # Create minimal mock HomeAssistant object
        class MockServices:
            def async_services(self):
                return {
                    "browser_mod": {"popup": {}, "navigate": {}, "notification": {}}
                }

        class MockHomeAssistant:
            def __init__(self):
                self.services = MockServices()

        mock_hass = MockHomeAssistant()
        assistant = BrowserModLWAAssistant(mock_hass)
        _LOGGER.info("✅ BrowserModLWAAssistant initialized successfully")

        # Test constants are accessible
        _LOGGER.info(
            "✅ Required redirect URIs: %s", len(assistant.REQUIRED_REDIRECT_URIS)
        )
        _LOGGER.info(
            "✅ Default profile config name: %s",
            assistant.DEFAULT_PROFILE_CONFIG["name"],
        )

        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        _LOGGER.error("❌ BrowserModLWAAssistant test failed: %s", e)
        return False


async def test_config_flow():
    """Test that config flow can be imported and initialized."""
    try:
        if ConfigFlow is None:
            raise ImportError("ConfigFlow could not be imported")

        # Test constants
        config_flow = ConfigFlow()
        _LOGGER.info("✅ Config flow version: %s", config_flow.VERSION)

        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        _LOGGER.error("❌ Config flow test failed: %s", e)
        return False


async def validate_hacs_structure():
    """Validate HACS directory structure."""
    required_files = [
        "custom_components/ha_external_connector/__init__.py",
        "custom_components/ha_external_connector/manifest.json",
        "custom_components/ha_external_connector/config_flow.py",
        "custom_components/ha_external_connector/const.py",
        "custom_components/ha_external_connector/services.py",
        "custom_components/ha_external_connector/services.yaml",
        "custom_components/ha_external_connector/browser_mod_lwa_assistant.py",
        "custom_components/ha_external_connector/browser_mod_lwa_demo.py",
        "hacs.json",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        _LOGGER.error("❌ Missing required files: %s", missing_files)
        return False

    _LOGGER.info("✅ All required HACS files present")
    return True


async def test_manifest_json():
    """Test manifest.json is valid."""

    try:
        manifest_path = (
            PROJECT_ROOT / "custom_components/ha_external_connector/manifest.json"
        )
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        required_keys = [
            "domain",
            "name",
            "version",
            "documentation",
            "issue_tracker",
            "codeowners",
        ]
        missing_keys = [key for key in required_keys if key not in manifest]

        if missing_keys:
            _LOGGER.error("❌ Missing manifest keys: %s", missing_keys)
            return False

        _LOGGER.info(
            "✅ Manifest valid - Domain: %s, Version: %s",
            manifest["domain"],
            manifest["version"],
        )
        _LOGGER.info(
            "✅ Browser Mod dependency: %s",
            "browser_mod" in manifest.get("dependencies", []),
        )

        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        _LOGGER.error("❌ Manifest validation failed: %s", e)
        return False


async def test_hacs_json():
    """Test hacs.json is valid."""

    try:
        hacs_path = PROJECT_ROOT / "hacs.json"
        with open(hacs_path, encoding="utf-8") as f:
            hacs_config = json.load(f)

        _LOGGER.info("✅ HACS config - Name: %s", hacs_config.get("name"))
        _LOGGER.info("✅ HA Version: %s", hacs_config.get("homeassistant"))
        _LOGGER.info("✅ HACS Version: %s", hacs_config.get("hacs"))

        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        _LOGGER.error("❌ HACS config validation failed: %s", e)
        return False


async def main():
    """Run all integration tests."""
    _LOGGER.info("🚀 Starting HA External Connector integration tests...")

    tests = [
        ("HACS Structure", validate_hacs_structure),
        ("Manifest JSON", test_manifest_json),
        ("HACS JSON", test_hacs_json),
        ("Integration Import", test_integration_import),
        ("Browser Mod Assistant", test_browser_mod_assistant_init),
        ("Config Flow", test_config_flow),
    ]

    results = []
    for test_name, test_func in tests:
        _LOGGER.info("\n🧪 Running %s test...", test_name)
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:  # pylint: disable=broad-exception-caught
            _LOGGER.error("❌ %s test crashed: %s", test_name, e)
            results.append((test_name, False))

    # Summary
    _LOGGER.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        _LOGGER.info("  %s: %s", test_name, status)
        if result:
            passed += 1

    _LOGGER.info("\n🎯 Overall: %s/%s tests passed", passed, len(results))

    if passed == len(results):
        _LOGGER.info("🎉 All tests passed! Integration is ready for local HA testing.")
        return True

    _LOGGER.error("💥 Some tests failed. Fix issues before proceeding.")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
