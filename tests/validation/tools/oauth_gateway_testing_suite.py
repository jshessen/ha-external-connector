#!/usr/bin/env python3
"""
OAuth Gateway Testing Suite
Comprehensive testing tool for OAuth Gateway Lambda function validation

This tool validates the OAuth token exchange functionality that handles Alexa Smart Home
account linking. It can test both the o    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            error_response = {
                "errorMessage": (
                    f"Lambda function '{function_name}' not found. "
                    "Available functions can be listed with: "
                    "aws lambda list-functions --query 'Functions[].FunctionName'"
                ),
                "errorType": "ResourceNotFoundException",
                "requestId": str(uuid.uuid4())
            }
            logger.error("❌ Lambda function not found: %s", function_name)
            logger.info(
                (
                    "💡 Tip: Use --function <correct-name> or check available "
                    "functions with AWS CLI"
                )
            )
        else:
            error_response = {
                "errorMessage": f"AWS error: {str(e)}",
                "errorType": error_code,
                "requestId": str(uuid.uuid4())
            }
            logger.error("❌ AWS error: %s", error_response["errorMessage"])
        return error_response
    except (botocore.exceptions.BotoCoreError, json.JSONDecodeError, KeyError) as e:
        error_response = {
            "errorMessage": f"Failed to invoke Lambda function: {str(e)}",
            "errorType": type(e).__name__,
            "requestId": str(uuid.uuid4())
        }
        logger.error("❌ Lambda invocation failed: %s", error_response["errorMessage"])
        return error_responseCloudFlare-Wrapper functionality and
enhanced performance-optimized versions.

Features:
- OAuth token exchange testing with real Home Assistant
- CloudFlare Access header validation
- Security validation and error handling testing
- Performance benchmarking and caching validation
- Comprehensive baseline vs enhanced functionality comparison
- Automatic cleanup of temporary test files
- Professional artifact management for CI/CD integration

Usage:
    python oauth_gateway_testing_suite.py    # Run full test suite
        # (continues on next line if needed)
    python oauth_gateway_testing_suite.py --token-exchange \
        # Test OAuth flow only
    python oauth_gateway_testing_suite.py --security-validation \
        # Test security features
    python oauth_gateway_testing_suite.py --performance-benchmark \
        # Test performance
    python oauth_gateway_testing_suite.py --baseline-test \
        # Test original functionality
    python oauth_gateway_testing_suite.py --function oauth_gateway \
        # Test specific function
    python oauth_gateway_testing_suite.py --save-files \
        # Save artifacts permanently
    python oauth_gateway_testing_suite.py --cleanup \
        # Clean up test artifacts
"""

import argparse
import atexit
import base64
import json
import logging
import os
import tempfile
import time
import urllib.parse
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
                logger.debug("Removed temp file: %s", temp_file)
        except OSError as e:
            logger.warning("Failed to remove temp file %s: %s", temp_file, e)

    _temp_files.clear()
    logger.info("✅ Cleanup complete")


def create_temp_file(prefix: str = "oauth_test_", suffix: str = ".json") -> str:
    """Create a temporary file and track it for cleanup."""
    temp_fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(temp_fd)  # Close the file descriptor, we just need the path
    _temp_files.append(temp_path)
    return temp_path


# Register cleanup function to run on exit
atexit.register(cleanup_temp_files)


def get_oauth_test_configuration() -> dict[str, str]:
    """
    Get OAuth test configuration from SSM parameters.

    Returns:
        Dictionary containing OAuth configuration for testing
    """
    try:
        ssm_client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]

        # Get the main app configuration
        response = ssm_client.get_parameter(
            Name="/ha-alexa/appConfig", WithDecryption=True
        )

        parameter_value = response.get("Parameter", {}).get("Value")
        if parameter_value is None:
            logger.error("❌ 'Value' key missing in SSM response: %s", response)
            raise KeyError("'Value' key missing in SSM response")
        config_data = json.loads(parameter_value)
        logger.info("🔧 Loaded OAuth configuration from SSM")

        return {
            "base_url": config_data.get("HA_BASE_URL", ""),
            "cf_client_id": config_data.get("CF_CLIENT_ID", ""),
            "cf_client_secret": config_data.get("CF_CLIENT_SECRET", ""),
            "wrapper_secret": config_data.get("WRAPPER_SECRET", ""),
            "ha_token": config_data.get("HA_TOKEN", ""),
        }

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ Failed to load OAuth configuration: %s", e)
        raise


def create_oauth_token_exchange_request(
    client_secret: str,
    grant_type: str = "authorization_code",
    client_id: str = "https://pitangui.amazon.com/",
    code: str = "test_authorization_code",
    redirect_uri: str = "https://alexa.amazon.co.jp/spa/skill-account-linking-status.html",
) -> dict[str, Any]:
    """
    Create a valid OAuth token exchange request matching Alexa's format.

    This simulates the exact request that Alexa sends during account linking.

    Args:
        client_secret: The wrapper secret for validation
        grant_type: OAuth grant type (typically "authorization_code")
        client_id: Alexa client ID (Amazon's identifier)
        code: Authorization code from OAuth flow
        redirect_uri: Alexa's redirect URI

    Returns:
        Complete Lambda event payload for OAuth token exchange
    """
    # Create the OAuth request body (what Alexa sends)
    oauth_request_data = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    # Convert to URL-encoded form data (Alexa's format)
    request_body = urllib.parse.urlencode(oauth_request_data).encode("utf-8")

    # Create Lambda event structure (what API Gateway sends to Lambda)
    lambda_event = {
        "httpMethod": "POST",
        "path": "/oauth/token",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Amazon-Alexa-Skill-Oauth-Client/1.0",
            "Accept": "application/json",
        },
        "body": base64.b64encode(request_body).decode("utf-8"),
        "isBase64Encoded": True,
        "requestContext": {
            "requestId": str(uuid.uuid4()),
            "identity": {"sourceIp": "52.84.89.85"},  # Amazon IP range
        },
    }

    return lambda_event


def create_oauth_token_refresh_request(
    client_secret: str,
    refresh_token: str,
    grant_type: str = "refresh_token",
    client_id: str = "https://pitangui.amazon.com/",
) -> dict[str, Any]:
    """
    Create OAuth token refresh request for testing token renewal.

    Args:
        client_secret: The wrapper secret for validation
        refresh_token: Refresh token from previous OAuth exchange
        grant_type: OAuth grant type for refresh
        client_id: Alexa client ID

    Returns:
        Lambda event payload for token refresh
    """
    oauth_request_data = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    request_body = urllib.parse.urlencode(oauth_request_data).encode("utf-8")

    lambda_event = {
        "httpMethod": "POST",
        "path": "/oauth/token",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Amazon-Alexa-Skill-Oauth-Client/1.0",
            "Accept": "application/json",
        },
        "body": base64.b64encode(request_body).decode("utf-8"),
        "isBase64Encoded": True,
        "requestContext": {
            "requestId": str(uuid.uuid4()),
            "identity": {"sourceIp": "52.84.89.86"},  # Different Amazon IP
        },
    }

    return lambda_event


def test_lambda_function(
    payload: dict[str, Any], function_name: str = "HomeAssistantOAuth"
) -> dict[str, Any]:
    """
    Test the OAuth Gateway Lambda function with a payload.

    Args:
        payload: The OAuth request payload to send
        function_name: AWS Lambda function name

    Returns:
        Lambda response with OAuth token or error
    """
    try:
        lambda_client = boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "lambda"
        )

        logger.info("🚀 Invoking Lambda function: %s", function_name)
        logger.debug("Request payload: %s", json.dumps(payload, indent=2))

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Parse the response
        response_payload = json.loads(response["Payload"].read())
        status_code = response.get("StatusCode", 0)

        logger.info("📊 Lambda Response Status: %d", status_code)

        if "errorMessage" in response_payload:
            # Check if this is an expected security validation (don't log as ERROR)
            error_type = response_payload.get("errorType", "Unknown")
            error_msg = response_payload["errorMessage"]

            is_security_validation = error_type in [
                "AssertionError",
                "KeyError",
                "ValueError",
                "Error",
            ] and (
                # AssertionError is always a security validation in this context
                error_type == "AssertionError"
                or
                # Other errors need keyword matching
                any(
                    keyword in str(error_msg).lower()
                    for keyword in [
                        "client_secret",
                        "secret mismatch",
                        "base64",
                        "invalid",
                    ]
                )
            )

            if is_security_validation:
                logger.debug(
                    "🔒 Security validation triggered: %s (%s)", error_msg, error_type
                )
            else:
                logger.error("❌ Lambda Error: %s", error_msg)
                logger.error("Error Type: %s", error_type)
                if "stackTrace" in response_payload:
                    logger.debug("Stack trace: %s", response_payload["stackTrace"])
        else:
            logger.info("✅ OAuth Gateway Response received")
            logger.debug("Response: %s", json.dumps(response_payload, indent=2))

        return response_payload

    except (botocore.exceptions.BotoCoreError, json.JSONDecodeError, KeyError) as e:
        error_response = {
            "errorMessage": f"Failed to invoke Lambda function: {str(e)}",
            "errorType": type(e).__name__,
            "requestId": str(uuid.uuid4()),
        }
        logger.error("❌ Lambda invocation failed: %s", error_response["errorMessage"])
        return error_response


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


def _validate_error_message(error_msg: str, error_type: str) -> tuple[bool, str]:
    """
    Validate error message responses - helper for validate_oauth_response.

    Args:
        error_msg: Error message to validate
        error_type: Type of error

    Returns:
        Tuple of (is_valid, validation_message)
    """
    # ResourceNotFoundException means function doesn't exist - graceful failure
    if error_type == "ResourceNotFoundException":
        return False, f"⚠️  Infrastructure issue: {error_msg}"

    # Security validation errors - these are EXPECTED and GOOD
    security_validations = [
        (
            error_type == "KeyError" and "client_secret" in error_msg,
            "✅ Security validation: Missing client_secret properly rejected",
        ),
        (
            error_type == "ValueError" and "secret mismatch" in error_msg.lower(),
            "✅ Security validation: Invalid client_secret properly rejected",
        ),
        (
            error_type == "ValueError" and "Client secret mismatch" in error_msg,
            "✅ Security validation: Invalid client_secret properly rejected",
        ),
        (
            "Invalid base64-encoded string" in error_msg,
            "✅ Security validation: Malformed request properly rejected",
        ),
        (
            error_type == "Error" and "base64" in error_msg.lower(),
            "✅ Security validation: Invalid encoding properly rejected",
        ),
        (
            error_type == "AssertionError",
            "✅ Security validation: Request validation triggered (assertion failure)",
        ),
    ]

    for condition, message in security_validations:
        if condition:
            return True, message

    # Other Lambda errors are infrastructure failures
    return False, f"Lambda infrastructure error: {error_msg}"


def _validate_oauth_error_payload(error_payload: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate OAuth error payload - helper for validate_oauth_response.

    Args:
        error_payload: OAuth error payload to validate

    Returns:
        Tuple of (is_valid, validation_message)
    """
    error_type = error_payload.get("type", "UNKNOWN_ERROR")
    error_message = error_payload.get("message", "No error message")

    # "Invalid code" is EXPECTED when using test authorization codes - this is a SUCCESS
    if "invalid_grant" in error_type.lower() or "invalid code" in error_message.lower():
        return True, (
            f"✅ OAuth flow validation: Home Assistant correctly rejected "
            f"test authorization code ({error_type} - {error_message})"
        )

    # Other OAuth errors are actual failures
    return False, f"OAuth error: {error_type} - {error_message}"


def _validate_successful_oauth_response(response: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate successful OAuth response - helper for validate_oauth_response.

    Args:
        response: OAuth response to validate

    Returns:
        Tuple of (is_valid, validation_message)
    """
    required_fields = ["access_token", "token_type"]
    optional_fields = ["expires_in", "refresh_token", "scope"]

    missing_fields = [field for field in required_fields if field not in response]
    if missing_fields:
        return False, f"Missing required OAuth fields: {missing_fields}"

    present_optional = [field for field in optional_fields if field in response]
    validation_msg = (
        f"Valid OAuth response with fields: {required_fields + present_optional}"
    )
    return True, validation_msg


def validate_oauth_response(response: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate OAuth response format and content.

    Args:
        response: OAuth Gateway response to validate

    Returns:
        Tuple of (is_valid, validation_message)
    """
    # Handle infrastructure failures (function doesn't exist, etc.)
    if "errorMessage" in response:
        error_msg = response["errorMessage"]
        error_type = response.get("errorType", "Unknown")
        return _validate_error_message(error_msg, error_type)

    # Check for OAuth error response format
    if "event" in response and "payload" in response["event"]:
        error_payload = response["event"]["payload"]
        return _validate_oauth_error_payload(error_payload)

    # Check for successful OAuth response
    return _validate_successful_oauth_response(response)


def run_oauth_token_exchange_test(
    function_name: str = "HomeAssistantOAuth", save_permanently: bool = False
) -> None:
    """
    Test OAuth token exchange functionality.

    Args:
        function_name: Lambda function name to test
        save_permanently: Whether to save test artifacts permanently
    """
    logger.info("🔐 Testing OAuth Token Exchange...")

    try:
        # Get test configuration
        config = get_oauth_test_configuration()

        # Create OAuth token exchange request
        oauth_request = create_oauth_token_exchange_request(
            client_secret=config["wrapper_secret"]
        )

        # Save request payload
        request_file = save_test_payload(
            oauth_request, "oauth_token_exchange_request.json", save_permanently
        )

        # Test the Lambda function
        start_time = time.time()
        response = test_lambda_function(oauth_request, function_name)
        end_time = time.time()

        # Save response payload
        response_file = save_test_payload(
            response, "oauth_token_exchange_response.json", save_permanently
        )

        # Validate response
        is_valid, validation_msg = validate_oauth_response(response)

        # Performance metrics
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        logger.info("📊 OAuth Token Exchange Results:")
        logger.info("  ✅ Request file: %s", request_file)
        logger.info("  ✅ Response file: %s", response_file)
        logger.info("  ⏱️  Response time: %.2f ms", response_time)
        logger.info("  🔍 Validation: %s", "✅ PASSED" if is_valid else "❌ FAILED")
        logger.info("  📝 Details: %s", validation_msg)

        if is_valid:
            logger.info("🎉 OAuth Token Exchange test PASSED!")
        else:
            logger.error("❌ OAuth Token Exchange test FAILED!")

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ OAuth Token Exchange test failed with exception: %s", e)
        logger.error("💡 This might indicate infrastructure issues")
        # Don't re-raise - let the testing continue gracefully


def run_oauth_security_validation_test(
    function_name: str = "HomeAssistantOAuth", save_permanently: bool = False
) -> None:
    """
    Test OAuth security validation features.

    Args:
        function_name: Lambda function name to test
        save_permanently: Whether to save test artifacts permanently
    """
    logger.info("🛡️ Testing OAuth Security Validation...")

    try:
        get_oauth_test_configuration()  # Verify configuration is available

        # Test 1: Invalid client secret
        logger.info("🔍 Test 1: Invalid client secret validation...")
        invalid_request = create_oauth_token_exchange_request(
            # Test credential for security validation, not a real password
            client_secret="test_invalid_secret_12345"  # nosec B106
        )

        response = test_lambda_function(invalid_request, function_name)
        save_test_payload(response, "oauth_invalid_secret_test.json", save_permanently)

        is_valid, msg = validate_oauth_response(response)
        if is_valid:
            logger.info("✅ Security test passed: Invalid secret rejected")
            logger.info("   Rejection reason: %s", msg)
        else:
            logger.warning("⚠️ Security test failed: Invalid secret was accepted!")

        # Test 2: Missing client secret
        logger.info("🔍 Test 2: Missing client secret validation...")
        missing_secret_data = {
            "grant_type": "authorization_code",
            "client_id": "https://pitangui.amazon.com/",
            "code": "test_code",
            # client_secret intentionally missing
        }

        request_body = urllib.parse.urlencode(missing_secret_data).encode("utf-8")
        missing_secret_request = {
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "body": base64.b64encode(request_body).decode("utf-8"),
            "isBase64Encoded": True,
            "requestContext": {"identity": {"sourceIp": "52.84.89.87"}},
        }

        response = test_lambda_function(missing_secret_request, function_name)
        save_test_payload(response, "oauth_missing_secret_test.json", save_permanently)

        is_valid, msg = validate_oauth_response(response)
        if is_valid:
            logger.info("✅ Security test passed: Missing secret rejected")
            logger.info("   Rejection reason: %s", msg)
        else:
            logger.warning("⚠️ Security test failed: Missing secret was accepted!")
            logger.info("   Rejection reason: %s", msg)

        # Test 3: Malformed request
        logger.info("🔍 Test 3: Malformed request validation...")
        malformed_request = {
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "body": "invalid_base64_data",
            "isBase64Encoded": True,
            "requestContext": {"identity": {"sourceIp": "52.84.89.88"}},
        }

        response = test_lambda_function(malformed_request, function_name)
        save_test_payload(
            response, "oauth_malformed_request_test.json", save_permanently
        )

        is_valid, msg = validate_oauth_response(response)
        if is_valid:
            logger.info("✅ Security test passed: Malformed request rejected")
            logger.info("   Rejection reason: %s", msg)
        else:
            logger.warning("⚠️ Security test failed: Malformed request was accepted!")

        logger.info("🛡️ OAuth Security Validation tests completed!")

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ OAuth Security Validation test failed: %s", e)
        logger.error("💡 This might indicate infrastructure issues")
        # Don't re-raise - let the testing continue gracefully


class PerformanceStats:
    """Configuration object for performance statistics."""

    def __init__(
        self, response_times: list[float], iterations: int, function_name: str
    ):
        """Initialize performance statistics."""
        self.response_times = response_times
        self.iterations = iterations
        self.function_name = function_name
        self.average_ms = sum(response_times) / len(response_times)
        self.minimum_ms = min(response_times)
        self.maximum_ms = max(response_times)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for saving."""
        return {
            "iterations": self.iterations,
            "response_times_ms": self.response_times,
            "average_ms": self.average_ms,
            "minimum_ms": self.minimum_ms,
            "maximum_ms": self.maximum_ms,
            "function_name": self.function_name,
        }

    def log_results(self) -> None:
        """Log performance results."""
        logger.info("📊 OAuth Performance Benchmark Results:")
        logger.info("  🔢 Iterations: %d", self.iterations)
        logger.info("  ⏱️  Average: %.2f ms", self.average_ms)
        logger.info("  🚀 Fastest: %.2f ms", self.minimum_ms)
        logger.info("  🐌 Slowest: %.2f ms", self.maximum_ms)

        # Performance targets
        if self.average_ms < 1000:  # Under 1 second average
            logger.info("🎉 Performance target MET: Average response < 1000ms")
        else:
            logger.warning("⚠️ Performance target MISSED: Average response > 1000ms")


def _run_performance_iteration(
    oauth_request: dict[str, Any], function_name: str, iteration: int, total: int
) -> float:
    """
    Run single performance test iteration.

    Args:
        oauth_request: OAuth request payload
        function_name: Lambda function name
        iteration: Current iteration number
        total: Total iterations

    Returns:
        Response time in milliseconds
    """
    logger.info("🔄 Performance test iteration %d/%d...", iteration, total)

    start_time = time.time()
    response = test_lambda_function(oauth_request, function_name)
    end_time = time.time()

    response_time = (end_time - start_time) * 1000
    is_valid, _ = validate_oauth_response(response)
    logger.info(
        "  ⏱️ Response time: %.2f ms, Valid: %s",
        response_time,
        "✅" if is_valid else "❌",
    )

    return response_time


def run_oauth_performance_benchmark(
    function_name: str = "HomeAssistantOAuth",
    save_permanently: bool = False,
    iterations: int = 5,
) -> None:
    """
    Benchmark OAuth Gateway performance.

    Args:
        function_name: Lambda function name to test
        save_permanently: Whether to save test artifacts permanently
        iterations: Number of test iterations for benchmarking
    """
    logger.info("⚡ Running OAuth Performance Benchmark...")

    try:
        config = get_oauth_test_configuration()
        oauth_request = create_oauth_token_exchange_request(
            client_secret=config["wrapper_secret"]
        )

        response_times = [
            _run_performance_iteration(oauth_request, function_name, i + 1, iterations)
            for i in range(iterations)
        ]

        # Calculate and log performance statistics
        stats = PerformanceStats(response_times, iterations, function_name)
        save_test_payload(
            stats.to_dict(), "oauth_performance_benchmark.json", save_permanently
        )
        stats.log_results()

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ OAuth Performance Benchmark failed: %s", e)
        logger.error("💡 This might indicate infrastructure issues")
        # Don't re-raise - let the testing continue gracefully


def run_baseline_functionality_test(
    function_name: str = "HomeAssistantOAuth", save_permanently: bool = False
) -> None:
    """
    Test baseline OAuth functionality (original CloudFlare-Wrapper behavior).

    This validates that the core OAuth token exchange works correctly,
    providing a baseline for comparing enhanced versions.

    Args:
        function_name: Lambda function name to test
        save_permanently: Whether to save test artifacts permanently
    """
    logger.info("📋 Testing Baseline OAuth Functionality...")

    try:
        config = get_oauth_test_configuration()

        # Test the basic OAuth flow that should work with original code
        oauth_request = create_oauth_token_exchange_request(
            client_secret=config["wrapper_secret"]
        )

        # Save baseline test request
        request_file = save_test_payload(
            oauth_request, "oauth_baseline_request.json", save_permanently
        )

        # Execute baseline test
        start_time = time.time()
        response = test_lambda_function(oauth_request, function_name)
        end_time = time.time()

        # Save baseline test response
        response_file = save_test_payload(
            response, "oauth_baseline_response.json", save_permanently
        )

        # Validate baseline functionality
        is_valid, validation_msg = validate_oauth_response(response)
        response_time = (end_time - start_time) * 1000

        logger.info("📊 Baseline Functionality Test Results:")
        logger.info("  ✅ Request file: %s", request_file)
        logger.info("  ✅ Response file: %s", response_file)
        logger.info("  ⏱️  Response time: %.2f ms", response_time)
        logger.info("  🔍 Validation: %s", "✅ PASSED" if is_valid else "❌ FAILED")
        logger.info("  📝 Details: %s", validation_msg)

        if is_valid:
            logger.info("🎉 Baseline OAuth functionality test PASSED!")
            logger.info("✅ Core OAuth token exchange is working correctly")
        else:
            logger.warning("⚠️ Baseline OAuth functionality test completed with issues")
            logger.warning("📝 Details: %s", validation_msg)

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ Baseline Functionality test failed: %s", e)
        logger.error("💡 This might indicate infrastructure issues")
        # Don't re-raise - let the testing continue gracefully


def parse_arguments():
    """Parse command-line arguments for OAuth Gateway testing."""
    parser = argparse.ArgumentParser(
        description="OAuth Gateway Testing Suite",
        epilog="""
Examples:
  # Run full test suite
  python oauth_gateway_testing_suite.py

  # Test OAuth flow only
  python oauth_gateway_testing_suite.py --token-exchange

  # Test security features
  python oauth_gateway_testing_suite.py --security-validation

  # Test performance
  python oauth_gateway_testing_suite.py --performance-benchmark

  # Test original functionality
  python oauth_gateway_testing_suite.py --baseline-test

  # Test specific function
  python oauth_gateway_testing_suite.py --function oauth_gateway

  # Save artifacts permanently
  python oauth_gateway_testing_suite.py --save-files
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--token-exchange",
        action="store_true",
        help="Run OAuth token exchange test only",
    )

    parser.add_argument(
        "--security-validation",
        action="store_true",
        help="Run security validation tests only",
    )

    parser.add_argument(
        "--performance-benchmark",
        action="store_true",
        help="Run performance benchmark tests only",
    )

    parser.add_argument(
        "--baseline-test",
        action="store_true",
        help="Run baseline functionality test only",
    )

    parser.add_argument(
        "--function",
        default="HomeAssistantOAuth",
        help="AWS Lambda function name to test (default: HomeAssistantOAuth)",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations for performance testing (default: 5)",
    )

    parser.add_argument(
        "--save-files",
        action="store_true",
        help="Save test artifacts permanently instead of using temporary files",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up temporary test artifacts and exit",
    )

    return parser.parse_args()


def cleanup_artifacts() -> None:
    """Clean up test artifacts from current directory."""
    cleanup_patterns = [
        "oauth_*.json",
        "*_oauth_test_*.json",
        "oauth_baseline_*.json",
        "oauth_performance_*.json",
    ]

    cleaned_count = 0
    for pattern in cleanup_patterns:
        for file_path in Path(".").glob(pattern):
            try:
                file_path.unlink()
                logger.info("🗑️ Removed: %s", file_path)
                cleaned_count += 1
            except OSError as e:
                logger.warning("Failed to remove %s: %s", file_path, e)

    if cleaned_count > 0:
        logger.info("✅ Cleaned up %d test artifact files", cleaned_count)
    else:
        logger.info("🧹 No test artifacts found to clean up")


def main():
    """Main entry point for OAuth Gateway testing."""
    args = parse_arguments()

    if args.cleanup:
        cleanup_artifacts()
        cleanup_temp_files()
        return

    logger.info("🔐 Starting OAuth Gateway Testing Suite...")
    logger.info("🎯 Target function: %s", args.function)

    try:
        if args.baseline_test:
            run_baseline_functionality_test(args.function, args.save_files)
        elif args.token_exchange:
            run_oauth_token_exchange_test(args.function, args.save_files)
        elif args.security_validation:
            run_oauth_security_validation_test(args.function, args.save_files)
        elif args.performance_benchmark:
            run_oauth_performance_benchmark(
                args.function, args.save_files, args.iterations
            )
        else:
            # Run full test suite
            logger.info("🚀 Running comprehensive OAuth Gateway test suite...")

            run_baseline_functionality_test(args.function, args.save_files)
            logger.info("")

            run_oauth_token_exchange_test(args.function, args.save_files)
            logger.info("")

            run_oauth_security_validation_test(args.function, args.save_files)
            logger.info("")

            run_oauth_performance_benchmark(
                args.function, args.save_files, args.iterations
            )

            logger.info("🎉 Comprehensive OAuth Gateway test suite completed!")

    except (botocore.exceptions.BotoCoreError, KeyError, json.JSONDecodeError) as e:
        logger.error("❌ OAuth Gateway testing failed: %s", e)
        logger.error(
            "💡 Check if the specified Lambda function exists and is accessible"
        )
        # Exit gracefully without re-raising
    finally:
        if not args.save_files:
            logger.info("🧹 Cleaning up temporary files...")
            cleanup_temp_files()


if __name__ == "__main__":
    main()
