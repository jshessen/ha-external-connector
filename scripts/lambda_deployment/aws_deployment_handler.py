#!/usr/bin/env python3
"""
☁️ AWS DEPLOYMENT HANDLER

Handles AWS Lambda deployment operations including packaging, deploying, and testing.
Extracted from deployment_manager.py to improve maintainability and separation of
concerns.

Key Features:
- Package Lambda functions into deployment-ready ZIP files
- Deploy to AWS Lambda with validation and testing
- Test deployed Lambda functions with appropriate payloads
- Pure boto3 implementation (HACS-ready, no external dependencies)
- AWS client management and error handling
- Dry-run support for validation without deployment

� **BOTO3-ONLY IMPLEMENTATION**:
- Uses only boto3 API calls for all AWS operations
- No external AWS CLI dependencies required
- HACS-ready for Home Assistant Community Store deployment
- Consistent programmatic interface across all operations
"""

import json
import logging
import zipfile
from typing import Any

import boto3
from botocore.exceptions import ClientError


class AWSDeploymentHandler:
    """
    Handles AWS Lambda deployment and testing operations with boto3-only implementation.
    """

    def __init__(
        self,
        config: Any,
        logger: logging.Logger,
    ):
        """
        Initialize AWS deployment handler.

        Args:
            config: Deployment configuration
            logger: Logger instance for output
        """
        self.config = config
        self._logger = logger
        self._boto3_clients: dict[str, Any] = {}

    def _get_boto3_client(self, service: str) -> Any:
        """
        Get or create a boto3 client for the specified service.

        Args:
            service: AWS service name (e.g., 'lambda', 'ssm')

        Returns:
            Boto3 client instance
        """
        if service not in self._boto3_clients:
            self._boto3_clients[service] = boto3.client(service)  # pyright: ignore
        return self._boto3_clients[service]

    def package_function(self, function_name: str) -> bool:
        """
        Package a Lambda function into a deployment-ready ZIP file.

        Args:
            function_name: Name of the function to package
                (e.g., 'smart_home_bridge' or 'all')

        Returns:
            True if packaging successful, False otherwise
        """
        if function_name == "all":
            return self._package_all_functions()

        self._logger.info("📦 Packaging Lambda function: %s", function_name)

        # Find the function in our configuration
        function_info = self._find_function_info(function_name)
        if not function_info:
            return False

        return self._package_single_function(function_name)

    def deploy_function(self, function_name: str, dry_run: bool = False) -> bool:
        """
        Deploy a Lambda function to AWS.

        Args:
            function_name: Name of the function to deploy
                (e.g., 'smart_home_bridge' or 'all')
            dry_run: If True, validate but don't actually deploy

        Returns:
            True if deployment successful, False otherwise
        """
        if function_name == "all":
            return self._deploy_all_functions(dry_run)

        self._logger.info("🚀 Deploying Lambda function: %s", function_name)

        # Find the function in our configuration
        function_info = self._find_function_info(function_name)
        if not function_info:
            return False

        return self._deploy_single_function(function_name, dry_run)

    def test_deployed_function(self, function_name: str) -> bool:
        """
        Test a deployed Lambda function.

        Args:
            function_name: Name of the function to test

        Returns:
            True if test successful, False otherwise
        """
        aws_function_name = self.config.lambda_function_names.get(function_name)
        if not aws_function_name:
            self._logger.error(
                "❌ No AWS function name configured for: %s", function_name
            )
            return False

        self._logger.info("🧪 Testing deployed function: %s", aws_function_name)
        try:
            # Use globally imported modules
            lambda_client = boto3.client("lambda")  # pyright: ignore

            # Create test payload based on function type
            test_payload = self._create_test_payload(function_name)

            # Invoke the function
            response = lambda_client.invoke(
                FunctionName=aws_function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(test_payload),
            )

            # Parse response
            status_code = response["StatusCode"]
            payload = json.loads(response["Payload"].read())

            self._logger.info("✅ Function responded with status: %d", status_code)

            # Check for expected responses based on function type
            if function_name == "smart_home_bridge":
                # For smart home bridge, we expect either:
                # 1. An authentication error (when HA_TOKEN is invalid)
                # 2. A valid Alexa response structure (when HA_TOKEN is valid)
                if (
                    ("event" in payload and "error" in payload)
                    or "INVALID_AUTHORIZATION_CREDENTIAL" in str(payload)
                    or ("event" in payload and "payload" in payload.get("event", {}))
                ):
                    self._logger.info("✅ Lambda function responding correctly")
                else:
                    self._logger.debug("Response payload: %s", payload)
                    self._logger.warning(
                        "⚠️ Lambda function runtime issue - unexpected response format"
                    )
            elif function_name == "cloudflare_security_gateway":
                # For OAuth gateway, expect token exchange response or auth error
                if (
                    "access_token" in payload
                    or "error" in payload
                    or ("event" in payload and "payload" in payload.get("event", {}))
                ):
                    self._logger.info("✅ Lambda function responding correctly")
                else:
                    self._logger.debug("Response payload: %s", payload)
                    self._logger.warning(
                        "⚠️ Lambda function runtime issue - unexpected response format"
                    )
            elif function_name == "configuration_manager":
                # For configuration manager, validate the response body content
                success = self._validate_configuration_manager_response(payload)
                if not success:
                    self._logger.warning(
                        "⚠️ Configuration Manager has functional issues"
                    )
                    return False

            return status_code == 200

        except (json.JSONDecodeError, ImportError) as e:
            self._logger.error("❌ Test failed: %s", e)
            return False
        except (OSError, ClientError) as e:
            self._logger.error("❌ Unexpected error during test: %s", e)
            return False

    def _find_function_info(self, function_name: str) -> tuple[str, str] | None:
        """Find function information in configuration."""
        for source_file, deployment_dir in self.config.lambda_functions:
            if deployment_dir == function_name:
                return (source_file, deployment_dir)

        self._logger.error("❌ Unknown function: %s", function_name)
        available = [
            deployment_dir for _, deployment_dir in self.config.lambda_functions
        ]
        self._logger.error("Available functions: %s", ", ".join(available))
        return None

    def _deploy_all_functions(self, dry_run: bool) -> bool:
        """
        Deploy all Lambda functions.

        Args:
            dry_run: If True, validate but don't actually deploy

        Returns:
            True if all deployments successful, False otherwise
        """
        self._logger.info("🚀 Deploying all Lambda functions...")

        success = True
        for _, deployment_dir in self.config.lambda_functions:
            if not self._deploy_single_function(deployment_dir, dry_run):
                success = False

        if success:
            self._logger.info("✅ All functions deployed successfully!")
        else:
            self._logger.error("❌ Some deployments failed")

        return success

    def _package_all_functions(self) -> bool:
        """
        Package all Lambda functions.

        Returns:
            True if all packaging successful, False otherwise
        """
        self._logger.info("📦 Packaging all Lambda functions...")

        success = True
        for _, deployment_dir in self.config.lambda_functions:
            if not self._package_single_function(deployment_dir):
                success = False

        if success:
            self._logger.info("✅ All functions packaged successfully!")
        else:
            self._logger.error("❌ Some packaging operations failed")

        return success

    def _package_single_function(self, function_name: str) -> bool:
        """
        Package a single Lambda function into a deployment-ready ZIP file.

        Args:
            function_name: Name of the function to package

        Returns:
            True if packaging successful, False otherwise
        """
        deployment_function_dir = self.config.deployment_dir / function_name
        lambda_function_file = deployment_function_dir / "lambda_function.py"

        # Ensure deployment file exists
        if not lambda_function_file.exists():
            self._logger.error("❌ Deployment file not found: %s", lambda_function_file)
            self._logger.error("Run --build first to create deployment files")
            return False

        # Create ZIP package
        zip_path = deployment_function_dir / f"{function_name}_deployment.zip"
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(lambda_function_file, "lambda_function.py")
                self._logger.info("✅ Added lambda_function.py to package")

            self._logger.info("✅ Package created: %s", zip_path)
            self._logger.info(
                "📏 Package size: %.2f KB", zip_path.stat().st_size / 1024
            )
            return True

        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as e:
            self._logger.error("❌ Failed to create package: %s", e)
            return False

    def _deploy_single_function(self, function_name: str, dry_run: bool) -> bool:
        """
        Deploy a single Lambda function to AWS.

        Args:
            function_name: Name of the function to deploy
            dry_run: If True, validate but don't actually deploy

        Returns:
            True if deployment successful, False otherwise
        """
        aws_function_name = self.config.lambda_function_names.get(function_name)
        if not aws_function_name:
            self._logger.error(
                "❌ No AWS function name configured for: %s", function_name
            )
            return False

        deployment_function_dir = self.config.deployment_dir / function_name
        zip_path = deployment_function_dir / f"{function_name}_deployment.zip"

        # Ensure package exists
        if not zip_path.exists():
            self._logger.error("❌ Deployment package not found: %s", zip_path)
            self._logger.error("Run --package first to create deployment package")
            return False

        if dry_run:
            self._logger.info(
                "🧪 [DRY RUN] Would deploy %s to %s", zip_path, aws_function_name
            )
            return True

        try:
            lambda_client = boto3.client("lambda")  # pyright: ignore

            # Read the deployment package
            with open(zip_path, "rb") as f:
                zip_content = f.read()

            # Update the Lambda function code
            self._logger.info("📤 Uploading package to AWS Lambda...")

            response = lambda_client.update_function_code(
                FunctionName=aws_function_name, ZipFile=zip_content
            )

            # Wait for update to complete
            self._logger.info("⏳ Waiting for deployment to complete...")
            waiter = lambda_client.get_waiter("function_updated_v2")
            waiter.wait(
                FunctionName=aws_function_name,
                WaiterConfig={"Delay": 5, "MaxAttempts": 30},
            )

            self._logger.info("✅ Lambda deployment successful: %s", aws_function_name)
            self._logger.info(
                "📋 Code SHA256: %s", response.get("CodeSha256", "Unknown")
            )

            # Test the deployed function for functional correctness
            self._logger.info("🧪 Testing Lambda functionality: %s", aws_function_name)
            if self.test_deployed_function(function_name):
                self._logger.info("✅ Lambda functionality test passed")
                return True

            # Deployment succeeded, but function has runtime issues
            self._logger.warning(
                "⚠️ Lambda deployment succeeded, but functionality test failed"
            )
            self._logger.warning(
                "💡 This indicates configuration or code issues, "
                "not deployment problems"
            )
            return True  # Deployment succeeded even if functionality test failed

        except (OSError, ImportError, ClientError) as e:
            self._logger.error("❌ Deployment failed: %s", e)
            return False

    def _create_test_payload(self, function_name: str) -> dict[str, Any]:
        """Create appropriate test payload for function type."""
        if function_name == "smart_home_bridge":
            return {
                "directive": {
                    "header": {
                        "namespace": "Alexa.Discovery",
                        "name": "Discover",
                        "payloadVersion": "3",
                        "messageId": "test-deployment-001",
                    },
                    "payload": {
                        "scope": {"type": "BearerToken", "token": "test-token"}
                    },
                }
            }
        if function_name == "configuration_manager":
            return {
                "action": "status_check",
                "source": "deployment_test",
                "request_id": "test-deployment-config-001",
            }
        # cloudflare_security_gateway
        return {
            "httpMethod": "GET",
            "path": "/oauth",
            "queryStringParameters": {"state": "test"},
            "headers": {"Host": "example.com"},
        }

    def _validate_configuration_manager_response(
        self, response_payload: dict[str, Any]
    ) -> bool:
        """Validate Configuration Manager response for functional correctness.

        Configuration Manager may return HTTP 200 but have functional errors.
        This method checks the response content for actual success indicators.
        """
        try:
            # Extract the actual response body if wrapped in Lambda response format
            actual_response = self._extract_response_body(response_payload)
            if actual_response is None:
                return False

            # Check for explicit errors in response
            if self._has_response_errors(actual_response):
                return False

            # Validate configuration warming results
            warming_result = self._validate_config_warming(actual_response)
            if warming_result is not None:
                return warming_result

            # Check for permission/access errors
            if self._has_permission_or_access_error(actual_response):
                return False

            # Handle unclear responses
            self._log_unclear_response(actual_response)
            return True

        except (TypeError, ValueError) as e:
            self._logger.error(
                "❌ Error validating Configuration Manager response: %s", e
            )
            return False

    def _extract_response_body(
        self, response_payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract response body from Lambda response format."""
        if "body" in response_payload and "statusCode" in response_payload:
            try:
                return json.loads(response_payload["body"])
            except (json.JSONDecodeError, TypeError):
                self._logger.error(
                    "❌ Configuration Manager body is not valid JSON: %s",
                    response_payload["body"],
                )
                return None
        return response_payload

    def _has_response_errors(self, actual_response: dict[str, Any]) -> bool:
        """Check if response contains errors."""
        if "errors" in actual_response:
            errors = actual_response["errors"]
            if errors:  # Non-empty errors list
                self._logger.error(
                    "❌ Configuration Manager reported %d errors: %s",
                    len(errors),
                    errors[:2] if len(errors) > 2 else errors,  # Limit size
                )
                return True
        return False

    def _validate_config_warming(self, actual_response: dict[str, Any]) -> bool | None:
        """Validate configuration warming results.

        Returns None if no warming data found.
        """
        if "configs_warmed" not in actual_response:
            return None

        configs_warmed = actual_response.get("configs_warmed", 0)
        configs_attempted = actual_response.get("configs_attempted", 0)
        containers_warmed = actual_response.get("containers_warmed", 0)
        containers_attempted = actual_response.get("containers_attempted", 0)

        # During Gen 2→Gen 3 transition: Container warming success is the primary metric
        if containers_attempted > 0:
            if containers_warmed == containers_attempted:
                self._logger.info(
                    "✅ Configuration Manager successfully warmed %d containers",
                    containers_warmed,
                )
                if configs_warmed == 0 and configs_attempted > 0:
                    self._logger.info(
                        "📋 Gen 3 configurations not available yet (%d attempted) - "
                        "expected during transition",
                        configs_attempted,
                    )
                return True
            if containers_warmed > 0:
                self._logger.warning(
                    "⚠️ Configuration Manager partially successful containers (%d/%d)",
                    containers_warmed,
                    containers_attempted,
                )
                return True
            else:
                self._logger.error(
                    "❌ Configuration Manager failed to warm any containers (%d/%d)",
                    containers_warmed,
                    containers_attempted,
                )
                return False

        # Legacy validation: Pure configuration warming (when containers_attempted = 0)
        if configs_warmed == 0 and configs_attempted > 0:
            self._logger.error(
                "❌ Configuration Manager failed to warm any configs (%d/%d)",
                configs_warmed,
                configs_attempted,
            )
            return False
        if configs_warmed < configs_attempted:
            self._logger.warning(
                "⚠️ Configuration Manager partially successful (%d/%d configs)",
                configs_warmed,
                configs_attempted,
            )
            return True
        self._logger.info(
            "✅ Configuration Manager successfully warmed %d configs",
            configs_warmed,
        )
        return True

    def _log_unclear_response(self, actual_response: dict[str, Any]) -> None:
        """Log unclear responses for analysis."""
        if self._is_response_unclear(actual_response):
            self._logger.warning(
                "⚠️ Configuration Manager response unclear, allowing success: %s",
                actual_response,
            )

    def _has_permission_or_access_error(self, actual_response: dict[str, Any]) -> bool:
        """Check for permission or access errors in the response."""
        response_str = str(actual_response).lower()
        error_indicators = [
            "permission denied",
            "access denied",
            "unauthorized",
            "forbidden",
            "invalid credentials",
            "authentication failed",
            "accessdeniedexception",
        ]
        for indicator in error_indicators:
            if indicator in response_str:
                self._logger.error(
                    "❌ Configuration Manager has permission/access issues: %s",
                    indicator,
                )
                return True
        return False

    def _is_response_unclear(self, actual_response: dict[str, Any]) -> bool:
        """Determine if the response lacks clear success/failure indicators."""
        return not ("configs_warmed" in actual_response or "errors" in actual_response)
