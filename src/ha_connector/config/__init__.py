"""Configuration management for the Home Assistant External Connector."""

from typing import Optional, Dict, Any
from pathlib import Path
import os

from pydantic import Field, validator
from pydantic_settings import BaseSettings

from .manager import (
    ConfigurationManager,
    ConfigurationState,
    InstallationScenario,
    ResourceRequirement,
    MatchedResource,
    ResourceDiscoveryResult,
    config_manager
)


class Settings(BaseSettings):
    """Application settings."""
    
    # AWS Configuration
    aws_profile: str = Field("default", env="AWS_PROFILE")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[str] = Field(None, env="AWS_SESSION_TOKEN")
    
    # CloudFlare Configuration
    cf_api_token: Optional[str] = Field(None, env="CF_API_TOKEN")
    cf_api_key: Optional[str] = Field(None, env="CF_API_KEY")
    cf_email: Optional[str] = Field(None, env="CF_EMAIL")
    cf_client_id: Optional[str] = Field(None, env="CF_CLIENT_ID")
    cf_client_secret: Optional[str] = Field(None, env="CF_CLIENT_SECRET")
    
    # Home Assistant Configuration
    ha_base_url: Optional[str] = Field(None, env="HA_BASE_URL")
    alexa_secret: Optional[str] = Field(None, env="ALEXA_SECRET")
    
    # Application Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    dry_run: bool = Field(False, env="DRY_RUN")
    verbose: bool = Field(False, env="VERBOSE")
    
    # Timeouts and Limits
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    retry_attempts: int = Field(3, env="RETRY_ATTEMPTS")
    
    # Lambda Configuration Defaults
    default_lambda_timeout: int = Field(30, env="DEFAULT_LAMBDA_TIMEOUT")
    default_lambda_memory: int = Field(512, env="DEFAULT_LAMBDA_MEMORY")
    
    @validator('aws_region')
    def validate_aws_region(cls, v):
        """Validate AWS region format."""
        if not v or len(v.split('-')) < 3:
            raise ValueError('Invalid AWS region format')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('ha_base_url')
    def validate_ha_base_url(cls, v):
        """Validate Home Assistant URL."""
        if v and not v.startswith('https://'):
            raise ValueError('Home Assistant URL must use HTTPS')
        return v
    
    @validator('alexa_secret')
    def validate_alexa_secret(cls, v):
        """Validate Alexa secret length."""
        if v and len(v) < 32:
            raise ValueError('Alexa secret must be at least 32 characters long')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_config(config_file: Optional[Path] = None) -> Settings:
    """Load configuration from environment and/or file."""
    if config_file and config_file.exists():
        return Settings(_env_file=config_file)
    return Settings()


def get_config_dir() -> Path:
    """Get configuration directory."""
    config_home = os.environ.get('XDG_CONFIG_HOME')
    if config_home:
        return Path(config_home) / 'ha-connector'
    
    return Path.home() / '.config' / 'ha-connector'


def ensure_config_dir() -> Path:
    """Ensure configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


__all__ = [
    # Settings
    'Settings',
    'load_config',
    'get_config_dir',
    'ensure_config_dir',
    
    # Configuration Manager
    'ConfigurationManager',
    'ConfigurationState', 
    'InstallationScenario',
    'ResourceRequirement',
    'MatchedResource',
    'ResourceDiscoveryResult',
    'config_manager',
]


# Global settings instance
settings = load_config()
