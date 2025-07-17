"""
AWS Adapters Package

This package provides AWS resource management capabilities with a pure JSON CRUD interface.
Replaces the bash aws_manager.sh with a modern Python implementation using boto3.
"""

from .aws_manager import (
    AWSResourceManager,
    AWSResourceType,
    AWSLambdaManager,
    AWSIAMManager,
    AWSSSMManager,
    AWSLogsManager,
    AWSTriggerManager,
    validate_aws_access,
    LambdaResourceSpec,
    IAMResourceSpec,
    SSMResourceSpec,
    LogsResourceSpec,
    AWSResourceResponse,
)

__all__ = [
    "AWSResourceManager",
    "AWSResourceType",
    "AWSLambdaManager",
    "AWSIAMManager",
    "AWSSSMManager",
    "AWSLogsManager",
    "AWSTriggerManager",
    "validate_aws_access",
    "LambdaResourceSpec",
    "IAMResourceSpec",
    "SSMResourceSpec",
    "LogsResourceSpec",
    "AWSResourceResponse",
]
