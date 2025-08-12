#!/usr/bin/env python3
"""
Alexa Smart Home Testing Suite
Comprehensive testing tool for Alexa Smart Home integration with Home Assistant

Features:
- Discovery testing to find all available endpoints
- Power control testing (turn on/off) for any endpoint
- Comprehensive endpoint validation and testing
- Automatic cleanup of temporary test files
- Optional permanent file saving with --save-files
- Manual cleanup with --cleanup command
- Professional artifact management

Usage:
    python alexa_smart_home_testing_suite.py                   # Run full test suite
    python alexa_smart_home_testing_suite.py --discovery       # Run discovery only
    python alexa_smart_home_testing_suite.py --turn-on <ID>    # Turn on endpoint
    python alexa_smart_home_testing_suite.py --turn-off <ID>   # Turn off endpoint
    python alexa_smart_home_testing_suite.py --test <ID>       # Test endpoint
    python alexa_smart_home_testing_suite.py --save-files      # Save files permanently
    python alexa_smart_home_testing_suite.py --cleanup         # Clean up artifacts
"""

import argparse
import atexit
import json
import logging
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import boto3
import botocore.exceptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global list to track temporary files for cleanup
_temp_files: list[str] = []


def cleanup_temp_files() -> None:
    """Clean up all temporary files created during testing."""
    if not _temp_files:
        return

    logger.info("🧹 Cleaning up %d temporary test files...", len(_temp_files))
    for temp_file in _temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug("  ✅ Removed: %s", temp_file)
        except OSError as e:
            logger.warning("  ⚠️ Failed to remove %s: %s", temp_file, e)

    _temp_files.clear()
    logger.info("✅ Cleanup complete")


def create_temp_file(prefix: str = "test_", suffix: str = ".json") -> str:
    """Create a temporary file and track it for cleanup."""
    temp_fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(temp_fd)  # Close the file descriptor, we just need the path
    _temp_files.append(temp_path)
    return temp_path


# Register cleanup function to run on exit
atexit.register(cleanup_temp_files)


def get_ha_bearer_token() -> str:
    """
    Get a real Home Assistant long-lived access token for testing.

    Uses the working HA token that successfully authenticates with Home Assistant.
    Since you've updated SSM to match the working token, this should now work.

    Returns:
        Real Home Assistant bearer token string (working token)
    """
    # Use the working HA token (the one that was in Lambda env and now updated in SSM)
    # This is the token that successfully worked: iat: 1751913010
    ha_token = (  # nosec B105 (test token provided by user for testing)
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJmYTMzYWI4ZjIxM2Y0ZWJmYTcxZGJjNjY3YzU0ZjI4ZiIs"
        "ImlhdCI6MTc1MTkxMzAxMCwiZXhwIjoyMDY3MjczMDEwfQ."
        "PeIfgTKCKNhRpoWKvqUCvbqXkzP6F6Hdp7K54rwlxwI"
    )

    logger.info("🎯 Using working HA bearer token: %s...", ha_token[:20])
    return ha_token


def create_power_controller_directive(
    endpoint_id: str, power_state: str
) -> dict[str, Any]:
    """
    Create a valid Alexa Smart Home event matching real Alexa skill payloads.

    Args:
        endpoint_id: The Home Assistant entity ID (e.g., "fan#guest_fan")
        power_state: "TurnOn" or "TurnOff"

    Returns:
        Complete Alexa Smart Home event payload (matches real skill format)
    """
    message_id = str(uuid.uuid4())
    correlation_token = str(uuid.uuid4())

    # Get a real Home Assistant bearer token
    bearer_token = get_ha_bearer_token()

    # Real Alexa Smart Home event structure (what skill sends to Lambda)
    alexa_event = {
        "directive": {
            "header": {
                "namespace": "Alexa.PowerController",
                "name": power_state,
                "payloadVersion": "3",
                "messageId": message_id,
                "correlationToken": correlation_token,
            },
            "endpoint": {
                "scope": {"type": "BearerToken", "token": bearer_token},
                "endpointId": endpoint_id,
                "cookie": {},
            },
            "payload": {},
        }
    }

    return alexa_event


def create_discovery_directive() -> dict[str, Any]:
    """
    Create Alexa Discovery directive with real HA token embedded properly.

    Returns:
        Alexa Discovery directive with properly structured bearer token
    """
    ha_token = get_ha_bearer_token()

    return {
        "directive": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover",
                "payloadVersion": "3",
                "messageId": str(uuid.uuid4()),
            },
            "payload": {"scope": {"type": "BearerToken", "token": ha_token}},
        }
    }


def test_lambda_function(
    payload: dict[str, Any], function_name: str = "HomeAssistant"
) -> dict[str, Any]:
    """
    Test the Lambda function directly with a payload.

    Args:
        payload: The test payload to send
        function_name: AWS Lambda function name

    Returns:
        Lambda response
    """
    try:
        lambda_client = boto3.client("lambda")  # pyright: ignore

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Parse the response
        response_payload = json.loads(response["Payload"].read())

        logger.info("✅ Lambda Response Status: %s", response["StatusCode"])
        logger.info("📋 Response: %s", json.dumps(response_payload, indent=2))

        return response_payload
    except (botocore.exceptions.BotoCoreError, json.JSONDecodeError, KeyError) as e:
        logger.error("❌ Lambda invocation failed: %s", e)
        return {"error": str(e)}


def save_test_payload(
    payload: dict[str, Any], filename: str, save_permanently: bool = False
) -> str:
    """
    Save test payload to a file.

    Args:
        payload: The payload to save
        filename: Base filename
        save_permanently: If True, save to current directory; if False, use temp file

    Returns:
        Path to the file created
    """
    if save_permanently:
        # Save to current directory with the specified filename
        filepath = filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("💾 Saved permanent file: %s", filepath)
        return filepath

    # Create a unique temporary file
    base_name = Path(filename).stem
    temp_file = create_temp_file(prefix=f"{base_name}_", suffix=".json")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("💾 Saved temporary file: %s", temp_file)
    return temp_file


def parse_arguments():
    """Parse command-line arguments for individual function execution."""
    parser = argparse.ArgumentParser(
        description="Alexa Smart Home Testing Suite",
        epilog="""
Examples:
  python alexa_smart_home_testing_suite.py                    # Run full test suite
  python alexa_smart_home_testing_suite.py --discovery        # Run discovery only
  python alexa_smart_home_testing_suite.py --turn-on fan#guest_outlet_2
  python alexa_smart_home_testing_suite.py --turn-off fan.guest_outlet_2
  python alexa_smart_home_testing_suite.py --test fan#guest_fan
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--discovery",
        action="store_true",
        help="Run discovery test to find available endpoints",
    )

    parser.add_argument(
        "--turn-on",
        metavar="ENDPOINT_ID",
        help="Turn on specific endpoint (e.g., fan#guest_outlet_2)",
    )

    parser.add_argument(
        "--turn-off",
        metavar="ENDPOINT_ID",
        help="Turn off specific endpoint (e.g., fan#guest_outlet_2)",
    )

    parser.add_argument(
        "--test",
        metavar="ENDPOINT_ID",
        help="Test specific endpoint with both on/off commands",
    )

    parser.add_argument(
        "--function",
        choices=["HomeAssistant"],
        default="HomeAssistant",
        help="AWS Lambda function name (default: HomeAssistant)",
    )

    parser.add_argument(
        "--save-files",
        action="store_true",
        help="Save test payload files permanently (default: use temporary files)",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up existing test artifacts and exit",
    )

    return parser.parse_args()


def cleanup_artifacts() -> None:
    """Clean up test artifacts from both root and validation directories."""
    logger.info("🧹 Cleaning up test artifacts...")

    # Patterns to clean up
    artifact_patterns = [
        "discovery_test.json",
        "guest_fan_*.json",
        "test_guest_fan_*.json",
        "response*.json",
        "test_discovery.json",
    ]

    # Directories to clean
    directories = [
        Path.cwd(),  # Current directory
        Path(__file__).parent,  # tests/validation directory
        Path(__file__).parent.parent.parent,  # Project root
    ]

    cleaned_count = 0
    for directory in directories:
        if not directory.exists():
            continue

        logger.info("  🔍 Checking directory: %s", directory)
        for pattern in artifact_patterns:
            for file_path in directory.glob(pattern):
                try:
                    file_path.unlink()
                    logger.info("    ✅ Removed: %s", file_path.name)
                    cleaned_count += 1
                except OSError as e:
                    logger.warning("    ⚠️ Failed to remove %s: %s", file_path, e)

    logger.info("✅ Cleanup complete: %d files removed", cleaned_count)


def run_discovery_test(
    function_name: str = "HomeAssistant", save_permanently: bool = False
) -> None:
    """Run discovery test to find available endpoints."""
    logger.info("🔍 Running Discovery Test")
    logger.info("=" * 50)

    discovery_payload = create_discovery_directive()
    save_test_payload(discovery_payload, "discovery_test.json", save_permanently)

    logger.info("📋 Testing Discovery to find actual endpoint IDs...")
    discovery_response = test_lambda_function(discovery_payload, function_name)

    if "error" not in discovery_response:
        logger.info("✅ Discovery successful - check response for available endpoints")
        if "event" in discovery_response and "payload" in discovery_response["event"]:
            endpoints = discovery_response["event"]["payload"].get("endpoints", [])
            if endpoints:
                logger.info("📋 Found %d endpoints:", len(endpoints))
                for endpoint in endpoints:
                    endpoint_id = endpoint.get("endpointId", "Unknown")
                    friendly_name = endpoint.get("friendlyName", "No name")
                    logger.info("  - %s (%s)", endpoint_id, friendly_name)
            else:
                logger.info("⚠️  No endpoints found in discovery response")
    else:
        logger.error("❌ Discovery failed: %s", discovery_response.get("error"))


def run_endpoint_test(
    endpoint_id: str,
    action: str,
    function_name: str = "HomeAssistant",
    save_permanently: bool = False,
) -> None:
    """Run a specific endpoint test (turn on/off)."""
    if action not in ["TurnOn", "TurnOff"]:
        logger.error("❌ Invalid action: %s. Must be 'TurnOn' or 'TurnOff'", action)
        sys.exit(1)

    logger.info("🔧 Testing %s for endpoint: %s", action, endpoint_id)
    logger.info("=" * 50)

    payload = create_power_controller_directive(endpoint_id, action)
    filename = (
        f"guest_fan_{action.lower()}_"
        f"{endpoint_id.replace('#', '_').replace('.', '_')}.json"
    )
    save_test_payload(payload, filename, save_permanently)

    logger.info("🎯 Testing %s for %s", action, endpoint_id)
    response = test_lambda_function(payload, function_name)

    if "error" not in response:
        logger.info("✅ SUCCESS: %s command sent to %s", action, endpoint_id)
    else:
        logger.error(
            "❌ FAILED: %s command to %s failed: %s",
            action,
            endpoint_id,
            response.get("error"),
        )


def run_full_endpoint_test(
    endpoint_id: str,
    function_name: str = "HomeAssistant",
    save_permanently: bool = False,
) -> None:
    """Run both turn on and turn off tests for an endpoint."""
    logger.info("🔧 Full Test for endpoint: %s", endpoint_id)
    logger.info("=" * 50)

    # Test Turn On
    run_endpoint_test(endpoint_id, "TurnOn", function_name, save_permanently)

    # Test Turn Off
    run_endpoint_test(endpoint_id, "TurnOff", function_name, save_permanently)

    logger.info("✅ Full test completed for %s", endpoint_id)


def main():
    """Run comprehensive Alexa Smart Home testing or individual commands."""
    args = parse_arguments()

    # Handle cleanup command
    if args.cleanup:
        cleanup_artifacts()
        cleanup_temp_files()
        return

    # Check if any individual command was specified
    if args.discovery:
        run_discovery_test(args.function, args.save_files)
        return

    if args.turn_on:
        run_endpoint_test(args.turn_on, "TurnOn", args.function, args.save_files)
        return

    if args.turn_off:
        run_endpoint_test(args.turn_off, "TurnOff", args.function, args.save_files)
        return

    if args.test:
        run_full_endpoint_test(args.test, args.function, args.save_files)
        return

    # Run comprehensive test suite if no individual command specified
    logger.info("🔧 Alexa Smart Home Testing Suite - Comprehensive Mode")
    logger.info("=" * 50)

    # Common guest fan endpoint variations
    guest_fan_endpoints = [
        "fan#guest_outlet_2",  # Based on your existing test file
        "fan.guest_outlet_2",  # Alternative format
        "fan#guest_fan",  # Generic name
        "switch#guest_outlet_2",  # If configured as switch
    ]

    logger.info("🔍 Step 1: Discovery Test")
    run_discovery_test(args.function, args.save_files)

    logger.info("\n🔋 Step 2: Guest Fan Control Tests")
    logger.info("Testing %d possible endpoint IDs...", len(guest_fan_endpoints))

    for i, endpoint_id in enumerate(guest_fan_endpoints, 1):
        logger.info("\n--- Test %d: %s ---", i, endpoint_id)
        run_full_endpoint_test(endpoint_id, args.function, args.save_files)

    logger.info("\n%s", "=" * 50)
    logger.info("🎯 Test Results Summary:")
    logger.info("- Check CloudWatch logs for detailed error information")
    logger.info("- Look for successful endpoint IDs in responses")
    logger.info("- Verify authentication is working (no 401 errors)")

    # Inform about cleanup behavior
    if args.save_files:
        logger.info("- Test files saved permanently for review")
    else:
        logger.info("- Test files will be cleaned up automatically on exit")

    logger.info("\n📝 Manual Test Instructions:")
    logger.info("1. Use --discovery to find exact endpoint ID")
    logger.info("2. Use --turn-on <ID> or --turn-off <ID> for individual control")
    logger.info("3. Use --test <ID> for full on/off testing of specific endpoint")
    logger.info("4. Use --save-files to keep test payloads for debugging")
    logger.info("5. Use --cleanup to remove all test artifacts")
    logger.info("6. Monitor Home Assistant for actual device state changes")


if __name__ == "__main__":
    main()
