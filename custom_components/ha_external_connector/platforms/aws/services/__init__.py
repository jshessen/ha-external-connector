"""AWS Services Module.

Modular AWS service implementations for the Home Assistant External Connector.
"""

from .base import AWSServiceResponse, BaseAWSService
from .iam_service import IAMService
from .lambda_service import LambdaService
from .logs_service import LogsService
from .models import (
    IAMResourceSpec,
    LambdaResourceSpec,
    LogQueryConfig,
    LogsResourceSpec,
    SSMResourceSpec,
    TriggerResourceSpec,
)
from .ssm_service import SSMService
from .trigger_service import TriggerService

__all__ = [
    # Base classes
    "AWSServiceResponse",
    "BaseAWSService",
    # Service implementations
    "IAMService",
    "LambdaService",
    "LogsService",
    "SSMService",
    "TriggerService",
    # Resource specifications
    "IAMResourceSpec",
    "LambdaResourceSpec",
    "LogQueryConfig",
    "LogsResourceSpec",
    "SSMResourceSpec",
    "TriggerResourceSpec",
]
