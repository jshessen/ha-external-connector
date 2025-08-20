"""AWS platform implementation."""

from .client import AWSPlatform
from .lambda_validator import LambdaSecurityValidator
from .models import (
    AWSResourceType,
    IAMResourceSpec,
    LambdaResourceSpec,
    LogsResourceSpec,
    SSMResourceSpec,
)
from .resource_manager import AWSResourceManager, AWSResourceResponse

__all__ = [
    "AWSPlatform",
    "AWSResourceType",
    "LambdaResourceSpec",
    "IAMResourceSpec",
    "SSMResourceSpec",
    "LogsResourceSpec",
    "LambdaSecurityValidator",
    "AWSResourceManager",
    "AWSResourceResponse",
]
