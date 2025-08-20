"""AWS Platform Client - Unified async implementation.

This module provides a unified AWS platform client with async operations
for AWS resource management through specialized service classes.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
)

from ..base import BasePlatform, ResourceOperation, ResourceResponse
from .models import (
    AWSResourceType,
    IAMResourceSpec,
    LambdaResourceSpec,
    LogsResourceSpec,
    SSMResourceSpec,
)
from .services import (
    IAMService,
    LambdaService,
    LogsService,
    SSMService,
    TriggerService,
)

if TYPE_CHECKING:
    from types_boto3_sts.client import STSClient


# Note: Previously imported legacy resource manager for backwards compatibility
# Removed to simplify architecture - AWS platform now uses unified service layer


class AWSPlatform(BasePlatform):
    """AWS platform implementation.

    This class provides a unified interface for AWS resource management
    through specialized service classes for different AWS resource types.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize AWS platform.

        Args:
            config: AWS configuration including region, credentials, etc.
        """
        super().__init__("aws", config)

        # AWS configuration
        self.region = config.get("region", "us-east-1") if config else "us-east-1"

        # Initialize services
        self.lambda_service = LambdaService(self.region)
        self.iam_service = IAMService(self.region)
        self.ssm_service = SSMService(self.region)
        self.logs_service = LogsService(self.region)
        self.trigger_service = TriggerService(self.region)

    async def create_resource(
        self,
        resource_type: str,
        resource_spec: Any,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Create a new AWS resource.

        Args:
            resource_type: Type of AWS resource to create
            resource_spec: Resource specification (Pydantic model)
            **kwargs: Additional AWS-specific parameters

        Returns:
            ResourceResponse with creation result
        """
        try:
            # Convert string to enum
            aws_resource_type = AWSResourceType(resource_type)

            # Route to appropriate service
            if aws_resource_type == AWSResourceType.LAMBDA:
                validated_spec = LambdaResourceSpec.model_validate(resource_spec)
                result = await self.lambda_service.create_or_update(validated_spec)
            elif aws_resource_type == AWSResourceType.IAM:
                validated_spec = IAMResourceSpec.model_validate(resource_spec)
                result = await self.iam_service.create_or_update(validated_spec)
            elif aws_resource_type == AWSResourceType.SSM:
                validated_spec = SSMResourceSpec.model_validate(resource_spec)
                result = await self.ssm_service.create_or_update(validated_spec)
            elif aws_resource_type == AWSResourceType.LOGS:
                validated_spec = LogsResourceSpec.model_validate(resource_spec)
                result = await self.logs_service.create_or_update(validated_spec)
            elif aws_resource_type == AWSResourceType.TRIGGER:
                result = await self.trigger_service.create_or_update(resource_spec)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.CREATE,
                    status="error",
                    resource=None,
                    resource_id=None,
                    errors=[f"Unsupported resource type: {resource_type}"],
                )  # Convert service response to platform response
            return ResourceResponse(
                operation=ResourceOperation.CREATE,
                status=result.status,
                resource=result.resource,
                resource_id=result.resource.get("id") if result.resource else None,
                errors=result.errors,
                metadata={"aws_region": self.region},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.CREATE,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Invalid resource type: {e}"],
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            return ResourceResponse(
                operation=ResourceOperation.CREATE,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Resource creation failed: {e}"],
            )

    async def read_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Read an existing AWS resource.

        Args:
            resource_type: Type of AWS resource to read
            resource_id: AWS resource identifier
            **kwargs: Additional AWS-specific parameters

        Returns:
            ResourceResponse with resource data
        """
        try:
            aws_resource_type = AWSResourceType(resource_type)

            # Route to appropriate service
            if aws_resource_type == AWSResourceType.LAMBDA:
                result = await self.lambda_service.read(resource_id)
            elif aws_resource_type == AWSResourceType.IAM:
                result = await self.iam_service.read(
                    resource_id, kwargs.get("iam_resource_type", "role")
                )
            elif aws_resource_type == AWSResourceType.SSM:
                result = await self.ssm_service.read(resource_id)
            elif aws_resource_type == AWSResourceType.LOGS:
                result = await self.logs_service.read(resource_id)
            elif aws_resource_type == AWSResourceType.TRIGGER:
                result = await self.trigger_service.read(resource_id)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.READ,
                    status="error",
                    resource=None,
                    resource_id=resource_id,
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.READ,
                status=result.status,
                resource=result.resource,
                resource_id=resource_id,
                errors=result.errors,
                metadata={"aws_region": self.region},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.READ,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Invalid resource type: {e}"],
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            return ResourceResponse(
                operation=ResourceOperation.READ,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Resource read failed: {e}"],
            )

    async def update_resource(
        self,
        resource_type: str,
        resource_id: str,
        resource_spec: Any,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Update an existing AWS resource.

        Args:
            resource_type: Type of AWS resource to update
            resource_id: AWS resource identifier
            resource_spec: Updated resource specification
            **kwargs: Additional AWS-specific parameters

        Returns:
            ResourceResponse with update result
        """
        # For most AWS resources, update is the same as create_or_update
        return await self.create_resource(resource_type, resource_spec, **kwargs)

    async def delete_resource(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """Delete an existing AWS resource.

        Args:
            resource_type: Type of AWS resource to delete
            resource_id: AWS resource identifier
            **kwargs: Additional AWS-specific parameters

        Returns:
            ResourceResponse with deletion result
        """
        try:
            aws_resource_type = AWSResourceType(resource_type)

            # Route to appropriate service
            if aws_resource_type == AWSResourceType.LAMBDA:
                result = await self.lambda_service.delete(resource_id)
            elif aws_resource_type == AWSResourceType.IAM:
                result = await self.iam_service.delete(resource_id)
            elif aws_resource_type == AWSResourceType.SSM:
                result = await self.ssm_service.delete(resource_id)
            elif aws_resource_type == AWSResourceType.LOGS:
                result = await self.logs_service.delete(resource_id)
            elif aws_resource_type == AWSResourceType.TRIGGER:
                result = await self.trigger_service.delete(resource_id)
            else:
                return ResourceResponse(
                    operation=ResourceOperation.DELETE,
                    status="error",
                    resource=None,
                    resource_id=resource_id,
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status=result.status,
                resource=result.resource,
                resource_id=resource_id,
                errors=result.errors,
                metadata={"aws_region": self.region},
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status="error",
                resource=None,
                resource_id=resource_id,
                errors=[f"Invalid resource type: {e}"],
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            return ResourceResponse(
                operation=ResourceOperation.DELETE,
                status="error",
                resource=None,
                resource_id=resource_id,
                errors=[f"Resource deletion failed: {e}"],
            )

    async def list_resources(
        self,
        resource_type: str,
        **kwargs: Any,
    ) -> ResourceResponse:
        """List AWS resources of a given type.

        Args:
            resource_type: Type of AWS resources to list
            **kwargs: Additional AWS-specific parameters

        Returns:
            ResourceResponse with list of resources
        """
        try:
            aws_resource_type = AWSResourceType(resource_type)

            # Route to appropriate service
            if aws_resource_type == AWSResourceType.LAMBDA:
                result = await self.lambda_service.list_functions()
            elif aws_resource_type == AWSResourceType.IAM:
                result = await self.iam_service.list_roles()
            elif aws_resource_type == AWSResourceType.SSM:
                result = await self.ssm_service.list_parameters()
            elif aws_resource_type == AWSResourceType.LOGS:
                result = await self.logs_service.list_log_groups()
            elif aws_resource_type == AWSResourceType.TRIGGER:
                result = await self.trigger_service.list_triggers()
            else:
                return ResourceResponse(
                    operation=ResourceOperation.LIST,
                    status="error",
                    resource=None,
                    resource_id=None,
                    errors=[f"Unsupported resource type: {resource_type}"],
                )

            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status=result.status,
                resource=result.resource,
                resource_id=None,  # List operations don't have single resource ID
                errors=result.errors,
                metadata={
                    "aws_region": self.region,
                    "resource_count": len(result.resource) if result.resource else 0,
                },
            )

        except ValueError as e:
            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Invalid resource type: {e}"],
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            return ResourceResponse(
                operation=ResourceOperation.LIST,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Resource listing failed: {e}"],
            )

    async def validate_access(self) -> ResourceResponse:
        """Validate AWS access and credentials.

        Returns:
            ResourceResponse with validation result
        """
        try:
            # Use STS to validate credentials
            sts_client: STSClient = cast(
                "STSClient",
                boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
                    "sts", region_name=self.region
                ),
            )

            # Run in executor to avoid blocking
            caller_identity = await asyncio.get_event_loop().run_in_executor(
                None, sts_client.get_caller_identity
            )

            arn = caller_identity.get("Arn", "unknown")

            return ResourceResponse(
                operation=ResourceOperation.VALIDATE,
                status="success",
                resource=dict(caller_identity),
                resource_id=arn,
                metadata={
                    "aws_region": self.region,
                    "caller_arn": arn,
                },
            )

        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            return ResourceResponse(
                operation=ResourceOperation.VALIDATE,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"AWS access validation failed: {e}"],
                metadata={"aws_region": self.region},
            )
        except (ValueError, BotoCoreError) as e:
            return ResourceResponse(
                operation=ResourceOperation.VALIDATE,
                status="error",
                resource=None,
                resource_id=None,
                errors=[f"Unexpected error during validation: {e}"],
                metadata={"aws_region": self.region},
            )
