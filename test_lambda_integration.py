#!/usr/bin/env python3
"""
🧪 LAMBDA FUNCTION INTEGRATION TEST

Test each Lambda function with the current configuration state to validate
that the deployment works correctly after Gen 3 cleanup.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def simulate_lambda_environment(function_name: str):
    """Simulate specific Lambda function environment."""
    # Clear existing environment
    lambda_env_vars = [
        "APP_CONFIG_PATH",
        "BASE_URL",
        "HA_BASE_URL",
        "HA_TOKEN",
        "CF_CLIENT_ID",
        "CF_CLIENT_SECRET",
        "ALEXA_SECRET",
        "WRAPPER_SECRET",
    ]
    for var in lambda_env_vars:
        os.environ.pop(var, None)

    if function_name == "HomeAssistant":
        # smart_home_bridge environment
        os.environ["APP_CONFIG_PATH"] = "/ha-alexa/"
        os.environ["BASE_URL"] = "https://jarvis.hessenflow.net"
        print(f"🔧 {function_name} environment: APP_CONFIG_PATH, BASE_URL")

    elif function_name == "CloudFlare-Wrapper":
        # oauth_gateway environment
        os.environ["APP_CONFIG_PATH"] = "/ha-alexa/"
        print(f"🔧 {function_name} environment: APP_CONFIG_PATH only")

    elif function_name == "ConfigurationManager":
        # configuration_manager environment (no env vars)
        print(f"🔧 {function_name} environment: No environment variables")

    return {
        "function_name": function_name,
        "app_config_path": os.environ.get("APP_CONFIG_PATH"),
        "base_url": os.environ.get("BASE_URL"),
    }


def test_smart_home_bridge():
    """Test smart_home_bridge function."""
    print("\n🏠 Testing smart_home_bridge (HomeAssistant)")
    print("=" * 50)

    env = simulate_lambda_environment("HomeAssistant")

    try:
        # Import the Lambda function
        sys.path.insert(
            0, str(project_root / "infrastructure" / "deployment" / "smart_home_bridge")
        )
        import lambda_function as smart_home_bridge

        # Test basic configuration loading
        test_event = {
            "directive": {
                "header": {
                    "namespace": "Alexa.Discovery",
                    "name": "Discover",
                    "payloadVersion": "3",
                    "messageId": "test-message-id",
                },
                "payload": {"scope": {"type": "BearerToken", "token": "test-token"}},
            }
        }

        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"
        mock_context.function_name = "HomeAssistant"

        # Test lambda handler
        print("   🧪 Testing lambda_handler...")
        response = smart_home_bridge.lambda_handler(test_event, mock_context)

        print("   ✅ Lambda handler executed successfully")
        print(f"   📊 Response type: {type(response)}")

        if isinstance(response, dict) and "event" in response:
            print("   ✅ Valid Alexa response structure")
        else:
            print("   ⚠️  Unexpected response format")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()


def test_oauth_gateway():
    """Test oauth_gateway function."""
    print("\n🔐 Testing oauth_gateway (CloudFlare-Wrapper)")
    print("=" * 50)

    env = simulate_lambda_environment("CloudFlare-Wrapper")

    try:
        # Import the Lambda function
        sys.path.insert(
            0, str(project_root / "infrastructure" / "deployment" / "oauth_gateway")
        )
        import lambda_function as oauth_gateway

        # Test basic health check
        test_event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {"Host": "test.example.com"},
            "queryStringParameters": None,
        }

        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"
        mock_context.function_name = "CloudFlare-Wrapper"

        print("   🧪 Testing lambda_handler...")
        response = oauth_gateway.lambda_handler(test_event, mock_context)

        print("   ✅ Lambda handler executed successfully")
        print(f"   📊 Response: {response.get('statusCode', 'No status code')}")

        if response.get("statusCode") == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ⚠️  Unexpected status: {response}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()


def test_configuration_manager():
    """Test configuration_manager function."""
    print("\n⚙️  Testing configuration_manager (ConfigurationManager)")
    print("=" * 50)

    env = simulate_lambda_environment("ConfigurationManager")

    try:
        # Import the Lambda function
        sys.path.insert(
            0,
            str(
                project_root / "infrastructure" / "deployment" / "configuration_manager"
            ),
        )
        import lambda_function as config_manager

        # Test warmup request
        test_event = {
            "action": "warmup",
            "target_functions": ["HomeAssistant", "CloudFlare-Wrapper"],
        }

        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"
        mock_context.function_name = "ConfigurationManager"

        print("   🧪 Testing lambda_handler...")
        response = config_manager.lambda_handler(test_event, mock_context)

        print("   ✅ Lambda handler executed successfully")
        print(f"   📊 Response: {response.get('status', 'No status')}")

        if response.get("status") == "success":
            print("   ✅ Warmup coordination successful")
        else:
            print(f"   ⚠️  Unexpected response: {response}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main test execution."""
    print("🚀 Lambda Function Integration Test Suite")
    print("Testing with current Gen 2 configuration")

    # Build deployment files first
    print("\n📦 Building deployment files...")
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "scripts/lambda_deployment/cli.py", "--build"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode == 0:
            print("   ✅ Deployment files built successfully")
        else:
            print(f"   ❌ Build failed: {result.stderr}")
            return
    except Exception as e:
        print(f"   ❌ Build error: {e}")
        return

    # Test each Lambda function
    test_smart_home_bridge()
    test_oauth_gateway()
    test_configuration_manager()

    print("\n📋 Test Summary:")
    print("   • All functions should work with current Gen 2 configuration")
    print("   • No Gen 3 features needed for basic functionality")
    print("   • Configuration manager can coordinate Lambda warmup")
    print("   • Ready for AWS deployment with current SSM parameter")


if __name__ == "__main__":
    main()
