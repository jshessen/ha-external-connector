"""Base AWS Service Module.

Common base classes, response models, and utilities for AWS services.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ....utils.aws_helpers import create_boto3_client


class AWSServiceResponse(BaseModel):
    """Response model for AWS service operations."""

    status: str
    resource: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


class BaseAWSService:
    """Base class for AWS services."""

    def __init__(self, region: str = "us-east-1") -> None:
        """Initialize base AWS service.

        Args:
            region: AWS region for service operations
        """
        self.region = region

    def _get_boto3_client(self, service: str):
        """Get a boto3 client for the specified service.

        Args:
            service: AWS service name (e.g., 'lambda', 'iam')

        Returns:
            Configured boto3 client instance
        """
        return create_boto3_client(service, region=self.region)
