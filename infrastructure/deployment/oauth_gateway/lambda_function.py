"""
🔐 CLOUDFLARE OAUTH GATEWAY: Dedicated OAuth Authentication Service 🌐

Handles OAuth token exchange for Alexa Smart Home account linking.
Provides optional CloudFlare protection for enhanced security.

Original work: Copyright 2019 Jason Hu <awaregit at gmail.com>
Enhanced by: Jeff Hessenflow <jeff.hessenflow@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# pylint: disable=too-many-lines,too-many-branches

from __future__ import annotations

import base64
import configparser
import json
import logging
import os
import re
import time
import urllib.parse
from typing import Any

import boto3
import urllib3
from botocore.exceptions import ClientError, NoCredentialsError

# Use generic boto3 client type for runtime compatibility
SSMClient = Any

# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===

# This section contains shared configuration embedded for deployment


# === PUBLIC API ===
# Unified configuration loading and caching functions
__all__ = [
    "load_configuration",
    "cache_configuration",
    "get_cache_stats",
    "test_dynamic_deployment",
    "load_environment",
    "validate_configuration",
    # Configuration management system
    "ConfigurationGeneration",
    "ConfigurationManager",
    "load_multi_generation_configuration",
    "get_configuration_stats",
    # Security infrastructure
    "SecurityConfig",
    "RateLimiter",
    "SecurityValidator",
    "SecurityEventLogger",
    "AlexaValidator",
    # Performance monitoring
    "PerformanceMonitor",
    "ConnectionPoolManager",
    "ResponseCache",
    "RequestBatcher",
    "create_structured_logger",
    "extract_correlation_id",
    # OAuth-specific helpers
    "OAuthRequestProcessor",
    "OAuthSecurityValidator",
    "OAuthConfigurationManager",
]


def test_dynamic_deployment() -> str:
    """Test function to prove dynamic deployment works automatically."""
    return "Dynamic deployment working! This function was auto-detected and embedded."


# === SHARED CONSTANTS ===
# These constants are used across all Lambda functions

# Cache and performance settings
CONTAINER_CACHE_TTL = int(os.environ.get("CONTAINER_CACHE_TTL", "300"))  # 5 minutes
SHARED_CACHE_TTL = int(os.environ.get("SHARED_CACHE_TTL", "900"))  # 15 minutes
OAUTH_TOKEN_TTL = int(os.environ.get("OAUTH_TOKEN_TTL", "3600"))  # 1 hour
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

# Security and rate limiting
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "60"))
MAX_REQUESTS_PER_IP_PER_MINUTE = int(
    os.environ.get("MAX_REQUESTS_PER_IP_PER_MINUTE", "10")
)
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_REQUEST_SIZE_BYTES = int(os.environ.get("MAX_REQUEST_SIZE_BYTES", "8192"))
MAX_CLIENT_SECRET_LENGTH = int(os.environ.get("MAX_CLIENT_SECRET_LENGTH", "512"))
MAX_URL_LENGTH = int(os.environ.get("MAX_URL_LENGTH", "2048"))
SUSPICIOUS_REQUEST_THRESHOLD = int(os.environ.get("SUSPICIOUS_REQUEST_THRESHOLD", "5"))
BLOCK_DURATION_SECONDS = int(os.environ.get("BLOCK_DURATION_SECONDS", "300"))

# Table names
SHARED_CACHE_TABLE = os.environ.get(
    "SHARED_CACHE_TABLE", "ha-external-connector-config-cache"
)
OAUTH_TOKEN_CACHE_TABLE = os.environ.get(
    "OAUTH_TOKEN_CACHE_TABLE", "ha-external-connector-oauth-cache"
)

# Shared clients for Lambda container reuse
_ssm_client: SSMClient | None = None
_dynamodb_client: Any = None  # DynamoDB types not available - use Any
_config_cache: dict[str, Any] = {}

# Logger for shared operations
_logger = logging.getLogger("SharedConfiguration")
_logger.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════
# Configuration Management System: Multi-Generation Configuration Management
# ═══════════════════════════════════════════════════════════════════════════


class ConfigurationGeneration:
    """Configuration generation detection and management."""

    GEN_1_ENV_ONLY = "generation_1_env_only"
    GEN_2_ENV_SSM_JSON = "generation_2_env_ssm_json"
    GEN_3_MODULAR_SSM = "generation_3_modular_ssm"


class ConfigurationManager:
    """
    Configuration Management Engine: Multi-Generation Support with Caching

    Handles all 3 generations of configuration with intelligent detection,
    environment variable overrides, and performance optimization through caching.

    CONFIGURATION GENERATION SUPPORT:

    **Generation 1 (ENV-only):**
    - Pure environment variables (HA_BASE_URL, HA_TOKEN, etc.)
    - No SSM dependencies
    - Fastest possible performance (0ms configuration loading)
    - Ideal for simple deployments

    **Generation 2 (ENV→SSM JSON):**
    - Environment variables with SSM fallback
    - Single JSON parameter in SSM (e.g., /homeassistant/config/appConfig)
    - Foundation pattern compatibility
    - Good for existing deployments transitioning to SSM

    **Generation 3 (Modular SSM + Caching):**
    - Structured SSM parameters
      (/homeassistant/alexa/ha_config, /homeassistant/oauth/config)
    - DynamoDB shared caching for performance
    - Environment variable overrides for any config option
    - Maximum flexibility and performance optimization

    CACHE-FIRST PERFORMANCE STRATEGY:

    1. **Environment Variables** (0ms) - Instant access, highest priority
    2. **Container Cache** (1-10ms) - Warm Lambda reuse
    3. **DynamoDB Shared Cache** (20-50ms) - Cross-Lambda sharing
    4. **SSM Parameter Store** (100-200ms) - Authoritative source
    5. **Graceful Fallback** (0ms) - Minimal working configuration
    """

    def __init__(self):
        self._ssm_client: SSMClient | None = None
        self._instance_dynamodb_client: Any = None  # type: ignore[reportUnknownMemberType]
        self._container_cache: dict[str, Any] = {}
        self._cache_ttl = 900  # 15 minutes

    def load_configuration(
        self,
        config_section: str = "ha_config",
        app_config_path: str | None = None,
        force_generation: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """
        Load configuration with generation detection and environment overrides.

        Args:
            config_section: Configuration section to load (ha_config,
                oauth_config, etc.)
            app_config_path: SSM path for Gen 2/3 configurations
            force_generation: Force specific generation for testing

        Returns:
            Tuple of (configuration_dict, generation_used)
        """
        _logger.info("Loading configuration for section: %s", config_section)

        # Check container cache first for performance
        cache_key = f"{config_section}:{app_config_path or 'env_only'}"
        cached_config = self._get_container_cache(cache_key)
        if cached_config:
            _logger.debug("Configuration loaded from container cache")
            return cached_config["config"], cached_config["generation"]

        # Detect configuration generation
        generation = force_generation or self._detect_configuration_generation(
            app_config_path
        )
        _logger.info("Detected configuration generation: %s", generation)

        # Load configuration based on generation
        if generation == ConfigurationGeneration.GEN_1_ENV_ONLY:
            config = self._load_generation_1_env_only(config_section)
        elif generation == ConfigurationGeneration.GEN_2_ENV_SSM_JSON:
            config = self._load_generation_2_env_ssm_json(
                config_section, app_config_path
            )
        elif generation == ConfigurationGeneration.GEN_3_MODULAR_SSM:
            config = self._load_generation_3_modular_ssm(
                config_section, app_config_path
            )
        else:
            _logger.warning("⚠️ Unknown generation, falling back to Gen 1")
            config = self._load_generation_1_env_only(config_section)
            generation = ConfigurationGeneration.GEN_1_ENV_ONLY

        # Apply environment variable overrides (works for all generations)
        config = self._apply_environment_overrides(config, config_section)

        # Cache the result for performance
        self._set_container_cache(cache_key, config, generation)

        _logger.info("✅ Configuration loaded successfully (%s)", generation)
        return config, generation

    def _detect_configuration_generation(self, app_config_path: str | None) -> str:
        """Detect which configuration generation is being used."""
        # Gen 1: Pure environment variables (no SSM path provided)
        if not app_config_path:
            if os.environ.get("HA_BASE_URL") and os.environ.get("HA_TOKEN"):
                return ConfigurationGeneration.GEN_1_ENV_ONLY
            return ConfigurationGeneration.GEN_1_ENV_ONLY

        # Gen 2 vs Gen 3: Check SSM structure
        try:
            ssm_client = self._get_ssm_client()

            # Try Gen 3 first (structured parameters)
            try:
                response = ssm_client.get_parameters_by_path(
                    Path=app_config_path,
                    Recursive=False,
                    WithDecryption=True,
                    MaxResults=5,
                )

                # Look for structured parameter names
                parameters = response.get("Parameters", [])
                param_names = [p.get("Name", "").split("/")[-1] for p in parameters]
                gen_3_sections = ["ha_config", "oauth_config", "cloudflare_config"]
                for param_name in param_names:
                    if any(section in param_name for section in gen_3_sections):
                        return ConfigurationGeneration.GEN_3_MODULAR_SSM

            except ClientError:
                pass

            # Try Gen 2 (single JSON parameter)
            try:
                gen_2_paths = [
                    f"{app_config_path.rstrip('/')}/appConfig",
                    app_config_path,
                ]
                for path in gen_2_paths:
                    try:
                        ssm_client.get_parameter(Name=path, WithDecryption=True)
                        return ConfigurationGeneration.GEN_2_ENV_SSM_JSON
                    except ClientError:
                        continue

            except ClientError:
                pass

        except (ClientError, NoCredentialsError):
            _logger.debug("SSM access failed, defaulting to Gen 1")

        # Default to Gen 1 if detection fails
        _logger.debug("No SSM configuration found, using Gen 1")
        return ConfigurationGeneration.GEN_1_ENV_ONLY

    def _load_generation_1_env_only(self, config_section: str) -> dict[str, Any]:
        """Load Generation 1 configuration (pure environment variables)."""
        _logger.debug("📍 Loading Gen 1 configuration from environment variables")

        if config_section == "ha_config":
            return {
                "base_url": os.environ.get("HA_BASE_URL", ""),
                "token": os.environ.get("HA_TOKEN", ""),
                "verify_ssl": os.environ.get("HA_VERIFY_SSL", "true").lower() == "true",
                "timeout": int(os.environ.get("HA_TIMEOUT", "30")),
            }
        if config_section == "oauth_config":
            return {
                "client_id": os.environ.get("OAUTH_CLIENT_ID", ""),
                "client_secret": os.environ.get("OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": os.environ.get("OAUTH_REDIRECT_URI", ""),
            }
        if config_section == "cloudflare_config":
            return {
                "client_id": os.environ.get("CF_CLIENT_ID", ""),
                "client_secret": os.environ.get("CF_CLIENT_SECRET", ""),
                "enabled": bool(os.environ.get("CF_CLIENT_ID")),
            }
        if config_section == "security_config":
            return {
                "alexa_secret": os.environ.get("ALEXA_SECRET", ""),
                "wrapper_secret": os.environ.get("WRAPPER_SECRET", ""),
                "api_key": os.environ.get("API_KEY", ""),
            }
        if config_section == "aws_config":
            return {
                "region": os.environ.get("AWS_REGION", "us-east-1"),
                "timeout": int(os.environ.get("AWS_TIMEOUT", "30")),
                "max_retries": int(os.environ.get("AWS_MAX_RETRIES", "3")),
            }
        _logger.warning("⚠️ Unknown config section for Gen 1: %s", config_section)
        return {}

    def _load_generation_2_env_ssm_json(
        self, config_section: str, app_config_path: str | None
    ) -> dict[str, Any]:
        """Load Generation 2 configuration (environment with SSM JSON fallback)."""
        _logger.debug("📍 Loading Gen 2 configuration (ENV → SSM JSON)")

        # Try environment variables first
        env_config = self._load_generation_1_env_only(config_section)
        if self._is_config_complete(env_config, config_section):
            _logger.debug("Using environment variables for Gen 2")
            return env_config

        # Fallback to SSM JSON parameter
        if not app_config_path:
            _logger.warning("⚠️ No SSM path provided for Gen 2 fallback")
            return env_config

        try:
            ssm_client = self._get_ssm_client()
            gen_2_paths = [
                f"{app_config_path.rstrip('/')}/appConfig",
                app_config_path,
                f"{app_config_path.rstrip('/')}/config",
            ]

            for path in gen_2_paths:
                try:
                    response = ssm_client.get_parameter(Name=path, WithDecryption=True)
                    param_value = response.get("Parameter", {}).get("Value", "")
                    json_config = json.loads(param_value)
                    structured_config = self._map_json_config_to_structure(
                        json_config, config_section
                    )
                    _logger.debug("✅ Loaded Gen 2 config from SSM: %s", path)
                    return structured_config
                except (ClientError, json.JSONDecodeError):
                    continue

            _logger.warning("⚠️ No SSM JSON parameter found, using environment config")
            return env_config

        except (ClientError, json.JSONDecodeError, NoCredentialsError) as e:
            _logger.warning("⚠️ Failed to load Gen 2 SSM config: %s", e)
            return env_config

    def _load_generation_3_modular_ssm(
        self, config_section: str, app_config_path: str | None
    ) -> dict[str, Any]:
        """Load Generation 3 configuration (modular SSM with caching)."""
        _logger.debug("📍 Loading Gen 3 configuration (Modular SSM + Caching)")

        # Check shared cache first
        cache_key = f"{app_config_path}:{config_section}"
        shared_config = self._get_shared_cache(cache_key)
        if shared_config:
            _logger.debug("Configuration loaded from shared cache")
            return shared_config

        # Load from SSM structured parameters
        try:
            ssm_client = self._get_ssm_client()
            if app_config_path is None:
                raise ValueError("app_config_path is required for Generation 3")
            param_path = f"{app_config_path.rstrip('/')}/{config_section}"

            response = ssm_client.get_parameter(Name=param_path, WithDecryption=True)
            param_value = response.get("Parameter", {}).get("Value", "")
            config = json.loads(param_value)

            # Cache for future requests
            self._set_shared_cache(cache_key, config)

            _logger.debug("✅ Loaded Gen 3 config from SSM: %s", param_path)
            return config

        except (ClientError, json.JSONDecodeError, NoCredentialsError) as e:
            _logger.warning("⚠️ Failed to load Gen 3 config: %s", e)

            # Fallback to environment variables
            _logger.debug("🔄 Falling back to environment variables")
            return self._load_generation_1_env_only(config_section)

    def _apply_environment_overrides(
        self, config: dict[str, Any], config_section: str
    ) -> dict[str, Any]:
        """Apply environment variable overrides to any configuration."""
        # Environment variable override mappings
        override_mappings: dict[
            str, dict[str, str | tuple[str, type[int]] | tuple[str, type[bool]]]
        ] = {
            "ha_config": {
                "HA_BASE_URL": "base_url",
                "HA_TOKEN": "token",
                "HA_VERIFY_SSL": ("verify_ssl", bool),
                "HA_TIMEOUT": ("timeout", int),
            },
            "oauth_config": {
                "OAUTH_CLIENT_ID": "client_id",
                "OAUTH_CLIENT_SECRET": "client_secret",
                "OAUTH_REDIRECT_URI": "redirect_uri",
            },
            "cloudflare_config": {
                "CF_CLIENT_ID": "client_id",
                "CF_CLIENT_SECRET": "client_secret",
                "CF_ENABLED": ("enabled", bool),
            },
            "security_config": {
                "ALEXA_SECRET": "alexa_secret",
                "WRAPPER_SECRET": "wrapper_secret",
                "API_KEY": "api_key",
            },
            "aws_config": {
                "AWS_REGION": "region",
                "AWS_TIMEOUT": ("timeout", int),
                "AWS_MAX_RETRIES": ("max_retries", int),
            },
        }

        section_overrides = override_mappings.get(config_section, {})
        override_count = 0

        for env_var, config_mapping in section_overrides.items():
            env_value = os.environ.get(env_var)
            if env_value:
                if isinstance(config_mapping, tuple):
                    config_key, transform_func = config_mapping
                    try:
                        if transform_func is bool:
                            # Handle boolean conversion specifically
                            config[config_key] = env_value.lower() == "true"
                        elif transform_func is int:
                            # Handle integer conversion
                            config[config_key] = int(env_value)
                        else:
                            # Generic transformation
                            config[config_key] = transform_func(env_value)
                        override_count += 1
                    except (ValueError, TypeError) as e:
                        _logger.warning("⚠️ Failed to transform %s: %s", env_var, e)
                else:
                    config[config_mapping] = env_value
                    override_count += 1

        if override_count > 0:
            _logger.info(
                "Applied %d environment overrides to %s",
                override_count,
                config_section,
            )

        return config

    def _is_config_complete(self, config: dict[str, Any], config_section: str) -> bool:
        """Check if configuration has required fields populated."""
        required_fields = {
            "ha_config": ["base_url"],
            "oauth_config": ["client_id"],
            "cloudflare_config": [],  # All optional
            "security_config": [],  # All optional
            "aws_config": ["region"],
        }

        section_required = required_fields.get(config_section, [])
        return all(config.get(field) for field in section_required)

    def _map_json_config_to_structure(
        self, json_config: dict[str, Any], config_section: str
    ) -> dict[str, Any]:
        """Map flat JSON configuration to structured format."""
        if config_section == "ha_config":
            return {
                "base_url": json_config.get("HA_BASE_URL", ""),
                "token": json_config.get("HA_TOKEN", ""),
                "verify_ssl": json_config.get("HA_VERIFY_SSL", True),
                "timeout": json_config.get("HA_TIMEOUT", 30),
            }
        if config_section == "oauth_config":
            return {
                "client_id": json_config.get("OAUTH_CLIENT_ID", ""),
                "client_secret": json_config.get("OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": json_config.get("OAUTH_REDIRECT_URI", ""),
            }
        if config_section == "cloudflare_config":
            return {
                "client_id": json_config.get("CF_CLIENT_ID", ""),
                "client_secret": json_config.get("CF_CLIENT_SECRET", ""),
                "enabled": bool(json_config.get("CF_CLIENT_ID")),
            }
        if config_section == "security_config":
            return {
                "alexa_secret": json_config.get("ALEXA_SECRET", ""),
                "wrapper_secret": json_config.get("WRAPPER_SECRET", ""),
                "api_key": json_config.get("API_KEY", ""),
            }
        if config_section == "aws_config":
            return {
                "region": json_config.get("AWS_REGION", "us-east-1"),
                "timeout": json_config.get("AWS_TIMEOUT", 30),
                "max_retries": json_config.get("AWS_MAX_RETRIES", 3),
            }
        return {}

    def _get_container_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get configuration from container cache."""
        if cache_key in self._container_cache:
            cache_entry = self._container_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self._cache_ttl:
                return cache_entry
            # Remove expired entry
            del self._container_cache[cache_key]
        return None

    def _set_container_cache(
        self, cache_key: str, config: dict[str, Any], generation: str
    ) -> None:
        """Store configuration in container cache."""
        self._container_cache[cache_key] = {
            "config": config,
            "generation": generation,
            "timestamp": time.time(),
        }

    def _get_shared_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get configuration from DynamoDB shared cache."""
        try:
            dynamodb = self._get_dynamodb_client()
            table_name = os.environ.get(
                "SHARED_CACHE_TABLE", "ha-external-connector-config-cache"
            )

            response = dynamodb.get_item(
                TableName=table_name, Key={"cache_key": {"S": cache_key}}
            )

            if "Item" in response:
                item = response["Item"]
                ttl = int(item.get("ttl", {}).get("N", "0"))
                if time.time() < ttl:
                    return json.loads(item["config"]["S"])
        except (ClientError, NoCredentialsError, ValueError, KeyError) as e:
            _logger.debug("Shared cache access failed: %s", e)
        return None

    def _set_shared_cache(self, cache_key: str, config: dict[str, Any]) -> None:
        """Store configuration in DynamoDB shared cache."""
        try:
            dynamodb = self._get_dynamodb_client()
            table_name = os.environ.get(
                "SHARED_CACHE_TABLE", "ha-external-connector-config-cache"
            )

            dynamodb.put_item(
                TableName=table_name,
                Item={
                    "cache_key": {"S": cache_key},
                    "config": {"S": json.dumps(config)},
                    "ttl": {"N": str(int(time.time() + self._cache_ttl))},
                    "generation": {"S": "cached_gen_3"},
                    "timestamp": {"S": str(time.time())},
                },
            )
        except (ClientError, NoCredentialsError, ValueError, KeyError) as e:
            _logger.debug("Shared cache store failed: %s", e)

    def _get_ssm_client(self) -> SSMClient:
        """Get SSM client with lazy initialization."""
        if self._ssm_client is None:
            self._ssm_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
                "ssm", region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
        return self._ssm_client

    def _get_dynamodb_client(self) -> Any:  # DynamoDB types not available
        """Get DynamoDB client with lazy initialization."""
        if self._instance_dynamodb_client is None:
            self._instance_dynamodb_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
                "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
        return self._instance_dynamodb_client  # pyright: ignore

    def get_stats(self) -> dict[str, Any]:
        """Get configuration manager statistics."""
        return {
            "container_cache_entries": len(self._container_cache),
            "cache_ttl_seconds": self._cache_ttl,
            "last_access_time": getattr(self, "_last_access", None),
            "current_instance_id": id(self),
        }


# Global configuration manager instance for Lambda container reuse
_config_manager = ConfigurationManager()


def load_multi_generation_configuration(
    config_section: str = "ha_config",
    app_config_path: str | None = None,
    force_generation: str | None = None,
) -> tuple[dict[str, Any], str]:
    """
    Public API for multi-generation configuration loading.

    Args:
        config_section: Configuration section to load (ha_config, oauth_config, etc.)
        app_config_path: SSM path for Gen 2/3 configurations
        force_generation: Force specific generation for testing

    Returns:
        Tuple of (configuration_dict, generation_used)
    """
    return _config_manager.load_configuration(
        config_section=config_section,
        app_config_path=app_config_path,
        force_generation=force_generation,
    )


def get_configuration_stats() -> dict[str, Any]:
    """
    Get comprehensive statistics about the configuration management system.

    Returns:
        Statistics including cache size, TTL, generation info, and
        system performance metrics.
    """
    try:
        # Get or create the global configuration manager instance
        global _config_manager  # pylint: disable=global-statement
        if not _config_manager:
            _config_manager = ConfigurationManager()

        supported_gens = ["Gen1_ENV_ONLY", "Gen2_ENV_TO_SSM", "Gen3_MODULAR_SSM"]
        manager_stats = _config_manager.get_stats()
        return {
            **manager_stats,
            "supported_generations": supported_gens,
        }
    except Exception as e:  # pylint: disable=broad-except
        _logger.warning("Failed to get configuration stats: %s", e)
        supported_gens = ["Gen1_ENV_ONLY", "Gen2_ENV_TO_SSM", "Gen3_MODULAR_SSM"]
        return {
            "error": str(e),
            "container_cache_entries": 0,
            "cache_ttl_seconds": 0,
            "supported_generations": supported_gens,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Shared Security Infrastructure
# ═══════════════════════════════════════════════════════════════════════════


class SecurityConfig:
    """
    Security Configuration: Enterprise Protection Standards

    Security operations manual containing all the rules, limits, and standards
    for enterprise-grade protection against DDoS attacks, memory exhaustion,
    injection attacks, and brute force attempts.

    Like managing building capacity and package inspection standards to prevent
    overcrowding and ensure visitor safety.
    """

    # Rate limiting settings (now using standardized configuration)
    MAX_REQUESTS_PER_MINUTE = MAX_REQUESTS_PER_MINUTE
    MAX_REQUESTS_PER_IP_PER_MINUTE = MAX_REQUESTS_PER_IP_PER_MINUTE
    RATE_LIMIT_WINDOW_SECONDS = RATE_LIMIT_WINDOW_SECONDS

    # Request validation limits (now using standardized configuration)
    MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_BYTES
    MAX_CLIENT_SECRET_LENGTH = MAX_CLIENT_SECRET_LENGTH
    MAX_URL_LENGTH = MAX_URL_LENGTH

    # Security monitoring (now using standardized configuration)
    SUSPICIOUS_REQUEST_THRESHOLD = SUSPICIOUS_REQUEST_THRESHOLD
    BLOCK_DURATION_SECONDS = BLOCK_DURATION_SECONDS


class RateLimiter:
    """
    Traffic Control System: Enterprise Visitor Flow Management

    Professional traffic control system that monitors visitor flow, prevents
    overcrowding, and temporarily blocks problematic visitors. In-memory rate
    limiting optimized for AWS Lambda with automatic cleanup and block management.

    Like a smart building entrance that remembers visitors, controls capacity,
    and blocks problem sources while reporting suspicious patterns.
    """

    def __init__(self) -> None:
        # Visitor tracking databases
        self._requests: dict[str, list[tuple[float]]] = {}  # {ip: [(timestamp,), ...]}
        self._blocked_ips: dict[str, float] = {}  # {ip: block_until_timestamp}
        self._global_requests: list[tuple[float]] = []  # [(timestamp,), ...]

    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.

        Returns:
            Tuple of (is_allowed: bool, reason: str)
        """
        current_time = time.time()

        # Clean up old entries
        self._cleanup_old_entries(current_time)

        # Check if IP is currently blocked
        if client_ip in self._blocked_ips:
            if current_time < self._blocked_ips[client_ip]:
                return False, f"IP {client_ip} is temporarily blocked"
            # Block expired, remove it
            del self._blocked_ips[client_ip]

        # Check global rate limit
        recent_global = [
            req
            for req in self._global_requests
            if current_time - req[0] < SecurityConfig.RATE_LIMIT_WINDOW_SECONDS
        ]

        if len(recent_global) >= SecurityConfig.MAX_REQUESTS_PER_MINUTE:
            _logger.warning(
                "🚨 Global rate limit exceeded: %d requests in last minute",
                len(recent_global),
            )
            return False, "Global rate limit exceeded"

        # Check per-IP rate limit
        if client_ip not in self._requests:
            self._requests[client_ip] = []

        recent_ip_requests = [
            req
            for req in self._requests[client_ip]
            if current_time - req[0] < SecurityConfig.RATE_LIMIT_WINDOW_SECONDS
        ]

        if len(recent_ip_requests) >= SecurityConfig.MAX_REQUESTS_PER_IP_PER_MINUTE:
            _logger.warning(
                "🚨 Per-IP rate limit exceeded for %s: %d requests in last minute",
                client_ip,
                len(recent_ip_requests),
            )

            # Block IP if too many violations
            if len(recent_ip_requests) >= SecurityConfig.SUSPICIOUS_REQUEST_THRESHOLD:
                self._blocked_ips[client_ip] = (
                    current_time + SecurityConfig.BLOCK_DURATION_SECONDS
                )
                _logger.error(
                    "🚫 Blocking suspicious IP %s for %d seconds",
                    client_ip,
                    SecurityConfig.BLOCK_DURATION_SECONDS,
                )

            return False, f"Per-IP rate limit exceeded for {client_ip}"

        # Record this request
        self._global_requests.append((current_time,))
        self._requests[client_ip].append((current_time,))

        return True, "Request allowed"

    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove old entries to prevent memory buildup."""
        cutoff_time = current_time - SecurityConfig.RATE_LIMIT_WINDOW_SECONDS

        # Clean global requests
        self._global_requests = [
            req for req in self._global_requests if req[0] > cutoff_time
        ]

        # Clean per-IP requests
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                req for req in self._requests[ip] if req[0] > cutoff_time
            ]
            # Remove IPs with no recent requests
            if not self._requests[ip]:
                del self._requests[ip]


class SecurityValidator:
    """
    Security Screening Department: Professional Validation Services

    Security screening department that inspects visitor credentials, packages,
    and documentation. Static validation methods with security-first design
    provide protection against injection and overflow attacks.

    Like airport security checking package size, credential format, and
    destination legitimacy before allowing entry.
    """

    @staticmethod
    def validate_request_size(content_length: int) -> tuple[bool, str]:
        """Validate request size is within acceptable limits."""
        if content_length > SecurityConfig.MAX_REQUEST_SIZE_BYTES:
            return (
                False,
                (
                    f"Request too large: {content_length} bytes "
                    f"(max: {SecurityConfig.MAX_REQUEST_SIZE_BYTES})"
                ),
            )
        return True, "Request size valid"

    @staticmethod
    def validate_client_secret(client_secret: str) -> tuple[bool, str]:
        """Validate client secret format and length."""
        if not client_secret:
            return False, "Client secret is required"

        if len(client_secret) > SecurityConfig.MAX_CLIENT_SECRET_LENGTH:
            return (
                False,
                (
                    f"Client secret too long: {len(client_secret)} chars "
                    f"(max: {SecurityConfig.MAX_CLIENT_SECRET_LENGTH})"
                ),
            )

        # Basic format validation - should be printable ASCII
        if not all(32 <= ord(c) <= 126 for c in client_secret):
            return False, "Client secret contains invalid characters"

        return True, "Client secret valid"

    @staticmethod
    def validate_destination_url(url: str) -> tuple[bool, str]:
        """Validate destination URL format and safety."""
        if not url:
            return False, "Destination URL is required"

        if len(url) > SecurityConfig.MAX_URL_LENGTH:
            return (
                False,
                (
                    f"URL too long: {len(url)} chars "
                    f"(max: {SecurityConfig.MAX_URL_LENGTH})"
                ),
            )

        # Basic URL format validation
        if not (url.startswith("https://") or url.startswith("http://")):
            return False, "URL must use HTTP or HTTPS protocol"

        # Check for obviously malicious patterns
        suspicious_patterns = ["../", "..\\", "javascript:", "data:", "file:"]
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return False, f"URL contains suspicious pattern: {pattern}"

        return True, "URL valid"

    @staticmethod
    def sanitize_log_data(data: str, max_length: int = 100) -> str:
        """Sanitize data for safe logging."""
        if not data:
            return "[empty]"

        # Truncate if too long
        if len(data) > max_length:
            data = data[:max_length] + "...[truncated]"

        # Remove potentially sensitive patterns
        sensitive_patterns = [
            (r'(?i)(password|secret|token|key)["\s]*[:=]["\s]*[^"\s]+', "[REDACTED]"),
            (r'(?i)authorization["\s]*:["\s]*[^"\s]+', "authorization: [REDACTED]"),
        ]

        for pattern, replacement in sensitive_patterns:
            data = re.sub(pattern, replacement, data)

        return data


class SecurityEventLogger:
    """
    Security Documentation Center: Professional Event Recording

    WHAT THIS CLASS DOES (In Plain English):

    This is like the SECURITY DOCUMENTATION CENTER in our Fortune 500 office building.
    These are the security professionals who maintain detailed records of every
    security event, visitor interaction, and incident for compliance and monitoring.

    PROFESSIONAL SECURITY DOCUMENTATION:

    COMPREHENSIVE EVENT RECORDING (Security Logging):
    - Incident documentation: Record all security events with full context
    - Visitor tracking: Log all visitor interactions and outcomes
    - Threat intelligence: Document suspicious activities and patterns
    - Like maintaining a professional security incident log book

    ENTERPRISE AUDIT TRAIL (Structured Logging):
    - Timestamped records: Every event gets precise time documentation
    - Severity classification: Events categorized by importance level
    - Structured format: All records follow consistent documentation standards
    - Correlation tracking: Events linked together for pattern analysis

    COMPLIANCE REPORTING (Security Metrics):
    - Event categorization: Security events grouped by type and severity
    - Trend analysis: Track security patterns over time
    - Regulatory compliance: Meet enterprise audit requirements
    - Real-time monitoring: Enable security team alerts and responses

    FOR NON-TECHNICAL PEOPLE:
    Think of this like a professional security logbook that:
    1. Documents every security event that happens
    2. Records the exact time and details of each incident
    3. Categorizes events by how serious they are
    4. Helps security teams spot patterns and threats

    FOR IT TEAMS:
    - Structured JSON logging for log aggregation systems
    - Severity-based log level routing
    - Security event correlation and tracking
    - Integration with monitoring and alerting systems
    """

    @staticmethod
    def log_security_event(
        event_type: str, client_ip: str, details: str, severity: str = "INFO"
    ) -> None:
        """Log security events with structured format."""
        log_entry = {
            "security_event": event_type,
            "client_ip": client_ip,
            "details": details,
            "timestamp": time.time(),
            "severity": severity,
        }

        if severity == "ERROR":
            _logger.error("🚨 SECURITY_EVENT: %s", json.dumps(log_entry))
        elif severity == "WARNING":
            _logger.warning("⚠️ SECURITY_EVENT: %s", json.dumps(log_entry))
        else:
            _logger.info("SECURITY_EVENT: %s", json.dumps(log_entry))

    @staticmethod
    def log_oauth_success(client_ip: str, destination: str) -> None:
        """Log successful OAuth completion."""
        SecurityEventLogger.log_security_event(
            "oauth_success",
            client_ip,
            f"OAuth token exchange completed successfully to {destination}",
            "INFO",
        )

    @staticmethod
    def log_oauth_failure(client_ip: str, reason: str, error_type: str) -> None:
        """Log OAuth failures for security monitoring."""
        SecurityEventLogger.log_security_event(
            "oauth_failure",
            client_ip,
            f"OAuth failed: {reason} (type: {error_type})",
            "WARNING",
        )

    @staticmethod
    def log_rate_limit_violation(client_ip: str, reason: str) -> None:
        """Log rate limiting violations."""
        SecurityEventLogger.log_security_event(
            "rate_limit_violation", client_ip, reason, "WARNING"
        )

    @staticmethod
    def log_validation_failure(
        client_ip: str, validation_type: str, reason: str
    ) -> None:
        """Log validation failures for security monitoring."""
        SecurityEventLogger.log_security_event(
            "validation_failure",
            client_ip,
            f"Validation failed: {validation_type} - {reason}",
            "WARNING",
        )


class AlexaValidator:
    """
    Alexa Request Validator: Smart Home Protocol Compliance & Authentication

    WHAT THIS CLASS DOES (In Plain English):

    This is like the RECEPTION DESK VALIDATION SPECIALIST who ensures every
    visitor (Alexa request) has proper credentials and follows company protocols
    before being allowed into the office building.

    PROFESSIONAL ALEXA PROTOCOL VALIDATION:

    DIRECTIVE STRUCTURE VALIDATION (Smart Home API Compliance):
    - Protocol compliance: Ensure requests follow Alexa Smart Home API v3 specification
    - Request format: Validate directive structure, headers, and payload versions
    - Error handling: Return properly formatted error responses for protocol violations
    - Like checking that visitors fill out forms correctly and use the right entrance

    AUTHENTICATION TOKEN EXTRACTION (Bearer Token Processing):
    - Token discovery: Extract bearer tokens from multiple possible locations in
      directives
    - Format validation: Ensure tokens follow expected bearer token structure
    - Debug support: Fallback token extraction for development environments
    - Multi-location search: Check endpoint scope, payload grantee, and payload scope

    ALEXA SIGNATURE VALIDATION (Amazon Request Authentication):
    - Certificate validation: Verify requests actually come from Amazon Alexa services
    - Timestamp validation: Ensure requests are recent and not replay attacks
    - Signature verification: Cryptographic validation of request authenticity
    - Security logging: Document validation attempts and failures for monitoring

    FOR NON-TECHNICAL PEOPLE:
    Think of this like a security checkpoint that:
    1. Checks that visitors have proper paperwork (directive validation)
    2. Verifies visitor ID badges are authentic (token extraction)
    3. Confirms visitors are who they claim to be (Alexa signature validation)
    4. Documents all security checks for compliance records

    FOR IT TEAMS:
    - Alexa Smart Home API v3 specification compliance
    - Bearer token extraction from various directive structures
    - Amazon certificate chain validation for request authenticity
    - Structured error responses compatible with Alexa skill requirements
    """

    @staticmethod
    def validate_directive(
        event: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """
        Directive Validation: Alexa Smart Home Protocol Compliance

        Validates the incoming Alexa directive structure according to the Smart Home
        API specification. Uses original dkaser pattern with assertions for validation.

        Args:
            event: Raw event from Alexa containing the directive

        Returns:
            Tuple of (directive_dict, error_response)
            - Success: (directive_dict, None)
            - Failure: (None, error_response_dict)
        """
        try:
            directive = event.get("directive")
            if directive is None:
                raise ValueError("Malformatted request - missing directive")

            payload_version = directive.get("header", {}).get("payloadVersion")
            if payload_version != "3":
                raise ValueError("Only support payloadVersion == 3")

            return directive, None

        except ValueError as e:
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_DIRECTIVE",
                        "message": str(e),
                    }
                }
            }

    @staticmethod
    def extract_auth_token(
        directive: dict[str, Any], app_config: dict[str, Any], debug_mode: bool = False
    ) -> tuple[str | None, dict[str, Any] | None]:
        """
        🔐 AUTHENTICATION TOKEN EXTRACTION: Bearer Token Discovery & Validation

        Extract authentication token from Alexa directive using original dkaser pattern.
        Searches multiple locations in the directive structure for bearer tokens.

        Args:
            directive: Alexa directive containing authentication information
            app_config: Application configuration for debug fallback tokens
            debug_mode: Whether to use debug fallback token extraction

        Returns:
            Tuple of (token_string, error_response)
            - Success: (token_string, None)
            - Failure: (None, error_response_dict)
        """
        try:
            # Original dkaser pattern for scope extraction
            scope = directive.get("endpoint", {}).get("scope")
            token_location = 1  # endpoint_scope
            if scope is None:
                # token is in grantee for Linking directive
                scope = directive.get("payload", {}).get("grantee")
                token_location = 2  # payload_grantee
            if scope is None:
                # token is in payload for Discovery directive
                scope = directive.get("payload", {}).get("scope")
                token_location = 3  # payload_scope

            if scope is None:
                raise ValueError("Malformatted request - missing endpoint.scope")
            if scope.get("type") != "BearerToken":
                raise ValueError("Only support BearerToken")

            token = scope.get("token")
            if token is None and debug_mode:
                # Original debug pattern with HA_TOKEN fallback
                token = app_config.get("HA_TOKEN")  # only for debug purpose
                token_location = 4  # debug_fallback
                logging.info(
                    "DEBUG: Using fallback HA_TOKEN (length: %s)",
                    len(token) if token else 0,
                )

            # Map location codes to descriptions for logging
            location_names = {
                1: "endpoint.scope",
                2: "payload.grantee",
                3: "payload.scope",
                4: "debug_fallback",
            }
            if token:
                location_desc = location_names.get(token_location, "unknown")
                logging.info(
                    "TOKEN DEBUG: Source=%s, Length=%s, First10=%s",
                    location_desc,
                    len(token),
                    token[:10] if len(token) > 10 else token,
                )

            if not token:
                raise ValueError("No authentication token provided")

            return token, None

        except ValueError as e:
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                        "message": str(e),
                    }
                }
            }

    @staticmethod
    def validate_alexa_signature(
        signature: str | None = None,
        certificate_url: str | None = None,
    ) -> tuple[bool, str]:
        """
        🛡️ ALEXA SIGNATURE VALIDATION: Amazon Request Authentication

        Validate that requests actually come from Amazon Alexa services by verifying
        the cryptographic signature and certificate chain. This prevents unauthorized
        requests from malicious sources.

        Args:
            signature: The signature header from the request
            certificate_url: The certificate URL header from the request

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        # Basic validation - ensure required headers are present
        if not signature:
            return False, "Missing Alexa signature header"

        if not certificate_url:
            return False, "Missing Alexa certificate URL header"

        # Basic certificate URL validation
        if not certificate_url.startswith("https://s3.amazonaws.com/echo.api/"):
            return False, "Invalid certificate URL domain"

        # For production implementation, this would include:
        # 1. Download and validate the Amazon certificate
        # 2. Extract the public key from the certificate
        # 3. Verify the signature using the public key
        # 4. Check certificate validity and chain of trust
        # 5. Validate timestamp to prevent replay attacks

        # Simplified validation for shared infrastructure
        # In production, implement full cryptographic validation

        return True, "Signature validation passed (simplified)"

    @staticmethod
    def create_alexa_error_response(error_type: str, message: str) -> dict[str, Any]:
        """
        Alexa Error Response Builder: Standardized Error Format

        Create properly formatted error responses that are compatible with
        Alexa Smart Home API requirements.

        Args:
            error_type: The Alexa error type (INVALID_DIRECTIVE, etc.)
            message: Human-readable error message

        Returns:
            Formatted error response dictionary
        """
        return {
            "event": {
                "payload": {
                    "type": error_type,
                    "message": message,
                }
            }
        }


# ═══════════════════════════════════════════════════════════════════════════
# OAuth Gateway Helper Infrastructure
# ═══════════════════════════════════════════════════════════════════════════


class OAuthSecurityValidator:
    """
    OAuth Gateway Security Validator: Enterprise Protection for OAuth Flows

    Specialized security validation for OAuth authentication flows, providing
    protection against rate limiting violations, request size attacks, and
    malformed OAuth requests.

    SECURITY VALIDATION FUNCTIONS:
    - Rate limiting enforcement with IP-based tracking
    - Request size validation to prevent DoS attacks
    - OAuth-specific parameter validation
    - Security event logging for audit trails
    """

    def __init__(
        self,
        rate_limiter: RateLimiter,
        security_validator: SecurityValidator,
        security_logger: SecurityEventLogger,
    ):
        self._rate_limiter = rate_limiter
        self._security_validator = security_validator
        self._security_logger = security_logger

    def validate_oauth_request(
        self, event: dict[str, Any], correlation_id: str
    ) -> tuple[bool, str | None, str]:
        """
        Validate OAuth request security including rate limiting and size checks.

        Args:
            event: Lambda event dictionary
            correlation_id: Request correlation ID for logging

        Returns:
            Tuple of (is_valid, error_message, client_ip)
        """
        # Extract client IP
        client_ip = event.get("headers", {}).get("X-Forwarded-For", "alexa-service")
        client_ip = client_ip.split(",")[0] if client_ip else "alexa-service"

        # Check rate limiting
        is_allowed, rate_limit_reason = self._rate_limiter.is_allowed(client_ip)
        if not is_allowed:
            self._security_logger.log_security_event(
                "rate_limit_exceeded", client_ip, rate_limit_reason
            )
            return False, f"Rate limit exceeded: {rate_limit_reason}", client_ip

        # Validate request size
        request_size = len(json.dumps(event).encode("utf-8"))
        if not self._security_validator.validate_request_size(request_size):
            self._security_logger.log_security_event(
                "request_too_large", client_ip, "Request exceeds maximum size"
            )
            return False, "Request too large", client_ip

        # Log successful validation
        self._security_logger.log_security_event(
            "request_validated",
            client_ip,
            f"OAuth request validated (correlation: {correlation_id})",
        )

        return True, None, client_ip


class OAuthConfigurationManager:
    """
    OAuth Configuration Manager: Specialized Configuration Loading for OAuth Flows

    Manages OAuth-specific configuration loading and validation with performance
    optimization through caching and intelligent fallback mechanisms.

    CONFIGURATION MANAGEMENT:
    - OAuth-specific parameter validation
    - CloudFlare configuration management
    - Home Assistant URL validation
    - Secret management and validation
    """

    @staticmethod
    def load_and_validate_oauth_config(
        app_config: dict[str, Any], correlation_id: str
    ) -> tuple[dict[str, str], list[str]]:
        """
        Load and validate OAuth configuration parameters.

        Args:
            app_config: Application configuration dictionary
            correlation_id: Request correlation ID for logging

        Returns:
            Tuple of (config_dict, validation_errors)
        """
        config: dict[str, str] = {}
        errors: list[str] = []

        # Extract and validate required OAuth parameters
        # Note: ConfigParser converts keys to lowercase when accessed as dict
        destination_url = app_config.get("ha_base_url")
        if not destination_url:
            errors.append("HA_BASE_URL is missing from configuration")
        else:
            config["destination_url"] = destination_url.strip("/")

        cf_client_id = app_config.get("cf_client_id")
        if not cf_client_id:
            errors.append("CF_CLIENT_ID is missing from configuration")
        else:
            config["cf_client_id"] = str(cf_client_id)

        cf_client_secret = app_config.get("cf_client_secret")
        if not cf_client_secret:
            errors.append("CF_CLIENT_SECRET is missing from configuration")
        else:
            config["cf_client_secret"] = str(cf_client_secret)

        wrapper_secret = app_config.get("wrapper_secret")
        if not wrapper_secret:
            errors.append("WRAPPER_SECRET is missing from configuration")
        else:
            config["wrapper_secret"] = wrapper_secret

        if errors:
            _logger.error(
                "OAuth configuration validation failed (correlation: %s): %s",
                correlation_id,
                ", ".join(errors),
            )

        return config, errors


class OAuthRequestProcessor:
    """
    OAuth Request Processor: High-Performance OAuth Token Exchange

    Handles OAuth token exchange requests with Home Assistant through CloudFlare
    protection. Optimized for minimal latency and maximum reliability.

    PROCESSING FUNCTIONS:
    - Request body extraction and validation
    - OAuth parameter parsing and validation
    - HTTP request execution with proper error handling
    - Response processing and formatting
    """

    @staticmethod
    def extract_and_validate_request_body(
        event: dict[str, Any], correlation_id: str
    ) -> tuple[bytes | None, str | None]:
        """
        Extract and validate OAuth request body.

        Args:
            event: Lambda event dictionary
            correlation_id: Request correlation ID for logging

        Returns:
            Tuple of (request_body_bytes, error_message)
        """
        event_body = event.get("body")
        if event_body is None:
            return None, "Request body is missing"

        try:
            req_body = (
                base64.b64decode(event_body)
                if event.get("isBase64Encoded")
                else event_body
            )
            return req_body, None
        except (ValueError, KeyError, UnicodeDecodeError) as e:
            _logger.error(
                "Request body processing failed (correlation: %s): %s",
                correlation_id,
                e,
            )
            return None, f"Request body processing failed: {e}"

    @staticmethod
    def validate_oauth_parameters(
        req_body: bytes, wrapper_secret: str, correlation_id: str
    ) -> tuple[bool, str | None]:
        """
        Validate OAuth request parameters including client secret.

        Args:
            req_body: Raw request body bytes
            wrapper_secret: Expected wrapper secret for validation
            correlation_id: Request correlation ID for logging

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            req_dict = urllib.parse.parse_qs(req_body)
            client_secret_bytes = req_dict.get(b"client_secret")

            if not client_secret_bytes:
                return False, "Client secret missing from request"

            client_secret = client_secret_bytes[0].decode("utf-8")

            if client_secret != wrapper_secret:
                _logger.error(
                    "Client secret mismatch (correlation: %s)", correlation_id
                )
                return False, "Client secret mismatch"

            return True, None

        except (ValueError, KeyError, UnicodeDecodeError) as e:
            _logger.error(
                "OAuth parameter validation failed (correlation: %s): %s",
                correlation_id,
                e,
            )
            return False, f"Parameter validation failed: {e}"

    @staticmethod
    def execute_oauth_request(
        destination_url: str,
        cf_client_id: str,
        cf_client_secret: str,
        req_body: bytes,
        correlation_id: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """
        Execute OAuth token exchange request to Home Assistant.

        Args:
            destination_url: Home Assistant base URL
            cf_client_id: CloudFlare client ID
            cf_client_secret: CloudFlare client secret
            req_body: Request body to forward
            correlation_id: Request correlation ID for logging

        Returns:
            Tuple of (success_response, error_response)
        """
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "CF-Access-Client-Id": cf_client_id,
                "CF-Access-Client-Secret": cf_client_secret,
            }

            http = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED",
                timeout=urllib3.Timeout(connect=2.0, read=10.0),
            )

            response = http.request(
                "POST", f"{destination_url}/auth/token", headers=headers, body=req_body
            )

            if response.status >= 400:
                error_type = (
                    "INVALID_AUTHORIZATION_CREDENTIAL"
                    if response.status in (401, 403)
                    else f"INTERNAL_ERROR {response.status}"
                )
                error_response = {
                    "event": {
                        "payload": {
                            "type": error_type,
                            "message": response.data.decode("utf-8"),
                        }
                    }
                }
                return None, error_response

            # Parse successful response
            success_response = json.loads(response.data.decode("utf-8"))
            return success_response, None

        except (urllib3.exceptions.HTTPError, json.JSONDecodeError, ValueError) as e:
            _logger.error(
                "OAuth request execution failed (correlation: %s): %s",
                correlation_id,
                e,
            )
            error_response = {
                "event": {
                    "payload": {
                        "type": "INTERNAL_ERROR",
                        "message": f"OAuth request failed: {e}",
                    }
                }
            }
            return None, error_response


# ═══════════════════════════════════════════════════════════════════════════
# Performance Monitoring Infrastructure
# ═══════════════════════════════════════════════════════════════════════════


class PerformanceMonitor:
    """
    Performance Optimization Engine: Sub-500ms Response Time Acceleration

    WHAT THIS CLASS DOES (In Plain English):

    This is like a PERFORMANCE TUNING SPECIALIST who optimizes every aspect
    of the system to achieve lightning-fast response times for voice commands.
    Think of it as a pit crew for Formula 1 racing - every millisecond counts!

    VOICE COMMAND SPEED TARGETS:
    - Container Cache: 0-1ms (instant for warm containers)
    - Shared Cache: 20-50ms (cross-Lambda sharing)
    - SSM Fallback: 100-200ms (authoritative source)
    - TOTAL TARGET: <500ms voice response time

    PERFORMANCE MONITORING & OPTIMIZATION:
    - Response time tracking with detailed breakdowns
    - Memory usage optimization for Lambda containers
    - Connection pooling for HTTP requests
    - Intelligent caching with predictive pre-loading
    - Request batching for Home Assistant API calls
    """

    def __init__(self) -> None:
        self._performance_metrics: dict[str, list[float]] = {}
        self._optimization_stats: dict[str, Any] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "response_times": [],
            "memory_usage": [],
            "connection_reuse": 0,
        }

    def start_timing(self, operation: str) -> float:
        """Start timing an operation."""
        start_time = time.time()
        if operation not in self._performance_metrics:
            self._performance_metrics[operation] = []
        return start_time

    def end_timing(self, operation: str, start_time: float) -> float:
        """End timing and record performance metrics."""
        duration = time.time() - start_time
        if operation in self._performance_metrics:
            self._performance_metrics[operation].append(duration)
        return duration

    def record_cache_hit(self) -> None:
        """Record successful cache hit for optimization tracking."""
        self._optimization_stats["cache_hits"] += 1

    def record_cache_miss(self) -> None:
        """Record cache miss for optimization analysis."""
        self._optimization_stats["cache_misses"] += 1

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = dict(self._optimization_stats)

        # Calculate average response times
        for operation, times in self._performance_metrics.items():
            if times:
                stats[f"{operation}_avg_ms"] = sum(times) / len(times) * 1000
                stats[f"{operation}_max_ms"] = max(times) * 1000
                stats[f"{operation}_min_ms"] = min(times) * 1000

        # Calculate cache hit ratio
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        if total_requests > 0:
            stats["cache_hit_ratio"] = stats["cache_hits"] / total_requests

        return stats


class ConnectionPoolManager:
    """
    🔗 HTTP CONNECTION POOLING: Optimized Network Performance

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like a PARKING GARAGE MANAGER for network connections. Instead of
    creating a new connection for every request (like finding a new parking spot
    every time), we keep a pool of ready-to-use connections that can be reused.

    CONNECTION REUSE BENEFITS:
    - Eliminates TCP handshake overhead (saves 20-100ms per request)
    - Reduces SSL/TLS negotiation time (saves 50-200ms per HTTPS request)
    - Maintains warm connections to Home Assistant
    - Optimizes memory usage in Lambda containers
    """

    def __init__(self, max_connections: int = 10, max_connections_per_host: int = 5):
        # Configure urllib3 connection pooling
        self._http = urllib3.PoolManager(
            num_pools=max_connections,
            maxsize=max_connections_per_host,
            block=False,
            timeout=urllib3.Timeout(connect=10.0, read=30.0),
            retries=urllib3.Retry(
                total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
            ),
        )
        self._connection_stats = {
            "reused_connections": 0,
            "new_connections": 0,
            "failed_connections": 0,
        }

    def make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
    ) -> Any:
        """Make HTTP request using connection pool."""
        try:
            response = self._http.request(
                method=method,
                url=url,
                headers=headers or {},
                body=body,
                preload_content=False,
            )
            # Track connection reuse
            if hasattr(response, "connection_pool_id"):
                self._connection_stats["reused_connections"] += 1
            else:
                self._connection_stats["new_connections"] += 1

            return response
        except Exception as e:
            self._connection_stats["failed_connections"] += 1
            raise e

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics."""
        return dict(self._connection_stats)


class ResponseCache:
    """
    💾 INTELLIGENT RESPONSE CACHING: Smart Data Acceleration

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like a MEMORY BANK for frequently requested information. When someone
    asks for the same thing multiple times, we remember the answer and give it
    instantly instead of looking it up again. Perfect for device states, discovery
    responses, and configuration data.

    🧠 **SMART CACHING STRATEGY:**
    - Device Discovery: Cache for 5 minutes (devices don't change often)
    - Device States: Cache for 30 seconds (balance freshness vs speed)
    - Configuration: Cache for 15 minutes (rarely changes)
    - Error Responses: Cache for 1 minute (prevent repeated failures)
    """

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
        }

    def get(self, cache_key: str) -> tuple[Any, bool]:
        """
        Get cached response.

        Returns:
            Tuple of (cached_data, is_hit)
        """
        current_time = time.time()

        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if current_time < cache_entry["expires_at"]:
                self._cache_stats["hits"] += 1
                return cache_entry["data"], True
            # Expired, remove it
            del self._cache[cache_key]
            self._cache_stats["evictions"] += 1

        self._cache_stats["misses"] += 1
        return None, False

    def set(self, cache_key: str, data: Any, ttl_seconds: int = 300) -> None:
        """Cache response data with TTL."""
        expires_at = time.time() + ttl_seconds
        self._cache[cache_key] = {
            "data": data,
            "expires_at": expires_at,
            "created_at": time.time(),
        }
        self._cache_stats["size"] = len(self._cache)

    def invalidate(self, cache_key: str) -> bool:
        """Remove specific cache entry."""
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._cache_stats["size"] = len(self._cache)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_stats["size"] = 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        stats: dict[str, Any] = dict(self._cache_stats)
        total_requests = stats["hits"] + stats["misses"]
        if total_requests > 0:
            stats["hit_ratio"] = stats["hits"] / total_requests
        return stats


class RequestBatcher:
    """
    Request Batching System: Home Assistant API Optimization

    WHAT THIS CLASS DOES (In Plain English):

    This is like a SMART DELIVERY COORDINATOR who groups multiple requests
    together to make fewer, more efficient trips. Instead of making 10 separate
    calls to Home Assistant, we batch them into 1-2 optimized requests.

    BATCHING BENEFITS:
    - Reduce Home Assistant API load (fewer network roundtrips)
    - Improve response times (parallel processing)
    - Optimize Lambda execution time (bulk operations)
    - Better error handling (grouped failure recovery)
    """

    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        self._max_batch_size = max_batch_size
        self._max_wait_time = max_wait_time
        self._pending_requests: list[dict[str, Any]] = []
        self._batch_stats = {
            "batches_processed": 0,
            "requests_batched": 0,
            "individual_requests": 0,
            "average_batch_size": 0.0,
        }

    def add_request(self, request_data: dict[str, Any]) -> None:
        """Add request to current batch."""
        self._pending_requests.append(request_data)

    def should_process_batch(self) -> bool:
        """Check if batch should be processed now."""
        if not self._pending_requests:
            return False

        if len(self._pending_requests) >= self._max_batch_size:
            return True

        # Check if oldest request has been waiting too long
        if self._pending_requests:
            oldest_request = self._pending_requests[0]
            wait_time = time.time() - oldest_request.get("timestamp", time.time())
            return wait_time >= self._max_wait_time

        return False

    def process_batch(self) -> list[dict[str, Any]]:
        """Process current batch and return results."""
        if not self._pending_requests:
            return []

        batch = list(self._pending_requests)
        self._pending_requests.clear()

        # Update statistics
        self._batch_stats["batches_processed"] += 1
        self._batch_stats["requests_batched"] += len(batch)

        # Calculate running average
        total_requests = self._batch_stats["requests_batched"]
        total_batches = self._batch_stats["batches_processed"]
        if total_batches > 0:
            self._batch_stats["average_batch_size"] = total_requests / total_batches

        return batch

    def get_batch_stats(self) -> dict[str, Any]:
        """Get batching performance statistics."""
        return dict(self._batch_stats)


def create_structured_logger(
    logger_name: str = "lambda_function",
    log_level: str = "INFO",
    correlation_id: str | None = None,
) -> logging.Logger | logging.LoggerAdapter[logging.Logger]:
    """
    Enhanced Lambda Logger: Performance-Optimized Logging

    Creates a high-performance logger optimized for AWS Lambda with:
    - Structured JSON logging for CloudWatch
    - Performance metrics tracking
    - Correlation ID support for request tracing
    - Memory-efficient log formatting
    """
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        handler = logging.StreamHandler()

        # Performance-optimized formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if correlation_id:
        logger = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

    return logger


def extract_correlation_id(context: Any) -> str:
    """
    Request Correlation: Extract Unique Request Identifier

    Extracts or generates a correlation ID for request tracking and performance
    monitoring. Essential for tracing requests across Lambda functions and
    identifying performance bottlenecks.
    """
    if hasattr(context, "aws_request_id"):
        return context.aws_request_id

    # Fallback to timestamp-based ID for testing
    return f"req_{int(time.time() * 1000)}"


# ═══════════════════════════════════════════════════════════════════════════
# Unified Configuration Loading API
# ═══════════════════════════════════════════════════════════════════════════


def load_configuration(
    app_config_path: str = "",
    config_section: str = "",
    return_format: str = "dict",
    required_keys: list[str] | None = None,
) -> dict[str, Any] | configparser.ConfigParser:
    """
    Unified Configuration Loader: Load Configuration from SSM/Cache

    This function loads configuration from SSM Parameter Store or cache.
    If app_config_path is empty, it will attempt to load from environment fallback.

    PERFORMANCE FEATURES:
    - 3-tier caching: Container (0-1ms) → DynamoDB (20-50ms) → SSM (100-200ms)
    - Automatic format detection and conversion
    - Foundation pattern backward compatibility
    - Fallback to environment variables if no app_config_path

    :param app_config_path: SSM parameter path (from APP_CONFIG_PATH env var)
    :param config_section: Configuration section (ha_config, oauth_config, etc.)
    :param return_format: "dict" (default) or "configparser" for legacy compatibility
    :param required_keys: Optional validation of required configuration keys
    :return: Configuration as dict or ConfigParser based on return_format
    """
    # If no app_config_path provided, cannot load from SSM
    if not app_config_path:
        if return_format == "configparser":
            # Return empty ConfigParser for legacy compatibility
            config = configparser.ConfigParser()
            config.add_section("appConfig")
            return config
        # Return empty dict for modern usage
        return {}

    if return_format == "configparser":
        # Legacy foundation pattern - return ConfigParser
        return _load_config_as_configparser(app_config_path)

    # Modern dict-based configuration (default)
    return _load_standardized_configuration(
        config_section, app_config_path, required_keys
    )


def cache_configuration(
    config_section: str,
    ssm_path: str,
    config: dict[str, Any],
    force_refresh: bool = False,
) -> None:
    """
    Cache Configuration: Public API for Configuration Caching

    Store configuration in both container and shared cache layers for optimal
    performance. This is useful for pre-warming caches, updating configuration
    after changes, or forcing cache refresh during deployment.

    CACHING STRATEGY:
    - Container Cache: Immediate access for current Lambda container
    - Shared Cache: Cross-Lambda sharing via DynamoDB for consistent performance
    - Force Refresh: Option to invalidate existing cache before storing new config

    :param config_section: Configuration section (ha_config, oauth_config, etc.)
    :param ssm_path: SSM parameter path for cache key generation
    :param config: Configuration dictionary to cache
    :param force_refresh: If True, clear existing cache before storing new config
    """
    if force_refresh:
        # Clear existing cache before storing new configuration
        _invalidate_cache(config_section, ssm_path)
        _logger.info("Cache invalidated for %s:%s", ssm_path, config_section)

    # Store in both cache layers
    cache_config_in_container(config_section, ssm_path, config)
    _cache_config_in_shared_cache(config_section, ssm_path, config)

    _logger.info("Configuration cached for %s:%s", ssm_path, config_section)


def get_cache_stats() -> dict[str, Any]:
    """
    Cache Monitoring: Get Cache Statistics for Performance Analysis

    Provides detailed cache performance metrics for monitoring, debugging, and
    optimization. This is essential for understanding cache hit ratios, memory
    usage, and identifying performance bottlenecks in production environments.

    MONITORING FEATURES:
    - Container cache statistics (valid/expired entries, total size)
    - Shared cache configuration details
    - TTL settings and cache configuration
    - Memory usage analysis for Lambda optimization

    :return: Dictionary with comprehensive cache statistics and configuration
    """
    return _get_cache_stats()


def load_environment() -> dict[str, str]:
    """
    Environment Variable Loader: Pure ENV Variable Extraction

    This function ONLY loads environment variables and puts them into a clean
    dictionary. No configuration loading, no validation, no fallbacks.
    Pure environment variable extraction.

    ENVIRONMENT VARIABLES EXTRACTED:
    - DEBUG (for logging control)
    - LOG_LEVEL (for explicit log level control)
    - APP_CONFIG_PATH (for configuration loading)
    - BASE_URL / HA_BASE_URL (for direct configuration)
    - CF_CLIENT_ID, CF_CLIENT_SECRET (CloudFlare settings)
    - LONG_LIVED_ACCESS_TOKEN / HA_TOKEN (debug authentication)
    - NOT_VERIFY_SSL (SSL verification control)

    Returns:
        Dictionary with all relevant environment variables (empty strings for missing)
    """
    return {
        "DEBUG": os.environ.get("DEBUG", ""),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", ""),
        "APP_CONFIG_PATH": os.environ.get("APP_CONFIG_PATH", ""),
        "BASE_URL": os.environ.get("BASE_URL", ""),
        "HA_BASE_URL": os.environ.get("HA_BASE_URL", ""),
        "CF_CLIENT_ID": os.environ.get("CF_CLIENT_ID", ""),
        "CF_CLIENT_SECRET": os.environ.get("CF_CLIENT_SECRET", ""),
        "LONG_LIVED_ACCESS_TOKEN": os.environ.get("LONG_LIVED_ACCESS_TOKEN", ""),
        "HA_TOKEN": os.environ.get("HA_TOKEN", ""),
        "NOT_VERIFY_SSL": os.environ.get("NOT_VERIFY_SSL", ""),
    }


def validate_configuration(app_config: dict[str, Any]) -> tuple[bool, str | None]:
    """
    ✅ CONFIGURATION VALIDATION: Validate Loaded Configuration

    Validates that the loaded configuration contains required fields
    and optional CloudFlare settings are properly configured.

    **VALIDATION CHECKS:**
    - Required: HA_BASE_URL / homeAssistantBaseUrl
    - Optional: CF_CLIENT_ID, CF_CLIENT_SECRET (CloudFlare)
    - Debug: HA_TOKEN (development authentication)

    Args:
        app_config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
        - Success: (True, None)
        - Failure: (False, error_message)
    """
    return _validate_configuration(app_config)


def _validate_configuration(app_config: dict[str, Any]) -> tuple[bool, str | None]:
    """Internal configuration validation logic."""
    # Check for required base URL
    base_url = app_config.get("homeAssistantBaseUrl") or app_config.get("HA_BASE_URL")
    if not base_url:
        return False, "Missing required HA_BASE_URL or homeAssistantBaseUrl"

    # Validate URL format
    if not base_url.startswith(("http://", "https://")):
        return False, f"Invalid URL format: {base_url}"

    # Check CloudFlare configuration (optional but should be complete if present)
    cf_id = app_config.get("cf_client_id") or app_config.get("CF_CLIENT_ID")
    cf_secret = app_config.get("cf_client_secret") or app_config.get("CF_CLIENT_SECRET")

    if cf_id and not cf_secret:
        return False, "CF_CLIENT_ID provided but CF_CLIENT_SECRET missing"
    if cf_secret and not cf_id:
        return False, "CF_CLIENT_SECRET provided but CF_CLIENT_ID missing"

    logging.debug("Configuration validation successful")
    return True, None


# ═══════════════════════════════════════════════════════════════════════════
# Internal Configuration Loading Functions
# ═══════════════════════════════════════════════════════════════════════════


def _create_ssm_client() -> SSMClient:
    """Create SSM client with lazy initialization."""
    global _ssm_client  # pylint: disable=global-statement
    if _ssm_client is None:
        _ssm_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            "ssm", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
    return _ssm_client


def _get_dynamodb_client() -> Any:  # DynamoDB types not available
    """Get DynamoDB client with lazy initialization."""
    global _dynamodb_client  # pylint: disable=global-statement
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType, reportUnknownVariableType]
            "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
    return _dynamodb_client  # pyright: ignore[reportUnknownVariableType]


def _load_standardized_configuration(
    config_section: str,
    ssm_path: str,
    _: list[str] | None = None,
) -> dict[str, Any]:
    """
    Speed-Optimized Configuration Loading: <500ms Voice Command Response

    Strategic 3-tier caching for optimal Lambda performance:
    1. Container Cache: 0-1ms (lambda warm start advantage)
    2. DynamoDB Shared Cache: 20-50ms (cross-lambda sharing)
    3. SSM Parameter Store: 100-200ms (authoritative source)

    :param config_section: Configuration section to load (ha_config, oauth_config, etc.)
    :param ssm_path: Base SSM path for configuration parameters
    :param required_keys: Optional list of required keys to validate
    :return: Configuration dictionary with all settings
    """
    _logger.info(
        "Loading configuration for section %s from path %s", config_section, ssm_path
    )

    # Tier 1: Container Cache (fastest)
    cached_config = get_container_cached_config(config_section, ssm_path)
    if cached_config:
        _logger.debug("Configuration loaded from container cache")
        return cached_config

    # Tier 2: Shared Cache (DynamoDB)
    shared_config = _get_shared_cached_config(config_section, ssm_path)
    if shared_config:
        _logger.debug("Configuration loaded from shared cache")
        cache_config_in_container(config_section, ssm_path, shared_config)
        return shared_config

    # Tier 3: SSM Parameter Store (authoritative source)
    try:
        config = _load_from_ssm_parameters(ssm_path, config_section)
        if config:
            # Cache for future requests
            _cache_config_in_shared_cache(config_section, ssm_path, config)
            cache_config_in_container(config_section, ssm_path, config)
            _logger.info("Configuration loaded from SSM and cached")
            return config
    except (ClientError, NoCredentialsError, ValueError, KeyError) as e:
        _logger.warning("Failed to load from SSM: %s", str(e))

    # Fallback: Minimal configuration to prevent Lambda failure
    fallback_config = _get_minimal_fallback_configuration(config_section)
    _logger.warning("Using fallback configuration for %s", config_section)
    return fallback_config


def get_container_cached_config(
    config_section: str, ssm_path: str
) -> dict[str, Any] | None:
    """Get configuration from container-level cache."""
    # Periodic cleanup every 50 cache operations to prevent memory bloat
    if len(_config_cache) >= 50:
        _cleanup_expired_cache()

    cache_key = f"{ssm_path}:{config_section}"
    if cache_key in _config_cache:
        cache_entry = _config_cache[cache_key]
        # Check TTL
        if time.time() - cache_entry["timestamp"] < CONTAINER_CACHE_TTL:
            return cache_entry["config"]  # type: ignore[no-any-return]
        # Remove expired entry
        del _config_cache[cache_key]
    return None


def _get_shared_cached_config(
    config_section: str, ssm_path: str
) -> dict[str, Any] | None:
    """Get configuration from DynamoDB shared cache."""
    try:
        dynamodb = _get_dynamodb_client()
        cache_key = f"{ssm_path}:{config_section}"

        response = dynamodb.get_item(
            TableName=SHARED_CACHE_TABLE, Key={"cache_key": {"S": cache_key}}
        )

        if "Item" in response:
            ttl = int(response["Item"].get("ttl", {}).get("N", "0"))
            if time.time() < ttl:
                config_json = response["Item"]["config"]["S"]
                return json.loads(config_json)  # type: ignore[no-any-return]
    except (ClientError, ValueError, KeyError, json.JSONDecodeError) as e:
        _logger.debug("Shared cache miss: %s", str(e))
    return None


def _cache_config_in_shared_cache(
    config_section: str, ssm_path: str, config: dict[str, Any]
) -> None:
    """Store configuration in DynamoDB shared cache."""
    try:
        dynamodb = _get_dynamodb_client()
        cache_key = f"{ssm_path}:{config_section}"

        dynamodb.put_item(
            TableName=SHARED_CACHE_TABLE,
            Item={
                "cache_key": {"S": cache_key},
                "config": {"S": json.dumps(config)},
                "ttl": {"N": str(int(time.time() + SHARED_CACHE_TTL))},
                "timestamp": {"S": str(time.time())},
            },
        )
    except (ClientError, ValueError, KeyError) as e:
        _logger.debug("Failed to cache in shared cache: %s", str(e))


def cache_config_in_container(
    config_section: str, ssm_path: str, config: dict[str, Any]
) -> None:
    """Store configuration in container-level cache."""
    cache_key = f"{ssm_path}:{config_section}"

    _config_cache[cache_key] = {"config": config, "timestamp": time.time()}


def _clear_container_cache(
    config_section: str | None = None, ssm_path: str | None = None
) -> None:
    """Clear container-level cache entries."""
    if config_section and ssm_path:
        # Clear specific cache entry
        cache_key = f"{ssm_path}:{config_section}"
        _config_cache.pop(cache_key, None)
        _logger.debug("Cleared container cache for %s", cache_key)
    else:
        # Clear all cache entries
        _config_cache.clear()
        _logger.debug("Cleared all container cache entries")


def _clear_shared_cache(config_section: str, ssm_path: str) -> None:
    """Clear shared cache entry from DynamoDB."""
    try:
        dynamodb = _get_dynamodb_client()
        cache_key = f"{ssm_path}:{config_section}"

        dynamodb.delete_item(
            TableName=SHARED_CACHE_TABLE, Key={"cache_key": {"S": cache_key}}
        )
        _logger.debug("Cleared shared cache for %s", cache_key)
    except (ClientError, ValueError, KeyError) as e:
        _logger.debug("Failed to clear shared cache: %s", str(e))


def _invalidate_cache(config_section: str, ssm_path: str) -> None:
    """Invalidate both container and shared cache for a configuration section."""
    _clear_container_cache(config_section, ssm_path)
    _clear_shared_cache(config_section, ssm_path)
    _logger.info("Cache invalidated for %s:%s", ssm_path, config_section)


def _get_cache_stats() -> dict[str, Any]:
    """Get cache statistics for monitoring and debugging."""
    container_cache_size = len(_config_cache)

    # Calculate cache hit/miss ratios and TTL info
    current_time = time.time()
    valid_entries = 0
    expired_entries = 0

    for _cache_key, cache_entry in _config_cache.items():
        if current_time - cache_entry["timestamp"] < CONTAINER_CACHE_TTL:
            valid_entries += 1
        else:
            expired_entries += 1

    return {
        "container_cache": {
            "total_entries": container_cache_size,
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": CONTAINER_CACHE_TTL,
        },
        "shared_cache": {
            "table_name": SHARED_CACHE_TABLE,
            "ttl_seconds": SHARED_CACHE_TTL,
        },
        "cache_config": {
            "container_ttl": CONTAINER_CACHE_TTL,
            "shared_ttl": SHARED_CACHE_TTL,
        },
    }


def _cleanup_expired_cache() -> None:
    """Remove expired entries from container cache."""
    current_time = time.time()
    expired_keys: list[str] = []

    for cache_key, cache_entry in _config_cache.items():
        if current_time - cache_entry["timestamp"] >= CONTAINER_CACHE_TTL:
            expired_keys.append(cache_key)

    for cache_key in expired_keys:
        del _config_cache[cache_key]

    if expired_keys:
        _logger.debug("Cleaned up %d expired cache entries", len(expired_keys))


def _get_minimal_fallback_configuration(config_section: str) -> dict[str, Any]:
    """Provide minimal fallback configuration to prevent Lambda failure."""
    fallbacks = {
        "ha_config": {
            "base_url": os.environ.get("HA_BASE_URL", "http://localhost:8123"),
            "token": os.environ.get("HA_TOKEN", "fallback_token"),
            "verify_ssl": True,
            "timeout": 30,
        },
        "oauth_config": {
            "client_id": os.environ.get("OAUTH_CLIENT_ID", "fallback_client"),
            "client_secret": os.environ.get("OAUTH_CLIENT_SECRET", "fallback_secret"),
            "redirect_uri": os.environ.get("OAUTH_REDIRECT_URI", "http://localhost"),
            "token_ttl": 3600,
        },
        "cloudflare_config": {
            "client_id": os.environ.get("CF_CLIENT_ID", ""),
            "client_secret": os.environ.get("CF_CLIENT_SECRET", ""),
            "enabled": False,
        },
        "security_config": {
            "alexa_secret": os.environ.get("ALEXA_SECRET", "fallback_secret"),
            "api_key": os.environ.get("API_KEY", ""),
        },
        "aws_config": {
            "region": os.environ.get("AWS_REGION", "us-east-1"),
            "timeout": 30,
            "max_retries": 3,
        },
    }
    return fallbacks.get(config_section, {})


def _load_from_ssm_parameters(ssm_path: str, config_section: str) -> dict[str, Any]:
    """Load configuration from SSM parameters with fallback to original format."""
    # Try original flat JSON format first (foundation pattern compatibility)
    original_config = _try_original_ssm_format(ssm_path, config_section)
    if original_config:
        return original_config

    # Try new structured format
    structured_config = _try_new_ssm_format(ssm_path, config_section)
    if structured_config:
        return structured_config

    # No configuration found
    raise ValueError(f"No configuration found for {config_section} at {ssm_path}")


def _try_original_ssm_format(
    ssm_path: str, config_section: str
) -> dict[str, Any] | None:
    """Try loading from original single JSON parameter format."""
    ssm_client = _create_ssm_client()

    # Support both APP_CONFIG_PATH and direct SSM path
    ssm_param_name = ssm_path
    needs_appconfig = not ssm_param_name.endswith(
        "appConfig"
    ) and not ssm_param_name.endswith("alexa")
    if needs_appconfig:
        ssm_param_name = f"{ssm_path.rstrip('/')}/appConfig"

    try:
        response = ssm_client.get_parameter(Name=ssm_param_name, WithDecryption=True)
        param_value = response.get("Parameter", {}).get("Value", "")
        original_config: dict[str, Any] = json.loads(param_value)

        _logger.info("Loaded flat configuration from SSM: %s", ssm_param_name)
        _logger.debug("Configuration keys: %s", list(original_config.keys()))

        # Map original format to standardized keys
        if config_section == "ha_config":
            return _map_original_ha_config(original_config)

        # For new features (OAuth, CloudFlare, Security, AWS),
        # just return relevant subset since no backwards compatibility needed
        return original_config

    except (ClientError, json.JSONDecodeError, KeyError) as e:
        _logger.debug(
            "Original SSM format not available for %s: %s", ssm_param_name, str(e)
        )
        return None


def _try_new_ssm_format(ssm_path: str, config_section: str) -> dict[str, Any] | None:
    """Try loading from new standardized SSM parameter format."""
    ssm_client = _create_ssm_client()

    try:
        response = ssm_client.get_parameters_by_path(
            Path=ssm_path, Recursive=False, WithDecryption=True, MaxResults=10
        )

        for param in response.get("Parameters", []):
            param_name = param.get("Name", "")
            if param_name.endswith(f"/{config_section}"):
                param_value = param.get("Value", "{}")
                return json.loads(param_value)  # type: ignore[no-any-return]

        return None

    except (ClientError, json.JSONDecodeError, KeyError) as e:
        _logger.debug("Standardized SSM format not available: %s", str(e))
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Configuration Mapping Functions
# ═══════════════════════════════════════════════════════════════════════════


def _map_original_ha_config(original_config: dict[str, Any]) -> dict[str, Any]:
    """Map original HA configuration keys to standardized format."""
    key_mapping: dict[str, str] = {
        "HA_BASE_URL": "base_url",
        "HA_TOKEN": "token",
        "HA_VERIFY_SSL": "verify_ssl",
        "HA_TIMEOUT": "timeout",
    }

    mapped_config: dict[str, Any] = {}
    for original_key, standard_key in key_mapping.items():
        if original_key in original_config:
            mapped_config[standard_key] = original_config[original_key]

    return mapped_config


# ═══════════════════════════════════════════════════════════════════════════
# Foundation Pattern Compatibility
# ═══════════════════════════════════════════════════════════════════════════


def _load_config_as_configparser(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    🔐 BACKWARDS COMPATIBLE CONFIGURATION MANAGER: Original Foundation Support

    Load configparser from config stored in SSM Parameter Store with full backwards
    compatibility for the original foundation pattern from dkaser's gist. This function
    ensures the original flat JSON configuration is properly loaded into an appConfig
    section as expected by the foundation code.

    **FOUNDATION COMPATIBILITY:**
    - Supports original flat JSON format with keys: HA_BASE_URL, CF_CLIENT_ID, etc.
    - Creates appConfig section as expected by original foundation pattern
    - APP_CONFIG_PATH environment variable support for existing deployments
    - ALEXA_SECRET replaces WRAPPER_SECRET for enhanced naming

    **CONFIGURATION SOURCES (Priority Order):**
    1. APP_CONFIG_PATH environment variable (existing deployments)
    2. Direct SSM path with /appConfig suffix
    3. Direct SSM path as provided
    4. Fallback to environment variables

    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser with appConfig section for foundation compatibility
    """
    _logger.info("Loading configuration using foundation-compatible pattern")
    configuration = configparser.ConfigParser()

    try:
        # PRIORITY 1: APP_CONFIG_PATH environment variable (existing deployments)
        app_config_path = os.environ.get("APP_CONFIG_PATH")
        if app_config_path:
            _logger.info("Using APP_CONFIG_PATH: %s", app_config_path)
            # Historical pattern: APP_CONFIG_PATH always gets "/appConfig" appended
            appconfig_path = f"{app_config_path.rstrip('/')}/appConfig"
            _logger.info("Trying appConfig path: %s", appconfig_path)
            config_dict = _load_flat_config_from_ssm(appconfig_path)
            if config_dict:
                configuration.add_section("appConfig")
                for key, value in config_dict.items():
                    configuration.set("appConfig", key, str(value))
                _logger.info("✅ Configuration loaded from appConfig path")
                return configuration

        # PRIORITY 2: Direct SSM path with /appConfig suffix
        if not ssm_parameter_path.endswith("/appConfig"):
            appconfig_path = f"{ssm_parameter_path.rstrip('/')}/appConfig"
            _logger.info("Trying appConfig path: %s", appconfig_path)
            config_dict = _load_flat_config_from_ssm(appconfig_path)
            if config_dict:
                configuration.add_section("appConfig")
                for key, value in config_dict.items():
                    configuration.set("appConfig", key, str(value))
                _logger.info("✅ Configuration loaded from appConfig path")
                return configuration

        # PRIORITY 3: Direct SSM path as provided
        _logger.info("Trying direct SSM path: %s", ssm_parameter_path)
        config_dict = _load_flat_config_from_ssm(ssm_parameter_path)
        if config_dict:
            configuration.add_section("appConfig")
            for key, value in config_dict.items():
                configuration.set("appConfig", key, str(value))
            _logger.info("✅ Configuration loaded from direct SSM path")
            return configuration

    except (ClientError, NoCredentialsError, ValueError, KeyError) as e:
        _logger.warning("SSM configuration loading failed: %s", str(e))

    # PRIORITY 4: Fallback to environment variables
    _logger.info("Using environment variable fallback")
    env_config = _get_env_fallback_config()
    configuration.add_section("appConfig")
    for key, value in env_config.items():
        configuration.set("appConfig", key, str(value))

    _logger.info("✅ Configuration loaded from environment fallback")
    return configuration


def _load_flat_config_from_ssm(ssm_path: str) -> dict[str, Any] | None:
    """Load flat JSON configuration from SSM parameter."""
    try:
        ssm_client = _create_ssm_client()
        response = ssm_client.get_parameter(Name=ssm_path, WithDecryption=True)
        param_value = response.get("Parameter", {}).get("Value", "")
        return json.loads(param_value)  # type: ignore[no-any-return]
    except (ClientError, NoCredentialsError, json.JSONDecodeError, KeyError) as e:
        _logger.debug("Failed to load flat config from %s: %s", ssm_path, str(e))
        return None


def _get_env_fallback_config() -> dict[str, Any]:
    """Get fallback configuration from environment variables."""
    return {
        "HA_BASE_URL": os.environ.get("HA_BASE_URL", "http://localhost:8123"),
        "HA_TOKEN": os.environ.get("HA_TOKEN", "fallback_token"),
        "CF_CLIENT_ID": os.environ.get("CF_CLIENT_ID", ""),
        "CF_CLIENT_SECRET": os.environ.get("CF_CLIENT_SECRET", ""),
        "ALEXA_SECRET": os.environ.get("ALEXA_SECRET", "fallback_secret"),
        "OAUTH_CLIENT_ID": os.environ.get("OAUTH_CLIENT_ID", "fallback_client"),
        "OAUTH_CLIENT_SECRET": os.environ.get("OAUTH_CLIENT_SECRET", "fallback_secret"),
    }


# === LOGGING CONFIGURATION ===
_debug = bool(os.environ.get("DEBUG"))

# Use shared configuration logger instead of local setup
_logger = create_structured_logger("OAuthGateway")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize boto3 client at global scope for connection reuse
client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]
_default_app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

# ⚡ PHASE 2 SECURITY: Initialize security components at global scope
_rate_limiter = RateLimiter()
_security_validator = SecurityValidator()
_security_logger = SecurityEventLogger()

# ⚡ PHASE 1B PERFORMANCE: Initialize performance optimizer at global scope
_performance_optimizer = PerformanceMonitor()

log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)


class HAConfig:
    """Configuration class for Home Assistant settings."""

    def __init__(self, config: configparser.ConfigParser) -> None:
        """
        Construct new app with configuration
        :param config: application configuration
        """
        self.config = config

    def get_config(self):
        return self.config


# Initialize app at global scope for reuse across invocations
def load_config(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    Load configparser from config stored in SSM Parameter Store
    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser holding loaded config
    """
    configuration = configparser.ConfigParser()
    try:
        # Get all parameters for this app
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        # Loop through the returned parameters and populate the ConfigParser
        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            for param in param_details.get("Parameters"):
                param_name = param.get("Name")
                param_value = param.get("Value")

                if param_name is None:
                    raise ValueError("SSM parameter 'Name' is missing")
                if param_value is None:
                    raise ValueError(f"SSM parameter '{param_name}' value is missing")

                param_path_array = param_name.split("/")
                section_position = len(param_path_array) - 1
                section_name = param_path_array[section_position]
                config_values = json.loads(param_value)
                config_dict = {section_name: config_values}
                configuration.read_dict(config_dict)
    except (ClientError, ValueError, KeyError) as err:
        print("Encountered an error loading config from SSM.")
        print(str(err))

    return configuration


def get_app_config() -> HAConfig:
    """
    ⚡ PERFORMANCE-OPTIMIZED: Load and return the HAConfig instance with 3-tier caching.

    CACHING STRATEGY:
    1. Container Cache: 0-1ms (warm Lambda containers)
    2. DynamoDB Shared Cache: 20-50ms (cross-Lambda sharing)
    3. SSM Parameter Store: 100-200ms (authoritative source)

    :return: HAConfig instance with loaded configuration
    """
    start_time = _performance_optimizer.start_timing("config_load")
    try:
        config = load_configuration(
            app_config_path=_default_app_config_path,
            config_section="appConfig",
            return_format="configparser",
        )

        if isinstance(config, configparser.ConfigParser):
            _performance_optimizer.record_cache_hit()
            duration = _performance_optimizer.end_timing("config_load", start_time)
            _logger.info("Configuration loaded (%.1fms)", duration * 1000)
            return HAConfig(config)

        # Fallback to legacy loading if needed
        config = load_config(_default_app_config_path)
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.info("Legacy configuration loaded (%.1fms)", duration * 1000)
        return HAConfig(config)

    except Exception as e:
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.error("Configuration loading failed (%.1fms): %s", duration * 1000, e)
        raise


def _validate_oauth_security(
    event: dict[str, Any], correlation_id: str
) -> tuple[bool, dict[str, Any] | None, str]:
    """
    Validate OAuth request security including rate limiting and size checks.

    Args:
        event: Lambda event dictionary
        correlation_id: Request correlation ID for logging

    Returns:
        Tuple of (is_valid, error_response_if_any, client_ip)
    """
    oauth_validator = OAuthSecurityValidator(
        _rate_limiter, _security_validator, _security_logger
    )
    is_valid, error_message, client_ip = oauth_validator.validate_oauth_request(
        event, correlation_id
    )

    if not is_valid:
        if error_message and "rate limit" in error_message.lower():
            return (
                False,
                {
                    "statusCode": 429,
                    "body": json.dumps(
                        {"error": "rate_limit_exceeded", "message": error_message}
                    ),
                },
                client_ip,
            )

        error_msg = error_message or "Request too large"
        return (
            False,
            {
                "statusCode": 413,
                "body": json.dumps(
                    {"error": "request_too_large", "message": error_msg}
                ),
            },
            client_ip,
        )

    return True, None, client_ip


def _load_and_validate_oauth_configuration(
    correlation_id: str,
) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """
    Load and validate OAuth configuration parameters.

    Args:
        correlation_id: Request correlation ID for logging

    Returns:
        Tuple of (oauth_config_if_valid, error_response_if_any)
    """
    app = get_app_config()
    app_config = app.get_config()["appConfig"]

    (oauth_config, validation_errors) = (
        OAuthConfigurationManager.load_and_validate_oauth_config(
            dict(app_config), correlation_id
        )
    )

    if validation_errors:
        errors_str = ", ".join(validation_errors)
        error_message = f"Configuration validation failed: {errors_str}"
        return None, {
            "event": {
                "payload": {
                    "type": "INVALID_CONFIGURATION",
                    "message": error_message,
                }
            }
        }

    return oauth_config, None


def _process_oauth_request_body(
    event: dict[str, Any], wrapper_secret: str, correlation_id: str
) -> tuple[bytes | None, dict[str, Any] | None]:
    """
    Extract and validate OAuth request body including client secret validation.

    Args:
        event: Lambda event dictionary
        wrapper_secret: Expected wrapper secret for validation
        correlation_id: Request correlation ID for logging

    Returns:
        Tuple of (request_body_if_valid, error_response_if_any)
    """
    req_body, extract_error = OAuthRequestProcessor.extract_and_validate_request_body(
        event, correlation_id
    )

    if extract_error:
        return None, {
            "event": {
                "payload": {
                    "type": "INVALID_REQUEST",
                    "message": extract_error,
                }
            }
        }

    # req_body is guaranteed to be non-None here due to error check above
    if req_body is None:
        return None, {
            "event": {
                "payload": {
                    "type": "INVALID_REQUEST",
                    "message": "Request body extraction failed",
                }
            }
        }

    is_valid, validation_error = OAuthRequestProcessor.validate_oauth_parameters(
        req_body, wrapper_secret, correlation_id
    )

    if not is_valid:
        return None, {
            "event": {
                "payload": {
                    "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                    "message": validation_error,
                }
            }
        }

    return req_body, None


def _execute_oauth_token_exchange(
    oauth_config: dict[str, str], req_body: bytes, correlation_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Execute OAuth token exchange with Home Assistant.

    Args:
        oauth_config: Validated OAuth configuration
        req_body: Validated request body
        correlation_id: Request correlation ID for logging

    Returns:
        Tuple of (success_response, error_response)
    """
    return OAuthRequestProcessor.execute_oauth_request(
        oauth_config["destination_url"],
        oauth_config["cf_client_id"],
        oauth_config["cf_client_secret"],
        req_body,
        correlation_id,
    )


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """
    ⚡ PERFORMANCE-OPTIMIZED: OAuth Gateway Lambda Handler

    Streamlined OAuth token exchange handler with performance monitoring
    and comprehensive security validation. Refactored for maintainability
    and reduced complexity.

    PROCESSING FLOW:
    1. Security validation (rate limiting, request size)
    2. Configuration loading and validation
    3. Request body processing and OAuth parameter validation
    4. OAuth token exchange execution
    5. Response processing and performance logging

    TARGET: <200ms OAuth token exchange time
    """
    # Initialize request context and performance tracking
    correlation_id = extract_correlation_id(context)
    request_start = _performance_optimizer.start_timing("total_request")

    _logger.info("=== OAUTH LAMBDA START (correlation: %s) ===", correlation_id)
    _logger.debug("Event: %s", event)

    # 1. Security validation
    (is_secure, security_error, _) = _validate_oauth_security(event, correlation_id)
    if not is_secure:
        _performance_optimizer.end_timing("total_request", request_start)
        return security_error  # type: ignore[return-value]  # Guaranteed non-None when is_secure is False

    # 2. Configuration loading and validation
    oauth_config, config_error = _load_and_validate_oauth_configuration(correlation_id)
    if config_error or oauth_config is None:
        _performance_optimizer.end_timing("total_request", request_start)
        return config_error or {"error": "Configuration loading failed"}

    # 3. Request body processing and OAuth parameter validation
    req_body, body_error = _process_oauth_request_body(
        event, oauth_config["wrapper_secret"], correlation_id
    )
    if body_error or req_body is None:
        _performance_optimizer.end_timing("total_request", request_start)
        return body_error or {"error": "Request body processing failed"}

    # 4. OAuth token exchange execution
    success_response, oauth_error = _execute_oauth_token_exchange(
        oauth_config, req_body, correlation_id
    )

    # 5. Response processing and performance logging
    total_duration = _performance_optimizer.end_timing("total_request", request_start)

    if oauth_error:
        _logger.warning(
            "⚠️ OAuth failed in %.1fms (correlation: %s)",
            total_duration * 1000,
            correlation_id,
        )
        return oauth_error

    _logger.info(
        "✅ OAuth completed in %.1fms (correlation: %s)",
        total_duration * 1000,
        correlation_id,
    )
    _logger.debug("Response: %s (correlation: %s)", success_response, correlation_id)
    _logger.info("=== OAUTH LAMBDA END (correlation: %s) ===", correlation_id)

    return success_response or {"error": "Unknown OAuth processing error"}
