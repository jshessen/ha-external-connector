"""AWS resource models and specifications.

This module defines Pydantic models for AWS resource specifications.
These models provide type-safe configuration for AWS resource creation
and management operations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AWSServiceResponse(BaseModel):
    """Response model for AWS service operations."""

    status: str
    resource: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


class BaseAWSService:
    """Base class for AWS service implementations."""

    def __init__(self, region: str = "us-east-1") -> None:
        """Initialize the AWS service.

        Args:
            region: AWS region for the service
        """
        self.region = region


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
    runtime: str = Field(default="python3.13", description="Runtime environment")
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


class SSMResourceSpec(BaseModel):
    """Specification model for AWS SSM resources."""

    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Parameter value")
    parameter_type: str = Field(default="String", description="Parameter type")
    description: str | None = Field(None, description="Parameter description")


class LogsResourceSpec(BaseModel):
    """Specification model for AWS CloudWatch Logs resources."""

    log_group_name: str = Field(..., description="Log group name")
    retention_days: int = Field(default=14, description="Retention in days")
    description: str | None = Field(None, description="Log group description")


class LogQueryConfig(BaseModel):
    """Configuration for log event queries."""

    log_group_name: str = Field(..., description="Name of the log group")
    log_stream_name: str | None = Field(
        None, description="Optional specific log stream name"
    )
    start_time: int | None = Field(
        None, description="Start time (Unix timestamp in milliseconds)"
    )
    end_time: int | None = Field(
        None, description="End time (Unix timestamp in milliseconds)"
    )
    limit: int = Field(
        default=100, description="Maximum number of log events to return"
    )


class TriggerResourceSpec(BaseModel):
    """Specification model for AWS trigger resources."""

    trigger_type: str = Field(..., description="Type of trigger (eventbridge, api)")
    source: str = Field(..., description="Trigger source")
    target_arn: str = Field(..., description="Target Lambda function ARN")
    rule_name: str | None = Field(None, description="EventBridge rule name")
    schedule_expression: str | None = Field(None, description="Schedule expression")
    event_pattern: dict[str, Any] | None = Field(None, description="Event pattern")
    description: str | None = Field(None, description="Trigger description")
