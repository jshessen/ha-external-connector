"""
AWS and CloudFlare Adapters Package

This package provides AWS and CloudFlare resource management capabilities
with a pure JSON CRUD interface.
"""

from .aws_manager import (
    AWSIAMManager,
    AWSLambdaManager,
    AWSLogsManager,
    AWSResourceManager,
    AWSResourceResponse,
    AWSResourceType,
    AWSSSMManager,
    AWSTriggerManager,
    IAMResourceSpec,
    LambdaResourceSpec,
    LogsResourceSpec,
    SSMResourceSpec,
)
from .cloudflare_manager import (
    AccessApplicationSpec,
    CloudFlareManager,
    CloudFlareResourceResponse,
    CloudFlareResourceType,
    DNSRecordSpec,
)

__all__ = [
    # AWS Adapters
    "AWSIAMManager",
    "AWSLambdaManager",
    "AWSLogsManager",
    "AWSResourceManager",
    "AWSResourceResponse",
    "AWSResourceType",
    "AWSSSMManager",
    "AWSTriggerManager",
    "IAMResourceSpec",
    "LambdaResourceSpec",
    "LogsResourceSpec",
    "SSMResourceSpec",
    # CloudFlare Adapters
    "AccessApplicationSpec",
    "CloudFlareManager",
    "CloudFlareResourceResponse",
    "CloudFlareResourceType",
    "DNSRecordSpec",
]
