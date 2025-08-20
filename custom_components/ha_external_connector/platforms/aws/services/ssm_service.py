"""AWS SSM Service Module.

Service for managing AWS SSM parameters with secure string support,
hierarchical organization, and sophisticated error handling patterns.
"""

from __future__ import annotations

import asyncio
from typing import Any

from botocore.exceptions import ClientError

from .base import AWSServiceResponse, BaseAWSService
from .models import SSMResourceSpec


class SSMService(BaseAWSService):
    """Service for managing AWS SSM parameters.

    Provides comprehensive parameter management with secure string support,
    hierarchical organization, and sophisticated error handling patterns.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        super().__init__(region)
        self._boto3_clients: dict[str, Any] = {}

    def _get_boto3_client(self, service: str) -> Any:
        """Get or create a boto3 client for the specified service.

        Args:
            service: AWS service name

        Returns:
            Boto3 client instance
        """
        if service not in self._boto3_clients:
            self._boto3_clients[service] = super()._get_boto3_client(service)
        return self._boto3_clients[service]

    async def create_or_update(self, spec: SSMResourceSpec) -> AWSServiceResponse:
        """Create or update SSM parameter.

        Args:
            spec: SSM parameter specification

        Returns:
            Response containing parameter status and details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._manage_ssm_parameter, spec
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"SSM operation failed: {str(e)}"]
            )

    def _check_ssm_parameter_exists(
        self, ssm_client, parameter_name: str
    ) -> tuple[bool, str | None]:
        """Check if SSM parameter exists and return current type.

        Args:
            ssm_client: SSM client instance
            parameter_name: Name of parameter to check

        Returns:
            Tuple of (exists, current_type)
        """
        try:
            existing_param = ssm_client.get_parameter(
                Name=parameter_name, WithDecryption=True
            )
            return True, existing_param["Parameter"]["Type"]
        except ClientError as e:
            error_response = e.response.get("Error", {})
            if error_response.get("Code") == "ParameterNotFound":
                return False, None
            raise

    def _build_ssm_put_params(
        self, spec: SSMResourceSpec, parameter_exists: bool
    ) -> dict[str, Any]:
        """Build parameters for SSM put_parameter call.

        Args:
            spec: SSM parameter specification
            parameter_exists: Whether parameter already exists

        Returns:
            Parameters dictionary for put_parameter
        """
        put_params = {
            "Name": spec.parameter_name,
            "Value": spec.parameter_value,
            "Type": spec.parameter_type,
            "Overwrite": parameter_exists,
        }

        if spec.description:
            put_params["Description"] = spec.description

        # Add KMS key for SecureString parameters
        if spec.parameter_type == "SecureString":
            put_params["KeyId"] = "alias/aws/ssm"

        return put_params

    def _get_ssm_parameter_metadata(
        self, ssm_client, spec: SSMResourceSpec, response: dict[str, Any]
    ) -> dict[str, Any]:
        """Get SSM parameter metadata for response.

        Args:
            ssm_client: SSM client instance
            spec: SSM parameter specification
            response: Response from put_parameter

        Returns:
            Parameter metadata dictionary
        """
        # Get parameter details for response
        param_response = ssm_client.get_parameter(
            Name=spec.parameter_name,
            WithDecryption=False,  # Don't decrypt for metadata
        )
        param_info = param_response["Parameter"]

        # Get parameter history for version info
        history_response = ssm_client.get_parameter_history(
            Name=spec.parameter_name, MaxResults=1
        )
        latest_version = (
            history_response["Parameters"][0]["Version"]
            if history_response["Parameters"]
            else 1
        )

        return {
            "parameter_name": param_info["Name"],
            "parameter_arn": param_info["ARN"],
            "parameter_type": param_info["Type"],
            "version": response.get("Version", latest_version),
            "last_modified_date": param_info["LastModifiedDate"].isoformat(),
            "data_type": param_info.get("DataType", "text"),
            "description": spec.description or "",
        }

    def _manage_ssm_parameter(self, spec: SSMResourceSpec) -> AWSServiceResponse:
        """Manage SSM parameter creation/update.

        Args:
            spec: SSM parameter specification

        Returns:
            Parameter management response
        """
        ssm_client = self._get_boto3_client("ssm")

        try:
            # Check if parameter exists and get current type
            parameter_exists, current_type = self._check_ssm_parameter_exists(
                ssm_client, spec.parameter_name
            )

            # Determine if we need to handle type change
            type_changed = parameter_exists and current_type != spec.parameter_type

            # Build and execute put parameter request
            put_params = self._build_ssm_put_params(spec, parameter_exists)
            response = ssm_client.put_parameter(**put_params)

            # Get parameter metadata for response
            metadata = self._get_ssm_parameter_metadata(ssm_client, spec, response)

            # Add operation and type change information
            metadata.update(
                {
                    "operation": "updated" if parameter_exists else "created",
                    "type_changed": type_changed,
                }
            )

            return AWSServiceResponse(status="success", resource=metadata)

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS SSM error ({error_code}): {error_message}"],
            )

    async def read(
        self, parameter_name: str, decrypt: bool = True
    ) -> AWSServiceResponse:
        """Read SSM parameter.

        Args:
            parameter_name: Name of the parameter to read
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            Response containing parameter details
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_ssm_parameter, parameter_name, decrypt
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Read operation failed: {str(e)}"]
            )

    def _get_ssm_parameter(
        self, parameter_name: str, decrypt: bool
    ) -> AWSServiceResponse:
        """Get SSM parameter details.

        Args:
            parameter_name: Name of the parameter
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            Parameter details response
        """
        ssm_client = self._get_boto3_client("ssm")

        try:
            response = ssm_client.get_parameter(
                Name=parameter_name, WithDecryption=decrypt
            )
            param_info = response["Parameter"]

            # Get parameter metadata
            try:
                metadata_response = ssm_client.describe_parameters(
                    Filters=[{"Key": "Name", "Values": [parameter_name]}]
                )
                metadata: dict[str, Any] = (
                    metadata_response["Parameters"][0]
                    if metadata_response["Parameters"]
                    else {}
                )
            except (ClientError, IndexError):
                metadata: dict[str, Any] = {}

            return AWSServiceResponse(
                status="success",
                resource={
                    "parameter_name": param_info["Name"],
                    "parameter_arn": param_info["ARN"],
                    "parameter_type": param_info["Type"],
                    "parameter_value": (
                        param_info["Value"] if decrypt else "[ENCRYPTED]"
                    ),
                    "version": param_info["Version"],
                    "last_modified_date": param_info["LastModifiedDate"].isoformat(),
                    "data_type": param_info.get("DataType", "text"),
                    "source_result": param_info.get("SourceResult", ""),
                    "description": metadata.get("Description", ""),
                    "key_id": metadata.get("KeyId", ""),
                    "tier": metadata.get("Tier", "Standard"),
                    "policies": metadata.get("Policies", []),
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            if error_response.get("Code") == "ParameterNotFound":
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"Parameter not found: {parameter_name}"],
                )

            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS SSM error ({error_code}): {error_message}"],
            )

    async def delete(self, parameter_name: str) -> AWSServiceResponse:
        """Delete SSM parameter.

        Args:
            parameter_name: Name of the parameter to delete

        Returns:
            Deletion response
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._delete_ssm_parameter, parameter_name
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Delete operation failed: {str(e)}"]
            )

    def _delete_ssm_parameter(self, parameter_name: str) -> AWSServiceResponse:
        """Delete SSM parameter.

        Args:
            parameter_name: Name of the parameter

        Returns:
            Deletion response
        """
        ssm_client = self._get_boto3_client("ssm")

        try:
            ssm_client.delete_parameter(Name=parameter_name)

            return AWSServiceResponse(
                status="success", resource={"deleted_parameter": parameter_name}
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            if error_response.get("Code") == "ParameterNotFound":
                return AWSServiceResponse(
                    status="not_found",
                    errors=[f"Parameter not found: {parameter_name}"],
                )

            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS SSM error ({error_code}): {error_message}"],
            )

    async def list_parameters(
        self, path_prefix: str | None = None
    ) -> AWSServiceResponse:
        """List SSM parameters.

        Args:
            path_prefix: Optional path prefix to filter parameters

        Returns:
            Response containing list of parameters
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._list_ssm_parameters, path_prefix
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"List operation failed: {str(e)}"]
            )

    def _list_ssm_parameters(self, path_prefix: str | None) -> AWSServiceResponse:
        """List SSM parameters.

        Args:
            path_prefix: Optional path prefix to filter parameters

        Returns:
            List of parameters response
        """
        ssm_client = self._get_boto3_client("ssm")

        try:
            describe_params = {}

            if path_prefix:
                describe_params["ParameterFilters"] = [
                    {"Key": "Name", "Option": "BeginsWith", "Values": [path_prefix]}
                ]

            response = ssm_client.describe_parameters(**describe_params)
            parameters: list[dict[str, Any]] = []

            for param in response["Parameters"]:
                parameters.append(
                    {
                        "parameter_name": param["Name"],
                        "parameter_type": param["Type"],
                        "version": param["Version"],
                        "last_modified_date": param["LastModifiedDate"].isoformat(),
                        "data_type": param.get("DataType", "text"),
                        "description": param.get("Description", ""),
                        "key_id": param.get("KeyId", ""),
                        "tier": param.get("Tier", "Standard"),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={
                    "parameters": parameters,
                    "count": len(parameters),
                    "path_prefix": path_prefix,
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS SSM error ({error_code}): {error_message}"],
            )

    async def get_parameters_by_path(
        self, path: str, recursive: bool = True
    ) -> AWSServiceResponse:
        """Get parameters by hierarchical path.

        Args:
            path: Hierarchical path to parameters
            recursive: Whether to retrieve all parameters within the hierarchy

        Returns:
            Response containing parameters under the path
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._get_parameters_by_path, path, recursive
            )
            return result
        except ClientError as e:
            return AWSServiceResponse(
                status="error", errors=[f"Get parameters by path failed: {str(e)}"]
            )

    def _get_parameters_by_path(self, path: str, recursive: bool) -> AWSServiceResponse:
        """Get parameters by hierarchical path.

        Args:
            path: Hierarchical path to parameters
            recursive: Whether to retrieve all parameters within the hierarchy

        Returns:
            Parameters by path response
        """
        ssm_client = self._get_boto3_client("ssm")

        try:
            response = ssm_client.get_parameters_by_path(
                Path=path,
                Recursive=recursive,
                WithDecryption=False,  # Don't decrypt by default for listing
            )

            parameters: list[dict[str, Any]] = []
            for param in response["Parameters"]:
                parameters.append(
                    {
                        "parameter_name": param["Name"],
                        "parameter_arn": param["ARN"],
                        "parameter_type": param["Type"],
                        "parameter_value": (
                            "[ENCRYPTED]"
                            if param["Type"] == "SecureString"
                            else param["Value"]
                        ),
                        "version": param["Version"],
                        "last_modified_date": param["LastModifiedDate"].isoformat(),
                        "data_type": param.get("DataType", "text"),
                        "source_result": param.get("SourceResult", ""),
                    }
                )

            return AWSServiceResponse(
                status="success",
                resource={
                    "parameters": parameters,
                    "count": len(parameters),
                    "path": path,
                    "recursive": recursive,
                },
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "Unknown")
            error_message = error_response.get("Message", "Unknown error")
            return AWSServiceResponse(
                status="error",
                errors=[f"AWS SSM error ({error_code}): {error_message}"],
            )
