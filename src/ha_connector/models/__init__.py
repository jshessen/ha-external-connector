"""Pydantic models for the Home Assistant External Connector."""

from enum import Enum
from typing import Dict, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, validator


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
    description: Optional[str] = Field(None, description="Role description")
    create_date: Optional[datetime] = Field(None, description="Creation timestamp")
    assume_role_policy: Optional[Dict] = Field(None, description="Trust policy document")
    attached_policies: List[str] = Field(default_factory=list, description="Attached policy ARNs")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LambdaFunction(BaseModel):
    """AWS Lambda Function model."""
    
    function_name: str = Field(..., description="Lambda function name")
    function_arn: Optional[str] = Field(None, description="Function ARN")
    runtime: str = Field("python3.11", description="Runtime environment")
    handler: str = Field(..., description="Function handler")
    role_arn: str = Field(..., description="IAM role ARN")
    description: Optional[str] = Field(None, description="Function description")
    timeout: int = Field(30, ge=1, le=900, description="Timeout in seconds")
    memory_size: int = Field(512, ge=128, le=10240, description="Memory size in MB")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    code_size: Optional[int] = Field(None, description="Code package size in bytes")
    code_sha256: Optional[str] = Field(None, description="Code SHA256 hash")
    version: Optional[str] = Field(None, description="Function version")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    state: Optional[str] = Field(None, description="Function state")
    
    @validator('memory_size')
    def validate_memory_size(cls, v):
        """Validate memory size is a valid Lambda value."""
        valid_sizes = [128, 192, 256, 320, 384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024]
        valid_sizes.extend(range(1024, 10241, 64))  # 1024-10240 in 64MB increments
        
        if v not in valid_sizes:
            # Find the nearest valid size
            nearest = min(valid_sizes, key=lambda x: abs(x - v))
            raise ValueError(f"Invalid memory size {v}MB. Nearest valid size is {nearest}MB")
        
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SSMParameter(BaseModel):
    """AWS SSM Parameter model."""
    
    name: str = Field(..., description="Parameter name")
    type: str = Field("SecureString", description="Parameter type")
    value: Optional[str] = Field(None, description="Parameter value")
    description: Optional[str] = Field(None, description="Parameter description")
    key_id: Optional[str] = Field(None, description="KMS key ID for encryption")
    last_modified_date: Optional[datetime] = Field(None, description="Last modification timestamp")
    version: Optional[int] = Field(None, description="Parameter version")
    tier: Optional[str] = Field("Standard", description="Parameter tier")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FunctionURL(BaseModel):
    """AWS Lambda Function URL model."""
    
    function_name: str = Field(..., description="Lambda function name")
    function_url: Optional[HttpUrl] = Field(None, description="Function URL")
    auth_type: str = Field("NONE", description="Authentication type")
    cors: Optional[Dict] = Field(None, description="CORS configuration")
    creation_time: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CloudWatchLogGroup(BaseModel):
    """AWS CloudWatch Log Group model."""
    
    log_group_name: str = Field(..., description="Log group name")
    creation_time: Optional[datetime] = Field(None, description="Creation timestamp")
    retention_in_days: Optional[int] = Field(None, description="Log retention period")
    stored_bytes: Optional[int] = Field(None, description="Stored log data size")
    arn: Optional[str] = Field(None, description="Log group ARN")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# CloudFlare Models

class CloudFlareZone(BaseModel):
    """CloudFlare Zone model."""
    
    id: str = Field(..., description="Zone ID")
    name: str = Field(..., description="Zone name (domain)")
    status: str = Field(..., description="Zone status")
    paused: bool = Field(False, description="Whether zone is paused")
    type: str = Field("full", description="Zone type")
    name_servers: List[str] = Field(default_factory=list, description="Name servers")
    created_on: Optional[datetime] = Field(None, description="Creation timestamp")
    modified_on: Optional[datetime] = Field(None, description="Last modification timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CloudFlareAccessApplication(BaseModel):
    """CloudFlare Access Application model."""
    
    id: Optional[str] = Field(None, description="Application ID")
    name: str = Field(..., description="Application name")
    domain: str = Field(..., description="Application domain")
    type: str = Field("self_hosted", description="Application type")
    session_duration: str = Field("24h", description="Session duration")
    allowed_idps: List[str] = Field(default_factory=list, description="Allowed identity providers")
    auto_redirect_to_identity: bool = Field(False, description="Auto-redirect to identity provider")
    app_launcher_visible: bool = Field(True, description="Visible in app launcher")
    service_auth_401_redirect: bool = Field(False, description="Redirect on 401")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CloudFlareServiceToken(BaseModel):
    """CloudFlare Service Token model."""
    
    id: Optional[str] = Field(None, description="Token ID")
    name: str = Field(..., description="Token name")
    client_id: Optional[str] = Field(None, description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")
    duration: Optional[str] = Field(None, description="Token duration")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Configuration Models

class HomeAssistantConfig(BaseModel):
    """Home Assistant configuration."""
    
    base_url: HttpUrl = Field(..., description="Home Assistant base URL")
    
    @validator('base_url')
    def validate_https(cls, v):
        """Ensure URL uses HTTPS."""
        if v.scheme != 'https':
            raise ValueError('Home Assistant URL must use HTTPS')
        return v


class AlexaConfig(BaseModel):
    """Alexa integration configuration."""
    
    secret: str = Field(..., min_length=32, description="Alexa secret for request validation")
    
    @validator('secret')
    def validate_secret_length(cls, v):
        """Ensure secret is long enough."""
        if len(v) < 32:
            raise ValueError('Alexa secret must be at least 32 characters long')
        return v


class CloudFlareConfig(BaseModel):
    """CloudFlare configuration."""
    
    client_id: Optional[str] = Field(None, description="CloudFlare Access client ID")
    client_secret: Optional[str] = Field(None, description="CloudFlare Access client secret")
    api_token: Optional[str] = Field(None, description="CloudFlare API token")
    api_key: Optional[str] = Field(None, description="CloudFlare API key")
    email: Optional[str] = Field(None, description="CloudFlare account email")
    
    @validator('client_secret')
    def validate_client_secret_with_id(cls, v, values):
        """Ensure client secret is provided when client ID is present."""
        if values.get('client_id') and not v:
            raise ValueError('client_secret required when client_id is provided')
        return v


class ServiceConfiguration(BaseModel):
    """Service-specific configuration."""
    
    scenario: InstallationScenario = Field(..., description="Installation scenario")
    aws_region: AWSRegion = Field(AWSRegion.US_EAST_1, description="AWS region")
    home_assistant: HomeAssistantConfig = Field(..., description="Home Assistant configuration")
    alexa: Optional[AlexaConfig] = Field(None, description="Alexa configuration")
    cloudflare: Optional[CloudFlareConfig] = Field(None, description="CloudFlare configuration")
    
    @validator('alexa')
    def validate_alexa_for_scenario(cls, v, values):
        """Ensure Alexa config is provided for Alexa scenarios."""
        scenario = values.get('scenario')
        if scenario in [InstallationScenario.DIRECT_ALEXA, InstallationScenario.CLOUDFLARE_ALEXA]:
            if not v:
                raise ValueError(f'Alexa configuration required for {scenario} scenario')
        return v
    
    @validator('cloudflare')
    def validate_cloudflare_for_scenario(cls, v, values):
        """Ensure CloudFlare config is provided for CloudFlare scenarios."""
        scenario = values.get('scenario')
        if scenario in [InstallationScenario.CLOUDFLARE_ALEXA, InstallationScenario.CLOUDFLARE_IOS]:
            if not v or not (v.client_id or v.api_token):
                raise ValueError(f'CloudFlare configuration required for {scenario} scenario')
        return v


# Resource Discovery Models

class ResourceMatch(BaseModel):
    """Resource match result."""
    
    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Expected resource identifier")
    resource: Optional[Union[IAMRole, LambdaFunction, SSMParameter, FunctionURL, CloudWatchLogGroup]] = Field(
        None, description="Found resource details"
    )
    exists: bool = Field(False, description="Whether resource exists")


class PossibleResourceMatch(BaseModel):
    """Possible resource match."""
    
    resource_type: ResourceType = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Expected resource identifier")
    matches: List[Union[IAMRole, LambdaFunction, SSMParameter, FunctionURL, CloudWatchLogGroup]] = Field(
        default_factory=list, description="Possible matching resources"
    )


class ResourceDiscoveryResult(BaseModel):
    """Resource discovery result."""
    
    found_resources: List[ResourceMatch] = Field(default_factory=list, description="Exact matches found")
    missing_resources: List[Dict[str, str]] = Field(default_factory=list, description="Resources not found")
    possible_resources: List[PossibleResourceMatch] = Field(default_factory=list, description="Possible matches")


# Deployment Models

class DeploymentPlan(BaseModel):
    """Deployment plan."""
    
    scenario: InstallationScenario = Field(..., description="Target scenario")
    strategy: DeploymentStrategy = Field(DeploymentStrategy.ROLLING, description="Deployment strategy")
    resources_to_create: List[Dict] = Field(default_factory=list, description="Resources to create")
    resources_to_update: List[Dict] = Field(default_factory=list, description="Resources to update")
    resources_to_delete: List[Dict] = Field(default_factory=list, description="Resources to delete")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    prerequisites_met: bool = Field(False, description="Whether prerequisites are satisfied")


class DeploymentResult(BaseModel):
    """Deployment result."""
    
    success: bool = Field(..., description="Whether deployment succeeded")
    created_resources: List[ResourceMatch] = Field(default_factory=list, description="Successfully created resources")
    failed_resources: List[Dict] = Field(default_factory=list, description="Failed resource operations")
    function_urls: Dict[str, str] = Field(default_factory=dict, description="Created function URLs")
    duration: Optional[float] = Field(None, description="Deployment duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if deployment failed")


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
    checks: Dict[str, bool] = Field(default_factory=dict, description="Individual check results")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    last_check: Optional[datetime] = Field(None, description="Last check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
