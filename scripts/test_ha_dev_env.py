#!/usr/bin/env python3
"""
Test Home Assistant Development Environment

Simple validation script to ensure HA modules are properly accessible.
This is used by the automated setup and CI/CD processes.
"""

import sys
from pathlib import Path


def test_homeassistant_imports():
    """Test that all critical Home Assistant modules can be imported."""
    test_cases = [
        # Core modules
        ("homeassistant", "core"),
        ("homeassistant.core", "HomeAssistant"),
        ("homeassistant.exceptions", "HomeAssistantError"),
        ("homeassistant.data_entry_flow", "FlowResult"),
        # Helper modules commonly used in integrations
        ("homeassistant.helpers.entity", "Entity"),
        ("homeassistant.helpers.config_validation", "string"),
        ("homeassistant.config_entries", "ConfigEntry"),
        # Component infrastructure
        ("homeassistant.const", "CONF_HOST"),
        ("homeassistant.components.sensor", "SensorEntity"),
    ]

    results = []
    for module_name, attribute in test_cases:
        try:
            module = __import__(module_name, fromlist=[attribute])
            if hasattr(module, attribute):
                results.append((module_name, attribute, "✅ PASS"))
            else:
                results.append(
                    (module_name, attribute, f"❌ FAIL - {attribute} not found")
                )
        except ImportError as e:
            results.append((module_name, attribute, f"❌ FAIL - Import error: {e}"))
        except (AttributeError, TypeError) as e:
            results.append((module_name, attribute, f"❌ FAIL - Unexpected error: {e}"))

    return results


def main():
    """Run all validation tests."""
    print("🏠 Home Assistant Development Environment Validation")
    print("=" * 55)

    # Test Python version
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current directory: {Path.cwd()}")

    # Test imports
    print("\n🧪 Testing Home Assistant imports...")
    results = test_homeassistant_imports()

    passed = 0
    failed = 0

    for module_name, attribute, status in results:
        print(f"   {status} {module_name}.{attribute}")
        if "PASS" in status:
            passed += 1
        else:
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 SUCCESS! Home Assistant development environment is fully functional!")
        return 0
    print("❌ FAILURE! Some Home Assistant modules are not accessible.")
    print("   Run 'python scripts/setup_ha_dev.py' to fix the environment.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
