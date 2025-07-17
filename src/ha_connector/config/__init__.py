"""Configuration management for the Home Assistant External Connector."""

from typing import Optional, Dict, Any
from pathlib import Path
import os

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    aws_profile: Optional[str] = None
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    # CloudFlare Configuration
    cf_api_token: Optional[str] = None
    cf_api_key: Optional[str] = None
    cf_email: Optional[str] = None
    cf_client_id: Optional[str] = None
    cf_client_secret: Optional[str] = None

    # Home Assistant Configuration
    ha_base_url: Optional[str] = None
    alexa_secret: Optional[str] = None

    # Application Configuration
    log_level: Optional[str] = None
    dry_run: Optional[bool] = None
    verbose: Optional[bool] = None

    # Timeouts and Limits
    request_timeout: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    retry_attempts: Optional[int] = None

    # Lambda Configuration Defaults
    default_lambda_timeout: Optional[int] = None
    default_lambda_memory: Optional[int] = None

    @validator('aws_region')
    @classmethod
    def validate_aws_region(cls, v):
        """Validate AWS region format."""
        if not v or len(v.split('-')) < 3:
            raise ValueError('Invalid AWS region format')
        return v

    @validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()

    @validator('ha_base_url')
    @classmethod
    def validate_ha_base_url(cls, v):
        """Validate Home Assistant URL."""
        if v and not v.startswith('https://'):
            raise ValueError('Home Assistant URL must use HTTPS')
        return v

    @validator('alexa_secret')
    @classmethod
    def validate_alexa_secret(cls, v):
        """Validate Alexa secret length."""
        if v and len(v) < 32:
            raise ValueError('Alexa secret must be at least 32 characters long')
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


def load_config() -> Settings:
    """Load configuration from environment and/or file."""
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
