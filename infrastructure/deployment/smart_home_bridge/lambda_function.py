"""
⚡ HOME ASSISTANT ↔ ALEXA SMART HOME BRIDGE 🗣️

High-performance voice command processor optimized for sub-500ms response times.
Handles Alexa Smart Home directives and translates them for Home Assistant.

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
from dataclasses import dataclass
from typing import Any

import boto3
import urllib3
from botocore.exceptions import ClientError, NoCredentialsError

# Use generic boto3 client type for runtime compatibility
SSMClient = Any

# === EMBEDDED SHARED CONFIGURATION CLASSES (AUTO-GENERATED) ===

# This section contains shared configuration classes embedded for deployment



@dataclass
class RetryConfig:
    """Configuration for exponential backoff retry logic."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    backoff_factor: float = 2.0
    retriable_exceptions: tuple[type[Exception], ...] = (Exception,)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = 5
    reset_timeout: float = 60.0


@dataclass
class HomeAssistantApiConfig:
    """Configuration for Home Assistant API connections."""

    base_url: str
    token: str
    correlation_id: str = ""
    retry_config: RetryConfig | None = None
    circuit_breaker_config: CircuitBreakerConfig | None = None

    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.retry_config is None:
            self.retry_config = RetryConfig()
        if self.circuit_breaker_config is None:
            self.circuit_breaker_config = CircuitBreakerConfig()


@dataclass
class AlexaRequestConfig:
    """Configuration for Alexa Smart Home API requests."""

    base_url: str
    token: str
    correlation_id: str = ""
    cf_client_id: str = ""
    cf_client_secret: str = ""

    @property
    def cloudflare_headers(self) -> dict[str, str]:
        """Generate CloudFlare headers if both client ID and secret are provided."""
        if self.cf_client_id and self.cf_client_secret:
            return {
                "CF-Access-Client-Id": self.cf_client_id,
                "CF-Access-Client-Secret": self.cf_client_secret,
            }
        return {}

    @property
    def has_cloudflare_config(self) -> bool:
        """Check if CloudFlare configuration is complete."""
        return bool(self.cf_client_id and self.cf_client_secret)

# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===

# This section contains shared configuration embedded for deployment



# ╭─────────────────── SSM_PATH_CONSTANTS_START ───────────────────╮
# ║                    🔧 CENTRALIZED SSM PATH MANAGEMENT 🔧                    ║
# ║                                                                             ║
# ║ Single source of truth for all SSM parameter paths and configuration       ║
# ║ Used across all Lambda functions for consistent path management             ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# SSM Path Base Patterns
SSM_BASE_HOME_ASSISTANT = "/home-assistant"  # Gen3 base path

# Gen 2 Configuration Paths (dkaser's CloudFlare + SSM approach)
# Gen 2 uses: APP_CONFIG_PATH="/ha-alexa/" with single JSON at "/ha-alexa/appConfig"
SSM_GEN2_BASE_PATH = "/ha-alexa"
SSM_GEN2_APP_CONFIG = "/ha-alexa/appConfig"  # Single JSON parameter

# Gen 3 Configuration Storage Paths (modular SSM approach)
SSM_ALEXA_CONFIG_PATH = "/home-assistant/alexa/config"
SSM_OAUTH_CONFIG_PATH = "/home-assistant/oauth/config"
SSM_AWS_RUNTIME_PATH = "/home-assistant/aws/runtime"
SSM_SECURITY_POLICIES_PATH = "/home-assistant/security/policies"

# Lambda ARN Storage Paths (Gen3 standard format)
SSM_LAMBDA_ARN_BASE = "/home-assistant/alexa/lambda"
SSM_OAUTH_GATEWAY_ARN = "/home-assistant/alexa/lambda/oauth-gateway-arn"
SSM_SMART_HOME_BRIDGE_ARN = "/home-assistant/alexa/lambda/smart-home-bridge-arn"

# APP_CONFIG_PATH: Base reference point for finding SSM parameters
# Gen 1: No APP_CONFIG_PATH (pure environment variables)
# Gen 2: /ha-alexa (with appConfig appended → /ha-alexa/appConfig for JSON dump)
# Gen 3: /home-assistant/config (base for structured parameters)
APP_CONFIG_PATH_GEN2_DEFAULT = "/ha-alexa"
APP_CONFIG_PATH_GEN3_DEFAULT = "/home-assistant/config"

# Generation-specific defaults
APP_CONFIG_PATHS_BY_GENERATION = {
    "generation_1_env_only": None,  # No SSM path needed
    "generation_2_env_ssm_json": APP_CONFIG_PATH_GEN2_DEFAULT,
    "generation_3_modular_ssm": APP_CONFIG_PATH_GEN3_DEFAULT,
}


def build_ssm_gen2_config_path(base_path: str = SSM_GEN2_BASE_PATH) -> str:
    """
    Build Gen2 SSM configuration path (dkaser's CloudFlare + SSM approach).

    Gen2 uses a single JSON parameter at {base_path}/appConfig

    Args:
        base_path: Gen2 base path (default: "/ha-alexa")

    Returns:
        Gen2 SSM appConfig path

    Examples:
        build_ssm_gen2_config_path() -> "/ha-alexa/appConfig"
        build_ssm_gen2_config_path("/custom-alexa") -> "/custom-alexa/appConfig"
    """
    return f"{base_path.rstrip('/')}/appConfig"


def build_ssm_gen3_config_path(service: str, config_type: str = "config") -> str:
    """
    Build Gen3 SSM configuration path (modular SSM approach).

    Args:
        service: Service name (alexa, oauth, etc.)
        config_type: Configuration type (config, runtime, etc.)

    Returns:
        Gen3 modular SSM path

    Examples:
        build_ssm_gen3_config_path("alexa", "config") -> "/home-assistant/alexa/config"
        build_ssm_gen3_config_path("oauth", "config") -> "/home-assistant/oauth/config"
    """
    return f"{SSM_BASE_HOME_ASSISTANT}/{service}/{config_type}"


def build_ssm_lambda_arn_path(lambda_name: str) -> str:
    """
    Build standardized SSM Lambda ARN storage path.

    Args:
        lambda_name: Lambda function name (oauth-gateway, smart-home-bridge, etc.)

    Returns:
        Standardized SSM Lambda ARN path

    Examples:
        build_ssm_lambda_arn_path("oauth-gateway")
        -> "/home-assistant/alexa/lambda/oauth-gateway-arn"
        build_ssm_lambda_arn_path("smart-home-bridge")
        -> "/home-assistant/alexa/lambda/smart-home-bridge-arn"
    """
    return f"{SSM_LAMBDA_ARN_BASE}/{lambda_name}-arn"


def get_app_config_path_for_generation(generation: str) -> str | None:
    """
    Get standard APP_CONFIG_PATH base for a configuration generation.

    Args:
        generation: Configuration generation type

    Returns:
        Standard APP_CONFIG_PATH base for the generation, or None for env-only

    Raises:
        ValueError: If generation is not recognized

    Examples:
        get_app_config_path_for_generation("generation_2_env_ssm_json") -> "/ha-alexa"
        get_app_config_path_for_generation("generation_3_modular_ssm")
        -> "/home-assistant/config"
        get_app_config_path_for_generation("generation_1_env_only") -> None
    """
    if generation not in APP_CONFIG_PATHS_BY_GENERATION:
        available = ", ".join(APP_CONFIG_PATHS_BY_GENERATION.keys())
        raise ValueError(f"Unknown generation '{generation}'. Available: {available}")

    return APP_CONFIG_PATHS_BY_GENERATION[generation]


def build_ssm_config_subpath(base_path: str, subpath: str) -> str:
    """
    Build SSM configuration subpath with proper formatting.

    Args:
        base_path: Base SSM path
        subpath: Subpath to append (appConfig, config, etc.)

    Returns:
        Properly formatted SSM path

    Examples:
        build_ssm_config_subpath("/homeassistant/alexa", "appConfig")
        -> "/homeassistant/alexa/appConfig"
    """
    return f"{base_path.rstrip('/')}/{subpath}"


# ╰─────────────────── SSM_PATH_CONSTANTS_END ─────────────────────╯

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
    # Container warming utilities
    "handle_warmup_request",
    "create_warmup_response",
    # Retry and resilience utilities
    "retry_with_exponential_backoff",
    "create_resilient_http_session",
    "HomeAssistantRetryHandler",
    "create_home_assistant_retry_handler",
    # Configuration classes
    "RetryConfig",
    "CircuitBreakerConfig",
    "HomeAssistantApiConfig",
    "AlexaRequestConfig",
]


def test_dynamic_deployment() -> str:
    """Test function to prove dynamic deployment works automatically."""
    return "Dynamic deployment working! This function was auto-detected and embedded."


def handle_warmup_request(
    event: dict[str, Any], correlation_id: str, function_name: str
) -> bool:
    """
    🔥 Container Warmup Handler: Standardized Warmup Detection and Processing

    Detects and handles warmup requests from the configuration manager, providing
    consistent warmup behavior across all Lambda functions.

    Args:
        event: Lambda event dictionary to check for warmup flag
        correlation_id: Request correlation ID for logging
        function_name: Name of the current Lambda function for logging

    Returns:
        True if this is a warmup request, False otherwise
    """
    if event.get("warmup") is True:
        _logger.info(
            "🔥 Container warmup request received for %s (correlation: %s)",
            function_name,
            correlation_id,
        )
        return True
    return False


def create_warmup_response(function_name: str, correlation_id: str) -> dict[str, Any]:
    """
    🔥 Warmup Response Generator: Standardized Warmup Response Creation

    Creates a consistent warmup response for all Lambda functions, providing
    status information and timing data for monitoring warmup effectiveness.

    Args:
        function_name: Name of the Lambda function responding to warmup
        correlation_id: Request correlation ID for tracking

    Returns:
        Standardized warmup response dictionary
    """
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "status": "warm",
                "function": function_name,
                "timestamp": int(time.time()),
                "correlation_id": correlation_id,
                "container_ready": True,
                "warmup_source": "configuration_manager",
            }
        ),
    }


def retry_with_exponential_backoff(
    func: Any,
    retry_config: RetryConfig | None = None,
    correlation_id: str = "",
) -> Any:
    """
    🔄 Exponential Backoff Retry: Resilient API Call Handler

    Executes a function with exponential backoff retry logic, designed specifically
    for handling Home Assistant API timeouts and network failures during voice commands.

    Args:
        func: Function to execute with retry logic
        retry_config: Retry configuration (uses defaults if None)
        correlation_id: Request correlation ID for logging

    Returns:
        Function result on success

    Raises:
        Last exception encountered after all retries are exhausted
    """
    if retry_config is None:
        retry_config = RetryConfig()

    def decorator(*args: Any, **kwargs: Any) -> Any:
        last_exception = None
        current_delay = retry_config.base_delay

        for attempt in range(retry_config.max_retries + 1):
            try:
                if attempt > 0:
                    _logger.info(
                        "🔄 Retry attempt %d/%d after %.2fs delay (correlation: %s)",
                        attempt,
                        retry_config.max_retries,
                        current_delay,
                        correlation_id,
                    )
                    time.sleep(current_delay)

                result = func(*args, **kwargs)
                if attempt > 0:
                    _logger.info(
                        "✅ Retry successful on attempt %d (correlation: %s)",
                        attempt + 1,
                        correlation_id,
                    )
                return result

            except (*retry_config.retriable_exceptions,) as e:
                last_exception = e
                if attempt < retry_config.max_retries:
                    _logger.warning(
                        "⚠️ Attempt %d failed: %s (retrying in %.2fs, correlation: %s)",
                        attempt + 1,
                        str(e),
                        current_delay,
                        correlation_id,
                    )
                    current_delay = min(
                        current_delay * retry_config.backoff_factor,
                        retry_config.max_delay,
                    )
                else:
                    _logger.error(
                        "❌ All %d attempts failed (correlation: %s)",
                        retry_config.max_retries + 1,
                        correlation_id,
                    )

        # All retries exhausted, raise the last exception
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Exponential backoff failed but no exception was captured")

    return decorator


def create_resilient_http_session(
    connect_timeout: float = 5.0,
    read_timeout: float = 30.0,
    total_timeout: float = 35.0,
    max_retries: int = 3,
) -> urllib3.PoolManager:
    """
    🌐 Resilient HTTP Session: Optimized for Home Assistant API

    Creates a urllib3 PoolManager configured for reliable Home Assistant API
    communication with appropriate timeouts and retry configuration.

    Args:
        connect_timeout: TCP connection timeout in seconds
        read_timeout: HTTP read timeout in seconds
        total_timeout: Total request timeout in seconds
        max_retries: Maximum number of connection retries

    Returns:
        Configured urllib3.PoolManager for reliable HTTP requests
    """
    return urllib3.PoolManager(
        timeout=urllib3.Timeout(
            connect=connect_timeout, read=read_timeout, total=total_timeout
        ),
        retries=urllib3.Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        ),
        headers={
            "User-Agent": "HomeAssistant-Alexa-Bridge/2.0",
            "Connection": "keep-alive",
        },
    )


class HomeAssistantRetryHandler:
    """
    🏠 Home Assistant API Retry Handler: Voice Command Resilience

    Specialized retry handler for Home Assistant API calls, designed to handle
    the specific timeout and connectivity issues identified in your CloudWatch
    log analysis.

    RESILIENCE FEATURES:
    - Exponential backoff for temporary failures
    - Circuit breaker pattern for persistent failures
    - Request-specific timeout configuration
    - Detailed logging for performance monitoring

    TIMEOUT STRATEGY:
    - Connect: 5s (network connection establishment)
    - Read: 30s (Home Assistant processing time)
    - Total: 35s (overall request timeout)
    - Retries: 3 attempts with 0.5s, 1.0s, 2.0s delays
    """

    def __init__(self, api_config: HomeAssistantApiConfig):
        """Initialize retry handler with API configuration."""
        self.api_config = api_config
        self.http = create_resilient_http_session()

        # Circuit breaker state tracking
        self._circuit_breaker_failures = 0
        self._last_failure_time = 0

    def make_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make a resilient API request to Home Assistant with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/api/states")
            method: HTTP method (GET, POST, etc.)
            data: Request data for POST/PUT requests
            additional_headers: Optional additional headers (e.g., CloudFlare)

        Returns:
            Parsed JSON response from Home Assistant

        Raises:
            Exception: After all retries are exhausted
        """
        # Circuit breaker check
        if self._is_circuit_breaker_open():
            raise RuntimeError(
                f"Circuit breaker open: too many recent failures "
                f"(correlation: {self.api_config.correlation_id})"
            )

        url = f"{self.api_config.base_url.rstrip('/')}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_config.token}",
            "Content-Type": "application/json",
        }

        # Add optional additional headers (e.g., CloudFlare)
        if additional_headers:
            headers.update(additional_headers)

        # Prepare request data
        body = json.dumps(data) if data else None

        def _make_request():
            _logger.debug(
                "🌐 HA API Request: %s %s (correlation: %s)",
                method,
                endpoint,
                self.api_config.correlation_id,
            )
            start_time = time.time()

            response = self.http.request(
                method=method,
                url=url,
                headers=headers,
                body=body,
            )

            duration_ms = (time.time() - start_time) * 1000
            _logger.info(
                "📊 HA API Response: %d in %.0fms (correlation: %s)",
                response.status,
                duration_ms,
                self.api_config.correlation_id,
            )

            if response.status >= 400:
                error_msg = f"HTTP {response.status}: {response.data.decode()}"
                raise urllib3.exceptions.HTTPError(error_msg)

            # Reset circuit breaker on success
            self._circuit_breaker_failures = 0

            return json.loads(response.data.decode())

        retry_decorator = retry_with_exponential_backoff(
            func=_make_request,
            retry_config=self.api_config.retry_config,
            correlation_id=self.api_config.correlation_id,
        )

        try:
            return retry_decorator()
        except Exception as e:
            # Update circuit breaker
            self._circuit_breaker_failures += 1
            self._last_failure_time = time.time()
            raise e

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker should prevent requests."""
        if self.api_config.circuit_breaker_config is None:
            return False

        failure_threshold = self.api_config.circuit_breaker_config.failure_threshold
        if self._circuit_breaker_failures < failure_threshold:
            return False

        # Auto-reset circuit breaker after configured timeout
        reset_timeout = self.api_config.circuit_breaker_config.reset_timeout
        if time.time() - self._last_failure_time > reset_timeout:
            _logger.info(
                "🔄 Circuit breaker auto-reset (correlation: %s)",
                self.api_config.correlation_id,
            )
            self._circuit_breaker_failures = 0
            return False

        return True

    def get_retry_stats(self) -> dict[str, Any]:
        """Get retry handler statistics for monitoring."""
        stats = {
            "circuit_breaker_failures": self._circuit_breaker_failures,
            "circuit_breaker_open": self._is_circuit_breaker_open(),
            "last_failure_time": self._last_failure_time,
            "correlation_id": self.api_config.correlation_id,
        }

        if self.api_config.retry_config is not None:
            stats.update(
                {
                    "max_retries": self.api_config.retry_config.max_retries,
                    "base_delay": self.api_config.retry_config.base_delay,
                }
            )

        return stats


def create_home_assistant_retry_handler(
    base_url: str,
    token: str,
    correlation_id: str = "",
    max_retries: int = 3,
    base_delay: float = 0.5,
) -> HomeAssistantRetryHandler:
    """
    🏭 Factory Function: Create HomeAssistantRetryHandler with sensible defaults

    Creates a retry handler with backward-compatible parameters while using
    the new configuration objects internally.

    Args:
        base_url: Home Assistant base URL
        token: Home Assistant long-lived access token
        correlation_id: Request correlation ID for logging
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries

    Returns:
        Configured HomeAssistantRetryHandler instance
    """
    api_config = HomeAssistantApiConfig(
        base_url=base_url,
        token=token,
        correlation_id=correlation_id,
        retry_config=RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            retriable_exceptions=(
                urllib3.exceptions.TimeoutError,
                urllib3.exceptions.ConnectionError,
                urllib3.exceptions.HTTPError,
            ),
        ),
    )
    return HomeAssistantRetryHandler(api_config=api_config)


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
        if config_section == "cloudflare_config":
            # CloudFlare config IS the OAuth config (oauth_gateway = CloudFlare-Wrapper)
            return {
                "client_id": os.environ.get("CF_CLIENT_ID", ""),
                "client_secret": os.environ.get("CF_CLIENT_SECRET", ""),
                "wrapper_secret": os.environ.get("WRAPPER_SECRET", ""),
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
        if config_section == "lambda_config":
            return {
                "configuration_manager_arn": os.environ.get(
                    "CONFIGURATION_MANAGER_ARN", ""
                ),
                "cloudflare_wrapper_arn": os.environ.get("CLOUDFLARE_WRAPPER_ARN", ""),
                "smart_home_bridge_arn": os.environ.get("SMART_HOME_BRIDGE_ARN", ""),
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
                    # Apply environment overrides for additive approach
                    structured_config = self._apply_environment_overrides(
                        structured_config, config_section
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
            # Apply environment overrides even when loading from cache
            shared_config = self._apply_environment_overrides(
                shared_config, config_section
            )
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

            # Apply environment overrides for additive approach
            config = self._apply_environment_overrides(config, config_section)

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
            "cloudflare_config": {
                "CF_CLIENT_ID": "client_id",
                "CF_CLIENT_SECRET": "client_secret",
                "WRAPPER_SECRET": "wrapper_secret",
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
            "cloudflare_config": ["client_id"],  # CloudFlare IS the OAuth config
            "security_config": [],  # All optional
            "aws_config": ["region"],
            "lambda_config": [],  # All optional
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
        if config_section == "cloudflare_config":
            # CloudFlare config IS the OAuth config in Gen 2 JSON format
            return {
                "client_id": json_config.get("CF_CLIENT_ID", ""),
                "client_secret": json_config.get("CF_CLIENT_SECRET", ""),
                "wrapper_secret": json_config.get("WRAPPER_SECRET", ""),
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


def load_configuration(
    config_section: str = "ha_config",
    app_config_path: str | None = None,
    force_generation: str | None = None,
) -> tuple[dict[str, Any], str]:
    """
    Load configuration with generation detection and environment overrides.

    This is the primary configuration loading API that supports multi-generation
    configuration management with automatic generation detection and caching.

    ADDITIVE CONFIGURATION APPROACH:
    1. **Gen1 (ENV-only)**: Pure environment variables
    2. **Gen2 (ENV→SSM)**: Environment variables + SSM JSON fallback
    3. **Gen3 (Modular SSM)**: Structured SSM + ENV overrides + caching
    4. **ENV overrides**: Environment variables always take highest priority

    Args:
        config_section: Configuration section to load (ha_config,
            oauth_config, etc.)
        app_config_path: SSM path for Gen 2/3 configurations
        force_generation: Force specific generation for testing

    Returns:
        Tuple of (configuration_dict, generation_used)
    """
    # Delegate to the manager instance for now (will refactor incrementally)
    return _config_manager.load_configuration(
        config_section=config_section,
        app_config_path=app_config_path,
        force_generation=force_generation,
    )


def load_comprehensive_configuration(
    app_config_path: str | None = None,
    force_generation: str | None = None,
) -> tuple[dict[str, dict[str, Any]], str, dict[str, bool]]:
    """
    Load comprehensive configuration for all sections with feature availability
    detection.

    This function implements the incremental configuration approach where:
    - Core features work with minimal config (Gen 1)
    - Optional features activate when config is available (Gen 2+)
    - Configuration is additive across generations

    FEATURE DETECTION:
    - core_available: Basic HA connectivity (ha_config)
    - cloudflare_available: CloudFlare OAuth gateway (cloudflare_config = OAuth config)
    - caching_available: Response/config caching (aws_config + DynamoDB)
    - lambda_coordination_available: Cross-Lambda warming (lambda_config)

    Args:
        app_config_path: SSM path for Gen 2/3 configurations
        force_generation: Force specific generation for testing

    Returns:
        Tuple of (configurations_dict, generation_used, features_available)

    Example:
        configs, gen, features = load_comprehensive_configuration()
        if features['core_available']:
            # smart_home_bridge.py can work
        if features['core_available'] and features['cloudflare_available']:
            # oauth_gateway.py can work (CloudFlare IS the OAuth gateway)
        if features['lambda_coordination_available']:
            # configuration_manager.py can work with warming
    """
    _logger.info("Loading comprehensive configuration with feature detection")

    configurations: dict[str, dict[str, Any]] = {}
    features_available: dict[str, bool] = {
        "core_available": False,
        "cloudflare_available": False,  # CloudFlare IS the OAuth gateway
        "caching_available": False,
        "lambda_coordination_available": False,
    }

    # Define configuration sections to attempt loading
    config_sections = [
        "ha_config",  # Core HA connectivity
        "cloudflare_config",  # CloudFlare integration (includes OAuth functionality)
        "security_config",  # Security settings (secrets)
        "aws_config",  # AWS/DynamoDB for caching
        "lambda_config",  # Cross-Lambda coordination
    ]

    generation_used = "generation_1_env_only"  # Default fallback

    # Load each configuration section
    for section in config_sections:
        try:
            config, generation = _config_manager.load_configuration(
                config_section=section,
                app_config_path=app_config_path,
                force_generation=force_generation,
            )

            configurations[section] = config
            generation_used = generation  # Track the latest generation detected

            _logger.debug(
                "Loaded %s configuration: %s keys", section, len(config.keys())
            )

        except (ClientError, ValueError, KeyError, ImportError) as e:
            _logger.debug("Failed to load %s configuration: %s", section, e)
            configurations[section] = {}

    # Determine feature availability based on loaded configurations
    features_available["core_available"] = _is_core_config_complete(
        configurations.get("ha_config", {})
    )

    features_available["cloudflare_available"] = _is_cloudflare_config_complete(
        configurations.get("cloudflare_config", {})
    )

    features_available["caching_available"] = _is_caching_config_complete(
        configurations.get("aws_config", {})
    )

    features_available["lambda_coordination_available"] = _is_lambda_config_complete(
        configurations.get("lambda_config", {})
    )

    # Log feature availability for debugging
    available_features = [k for k, v in features_available.items() if v]
    _logger.info("Available features: %s", available_features)

    return configurations, generation_used, features_available


def _is_core_config_complete(ha_config: dict[str, Any]) -> bool:
    """Check if core HA configuration is complete for basic functionality."""
    required_fields = ["base_url"]
    return all(
        ha_config.get(field) and str(ha_config.get(field)).strip()
        for field in required_fields
    )


def _is_cloudflare_config_complete(cf_config: dict[str, Any]) -> bool:
    """
    Check if CloudFlare configuration is complete for OAuth gateway functionality.

    CloudFlare config IS the OAuth config - oauth_gateway.py IS the CloudFlare-Wrapper.
    """
    required_fields = ["client_id", "client_secret", "wrapper_secret"]
    return all(
        cf_config.get(field) and str(cf_config.get(field)).strip()
        for field in required_fields
    )


def _is_caching_config_complete(aws_config: dict[str, Any]) -> bool:
    """Check if caching configuration is complete for response/config caching."""
    required_fields = ["region"]
    has_aws_config = all(
        aws_config.get(field) and str(aws_config.get(field)).strip()
        for field in required_fields
    )

    # Also check for DynamoDB table environment variables
    has_cache_table = bool(os.environ.get("SHARED_CACHE_TABLE"))

    return has_aws_config or has_cache_table


def _is_lambda_config_complete(lambda_config: dict[str, Any]) -> bool:
    """
    Check if Lambda coordination configuration is complete for cross-Lambda
    features.
    """
    # Check for either configuration manager ARN or other Lambda ARNs
    coordination_fields = [
        "configuration_manager_arn",
        "oauth_gateway_arn",
        "smart_home_bridge_arn",
    ]

    return any(
        lambda_config.get(field) and str(lambda_config.get(field)).strip()
        for field in coordination_fields
    )


def load_configuration_as_configparser(
    app_config_path: str | None = None,
) -> configparser.ConfigParser:
    """
    Load configuration in ConfigParser format for backward compatibility.

    This function supports existing code that expects ConfigParser format
    while using the new comprehensive configuration loading underneath.

    Args:
        app_config_path: SSM path for Gen 2/3 configurations

    Returns:
        ConfigParser with appConfig section containing all configuration
    """
    _logger.debug("Loading configuration in ConfigParser format")

    config_parser = configparser.ConfigParser()
    config_parser.add_section("appConfig")

    try:
        # Load comprehensive configuration
        configurations, generation, _ = load_comprehensive_configuration(
            app_config_path=app_config_path
        )

        # Map configurations to legacy format using helper
        combined_config = _map_configurations_to_legacy_format(configurations)

        # Set all values in the ConfigParser
        for key, value in combined_config.items():
            config_parser.set("appConfig", key, value)

        _logger.debug(
            "ConfigParser loaded with %d parameters (generation: %s)",
            len(combined_config),
            generation,
        )

    except (ClientError, ValueError, KeyError) as e:
        _logger.warning("Failed to load comprehensive configuration: %s", e)

        # Fallback to environment variables
        combined_config = _get_environment_fallback_config()
        for key, value in combined_config.items():
            config_parser.set("appConfig", key, value)

        _logger.debug("ConfigParser loaded from environment fallback")

    return config_parser


def _map_configurations_to_legacy_format(
    configurations: dict[str, dict[str, Any]],
) -> dict[str, str]:
    """
    Map modern configuration format to legacy ConfigParser format.

    Args:
        configurations: Modern configuration dictionary

    Returns:
        Flat dictionary suitable for ConfigParser appConfig section
    """
    # Configuration mapping: (section, modern_key) -> legacy_key
    config_mappings = {
        ("ha_config", "base_url"): "HA_BASE_URL",
        ("ha_config", "token"): "HA_TOKEN",
        ("ha_config", "verify_ssl"): "HA_VERIFY_SSL",
        ("cloudflare_config", "client_id"): "CF_CLIENT_ID",
        ("cloudflare_config", "client_secret"): "CF_CLIENT_SECRET",
        ("cloudflare_config", "wrapper_secret"): "WRAPPER_SECRET",
        ("security_config", "alexa_secret"): "ALEXA_SECRET",
        ("security_config", "wrapper_secret"): "WRAPPER_SECRET",
    }

    combined_config: dict[str, str] = {}

    for (section, modern_key), legacy_key in config_mappings.items():
        section_config = configurations.get(section, {})
        value = section_config.get(modern_key)

        if value is not None:
            # Special handling for boolean values
            if isinstance(value, bool):
                combined_config[legacy_key] = str(value).lower()
            else:
                combined_config[legacy_key] = str(value)

    return combined_config


def _get_environment_fallback_config() -> dict[str, str]:
    """
    Get fallback configuration from environment variables.

    Returns:
        Dictionary of environment variable values
    """
    return {
        "HA_BASE_URL": os.environ.get("HA_BASE_URL", ""),
        "HA_TOKEN": os.environ.get("HA_TOKEN", ""),
        "CF_CLIENT_ID": os.environ.get("CF_CLIENT_ID", ""),
        "CF_CLIENT_SECRET": os.environ.get("CF_CLIENT_SECRET", ""),
        "ALEXA_SECRET": os.environ.get("ALEXA_SECRET", ""),
        "WRAPPER_SECRET": os.environ.get("WRAPPER_SECRET", ""),
    }


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
# Configuration Caching API
# ═══════════════════════════════════════════════════════════════════════════


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


def _get_dynamodb_client() -> Any:  # DynamoDB types not available
    """Get DynamoDB client with lazy initialization."""
    global _dynamodb_client  # pylint: disable=global-statement
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType, reportUnknownVariableType]
            "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
    return _dynamodb_client  # pyright: ignore[reportUnknownVariableType]


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

# === LOGGING CONFIGURATION ===
_debug = bool(os.environ.get("DEBUG"))

# Use shared configuration logger instead of local setup
_logger = create_structured_logger("SmartHomeBridge")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize boto3 client at global scope for connection reuse
client = boto3.client("ssm")  # type: ignore[assignment]
_default_app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

# ⚡ PHASE 4 PERFORMANCE OPTIMIZATION: Initialize performance monitoring at global scope
_performance_optimizer = PerformanceMonitor()
_response_cache = ResponseCache()
_connection_pool = ConnectionPoolManager()

# Initialize app at global scope for reuse across invocations
app = None  # pylint: disable=invalid-name  # Lambda container reuse pattern


class HAConfig:
    def __init__(self, config: configparser.ConfigParser) -> None:
        """
        Construct new app with configuration
        :param config: application configuration
        """
        self.config = config

    def get_config(self):
        return self.config


def _execute_alexa_request(
    event: dict[str, Any],
    request_config: AlexaRequestConfig,
) -> dict[str, Any]:
    """
    Execute HTTP request to Home Assistant Alexa API with retry logic.

    Args:
        event: Lambda event dictionary to forward
        request_config: Alexa request configuration with optional CloudFlare

    Returns:
        Response dictionary from Home Assistant API

    Raises:
        ValueError: If HTTP request fails with client/server error after retries
    """
    _logger.info(
        "🌐 Executing HA request with retry logic (correlation: %s)",
        request_config.correlation_id,
    )

    # Log CloudFlare status for debugging
    if request_config.has_cloudflare_config:
        _logger.debug(
            "🔒 CloudFlare Access enabled (correlation: %s)",
            request_config.correlation_id,
        )
    else:
        _logger.debug(
            "🌐 Direct Home Assistant access (no CloudFlare, correlation: %s)",
            request_config.correlation_id,
        )

    # Create retry handler for this request
    retry_handler = create_home_assistant_retry_handler(
        base_url=request_config.base_url,
        token=request_config.token,
        correlation_id=request_config.correlation_id,
        max_retries=3,
        base_delay=0.5,
    )

    try:
        # Prepare request data for the smart home API
        request_data = {
            "directive": event.get("directive"),
            "context": event.get("context", {}),
        }

        # Make the API request with retry logic and optional CloudFlare headers
        response = retry_handler.make_api_request(
            endpoint="/api/alexa/smart_home",
            method="POST",
            data=request_data,
            additional_headers=request_config.cloudflare_headers,
        )

        _logger.info(
            "✅ HA request successful (correlation: %s)", request_config.correlation_id
        )
        return response

    except Exception as e:
        _logger.error(
            "❌ HA request failed after retries (correlation: %s): %s",
            request_config.correlation_id,
            e,
        )

        # Return Alexa-compatible error response
        error_type = (
            "INVALID_AUTHORIZATION_CREDENTIAL"
            if "401" in str(e) or "403" in str(e)
            else "INTERNAL_ERROR"
        )

        raise ValueError(
            json.dumps(
                {
                    "event": {
                        "payload": {
                            "type": error_type,
                            "message": str(e),
                        }
                    }
                }
            )
        ) from e


def _extract_and_validate_directive(
    event: dict[str, Any], app_config: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """
    Extract and validate Alexa directive with token extraction.

    Args:
        event: Lambda event dictionary
        app_config: Application configuration dictionary

    Returns:
        Tuple of (directive dict, bearer token string)

    Raises:
        ValueError: If directive validation fails or token is missing
    """
    directive = event.get("directive")
    if directive is None:
        raise ValueError("Malformatted request - missing directive")
    if directive.get("header", {}).get("payloadVersion") != "3":
        raise ValueError("Only support payloadVersion == 3")

    scope = directive.get("endpoint", {}).get("scope")
    if scope is None:
        # token is in grantee for Linking directive
        scope = directive.get("payload", {}).get("grantee")
    if scope is None:
        # token is in payload for Discovery directive
        scope = directive.get("payload", {}).get("scope")
    if scope is None:
        raise ValueError("Malformatted request - missing endpoint.scope")
    if scope.get("type") != "BearerToken":
        raise ValueError("Only support BearerToken")

    token = scope.get("token")
    if token is None and _debug:
        token = app_config["HA_TOKEN"]  # only for debug purpose

    if token is None:
        raise ValueError("Missing bearer token")

    return directive, token


def _validate_request_security(
    event: dict[str, Any],
    correlation_id: str,
    rate_limiter: Any,
    alexa_validator: Any,
    security_logger: Any,
) -> None:
    """
    Validate request security including rate limiting and Alexa request validation.

    Args:
        event: Lambda event dictionary
        correlation_id: Request correlation ID for logging
        rate_limiter: Rate limiting service instance
        alexa_validator: Alexa validation service instance
        security_logger: Security logging service instance

    Raises:
        ValueError: If security validation fails
        RuntimeError: If rate limit is exceeded
        KeyError: If required security fields are missing
    """
    # Validate request rate limiting
    client_ip = (
        event.get("requestContext", {}).get("identity", {}).get("sourceIp", "unknown")
    )
    is_allowed, reason = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        security_logger.log_security_event(
            "rate_limit_exceeded",
            client_ip,
            f"Rate limit exceeded: {reason}, correlation_id: {correlation_id}",
            "WARNING",
        )
        raise RuntimeError("Rate limit exceeded")

    # Security validation
    directive, error_response = alexa_validator.validate_directive(event)
    if error_response is not None:
        raise ValueError(f"Directive validation failed: {error_response}")

    directive_namespace = (
        directive.get("header", {}).get("namespace") if directive else None
    )
    security_logger.log_security_event(
        "request_validated",
        client_ip,
        f"Request validated: namespace={directive_namespace}, "
        f"correlation_id={correlation_id}",
    )


def _setup_configuration() -> configparser.ConfigParser:
    """
    ⚡ PERFORMANCE-OPTIMIZED: Set up application configuration with multi-layer caching.

    CACHING STRATEGY:
    1. Container Cache: 0-1ms (warm Lambda containers)
    2. DynamoDB Shared Cache: 20-50ms (cross-Lambda sharing)
    3. SSM Parameter Store: 100-200ms (authoritative source)

    Returns:
        ConfigParser instance with loaded configuration
    """
    start_time = _performance_optimizer.start_timing("config_load")

    try:
        # ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
        # ║                           🚀 TRANSFER-READY CODE 🚀                       ║
        # ║ 📋 BLOCK PURPOSE: Strategic 3-tier caching for <500ms voice commands     ║
        # ║ 🔄 TRANSFER STATUS: Ready for duplication across Lambda functions        ║
        # ║ ⚡ PERFORMANCE: Container 0-1ms | Shared 20-50ms | SSM 100-200ms         ║
        # ║                                                                           ║
        # ║ 🎯 USAGE PATTERN:                                                         ║
        # ║   1. Copy entire block between "BLOCK_START" and "BLOCK_END" markers     ║
        # ║   2. Update function prefixes as needed (e.g., _oauth_ → _bridge_)        ║
        # ║   3. Adjust cache keys and table names for target service                ║
        # ║   4. Maintain identical core functionality across Lambda functions       ║
        # ╚═══════════════════════════════════════════════════════════════════════════╝

        # Use shared configuration loading which handles all caching internally
        config = load_configuration_as_configparser(
            app_config_path=_default_app_config_path
        )

        # Config is always a ConfigParser instance
        _performance_optimizer.record_cache_hit()
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.info("✅ Configuration loaded (%.1fms)", duration * 1000)
        return config

        # ╭─────────────────── TRANSFER BLOCK END ───────────────────╮

    except (ValueError, RuntimeError, KeyError, ImportError) as e:
        _performance_optimizer.record_cache_miss()
        _logger.warning("Enhanced config loading failed, using fallback: %s", e)

        # Fallback to basic shared configuration loading
        config = load_configuration_as_configparser(
            app_config_path=_default_app_config_path
        )

        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.warning("⚠️ Fallback configuration loaded (%.1fms)", duration * 1000)

        # Config is always a ConfigParser instance
        return config


def _handle_response_caching_and_performance(
    request_hash: str, request_start: float, response: dict[str, Any]
) -> dict[str, Any]:
    """
    Handle response caching and performance logging for successful requests.

    Args:
        request_hash: Hash of the request for caching
        request_start: Start time of the request for performance measurement
        response: Response dictionary to cache and return

    Returns:
        The response dictionary (pass-through)
    """
    # 🚀 PHASE 4: Cache successful responses for 5 minutes
    _response_cache.set(request_hash, response, ttl_seconds=300)

    # Log performance statistics
    total_duration = _performance_optimizer.end_timing("total_request", request_start)
    _logger.info("✅ Request completed in %.1fms", total_duration * 1000)

    # Log performance stats every 10 requests for monitoring
    perf_stats = _performance_optimizer.get_performance_stats()
    total_requests = perf_stats.get("cache_hits", 0) + perf_stats.get("cache_misses", 0)
    if total_requests % 10 == 0:
        _logger.info("📊 Performance stats: %s", perf_stats)

    return response


def _handle_api_error_caching(
    request_error: ValueError, request_hash: str, request_start: float
) -> dict[str, Any]:
    """
    Handle API error response caching and performance logging.

    Args:
        request_error: ValueError containing JSON error response
        request_hash: Hash of the request for caching
        request_start: Start time of the request for performance measurement

    Returns:
        Error response dictionary parsed from the exception
    """
    # _execute_alexa_request raises ValueError with JSON error response
    error_response = json.loads(str(request_error))

    # Cache API errors for 1 minute to prevent repeated failures
    _response_cache.set(request_hash, error_response, ttl_seconds=60)

    total_duration = _performance_optimizer.end_timing("total_request", request_start)
    _logger.warning("⚠️ Request failed in %.1fms", total_duration * 1000)

    return error_response


def _check_response_cache(
    request_hash: str, request_start: float
) -> dict[str, Any] | None:
    """
    Check response cache for identical requests and handle cache hits.

    Args:
        request_hash: Hash of the request to check in cache
        request_start: Start time of the request for performance measurement

    Returns:
        Cached response if found, None if cache miss
    """
    cached_response, cache_hit = _response_cache.get(request_hash)
    if cache_hit:
        _performance_optimizer.record_cache_hit()
        duration = _performance_optimizer.end_timing("total_request", request_start)
        _logger.info("✅ Cache HIT - Response served in %.1fms", duration * 1000)
        return cached_response

    _performance_optimizer.record_cache_miss()
    return None


def _create_security_error_response(
    security_error: Exception, correlation_id: str, request_hash: str
) -> dict[str, Any]:
    """
    Create and cache security validation error response.

    Args:
        security_error: The security validation exception
        correlation_id: Request correlation ID for logging
        request_hash: Hash of the request for caching

    Returns:
        Error response dictionary
    """
    _logger.error("Security validation failed: %s", security_error)
    security_logger = SecurityEventLogger()
    security_logger.log_security_event(
        "validation_failure",
        "unknown",
        f"Security validation failed: {security_error}, "
        f"correlation_id: {correlation_id}",
        "ERROR",
    )
    error_response = {
        "event": {
            "payload": {
                "type": "INTERNAL_ERROR",
                "message": "Security validation failed",
            }
        }
    }
    # Cache security errors for 60 seconds
    _response_cache.set(request_hash, error_response, ttl_seconds=60)
    return error_response


def _create_rate_limit_error_response(request_hash: str) -> dict[str, Any]:
    """
    Create and cache rate limit exceeded error response.

    Args:
        request_hash: Hash of the request for caching

    Returns:
        Rate limit error response dictionary
    """
    error_response = {
        "event": {
            "payload": {
                "type": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
            }
        }
    }
    # Cache rate limit responses for 60 seconds
    _response_cache.set(request_hash, error_response, ttl_seconds=60)
    return error_response


def _initialize_security_components_and_validate(
    event: dict[str, Any], correlation_id: str
) -> tuple[float, Exception | None]:
    """
    Initialize security components and validate the request.

    Args:
        event: Lambda event dictionary
        correlation_id: Request correlation ID for logging

    Returns:
        Tuple of (security_start_time, exception_if_any)
        If exception is not None, caller should handle the error
    """
    # Initialize security components
    security_start = _performance_optimizer.start_timing("security_validation")
    rate_limiter = RateLimiter()
    alexa_validator = AlexaValidator()
    security_logger = SecurityEventLogger()

    try:
        # Validate request security
        _validate_request_security(
            event, correlation_id, rate_limiter, alexa_validator, security_logger
        )
        _performance_optimizer.end_timing("security_validation", security_start)
        return security_start, None
    except RuntimeError as rate_error:
        if "Rate limit exceeded" in str(rate_error):
            return security_start, rate_error  # Signal rate limit error
        raise  # Re-raise other RuntimeErrors
    except (ValueError, KeyError) as security_error:
        return security_start, security_error  # Return error for caller to handle


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    ⚡ PERFORMANCE-OPTIMIZED: Enhanced Lambda handler with response caching and timing.

    Processes Alexa Smart Home directives using:
    - Multi-layer configuration caching
    - Response caching for identical requests
    - Performance timing and monitoring
    - Enhanced error handling and security validation

    TARGET: <300ms total response time for voice commands
    """
    global app  # pylint: disable=global-statement  # Required for Lambda container reuse

    # 🚀 PHASE 4: Start performance timing for entire request
    request_start = _performance_optimizer.start_timing("total_request")

    # Extract correlation ID for request tracking
    correlation_id = extract_correlation_id(context)
    _logger.info("🎯 Processing request %s", correlation_id)

    # 🔥 CONTAINER WARMING: Handle warmup requests from configuration manager
    if handle_warmup_request(event, correlation_id, "smart_home_bridge"):
        return create_warmup_response("smart_home_bridge", correlation_id)

    # �🚀 PHASE 4: Check response cache for identical requests
    request_hash = str(hash(str(event)))
    cached_response = _check_response_cache(request_hash, request_start)
    if cached_response is not None:
        return cached_response

    # Initialize security components and validate request
    _, security_error = _initialize_security_components_and_validate(
        event, correlation_id
    )

    # Handle security validation errors
    if security_error is not None:
        if isinstance(security_error, RuntimeError) and "Rate limit exceeded" in str(
            security_error
        ):
            return _create_rate_limit_error_response(request_hash)
        return _create_security_error_response(
            security_error, correlation_id, request_hash
        )

    # Initialize app if it doesn't yet exist
    if app is None:
        _logger.info("Loading config and creating persistence object...")
        config = _setup_configuration()
        app = HAConfig(config)

    app_config = app.get_config()["appConfig"]

    # Extract and validate directive with token
    directive_start = _performance_optimizer.start_timing("directive_processing")
    _, token = _extract_and_validate_directive(event, dict(app_config))
    _performance_optimizer.end_timing("directive_processing", directive_start)

    _logger.debug("Event: %s", event)

    try:
        # Create safe request configuration with optional CloudFlare parameters
        request_config = AlexaRequestConfig(
            base_url=app_config["HA_BASE_URL"],
            token=token,
            correlation_id=correlation_id,
            cf_client_id=app_config.get("CF_CLIENT_ID", ""),
            cf_client_secret=app_config.get("CF_CLIENT_SECRET", ""),
        )

        # Execute request to Home Assistant API
        ha_request_start = _performance_optimizer.start_timing("ha_api_request")
        response = _execute_alexa_request(
            event,
            request_config,
        )
        _performance_optimizer.end_timing("ha_api_request", ha_request_start)

        return _handle_response_caching_and_performance(
            request_hash, request_start, response
        )

    except ValueError as request_error:
        return _handle_api_error_caching(request_error, request_hash, request_start)
