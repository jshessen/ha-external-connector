"""AWS Lambda Service Module.

Service for managing AWS Lambda functions with sophisticated packaging,
deployment, and testing capabilities.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import zipfile
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError

from .base import AWSServiceResponse, BaseAWSService
from .models import LambdaResourceSpec


class LambdaService(BaseAWSService):
    """Service for managing AWS Lambda functions.

    Integrated from development/scripts/lambda_deployment/aws_deployment_handler.py
    with sophisticated packaging, deployment, and testing capabilities.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        super().__init__(region)
        self._boto3_clients: dict[str, Any] = {}

    def _get_boto3_client(self, service: str) -> Any:
        """Get or create a boto3 client for the specified service.

        Args:
            service: AWS service name (e.g., 'lambda', 'ssm')

        Returns:
            Boto3 client instance
        """
        if service not in self._boto3_clients:
            self._boto3_clients[service] = super()._get_boto3_client(service)
        return self._boto3_clients[service]

    async def create_or_update(self, spec: LambdaResourceSpec) -> AWSServiceResponse:
        """Create or update Lambda function.

        Args:
            spec: Lambda resource specification

        Returns:
            Response containing deployment status and details
        """
        try:
            # Execute deployment in executor to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.deploy_lambda_function, spec
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    def deploy_lambda_function(self, spec: LambdaResourceSpec) -> AWSServiceResponse:
        """Deploy Lambda function using sophisticated deployment patterns.

        Adapted from AWSDeploymentHandler with async integration.

        Args:
            spec: Lambda resource specification

        Returns:
            Deployment response with status and details
        """
        lambda_client = self._get_boto3_client("lambda")

        try:
            # Check if function exists
            try:
                lambda_client.get_function(FunctionName=spec.function_name)
                function_exists = True
            except ClientError as e:
                error_response = e.response.get("Error", {})
                if error_response.get("Code") == "ResourceNotFoundException":
                    function_exists = False
                else:
                    raise

            # Read deployment package
            package_path = Path(spec.package_path)
            if not package_path.exists():
                return AWSServiceResponse(
                    status="error", errors=[f"Package not found: {spec.package_path}"]
                )

            with open(package_path, "rb") as package_file:
                zip_content = package_file.read()

            if function_exists:
                # Update existing function
                response = lambda_client.update_function_code(
                    FunctionName=spec.function_name, ZipFile=zip_content
                )

                # Update configuration if needed
                lambda_client.update_function_configuration(
                    FunctionName=spec.function_name,
                    Runtime=spec.runtime,
                    Handler=spec.handler,
                    Role=spec.role_arn,
                    Timeout=spec.timeout,
                    MemorySize=spec.memory_size,
                    Description=spec.description or "",
                    Environment={"Variables": spec.environment_variables or {}},
                )
            else:
                # Create new function
                response = lambda_client.create_function(
                    FunctionName=spec.function_name,
                    Runtime=spec.runtime,
                    Role=spec.role_arn,
                    Handler=spec.handler,
                    Code={"ZipFile": zip_content},
                    Description=spec.description or "",
                    Timeout=spec.timeout,
                    MemorySize=spec.memory_size,
                    Environment={"Variables": spec.environment_variables or {}},
                )

            # Create function URL if requested
            function_url = None
            if spec.create_url:
                try:
                    url_response = lambda_client.create_function_url_config(
                        FunctionName=spec.function_name, AuthType=spec.url_auth_type
                    )
                    function_url = url_response["FunctionUrl"]
                except ClientError as e:
                    error_response = e.response.get("Error", {})
                    if error_response.get("Code") != "ResourceConflictException":
                        raise

            return AWSServiceResponse(
                status="success",
                resource={
                    "function_name": response["FunctionName"],
                    "function_arn": response["FunctionArn"],
                    "function_url": function_url,
                    "runtime": response["Runtime"],
                    "handler": response["Handler"],
                    "last_modified": response["LastModified"],
                    "state": response.get("State", "Active"),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    async def read(self, function_name: str) -> AWSServiceResponse:
        """Read Lambda function configuration.

        Args:
            function_name: Name of the function to read

        Returns:
            Response containing function details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.get_lambda_function, function_name
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(status="error", errors=[f"Read failed: {str(e)}"])

    def get_lambda_function(self, function_name: str) -> AWSServiceResponse:
        """Get Lambda function details.

        Args:
            function_name: Name of the function

        Returns:
            Function details response
        """
        lambda_client = self._get_boto3_client("lambda")

        try:
            response = lambda_client.get_function(FunctionName=function_name)
            function_config = response["Configuration"]

            # Try to get function URL
            function_url = None
            try:
                url_response = lambda_client.get_function_url_config(
                    FunctionName=function_name
                )
                function_url = url_response["FunctionUrl"]
            except ClientError:
                pass  # No URL configured

            return AWSServiceResponse(
                status="success",
                resource={
                    "function_name": function_config["FunctionName"],
                    "function_arn": function_config["FunctionArn"],
                    "function_url": function_url,
                    "runtime": function_config["Runtime"],
                    "handler": function_config["Handler"],
                    "role": function_config["Role"],
                    "timeout": function_config["Timeout"],
                    "memory_size": function_config["MemorySize"],
                    "description": function_config.get("Description", ""),
                    "last_modified": function_config["LastModified"],
                    "state": function_config.get("State", "Active"),
                    "environment": function_config.get("Environment", {}).get(
                        "Variables", {}
                    ),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            if (
                error_response.get("Code", "ResourceNotFoundException")
                == "ResourceNotFoundException"
            ):
                return AWSServiceResponse(
                    status="not_found", errors=[f"Function not found: {function_name}"]
                )
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS error ({error_code}): {error_message}"],
            )

    async def delete(self, function_name: str) -> AWSServiceResponse:
        """Delete Lambda function.

        Args:
            function_name: Name of the function to delete

        Returns:
            Deletion response
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._delete_lambda_function, function_name
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    def _delete_lambda_function(self, function_name: str) -> AWSServiceResponse:
        """Delete Lambda function.

        Args:
            function_name: Name of the function

        Returns:
            Deletion response
        """
        lambda_client = self._get_boto3_client("lambda")

        try:
            # Delete function URL if it exists
            with contextlib.suppress(ClientError):
                lambda_client.delete_function_url_config(FunctionName=function_name)

            # Delete function
            lambda_client.delete_function(FunctionName=function_name)

            return AWSServiceResponse(
                status="success", resource={"deleted_function": function_name}
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                return AWSServiceResponse(
                    status="not_found", errors=[f"Function not found: {function_name}"]
                )
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS error ({error_code}): {error_message}"],
            )

    async def list_functions(self) -> AWSServiceResponse:
        """List Lambda functions.

        Returns:
            Response containing list of functions
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._list_lambda_functions
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    def _list_lambda_functions(self) -> AWSServiceResponse:
        """List Lambda functions.

        Returns:
            List of functions response
        """
        lambda_client = self._get_boto3_client("lambda")

        try:
            response = lambda_client.list_functions()
            functions: list[dict[str, Any]] = []

            for func in response["Functions"]:
                functions.append(
                    {
                        "function_name": func["FunctionName"],
                        "function_arn": func["FunctionArn"],
                        "runtime": func["Runtime"],
                        "handler": func["Handler"],
                        "role": func["Role"],
                        "timeout": func["Timeout"],
                        "memory_size": func["MemorySize"],
                        "description": func.get("Description", ""),
                        "last_modified": func["LastModified"],
                        "state": func.get("State", "Active"),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={"functions": functions, "count": len(functions)},
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    async def test_function(
        self, function_name: str, payload: dict[str, Any] | None = None
    ) -> AWSServiceResponse:
        """Test a deployed Lambda function.

        Adapted from AWSDeploymentHandler testing patterns.

        Args:
            function_name: Name of the function to test
            payload: Test payload (auto-generated if None)

        Returns:
            Test response with results
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._test_lambda_function, function_name, payload
            )
            return result
        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", str(e))
            return AWSServiceResponse(
                status="error", errors=[f"AWS error ({error_code}): {error_message}"]
            )

    def _test_lambda_function(
        self, function_name: str, payload: dict[str, Any] | None = None
    ) -> AWSServiceResponse:
        """Test Lambda function with appropriate payload.

        Args:
            function_name: Name of the function
            payload: Test payload

        Returns:
            Test results response
        """
        lambda_client = self._get_boto3_client("lambda")

        try:
            # Create test payload if not provided
            if payload is None:
                payload = self._create_test_payload(function_name)

            # Invoke the function
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            # Parse response
            status_code = response["StatusCode"]
            response_payload = json.loads(response["Payload"].read())

            # Validate response based on function type
            validation_result = self._validate_function_response(
                function_name, response_payload
            )

            return AWSServiceResponse(
                status=(
                    "success" if status_code == 200 and validation_result else "warning"
                ),
                resource={
                    "status_code": status_code,
                    "payload": response_payload,
                    "validation_passed": validation_result,
                    "function_name": function_name,
                },
                errors=[] if validation_result else ["Response validation failed"],
            )

        except (json.JSONDecodeError, ClientError) as e:
            return AWSServiceResponse(
                status="error", errors=[f"Test execution failed: {str(e)}"]
            )

    def _create_test_payload(self, function_name: str) -> dict[str, Any]:
        """Create appropriate test payload for function type.

        Adapted from AWSDeploymentHandler test payload patterns.

        Args:
            function_name: Name of the function

        Returns:
            Test payload dictionary
        """
        # Default test payload
        base_payload = {
            "test": True,
            "timestamp": "2025-08-19T12:00:00Z",
            "source": "ha_external_connector_test",
        }

        # Function-specific payloads based on AWSDeploymentHandler patterns
        if "smart_home" in function_name.lower() or "bridge" in function_name.lower():
            return {
                **base_payload,
                "directive": {
                    "header": {
                        "namespace": "Alexa.Discovery",
                        "name": "Discover",
                        "payloadVersion": "3",
                        "messageId": "test-message-id",
                    },
                    "payload": {
                        "scope": {"type": "BearerToken", "token": "test-token"}
                    },
                },
            }
        if "cloudflare" in function_name.lower() or "gateway" in function_name.lower():
            return {
                **base_payload,
                "code": "test_auth_code",
                "state": "test_state_value",
            }
        if (
            "configuration" in function_name.lower()
            or "config" in function_name.lower()
        ):
            return {**base_payload, "action": "get_config", "parameters": {}}
        return base_payload

    def _validate_function_response(
        self, function_name: str, payload: dict[str, Any]
    ) -> bool:
        """Validate function response based on type.

        Adapted from AWSDeploymentHandler validation patterns.

        Args:
            function_name: Name of the function
            payload: Response payload

        Returns:
            True if validation passes, False otherwise
        """
        try:
            if (
                "smart_home" in function_name.lower()
                or "bridge" in function_name.lower()
            ):
                # For smart home bridge, expect Alexa response structure or auth error
                return (
                    ("event" in payload and "error" in payload)
                    or "INVALID_AUTHORIZATION_CREDENTIAL" in str(payload)
                    or ("event" in payload and "payload" in payload.get("event", {}))
                )
            if (
                "cloudflare" in function_name.lower()
                or "gateway" in function_name.lower()
            ):
                # For OAuth gateway, expect token exchange response or auth error
                return (
                    "access_token" in payload
                    or "error" in payload
                    or ("event" in payload and "payload" in payload.get("event", {}))
                )
            if (
                "configuration" in function_name.lower()
                or "config" in function_name.lower()
            ):
                # For configuration manager, expect config data or error
                return (
                    "config" in payload
                    or "configuration" in payload
                    or "error" in payload
                    or payload.get("statusCode") == 200
                )
            # Generic validation - check for basic response structure
            return isinstance(payload, dict) and len(payload) > 0

        except json.JSONDecodeError:
            return False
        except ClientError:
            return False

    async def package_function(
        self, function_path: str, output_path: str
    ) -> AWSServiceResponse:
        """Package Lambda function into deployment-ready ZIP file.

        Adapted from AWSDeploymentHandler packaging patterns.

        Args:
            function_path: Path to function directory
            output_path: Path for output ZIP file

        Returns:
            Packaging response
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._package_lambda_function, function_path, output_path
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Packaging failed: {str(e)}"]
            )

    def _package_lambda_function(
        self, function_path: str, output_path: str
    ) -> AWSServiceResponse:
        """Package Lambda function into ZIP file.

        Args:
            function_path: Path to function directory
            output_path: Path for output ZIP file

        Returns:
            Packaging response
        """
        try:
            function_dir = Path(function_path)
            output_zip = Path(output_path)

            if not function_dir.exists():
                return AWSServiceResponse(
                    status="error",
                    errors=[f"Function directory not found: {function_path}"],
                )

            # Ensure output directory exists
            output_zip.parent.mkdir(parents=True, exist_ok=True)

            # Create ZIP package
            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in function_dir.rglob("*"):
                    if file_path.is_file():
                        # Calculate relative path for ZIP archive
                        arc_name = file_path.relative_to(function_dir)
                        zipf.write(file_path, arc_name)

            # Verify ZIP was created
            if not output_zip.exists():
                return AWSServiceResponse(
                    status="error", errors=["Failed to create ZIP package"]
                )

            zip_size = output_zip.stat().st_size
            return AWSServiceResponse(
                status="success",
                resource={
                    "package_path": str(output_zip),
                    "package_size": zip_size,
                    "function_path": str(function_dir),
                },
            )

        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Packaging error: {str(e)}"]
            )
