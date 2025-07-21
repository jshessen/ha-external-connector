"""Pydantic models for the Home Assistant External Connector."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


def _datetime_encoder(v: datetime) -> str:
    """Encode datetime to ISO format string."""
    return v.isoformat()


class InstallationScenario(str, Enum):
    """Supported installation scenarios."""

    DIRECT_ALEXA = "direct_alexa"
    CLOUDFLARE_ALEXA = "cloudflare_alexa"
    CLOUDFLARE_IOS = "cloudflare_ios"


class AWSRegion(str, Enum):
    """Supported AWS regions for Alexa Smart Home."""

    US_EAST_1 = "us-east-1"
    EU_WEST_1 = "eu-west-1"
    US_WEST_2 = "us-west-2"


class ResourceType(str, Enum):
    """AWS resource types."""

    IAM_ROLE = "iam"
    LAMBDA_FUNCTION = "lambda"
    SSM_PARAMETER = "ssm"
    FUNCTION_URL = "url"
    LOG_GROUP = "logs"


class DeploymentStrategy(str, Enum):
    """Deployment strategies."""

    IMMEDIATE = "immediate"
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


# AWS Resource Models


class IAMRole(BaseModel):
    """AWS IAM Role model."""

    role_name: str = Field(..., description="IAM role name")
    arn: str = Field(..., description="Role ARN")
    description: str | None = Field(None, description="Role description")
    create_date: datetime | None = Field(None, description="Creation timestamp")
    assume_role_policy: dict[str, Any] | None = Field(
        None, description="Trust policy document"
    )
    attached_policies: list[str] = Field(
        default_factory=list, description="Attached policy ARNs"
    )

    class Config:
        """Pydantic configuration for IAMRole model."""

        json_encoders = {datetime: _datetime_encoder}


class LambdaFunction(BaseModel):
    """AWS Lambda Function model."""

    function_name: str = Field(..., description="Lambda function name")
    function_arn: str | None = Field(None, description="Function ARN")
    runtime: str = Field("python3.11", description="Runtime environment")
    handler: str = Field(..., description="Function handler")
    role_arn: str = Field(..., description="IAM role ARN")
    description: str | None = Field(None, description="Function description")
    timeout: int = Field(30, ge=1, le=900, description="Timeout in seconds")
    memory_size: int = Field(512, ge=128, le=10240, description="Memory size in MB")
    environment_variables: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    code_size: int | None = Field(None, description="Code package size in bytes")
    code_sha256: str | None = Field(None, description="Code SHA256 hash")
    version: str | None = Field(None, description="Function version")
    last_modified: datetime | None = Field(
        None, description="Last modification timestamp"
    )
    state: str | None = Field(None, description="Function state")

    @field_validator("memory_size")
    @classmethod
    def validate_memory_size(cls, v: int) -> int:
        """Validate memory size is a valid Lambda value."""
        valid_sizes = [
            128,
            192,
            256,
            320,
            384,
            448,
            512,
            576,
            640,
            704,
            768,
            832,
            896,
            960,
            1024,
        ]
        valid_sizes.extend(range(1024, 10241, 64))  # 1024-10240 in 64MB increments

        if v not in valid_sizes:
            # Find the nearest valid size
            nearest = min(valid_sizes, key=lambda x: abs(x - v))
            raise ValueError(
                f"Invalid memory size {v}MB. Nearest valid size is {nearest}MB"
            )

        return v

    class Config:
        """Pydantic configuration for LambdaFunction model."""

        json_encoders = {datetime: _datetime_encoder}


class SSMParameter(BaseModel):
    """AWS SSM Parameter model."""

    name: str = Field(..., description="Parameter name")
    type: str = Field("SecureString", description="Parameter type")
    value: str | None = Field(None, description="Parameter value")
    description: str | None = Field(None, description="Parameter description")
    key_id: str | None = Field(None, description="KMS key ID for encryption")
    last_modified_date: datetime | None = Field(
        None, description="Last modification timestamp"
    )
    version: int | None = Field(None, description="Parameter version")
    tier: str | None = Field("Standard", description="Parameter tier")

    class Config:
        """Pydantic configuration for SSMParameter model."""

        json_encoders = {datetime: _datetime_encoder}


class FunctionURL(BaseModel):
    """AWS Lambda Function URL model."""

    function_name: str = Field(..., description="Lambda function name")
    function_url: HttpUrl | None = Field(None, description="Function URL")
    auth_type: str = Field("NONE", description="Authentication type")
    cors: dict[str, Any] | None = Field(None, description="CORS configuration")
    creation_time: datetime | None = Field(None, description="Creation timestamp")

    class Config:
        """Pydantic configuration for FunctionURL model."""

        json_encoders = {datetime: _datetime_encoder}


class CloudWatchLogGroup(BaseModel):
    """AWS CloudWatch Log Group model."""

    log_group_name: str = Field(..., description="Log group name")
    creation_time: datetime | None = Field(None, description="Creation timestamp")
    retention_in_days: int | None = Field(None, description="Log retention period")
    stored_bytes: int | None = Field(None, description="Stored log data size")
    arn: str | None = Field(None, description="Log group ARN")

    class Config:
        """Pydantic configuration for CloudWatchLogGroup model."""

        json_encoders = {datetime: _datetime_encoder}


# Type aliases for complex union types
AWSResource = IAMRole | LambdaFunction | SSMParameter | FunctionURL | CloudWatchLogGroup


# CloudFlare Models


class CloudFlareZone(BaseModel):
    """CloudFlare Zone model."""

    id: str = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name (domain)")
    status: str = Field(..., description="Zone status")
    paused: bool = Field(False, description="Whether zone is paused")
    type: str = Field("full", description="Zone type")
    name_servers: list[str] = Field(default_factory=list, description="Name servers")
    created_on: datetime | None = Field(None, description="Creation timestamp")
    modified_on: datetime | None = Field(
        None, description="Last modification timestamp"
    )

    class Config:
        """Pydantic configuration for CloudFlareZone model."""

        json_encoders = {datetime: _datetime_encoder}


class CloudFlareAccessApplication(BaseModel):
    """CloudFlare Access Application model."""

    id: str | None = Field(None, description="Application ID")
    name: str = Field(..., description="Application name")
    domain: str = Field(..., description="Application domain")
    type: str = Field("self_hosted", description="Application type")
    session_duration: str = Field("24h", description="Session duration")
    allowed_idps: list[str] = Field(
        default_factory=list, description="Allowed identity providers"
    )
    auto_redirect_to_identity: bool = Field(
        False, description="Auto-redirect to identity provider"
    )
    app_launcher_visible: bool = Field(True, description="Visible in app launcher")
    service_auth_401_redirect: bool = Field(False, description="Redirect on 401")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration for CloudFlareAccessApplication model."""

        json_encoders = {datetime: _datetime_encoder}


class CloudFlareServiceToken(BaseModel):
    """CloudFlare Service Token model."""

    id: str | None = Field(None, description="Token ID")
    name: str = Field(..., description="Token name")
    client_id: str | None = Field(None, description="Client ID")
    client_secret: str | None = Field(None, description="Client secret")
    duration: str | None = Field(None, description="Token duration")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")

    class Config:
        """Pydantic configuration for CloudFlareServiceToken model."""

        json_encoders = {datetime: _datetime_encoder}


# Configuration Models


class HomeAssistantConfig(BaseModel):
    """Home Assistant configuration."""

    base_url: HttpUrl = Field(..., description="Home Assistant base URL")

    @field_validator("base_url")
    @classmethod
    def validate_https(cls, v: HttpUrl) -> HttpUrl:
        """Ensure URL uses HTTPS."""
        if v.scheme != "https":
            raise ValueError("Home Assistant URL must use HTTPS")
        return v


class AlexaConfig(BaseModel):
    """Alexa integration configuration."""

    secret: str = Field(
        ..., min_length=32, description="Alexa secret for request validation"
    )

    @field_validator("secret")
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        """Ensure secret is long enough."""
        if len(v) < 32:
            raise ValueError("Alexa secret must be at least 32 characters long")
        return v


class CloudFlareConfig(BaseModel):
    """CloudFlare configuration."""

    client_id: str | None = Field(None, description="CloudFlare Access client ID")
    client_secret: str | None = Field(
        None, description="CloudFlare Access client secret"
    )
    api_token: str | None = Field(None, description="CloudFlare API token")
    api_key: str | None = Field(None, description="CloudFlare API key")
    email: str | None = Field(None, description="CloudFlare account email")

    @model_validator(mode="after")
    def validate_client_secret_with_id(self) -> CloudFlareConfig:
        """Ensure client secret is provided when client ID is present."""
        if self.client_id and not self.client_secret:
            raise ValueError("client_secret required when client_id is provided")
        return self


class ServiceConfiguration(BaseModel):
    """Service-specific configuration."""

    scenario: InstallationScenario = Field(..., description="Installation scenario")
    aws_region: AWSRegion = Field(AWSRegion.US_EAST_1, description="AWS region")
    home_assistant: HomeAssistantConfig = Field(
        ..., description="Home Assistant configuration"
    )
    alexa: AlexaConfig | None = Field(None, description="Alexa configuration")
    cloudflare: CloudFlareConfig | None = Field(
        None, description="CloudFlare configuration"
    )

    @field_validator("alexa")
    @classmethod
    def validate_alexa_for_scenario(cls, v: AlexaConfig | None) -> AlexaConfig | None:
        """Ensure Alexa config is provided for Alexa scenarios."""
        # This validation is now done at the model level in validate_service_config
        return v

    @model_validator(mode="after")
    def validate_service_config(self) -> ServiceConfiguration:
        """Validate cross-field dependencies for service configuration."""
        # Validate Alexa config for Alexa scenarios
        alexa_scenarios = [
            InstallationScenario.DIRECT_ALEXA,
            InstallationScenario.CLOUDFLARE_ALEXA,
        ]
        if self.scenario in alexa_scenarios and not self.alexa:
            raise ValueError(
                f"Alexa configuration required for {self.scenario} scenario"
            )

        # Validate CloudFlare config for CloudFlare scenarios
        cf_scenarios = [
            InstallationScenario.CLOUDFLARE_ALEXA,
            InstallationScenario.CLOUDFLARE_IOS,
        ]
        cf_config_missing = not self.cloudflare or not (
            self.cloudflare.client_id or self.cloudflare.api_token
        )
        if self.scenario in cf_scenarios and cf_config_missing:
            raise ValueError(
                f"CloudFlare configuration required for {self.scenario} scenario"
            )

        return self


# Resource Discovery Models


class ResourceMatch(BaseModel):
    """Resource match result."""

    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Expected resource identifier")
    resource: AWSResource | None = Field(None, description="Found resource details")
    exists: bool = Field(False, description="Whether resource exists")


class PossibleResourceMatch(BaseModel):
    """Possible resource match."""

    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Expected resource identifier")
    matches: list[Any] = Field(
        default_factory=list, description="Possible matching resources"
    )


class ResourceDiscoveryResult(BaseModel):
    """Resource discovery result."""

    found_resources: list[Any] = Field(
        default_factory=list, description="Exact matches found"
    )
    missing_resources: list[Any] = Field(
        default_factory=list, description="Resources not found"
    )
    possible_resources: list[Any] = Field(
        default_factory=list, description="Possible matches"
    )


# Deployment Models


class DeploymentPlan(BaseModel):
    """Deployment plan."""

    scenario: InstallationScenario = Field(..., description="Target scenario")
    strategy: DeploymentStrategy = Field(
        DeploymentStrategy.ROLLING, description="Deployment strategy"
    )
    resources_to_create: list[Any] = Field(
        default_factory=list, description="Resources to create"
    )
    resources_to_update: list[Any] = Field(
        default_factory=list, description="Resources to update"
    )
    resources_to_delete: list[Any] = Field(
        default_factory=list, description="Resources to delete"
    )
    estimated_duration: int | None = Field(
        None, description="Estimated duration in seconds"
    )
    prerequisites_met: bool = Field(
        False, description="Whether prerequisites are satisfied"
    )


class DeploymentResult(BaseModel):
    """Deployment result."""

    success: bool = Field(..., description="Whether deployment succeeded")
    created_resources: list[Any] = Field(
        default_factory=list, description="Successfully created resources"
    )
    failed_resources: list[Any] = Field(
        default_factory=list, description="Failed resource operations"
    )
    function_urls: dict[str, str] = Field(
        default_factory=dict, description="Created function URLs"
    )
    duration: float | None = Field(None, description="Deployment duration in seconds")
    error_message: str | None = Field(
        None, description="Error message if deployment failed"
    )


# Health Check Models


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ServiceHealth(BaseModel):
    """Service health check result."""

    service_name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Health status")
    checks: dict[str, bool] = Field(
        default_factory=dict, description="Individual check results"
    )
    response_time: float | None = Field(None, description="Response time in seconds")
    last_check: datetime | None = Field(None, description="Last check timestamp")
    error_message: str | None = Field(None, description="Error message if unhealthy")

    class Config:
        """Pydantic configuration for ServiceHealth model."""

        json_encoders = {datetime: _datetime_encoder}
