"""Alexa integration data models."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SkillType(Enum):
    """Alexa skill types."""

    SMART_HOME = "smart_home"
    CUSTOM = "custom"
    FLASH_BRIEFING = "flash_briefing"


class DeploymentStatus(Enum):
    """Lambda deployment status."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    UPDATING = "updating"


@dataclass
class AlexaSkillURLs:
    """Alexa skill URLs configuration."""

    redirect_urls: list[str]
    privacy_policy_url: str | None = None
    terms_of_use_url: str | None = None


@dataclass
class AlexaSkillCredentials:
    """Alexa skill credentials configuration."""

    client_id: str
    client_secret: str


@dataclass
class AlexaSkillConfig:
    """Alexa skill configuration."""

    skill_id: str
    skill_name: str
    skill_type: SkillType
    credentials: AlexaSkillCredentials
    urls: AlexaSkillURLs


@dataclass
class LambdaFunctionConfig:
    """Lambda function configuration."""

    function_name: str
    runtime: str
    handler: str
    memory_size: int
    timeout: int
    environment_variables: dict[str, str]
    layers: list[str] | None = None


@dataclass
class AlexaDeploymentConfig:
    """Alexa deployment configuration."""

    aws_region: str
    lambda_functions: list[LambdaFunctionConfig]
    dynamodb_tables: list[str]
    cloudformation_stack_name: str
    deployment_bucket: str | None = None


@dataclass
class AlexaIntegrationStatus:
    """Alexa integration status."""

    skill_enabled: bool
    lambda_status: DeploymentStatus
    last_deployment: str | None = None
    error_message: str | None = None
    devices_synced: int = 0
    last_sync: str | None = None


@dataclass
class DeviceSyncResult:
    """Device synchronization result."""

    total_devices: int
    synced_devices: int
    failed_devices: int
    errors: list[str]
    sync_timestamp: str


@dataclass
class AlexaResponse:
    """Alexa API response."""

    success: bool
    data: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
