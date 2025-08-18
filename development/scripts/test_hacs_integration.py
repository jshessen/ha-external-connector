#!/usr/bin/env python3
"""
Local testing script for HACS-restructured HA External Connector integration.

This script sets up a minimal Home Assistant test environment to validate our
Browser Mod integration works correctly in the HACS structure.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add our custom component to Python path
PROJECT_ROOT = Path(__file__).parent.parent
CUSTOM_COMPONENTS_PATH = PROJECT_ROOT / "custom_components"
sys.path.insert(0, str(CUSTOM_COMPONENTS_PATH))

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


async def test_integration_import():
    """Test that our integration can be imported correctly."""
    try:
        # Test importing the integration modules
        from ha_external_connector import (
            DOMAIN,
            PLATFORMS,
            async_setup,
            async_setup_entry,
            async_unload_entry,
        )
        from ha_external_connector.browser_mod_lwa_assistant import (
            BrowserModLWAAssistant,
        )
        from ha_external_connector.config_flow import ConfigFlow
        from ha_external_connector.const import DOMAIN as CONST_DOMAIN
        from ha_external_connector.services import (
            async_setup_services,
            async_unload_services,
        )

        _LOGGER.info("✅ All integration modules imported successfully")
        _LOGGER.info(f"✅ Domain: {DOMAIN}")
        _LOGGER.info(f"✅ Platforms: {PLATFORMS}")
        _LOGGER.info(f"✅ Const Domain: {CONST_DOMAIN}")

        return True

    except ImportError as e:
        _LOGGER.error(f"❌ Import failed: {e}")
        return False


async def test_browser_mod_assistant_init():
    """Test that BrowserModLWAAssistant can be initialized."""
    try:
        # Create minimal mock HomeAssistant object
        class MockHomeAssistant:
            def __init__(self):
                self.services = MockServices()

        class MockServices:
            def async_services(self):
                return {
                    "browser_mod": {"popup": {}, "navigate": {}, "notification": {}}
                }

        mock_hass = MockHomeAssistant()

        # Test BrowserModLWAAssistant initialization
        from ha_external_connector.browser_mod_lwa_assistant import (
            BrowserModLWAAssistant,
        )

        assistant = BrowserModLWAAssistant(mock_hass)
        _LOGGER.info("✅ BrowserModLWAAssistant initialized successfully")

        # Test constants are accessible
        _LOGGER.info(
            f"✅ Required redirect URIs: {len(assistant.REQUIRED_REDIRECT_URIS)}"
        )
        _LOGGER.info(
            f"✅ Default profile config name: {assistant.DEFAULT_PROFILE_CONFIG['name']}"
        )

        return True

    except Exception as e:
        _LOGGER.error(f"❌ BrowserModLWAAssistant test failed: {e}")
        return False


async def test_config_flow():
    """Test that config flow can be imported and initialized."""
    try:
        from ha_external_connector.config_flow import ConfigFlow

        # Test constants
        config_flow = ConfigFlow()
        _LOGGER.info(f"✅ Config flow version: {config_flow.VERSION}")

        return True

    except Exception as e:
        _LOGGER.error(f"❌ Config flow test failed: {e}")
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
        _LOGGER.error(f"❌ Missing required files: {missing_files}")
        return False

    _LOGGER.info("✅ All required HACS files present")
    return True


async def test_manifest_json():
    """Test manifest.json is valid."""
    import json

    try:
        manifest_path = (
            PROJECT_ROOT / "custom_components/ha_external_connector/manifest.json"
        )
        with open(manifest_path) as f:
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
            _LOGGER.error(f"❌ Missing manifest keys: {missing_keys}")
            return False

        _LOGGER.info(
            f"✅ Manifest valid - Domain: {manifest['domain']}, Version: {manifest['version']}"
        )
        _LOGGER.info(
            f"✅ Browser Mod dependency: {'browser_mod' in manifest.get('dependencies', [])}"
        )

        return True

    except Exception as e:
        _LOGGER.error(f"❌ Manifest validation failed: {e}")
        return False


async def test_hacs_json():
    """Test hacs.json is valid."""
    import json

    try:
        hacs_path = PROJECT_ROOT / "hacs.json"
        with open(hacs_path) as f:
            hacs_config = json.load(f)

        _LOGGER.info(f"✅ HACS config - Name: {hacs_config.get('name')}")
        _LOGGER.info(f"✅ HA Version: {hacs_config.get('homeassistant')}")
        _LOGGER.info(f"✅ HACS Version: {hacs_config.get('hacs')}")

        return True

    except Exception as e:
        _LOGGER.error(f"❌ HACS config validation failed: {e}")
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
        _LOGGER.info(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            _LOGGER.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    _LOGGER.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        _LOGGER.info(f"  {test_name}: {status}")
        if result:
            passed += 1

    _LOGGER.info(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        _LOGGER.info("🎉 All tests passed! Integration is ready for local HA testing.")
        return True
    else:
        _LOGGER.error("💥 Some tests failed. Fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
