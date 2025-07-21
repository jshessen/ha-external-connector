"""Configuration management for the Home Assistant External Connector."""

import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .manager import (
    ConfigurationManager,
    ConfigurationState,
    InstallationScenario,
    MatchedResource,
    ResourceDiscoveryResult,
    ResourceRequirement,
    config_manager,
)


class Settings(BaseSettings):
    """
    Application settings.
    """

    # AWS Configuration
    aws_profile: str | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None

    # CloudFlare Configuration
    cf_api_token: str | None = None
    cf_api_key: str | None = None
    cf_email: str | None = None
    cf_client_id: str | None = None
    cf_client_secret: str | None = None

    # Home Assistant Configuration
    ha_base_url: str | None = None
    alexa_secret: str | None = None

    # Application Configuration
    log_level: str | None = None
    dry_run: bool | None = None
    verbose: bool | None = None

    # Timeouts and Limits
    request_timeout: int | None = None
    max_concurrent_requests: int | None = None
    retry_attempts: int | None = None

    # Lambda Configuration Defaults
    default_lambda_timeout: int | None = None
    default_lambda_memory: int | None = None

    @field_validator("aws_region")
    @classmethod
    def validate_aws_region(cls, v: str | None) -> str:
        """Validate AWS region format."""
        if not v:
            return "us-east-1"  # Default region
        if len(v.split("-")) < 3:
            raise ValueError("Invalid AWS region format")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str | None) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v is None:
            return "INFO"  # Default log level
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("ha_base_url")
    @classmethod
    def validate_ha_base_url(cls, v: str | None) -> str | None:
        """Validate Home Assistant URL."""
        if v and not v.startswith("https://"):
            raise ValueError("Home Assistant URL must use HTTPS")
        return v

    @field_validator("alexa_secret")
    @classmethod
    def validate_alexa_secret(cls, v: str | None) -> str | None:
        """Validate Alexa secret length."""
        if v and len(v) < 32:
            raise ValueError("Alexa secret must be at least 32 characters long")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


def load_config() -> Settings:
    """Load configuration from environment and/or file."""
    return Settings()


def get_config_dir() -> Path:
    """Get configuration directory."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "ha-connector"

    return Path.home() / ".config" / "ha-connector"


def ensure_config_dir() -> Path:
    """Ensure configuration directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


__all__ = [
    # Settings
    "Settings",
    "load_config",
    "get_config_dir",
    "ensure_config_dir",
    # Configuration Manager
    "ConfigurationManager",
    "ConfigurationState",
    "InstallationScenario",
    "ResourceRequirement",
    "MatchedResource",
    "ResourceDiscoveryResult",
    "config_manager",
]


# Global settings instance
settings = load_config()
