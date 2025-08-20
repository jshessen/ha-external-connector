"""AWS-specific helper utilities.

This module provides common AWS utilities and patterns used across
AWS platform services and integrations.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from .common import mask_sensitive_data
from .exceptions import AWSError

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

# Common AWS error codes
AWS_ACCESS_DENIED = "AccessDenied"
AWS_RESOURCE_NOT_FOUND = "ResourceNotFoundException"
AWS_RESOURCE_ALREADY_EXISTS = "ResourceAlreadyExistsException"
AWS_THROTTLING = "Throttling"
AWS_SERVICE_UNAVAILABLE = "ServiceUnavailable"

# Common AWS regions
AWS_REGIONS = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "Europe (Ireland)",
    "eu-central-1": "Europe (Frankfurt)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
}


def handle_aws_error(error: ClientError, context: str = "") -> None:
    """Handle AWS ClientError with proper error messages.

    Args:
        error: The AWS ClientError exception
        context: Optional context for the error

    Raises:
        AWSError: Converted AWS error with appropriate message
    """
    error_info = error.response.get("Error", {})
    error_code = error_info.get("Code", "Unknown")
    error_message = error_info.get("Message", str(error))

    full_message = f"{context}: {error_message}" if context else error_message

    _LOGGER.error("AWS Error [%s]: %s", error_code, full_message)

    if error_code == AWS_ACCESS_DENIED:
        raise AWSError(f"Access denied: {full_message}") from error
    if error_code == AWS_RESOURCE_NOT_FOUND:
        raise AWSError(f"Resource not found: {full_message}") from error
    if error_code == AWS_RESOURCE_ALREADY_EXISTS:
        raise AWSError(f"Resource already exists: {full_message}") from error
    if error_code in [AWS_THROTTLING, AWS_SERVICE_UNAVAILABLE]:
        raise AWSError(
            f"AWS service temporarily unavailable: {full_message}"
        ) from error
    raise AWSError(f"AWS error ({error_code}): {full_message}") from error


def validate_aws_region(region: str) -> bool:
    """Validate AWS region format.

    Args:
        region: AWS region string to validate

    Returns:
        True if valid region

    Raises:
        ValueError: If region format is invalid
    """
    if not region:
        raise ValueError("AWS region cannot be empty")

    if region not in AWS_REGIONS:
        _LOGGER.warning("Unknown AWS region: %s", region)

    return True


def create_lambda_policy_document(
    resources: list[str] | None = None,
    actions: list[str] | None = None,
) -> dict[str, Any]:
    """Create a basic Lambda execution policy document.

    Args:
        resources: List of resource ARNs to grant access to
        actions: List of actions to allow

    Returns:
        Policy document dictionary
    """
    default_actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
    ]

    policy_actions = (actions or []) + default_actions
    policy_resources = resources or ["*"]

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": policy_actions,
                "Resource": policy_resources,
            }
        ],
    }


def create_assume_role_policy_document(service: str = "lambda") -> dict[str, Any]:
    """Create a basic assume role policy document.

    Args:
        service: AWS service to allow assumption (default: lambda)

    Returns:
        Assume role policy document dictionary
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": f"{service}.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }


def sanitize_aws_name(name: str) -> str:
    """Sanitize a name for AWS resource naming conventions.

    Args:
        name: Name to sanitize

    Returns:
        Sanitized name suitable for AWS resources
    """

    # Replace invalid characters with hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9-_]", "-", name)
    sanitized = re.sub(r"[^a-zA-Z0-9-_]", "-", name)
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)
    # Strip leading/trailing hyphens
    sanitized = sanitized.strip("-")
    # Ensure it starts with a letter or number
    if sanitized and not sanitized[0].isalnum():
        sanitized = "resource-" + sanitized

    return sanitized or "unnamed-resource"


def format_aws_arn(
    service: str,
    region: str,
    account_id: str,
    resource_type: str,
    resource_name: str,
    *,
    partition: str = "aws",
) -> str:
    """Format AWS ARN string.

    Args:
        service: AWS service name
        region: AWS region
        account_id: AWS account ID
        resource_type: Type of resource
        resource_name: Name of the resource
        partition: AWS partition (default: aws)

    Returns:
        Formatted ARN string
    """
    return (
        f"arn:{partition}:{service}:{region}:{account_id}:"
        f"{resource_type}/{resource_name}"
    )


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON data with fallback.

    Args:
        data: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as err:
        _LOGGER.warning("Failed to parse JSON data: %s", err)
        return default


def create_boto3_client(service_name: str, region: str = "us-east-1") -> Any:
    """Create a boto3 client with proper type handling.

    This helper addresses Pylance/mypy issues with boto3.client() expecting
    literal service names while we need dynamic service selection.

    Args:
        service_name: AWS service name (e.g., 'lambda', 'iam', 'ssm')
        region: AWS region name

    Returns:
        Boto3 client instance

    Raises:
        AWSError: If client creation fails
    """
    try:
        # pyright: ignore[reportArgumentType, reportUnknownMemberType]
        return boto3.client(service_name, region_name=region)
    except Exception as err:
        raise AWSError(f"Failed to create {service_name} client: {err}") from err


def mask_aws_credentials(data: dict[str, Any]) -> dict[str, Any]:
    """Mask AWS credentials in data for logging.

    Args:
        data: Dictionary potentially containing AWS credentials

    Returns:
        Dictionary with credentials masked
    """
    aws_sensitive_keys = {
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "secret_key",
        "access_key",
        "token",
        "password",
        "credential",
    }

    return mask_sensitive_data(data, aws_sensitive_keys)
