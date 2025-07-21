"""
AWS Resource Manager - Pure JSON CRUD interface over AWS resources.

Modern Python implementation for AWS resource management.
"""

# http://github.com/microsoft/pyright/issues/698
# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false

from __future__ import annotations

from enum import Enum
from typing import Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from mypy_boto3_iam import IAMClient
from mypy_boto3_sts import STSClient
from pydantic import BaseModel, Field

# Local imports
from ..utils import HAConnectorLogger, ValidationError, assert_never

# Global instance storage for backwards compatibility
_global_managers: dict[str, AWSResourceManager] = {}


def get_aws_manager(region: str = "us-east-1") -> AWSResourceManager:
    """Get or create global AWS resource manager instance"""
    if region not in _global_managers:
        _global_managers[region] = AWSResourceManager(region)
    return _global_managers[region]


class AWSResourceResponse(BaseModel):
    """Response model for AWS resource operations."""

    status: str
    resource: Any = None
    errors: list[str] = []


# --- Base Manager ---
class AWSBaseManager:
    """Base class for AWS resource managers."""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.logger = HAConnectorLogger(self.__class__.__name__)


class AWSResourceType(str, Enum):
    """Enumeration of supported AWS resource types."""

    LAMBDA = "lambda"
    IAM = "iam"
    SSM = "ssm"
    LOGS = "logs"
    TRIGGER = "trigger"


class LambdaResourceSpec(BaseModel):
    """Specification model for AWS Lambda resources."""

    function_name: str = Field(..., description="Name of the Lambda function")
    runtime: str = Field(default="python3.11", description="Runtime environment")
    handler: str = Field(
        ..., description="Handler function (e.g., index.lambda_handler)"
    )
    role_arn: str = Field(..., description="IAM role ARN for the function")
    package_path: str = Field(..., description="Path to the deployment package")
    create_url: bool = Field(
        default=False, description="Whether to create function URL"
    )
    url_auth_type: str = Field(default="NONE", description="Function URL auth type")
    timeout: int = Field(default=30, description="Function timeout in seconds")
    memory_size: int = Field(default=128, description="Memory size in MB")
    description: str | None = Field(None, description="Function description")
    environment_variables: dict[str, str] | None = Field(
        None, description="Environment variables"
    )


class IAMResourceSpec(BaseModel):
    """Specification model for AWS IAM resources."""

    resource_type: str = Field(..., description="Type of IAM resource (role, policy)")
    name: str = Field(..., description="Name of the IAM resource")
    assume_role_policy: dict[str, Any] | None = Field(
        None, description="Trust policy for roles"
    )
    policy_document: dict[str, Any] | None = Field(None, description="Policy document")
    description: str | None = Field(None, description="Resource description")


# --- SSM ResourceSpec and Manager (move after base classes and AWSResourceResponse) ---

# ...existing code...

# Place SSMResourceSpec and AWSSSMManager after AWSResourceResponse definition

# ...existing code...


# --- SSM Parameter Spec and Manager ---


# --- SSM Parameter Spec ---
class SSMResourceSpec(BaseModel):
    """Specification model for AWS SSM resources."""

    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Parameter value")
    parameter_type: str = Field(default="String", description="Parameter type")


# --- Manager Stubs (to avoid NameError) ---


class AWSLambdaManager(AWSBaseManager):
    """Manager for AWS Lambda resources (placeholder)."""

    def create_or_update(self, _spec: LambdaResourceSpec) -> AWSResourceResponse:
        """Stub: Create or update Lambda resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def read(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Read Lambda resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def delete(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Delete Lambda resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])


class AWSSSMManager(AWSBaseManager):
    """Manager for AWS SSM resources (placeholder)."""

    def create_or_update(self, _spec: SSMResourceSpec) -> AWSResourceResponse:
        """Stub: Create or update SSM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def read(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Read SSM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def delete(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Delete SSM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])


# --- Logs Resource Spec ---
class LogsResourceSpec(BaseModel):
    """Specification model for AWS CloudWatch Logs resources."""

    log_group_name: str = Field(..., description="Log group name")
    retention_days: int = Field(default=14, description="Retention in days")


class AWSIAMManager(AWSBaseManager):
    """Manager for AWS IAM resources (placeholder)."""

    def __init__(self, region: str = "us-east-1") -> None:
        super().__init__(region)
        self.client: IAMClient = boto3.client(  # type: ignore[arg-type]
            "iam", region_name=region
        )

    def create_or_update(self, _spec: IAMResourceSpec) -> AWSResourceResponse:
        """Stub: Create or update IAM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def read(
        self, _resource_id: str, _resource_type: str = "role"
    ) -> AWSResourceResponse:
        """Stub: Read IAM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def delete(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Delete IAM resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])


class AWSLogsManager(AWSBaseManager):
    """Manager for AWS CloudWatch Logs resources (placeholder)."""

    def create_or_update(self, _spec: LogsResourceSpec) -> AWSResourceResponse:
        """Stub: Create or update CloudWatch Logs resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def read(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Read CloudWatch Logs resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])

    def delete(self, _resource_id: str) -> AWSResourceResponse:
        """Stub: Delete CloudWatch Logs resource"""
        return AWSResourceResponse(status="not_implemented", errors=["Not implemented"])


class AWSTriggerManager(AWSBaseManager):
    """Manager for AWS trigger resources (placeholder)."""

    def create_or_update(self, _spec: dict[str, Any]) -> AWSResourceResponse:
        """Create or update trigger (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented",
            errors=["Trigger resource creation not implemented"],
        )

    def read(self, _trigger_id: str) -> AWSResourceResponse:
        """Read trigger (placeholder)"""
        return AWSResourceResponse(
            status="success", errors=["Trigger resource reading not implemented"]
        )

    def delete(self, _trigger_id: str) -> AWSResourceResponse:
        """Delete trigger (placeholder)"""
        return AWSResourceResponse(
            status="not_implemented", errors=["Trigger delete not implemented"]
        )


class AWSResourceManager:
    """
    Main AWS resource manager providing CRUD operations for AWS resources.

    This class serves as the primary interface for managing AWS resources
    including Lambda functions, IAM roles, SSM parameters, CloudWatch logs,
    and event triggers.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        self.region: str = region
        self.logger: HAConnectorLogger = HAConnectorLogger("aws_resource_manager")

        # Initialize resource managers
        self.lambda_manager: AWSLambdaManager = AWSLambdaManager(region)
        self.iam_manager: AWSIAMManager = AWSIAMManager(region)
        self.ssm_manager: AWSSSMManager = AWSSSMManager(region)
        self.logs_manager: AWSLogsManager = AWSLogsManager(region)
        self.trigger_manager: AWSTriggerManager = AWSTriggerManager(region)

    def create_resource(
        self, resource_type: AWSResourceType, resource_spec: dict[str, Any]
    ) -> AWSResourceResponse:
        """Create a resource based on type and specification"""
        try:
            # Resource type handlers mapping
            handlers = {
                AWSResourceType.LAMBDA: lambda: self.lambda_manager.create_or_update(
                    LambdaResourceSpec(**resource_spec)
                ),
                AWSResourceType.IAM: lambda: self.iam_manager.create_or_update(
                    IAMResourceSpec(**resource_spec)
                ),
                AWSResourceType.SSM: lambda: self.ssm_manager.create_or_update(
                    SSMResourceSpec(**resource_spec)
                ),
                AWSResourceType.LOGS: lambda: self.logs_manager.create_or_update(
                    LogsResourceSpec(**resource_spec)
                ),
                AWSResourceType.TRIGGER: lambda: self.trigger_manager.create_or_update(
                    resource_spec
                ),
            }

            handler = handlers.get(resource_type)
            if handler:
                return handler()

            # This should never happen with current enum
            assert_never(resource_type)
        except ValidationError as e:
            return AWSResourceResponse(
                status="error", errors=[f"Invalid resource specification: {str(e)}"]
            )
        except (ImportError, TypeError, ValueError) as e:
            self.logger.error(f"Resource creation failed for {resource_type}: {str(e)}")
            return AWSResourceResponse(
                status="error", errors=[f"Resource creation failed: {str(e)}"]
            )

    def read_resource(
        self, resource_type: AWSResourceType, resource_id: str, **kwargs: Any
    ) -> AWSResourceResponse:
        """Read a resource's current state"""
        try:
            # Resource type handlers mapping
            handlers = {
                AWSResourceType.LAMBDA: lambda: self.lambda_manager.read(resource_id),
                AWSResourceType.IAM: lambda: self.iam_manager.read(
                    resource_id, kwargs.get("resource_subtype", "role")
                ),
                AWSResourceType.SSM: lambda: self.ssm_manager.read(resource_id),
                AWSResourceType.LOGS: lambda: self.logs_manager.read(resource_id),
                AWSResourceType.TRIGGER: lambda: self.trigger_manager.read(resource_id),
            }

            handler = handlers.get(resource_type)
            if handler:
                return handler()

            # This should never happen with current enum
            assert_never(resource_type)
        except (ImportError, TypeError, ValueError) as e:
            self.logger.error(
                f"Resource read failed for {resource_type} {resource_id}: {str(e)}"
            )
            return AWSResourceResponse(
                status="error", errors=[f"Resource read failed: {str(e)}"]
            )

    def update_resource(
        self,
        resource_type: AWSResourceType,
        _resource_id: str,
        resource_spec: dict[str, Any],
    ) -> AWSResourceResponse:
        """Update a resource"""
        # For most resources, update is the same as create_or_update
        return self.create_resource(resource_type, resource_spec)

    def delete_resource(
        self, resource_type: AWSResourceType, resource_id: str
    ) -> AWSResourceResponse:
        """Delete a resource"""
        try:
            # Resource type handlers mapping
            handlers = {
                AWSResourceType.LAMBDA: lambda: self.lambda_manager.delete(resource_id),
                AWSResourceType.IAM: lambda: self.iam_manager.delete(resource_id),
                AWSResourceType.SSM: lambda: self.ssm_manager.delete(resource_id),
                AWSResourceType.LOGS: lambda: self.logs_manager.delete(resource_id),
                AWSResourceType.TRIGGER: lambda: self.trigger_manager.delete(
                    resource_id
                ),
            }

            handler = handlers.get(resource_type)
            if handler:
                return handler()

            # This should never happen with current enum
            assert_never(resource_type)
        except (ImportError, TypeError, ValueError) as e:
            self.logger.error(
                f"Resource deletion failed for {resource_type} {resource_id}: {str(e)}"
            )
            return AWSResourceResponse(
                status="error",
                resource=None,
                errors=[f"Resource deletion failed: {str(e)}"],
            )

    def validate_aws_access(self) -> AWSResourceResponse:
        """Validate AWS access and permissions"""
        try:
            # Basic AWS access validation using STS
            sts_client: STSClient = boto3.client(  # type: ignore[arg-type]
                "sts", region_name=self.region
            )
            caller_identity = sts_client.get_caller_identity()
            self.logger.info(f"AWS access validated for: {caller_identity['Arn']}")
            return AWSResourceResponse(
                status="success", resource=caller_identity, errors=[]
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            self.logger.error(f"AWS access validation failed: {str(e)}")
            return AWSResourceResponse(
                status="error",
                resource=None,
                errors=[f"AWS access validation failed: {str(e)}"],
            )


# Global instance for backwards compatibility
