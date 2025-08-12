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
- AWS client management and error handling
- Dry-run support for validation without deployment
"""

import json
import logging
import zipfile
from typing import Any

import boto3
from botocore.exceptions import ClientError


class AWSDeploymentHandler:
    """Handles AWS Lambda deployment and testing operations."""

    def __init__(self, config: Any, logger: logging.Logger):
        """
        Initialize AWS deployment handler.

        Args:
            config: Deployment configuration
            logger: Logger instance for output
        """
        self.config = config
        self._logger = logger

    def package_function(self, function_name: str) -> bool:
        """
        Package a Lambda function into a deployment-ready ZIP file.

        Args:
            function_name: Name of the function to package (e.g., 'smart_home_bridge')

        Returns:
            True if packaging successful, False otherwise
        """
        self._logger.info("📦 Packaging Lambda function: %s", function_name)

        # Find the function in our configuration
        function_info = self._find_function_info(function_name)
        if not function_info:
            return False

        _, deployment_dir = function_info
        deployment_function_dir = self.config.deployment_dir / deployment_dir
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

            # Check for expected responses
            if function_name == "smart_home_bridge":
                if (
                    "event" in payload
                    and "error" in payload
                    or "INVALID_AUTHORIZATION_CREDENTIAL" in str(payload)
                ):
                    self._logger.info("✅ Function returning expected auth errors")
                else:
                    self._logger.warning("⚠️ Unexpected response format")

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

            self._logger.info(
                "✅ Function %s deployed successfully!", aws_function_name
            )
            self._logger.info(
                "📋 Code SHA256: %s", response.get("CodeSha256", "Unknown")
            )

            # Test the deployed function
            if self.test_deployed_function(function_name):
                self._logger.info("✅ Deployment test passed")
                return True
            self._logger.warning("⚠️ Deployment test failed, but function was deployed")
            return True  # Deployment succeeded even if test failed

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
        # oauth_gateway
        return {
            "httpMethod": "GET",
            "path": "/oauth",
            "queryStringParameters": {"state": "test"},
            "headers": {"Host": "example.com"},
        }
