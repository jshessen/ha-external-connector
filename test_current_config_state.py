#!/usr/bin/env python3
"""
🔍 CONFIGURATION VALIDATION TEST

Test the current configuration loading state after Gen 3 cleanup.
Validates progressive configuration upgrade path:
1. Current state (Gen 2 only) - smart_home_bridge and oauth_gateway should work
2. After adding lambda config - configuration_manager should work
3. After adding cache config - all should have enhanced features
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.ha_connector.integrations.alexa.lambda_functions.shared_configuration import (
        load_comprehensive_configuration,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_configuration_loading(test_name: str, app_config_path: str) -> None:
    """Test configuration loading for a specific scenario."""
    print(f"\n🔍 {test_name}")
    print("=" * 60)

    try:
        # Test comprehensive configuration loading
        configurations, generation, features = load_comprehensive_configuration(
            app_config_path=app_config_path
        )

        print("✅ Configuration loaded successfully!")
        print(f"📊 Generation: {generation}")
        print(f"🎯 Available features: {features}")
        print("📋 Configuration sections:")

        for section, config in configurations.items():
            print(f"   • {section}: {len(config) if config else 0} parameters")
            if config:
                # Show non-sensitive keys
                secret_keywords = ["token", "secret", "password", "key"]
                safe_keys = [
                    k
                    for k in config
                    if not any(secret in k.lower() for secret in secret_keywords)
                ]
                if safe_keys:
                    print(f"     Safe keys: {safe_keys}")

        # Test specific function scenarios
        print("\n🧪 Function-specific tests:")

        # Test smart_home_bridge (should work with ha_config)
        ha_config = configurations.get("ha_config", {})
        if ha_config.get("base_url") and ha_config.get("token"):
            print("   ✅ smart_home_bridge: Should work (has HA config)")
        else:
            print("   ❌ smart_home_bridge: Missing HA configuration")

        # Test oauth_gateway (should work with cloudflare_config)
        cf_config = configurations.get("cloudflare_config", {})
        if cf_config.get("client_id") and cf_config.get("client_secret"):
            print("   ✅ oauth_gateway: Should work (has CloudFlare config)")
        else:
            print("   ❌ oauth_gateway: Missing CloudFlare configuration")

        # Test configuration_manager (needs lambda_config for full functionality)
        lambda_config = configurations.get("lambda_config", {})
        if lambda_config:
            print("   ✅ configuration_manager: Should work (has Lambda config)")
        else:
            print(
                "   ⚠️  configuration_manager: Limited functionality (no Lambda config)"
            )

        # Test caching features
        cache_config = configurations.get("cache_config", {})
        if cache_config:
            print("   ✅ Enhanced caching: Available")
        else:
            print("   ⚠️  Enhanced caching: Not configured")

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback

        traceback.print_exc()


def simulate_current_aws_environment():
    """Simulate the current AWS Lambda environment variables."""
    print("🔧 Simulating current AWS environment:")

    # HomeAssistant Lambda environment
    os.environ["APP_CONFIG_PATH"] = "/ha-alexa/"
    os.environ["BASE_URL"] = "https://jarvis.hessenflow.net"

    # CloudFlare-Wrapper Lambda environment
    # (APP_CONFIG_PATH already set above)

    # ConfigurationManager Lambda environment
    # (no environment variables)

    print("   • APP_CONFIG_PATH: /ha-alexa/")
    print("   • BASE_URL: https://jarvis.hessenflow.net")
    print("   • No other environment variables set")


def main():
    """Main test execution."""
    print("🚀 Configuration Validation Test Suite")
    print("Testing current state after Gen 3 cleanup")

    # Simulate current environment
    simulate_current_aws_environment()

    # Test current configuration (should be Gen 2)
    test_configuration_loading("Current State - Gen 2 Configuration", "/ha-alexa/")

    print("\n📋 Expected Results:")
    print("   • Generation: Should be GEN_2_ENV_SSM_JSON")
    print("   • smart_home_bridge: Should work (HA config available)")
    print("   • oauth_gateway: Should work (CloudFlare config available)")
    print("   • configuration_manager: Limited functionality (no Lambda config)")
    print("   • Enhanced caching: Not available (no cache config)")

    print("\n🎯 Next Steps:")
    print("   1. Add lambda_config to SSM to enable configuration_manager")
    print("   2. Add cache_config to SSM to enable enhanced caching")
    print("   3. This will upgrade to Gen 3 automatically")


if __name__ == "__main__":
    main()
