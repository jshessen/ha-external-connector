"""AWS Resource Specification Models.

Pydantic models defining specifications for various AWS resources.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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


class SSMResourceSpec(BaseModel):
    """Specification model for AWS SSM resources."""

    parameter_name: str = Field(..., description="Name of the SSM parameter")
    parameter_value: str = Field(..., description="Value of the SSM parameter")
    parameter_type: str = Field(default="String", description="Type of parameter")
    description: str | None = Field(None, description="Parameter description")


class LogsResourceSpec(BaseModel):
    """Specification model for AWS CloudWatch Logs resources."""

    log_group_name: str = Field(..., description="Log group name")
    retention_days: int = Field(default=14, description="Retention in days")
    kms_key_id: str | None = Field(None, description="KMS key ID for encryption")
    tags: dict[str, str] | None = Field(None, description="Resource tags")


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
    """Resource specification for AWS triggers."""

    trigger_type: str = Field(
        ..., description="Type of trigger (eventbridge, apigateway)"
    )
    name: str = Field(..., description="Trigger name")
    target_function_arn: str = Field(..., description="Target Lambda function ARN")

    # EventBridge specific
    event_pattern: dict[str, Any] | None = Field(
        None, description="EventBridge event pattern"
    )
    schedule_expression: str | None = Field(
        None, description="Schedule expression for timed triggers"
    )
    event_bus_name: str | None = Field(None, description="Custom event bus name")

    # API Gateway specific
    api_id: str | None = Field(None, description="API Gateway ID")
    resource_path: str | None = Field(None, description="API resource path")
    http_method: str | None = Field(None, description="HTTP method")

    # Common
    description: str | None = Field(None, description="Trigger description")
    tags: dict[str, str] | None = Field(None, description="Resource tags")
