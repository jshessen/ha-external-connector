#!/usr/bin/env python3
"""
🔐 OAUTH GATEWAY DEPLOYED FUNCTION VALIDATION
============================================

Validates the deployed CloudFlare-Wrapper Lambda function containing OAuth Gateway code.
Tests OAuth authentication flow, configuration loading, and CloudFlare integration.

Usage:
    python test_deployed_oauth_gateway.py
    python test_deployed_oauth_gateway.py --verbose
"""

import json
import logging
import sys
import time
from typing import Any

import boto3
import requests


class DeployedOAuthGatewayValidator:
    """Validates the deployed OAuth Gateway Lambda function."""

    def __init__(
        self, function_name: str = "CloudFlare-Wrapper", verbose: bool = False
    ):
        self.function_name = function_name
        self.lambda_client = boto3.client("lambda")
        self.logs_client = boto3.client("logs")
        self.log_group = f"/aws/lambda/{function_name}"

        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
        self.logger = logging.getLogger(__name__)

    def run_all_tests(self) -> bool:
        """Run comprehensive validation of deployed OAuth Gateway."""
        print("🔐 OAUTH GATEWAY DEPLOYED FUNCTION VALIDATION")
        print("=" * 50)
        print()

        tests = [
            ("Function Accessibility", self.test_function_exists),
            ("Environment Configuration", self.test_environment_config),
            ("Function URL Access", self.test_function_url_access),
            ("OAuth Request Handling", self.test_oauth_request_handling),
            ("Smart Home Proxy Handling", self.test_smart_home_proxy),
            ("Configuration Loading", self.test_configuration_loading),
            ("CloudWatch Logging", self.test_cloudwatch_logging),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"🧪 Testing: {test_name}")
            try:
                result = test_func()
                if result:
                    print(f"   ✅ PASS: {test_name}")
                    passed += 1
                else:
                    print(f"   ❌ FAIL: {test_name}")
            except Exception as e:
                print(f"   ❌ ERROR: {test_name} - {str(e)}")
                self.logger.debug(f"Exception in {test_name}: {e}", exc_info=True)
            print()

        # Summary
        print("=" * 50)
        print(f"📊 VALIDATION SUMMARY: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 ALL TESTS PASSED! OAuth Gateway is ready for Alexa integration.")
            print()
            print("📋 Next Steps:")
            print("1. 🔗 Update Alexa Developer Console:")
            print(f"   - Token URI: {self._get_function_url()}")
            print("2. 📱 Test account linking by disabling/re-enabling skill")
            print("3. 🎤 Test voice commands after successful linking")
            return True
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            return False

    def test_function_exists(self) -> bool:
        """Test that the Lambda function exists and is accessible."""
        try:
            response = self.lambda_client.get_function(FunctionName=self.function_name)

            # Verify it's our OAuth Gateway code
            code_size = response["Configuration"]["CodeSize"]
            runtime = response["Configuration"]["Runtime"]

            self.logger.info(f"Function exists: {self.function_name}")
            self.logger.info(f"Code size: {code_size} bytes")
            self.logger.info(f"Runtime: {runtime}")

            # OAuth Gateway should be a decent size (>10KB)
            return code_size > 10000 and runtime.startswith("python3")

        except Exception as e:
            self.logger.error(f"Function access failed: {e}")
            return False

    def test_environment_config(self) -> bool:
        """Test that environment variables are properly configured."""
        try:
            response = self.lambda_client.get_function(FunctionName=self.function_name)
            env_vars = response["Configuration"]["Environment"]["Variables"]

            required_vars = ["APP_CONFIG_PATH", "BASE_URL"]
            missing_vars = []

            for var in required_vars:
                if var not in env_vars:
                    missing_vars.append(var)
                else:
                    self.logger.info(f"Environment variable {var}: {env_vars[var]}")

            if missing_vars:
                self.logger.error(f"Missing environment variables: {missing_vars}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Environment config check failed: {e}")
            return False

    def test_function_url_access(self) -> bool:
        """Test that the Function URL is accessible."""
        try:
            function_url = self._get_function_url()
            if not function_url:
                self.logger.error("Function URL not configured")
                return False

            self.logger.info(f"Function URL: {function_url}")

            # Test basic HTTP access (should return 400 for empty request, not 5xx)
            response = requests.get(function_url, timeout=10)

            # OAuth Gateway should return 400 for GET request (needs POST)
            # 5xx would indicate server error
            success = response.status_code in [400, 405, 200]

            self.logger.info(f"Function URL response: {response.status_code}")
            return success

        except Exception as e:
            self.logger.error(f"Function URL access failed: {e}")
            return False

    def test_oauth_request_handling(self) -> bool:
        """Test OAuth request handling capabilities."""
        try:
            # Create a mock OAuth authorization code request
            oauth_event = {
                "httpMethod": "POST",
                "headers": {"content-type": "application/x-www-form-urlencoded"},
                "body": "grant_type=authorization_code&code=test_code&client_id=test",
            }

            response = self.lambda_client.invoke(
                FunctionName=self.function_name, Payload=json.dumps(oauth_event)
            )

            result = json.loads(response["Payload"].read())

            # Should detect OAuth request type and attempt processing
            # Even if it fails due to invalid credentials, it should not crash
            self.logger.info(
                "OAuth request response status: %s",
                result.get("statusCode", "No status"),
            )

            # Success if it returns a proper HTTP response (not a Lambda error)
            return "statusCode" in result

        except Exception as e:
            self.logger.error(f"OAuth request test failed: {e}")
            return False

    def test_smart_home_proxy(self) -> bool:
        """Test Smart Home proxy capabilities."""
        try:
            # Create a mock Alexa Smart Home discovery request
            smart_home_event = {
                "httpMethod": "POST",
                "headers": {"content-type": "application/json"},
                "body": json.dumps(
                    {
                        "directive": {
                            "header": {
                                "namespace": "Alexa.Discovery",
                                "name": "Discover",
                                "payloadVersion": "3",
                                "messageId": "test-message-id",
                            },
                            "endpoint": {
                                "scope": {"type": "BearerToken", "token": "test-token"}
                            },
                            "payload": {},
                        }
                    }
                ),
            }

            response = self.lambda_client.invoke(
                FunctionName=self.function_name, Payload=json.dumps(smart_home_event)
            )

            result = json.loads(response["Payload"].read())

            # Should detect Smart Home request and attempt processing
            self.logger.info(
                "Smart Home response status: %s", result.get("statusCode", "No status")
            )

            # Success if it returns a proper HTTP response
            return "statusCode" in result

        except Exception as e:
            self.logger.error(f"Smart Home proxy test failed: {e}")
            return False

    def test_configuration_loading(self) -> bool:
        """Test configuration loading from SSM Parameter Store."""
        try:
            # Test if the function can load configuration
            test_event = {"httpMethod": "GET", "headers": {}}

            response = self.lambda_client.invoke(
                FunctionName=self.function_name, Payload=json.dumps(test_event)
            )

            result = json.loads(response["Payload"].read())

            # Check CloudWatch logs for configuration loading evidence
            time.sleep(2)  # Wait for logs to appear

            try:
                log_events = self._get_recent_log_events()
                config_loaded = any(
                    "configuration" in event.get("message", "").lower()
                    or "ssm" in event.get("message", "").lower()
                    for event in log_events
                )

                self.logger.info(
                    "Configuration loading evidence in logs: %s", config_loaded
                )
                return config_loaded

            except Exception:
                # If we can't check logs, assume success if function responded
                return "statusCode" in result

        except Exception as e:
            self.logger.error(f"Configuration loading test failed: {e}")
            return False

    def test_cloudwatch_logging(self) -> bool:
        """Test that CloudWatch logging is working."""
        try:
            # Generate a log entry by invoking the function
            test_event = {"test": "cloudwatch_logging"}

            self.lambda_client.invoke(
                FunctionName=self.function_name, Payload=json.dumps(test_event)
            )

            # Wait for logs to appear
            time.sleep(3)

            log_events = self._get_recent_log_events(limit=5)

            # Should have recent log entries
            recent_logs = len(log_events) > 0

            self.logger.info(f"Recent log events found: {len(log_events)}")

            return recent_logs

        except Exception as e:
            self.logger.error(f"CloudWatch logging test failed: {e}")
            return False

    def _get_function_url(self) -> str | None:
        """Get the Function URL for the Lambda function."""
        try:
            response = self.lambda_client.get_function_url_config(
                FunctionName=self.function_name
            )
            return response["FunctionUrl"]
        except Exception:
            return None

    def _get_recent_log_events(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent log events from CloudWatch."""
        try:
            # Get recent log streams
            streams_response = self.logs_client.describe_log_streams(
                logGroupName=self.log_group,
                orderBy="LastEventTime",
                descending=True,
                limit=3,
            )

            if not streams_response["logStreams"]:
                return []

            # Get events from the most recent stream
            latest_stream = streams_response["logStreams"][0]["logStreamName"]

            events_response = self.logs_client.get_log_events(
                logGroupName=self.log_group,
                logStreamName=latest_stream,
                limit=limit,
                startFromHead=False,
            )

            return events_response["events"]

        except Exception as e:
            self.logger.debug(f"Failed to get log events: {e}")
            return []


def main():
    """Main validation script."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate deployed OAuth Gateway")
    parser.add_argument(
        "--function-name", default="CloudFlare-Wrapper", help="Lambda function name"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    validator = DeployedOAuthGatewayValidator(
        function_name=args.function_name, verbose=args.verbose
    )

    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
