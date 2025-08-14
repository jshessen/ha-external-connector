"""
💼 SMART HOME BRIDGE: Professional Executive Receptionist Services 🗣️

The Executive Receptionist handles all daily voice command operations with
exceptional efficiency and professionalism. Translates visitor requests
into precise Home Assistant actions while maintaining sub-500ms response times.

EXECUTIVE RECEPTIONIST RESPONSIBILITIES:
- Voice Command Processing: Alexa directive translation and execution
- Home Assistant Coordination: Efficient API communication and device control
- Response Management: Professional status updates and error handling
- Performance Monitoring: Service quality tracking and optimization

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

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import configparser
import json
import logging
import os
from typing import Any

import boto3

# === SHARED CONFIGURATION IMPORTS ===
from .shared_configuration import (
    AlexaRequestConfig,
    AlexaValidator,
    ConnectionPoolManager,
    PerformanceMonitor,
    RateLimiter,
    ResponseCache,
    SecurityEventLogger,
    create_home_assistant_retry_handler,
    create_structured_logger,
    create_warmup_response,
    extract_correlation_id,
    handle_warmup_request,
    load_configuration_as_configparser,
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === EXECUTIVE RECEPTIONIST INITIALIZATION ===
_debug = bool(os.environ.get("DEBUG"))

# Executive Receptionist logging setup
_logger = create_structured_logger("SmartHomeBridge")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize AWS SSM client for configuration access
client = boto3.client("ssm")  # type: ignore[assignment]
_default_app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

# Initialize performance monitoring for voice command operations
_performance_optimizer = PerformanceMonitor()
_response_cache = ResponseCache()
_connection_pool = ConnectionPoolManager()

# Initialize application instance for Lambda container reuse
app = None  # pylint: disable=invalid-name  # Lambda container optimization


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
            "Executive Receptionist: HA request successful (correlation: %s)",
            request_config.correlation_id,
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
    Executive Receptionist Configuration Setup: Load office operating procedures.

    Retrieves operational configuration through multi-tier caching for optimal
    voice command response times. Essential for Home Assistant communication
    and Alexa directive processing.

    Returns:
        ConfigParser instance with loaded operational configuration
    """
    start_time = _performance_optimizer.start_timing("config_load")

    try:
        # ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
        # ║                    TRANSFER-READY CODE                       ║
        # ║ PURPOSE: Strategic 3-tier caching for <500ms voice commands ║
        # ║ STATUS: Ready for duplication across Lambda functions        ║
        # ║ PERFORMANCE: Container 0-1ms | Shared 20-50ms | SSM 100-200ms ║
        # ║                                                              ║
        # ║ USAGE PATTERN:                                               ║
        # ║   1. Copy entire block between "BLOCK_START" and "BLOCK_END" ║
        # ║   2. Update function prefixes as needed (_bridge_, etc.)     ║
        # ║   3. Adjust cache keys and table names for target service    ║
        # ║   4. Maintain identical core functionality                   ║
        # ╚══════════════════════════════════════════════════════════════╝

        # Use shared configuration loading which handles all caching internally
        config = load_configuration_as_configparser(
            app_config_path=_default_app_config_path
        )

        # Configuration successfully loaded
        _performance_optimizer.record_cache_hit()
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.info(
            "Executive Receptionist: Configuration loaded (%.1fms)", duration * 1000
        )
        return config

        # ╭─────────────────── TRANSFER BLOCK END ───────────────────╮

    except (ValueError, RuntimeError, KeyError, ImportError) as e:
        _performance_optimizer.record_cache_miss()
        _logger.warning("Configuration loading failed, using fallback: %s", e)

        # Fallback to basic shared configuration loading
        config = load_configuration_as_configparser(
            app_config_path=_default_app_config_path
        )

        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.warning(
            "Executive Receptionist: Fallback configuration loaded (%.1fms)",
            duration * 1000,
        )

        # Configuration fallback successful
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


# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
