#!/usr/bin/env python3
"""Test script to check Home Assistant module availability."""

try:
    import importlib.util

    if importlib.util.find_spec("homeassistant.config_entries") is not None:
        print("✅ homeassistant.config_entries module is available")
    else:
        print("❌ homeassistant.config_entries module is NOT available")
    if importlib.util.find_spec("homeassistant.core") is not None:
        print("✅ homeassistant.core module is available")
    else:
        print("❌ homeassistant.core module is NOT available")
    if importlib.util.find_spec("homeassistant.exceptions") is not None:
        print("✅ homeassistant.exceptions module is available")
    else:
        print("❌ homeassistant.exceptions module is NOT available")
except ImportError as e:
    print(f"❌ Failed to import Home Assistant modules: {e}")
    print("\nTrying alternative import method...")
    try:
        import sys

        print(f"Python path includes: {sys.path}")
    except ImportError as e2:
        print(f"Error checking Python path: {e2}")
