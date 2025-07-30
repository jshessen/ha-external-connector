"""
🌐 STREAMLINED CLOUDFLARE OAUTH GATEWAY: Essential Security Bridge for Alexa 🔐

=== WHAT THIS FILE DOES (In Plain English) ===

This file is your streamlined "security checkpoint" that sits between Amazon Alexa and
your Home Assistant, with essential OAuth and CloudFlare functionality. Think of it as
having a professional security guard instead of an entire security department.

1. 📱 You open Alexa app and click "Link Account" for your smart home skill
2. 🌐 Alexa sends you to THIS CODE for OAuth authentication
3. 🔐 THIS CODE handles the OAuth "handshake" using shared security framework
4. 🛡️ THIS CODE adds CloudFlare headers for protection
5. 🏠 Your request gets forwarded to Home Assistant through CloudFlare
6. ✅ Home Assistant confirms your identity and grants access
7. 📱 Alexa app shows "Account successfully linked!"

=== THE STREAMLINED ALEXA SKILL ECOSYSTEM ===

🏢 **PROFESSIONAL OFFICE WITH STREAMLINED SECURITY**

👮‍♂️ **SECURITY CHECKPOINT (THIS FILE - oauth_gateway.py)**
- 🏛️ **Job**: OAuth authentication and CloudFlare proxy with shared security
- 🎫 **Location**: Main entrance (OAuth authentication + Smart Home proxy endpoint)
- 📋 **Responsibilities**:
  * DUAL-MODE OPERATIONS: Handle both OAuth authentication AND Smart Home proxy
  * Use shared security framework (RateLimiter, SecurityValidator, etc.)
  * Essential OAuth token exchange and caching
  * CloudFlare header management for protected access
  * Streamlined error handling with correlation tracking

💼 **EXECUTIVE RECEPTIONIST (smart_home_bridge.py)**
- 🏢 **Job**: Fast voice command processing for daily operations
- 📞 **Location**: Executive floor (Optimized for <500ms voice responses)
- 📋 **Responsibilities**:
  * Process voice commands with maximum speed
  * Use shared AlexaValidator for consistent validation
  * Optimized for performance over comprehensive security

Author: Jeff Hessenflow <jeff.hessenflow@gmail.com>
Based on original work by: Jason Hu <awaregit@gmail.com>
Copyright 2019 Jason Hu <awaregit at gmail.com>
Licensed under the Apache License, Version 2.0
"""

# pylint: disable=too-many-lines  # Lambda functions must be standalone
# pylint: disable=duplicate-code  # Lambda functions must be standalone - no shared modules

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import configparser
import json
import logging
import os
import time
import urllib
import urllib.parse
from dataclasses import dataclass
from typing import Any, cast

import boto3
import urllib3
from botocore.exceptions import BotoCoreError, ClientError

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import (
    OAUTH_TOKEN_CACHE_TABLE,
    AlexaValidator,
    RateLimiter,
    SecurityEventLogger,
    SecurityValidator,
    cache_config_in_container,
    create_error_response,
    create_http_client,
    create_lambda_logger,
    extract_correlation_id,
    get_container_cached_config,
    load_configuration,
    load_environment,
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === LOGGING CONFIGURATION ===


def _initialize_logging() -> logging.Logger:
    """🔧 LOGGING INITIALIZER: Setup Smart Logging System"""
    logger = create_lambda_logger("StreamlinedOAuthGateway")
    initial_debug = bool(os.environ.get("DEBUG"))
    logger.setLevel(logging.DEBUG if initial_debug else logging.INFO)
    return logger


_logger = _initialize_logging()

# Global security components (HIGH security level for OAuth)
_rate_limiter = RateLimiter()

# === SIMPLIFIED CONFIGURATION CLASSES ===


@dataclass
class OAuthConfiguration:
    """Simple OAuth configuration object using shared loading infrastructure."""

    base_url: str
    client_id: str
    client_secret: str
    cf_client_id: str | None = None
    cf_client_secret: str | None = None
    verify_ssl: bool = True

    @classmethod
    def from_environment(cls) -> "OAuthConfiguration":
        """Load OAuth configuration using shared configuration system."""
        env_vars = load_environment()

        # Try to load from SSM configuration first
        app_config: dict[str, Any] = {}
        try:
            config = load_configuration(
                app_config_path=env_vars.get("APP_CONFIG_PATH", ""),
                return_format="configparser",
            )
            if isinstance(config, configparser.ConfigParser) and config.has_section(
                "appConfig"
            ):
                app_config = dict(config["appConfig"])
        except (ValueError, KeyError, TypeError) as e:
            _logger.warning("Failed to load configuration from SSM: %s", str(e))

        # Environment variables take priority
        base_url = (
            env_vars.get("BASE_URL")
            or env_vars.get("HA_BASE_URL")
            or app_config.get("HA_BASE_URL")
        )
        client_id = env_vars.get("CF_CLIENT_ID") or app_config.get("CF_CLIENT_ID")
        client_secret = env_vars.get("CF_CLIENT_SECRET") or app_config.get(
            "CF_CLIENT_SECRET"
        )

        # CloudFlare credentials (optional)
        cf_client_id = app_config.get("cf_client_id") or app_config.get("CF_CLIENT_ID")
        cf_client_secret = app_config.get("cf_client_secret") or app_config.get(
            "CF_CLIENT_SECRET"
        )

        verify_ssl = not bool(env_vars.get("NOT_VERIFY_SSL"))

        if not base_url:
            raise ValueError("Base URL not configured in environment or SSM")

        return cls(
            base_url=base_url.strip("/"),
            client_id=client_id or "",
            client_secret=client_secret or "",
            cf_client_id=cf_client_id,
            cf_client_secret=cf_client_secret,
            verify_ssl=verify_ssl,
        )


# === OAUTH CACHING FUNCTIONS ===


def _get_oauth_cache_client() -> Any:
    """Get DynamoDB client with lazy initialization (function attribute cache)."""
    if not hasattr(_get_oauth_cache_client, "client"):
        _get_oauth_cache_client.client = boto3.resource("dynamodb")  # pyright: ignore
    # Direct attribute access for type checkers
    return _get_oauth_cache_client.client  # type: ignore[attr-defined]


def _generate_oauth_cache_key(req_dict: dict[bytes, list[bytes]]) -> str | None:
    """Generate cache key for OAuth request."""
    try:
        # Extract key parameters for cache key generation
        grant_type = req_dict.get(b"grant_type", [b""])[0].decode("utf-8")
        code = req_dict.get(b"code", [b""])[0].decode("utf-8")

        if grant_type == "authorization_code" and code:
            # Cache by authorization code for token exchange
            return f"oauth_token_{hash(code)}"
        if grant_type == "refresh_token":
            refresh_token = req_dict.get(b"refresh_token", [b""])[0].decode("utf-8")
            if refresh_token:
                return f"oauth_refresh_{hash(refresh_token)}"

        return None
    except (UnicodeDecodeError, KeyError, IndexError):
        return None


def _get_cached_oauth_token(cache_key: str) -> dict[str, Any] | None:
    """
    Retrieve cached OAuth token with dual-layer caching.

    Uses both container-level cache (fastest) and DynamoDB (persistent).
    This allows oauth_gateway.py to benefit from shared caching infrastructure
    while maintaining OAuth-specific token caching for normal requests.
    """
    # First, try container-level cache (shared infrastructure)
    try:
        container_cached = get_container_cached_config("oauth", f"token:{cache_key}")
        if container_cached:
            token_data = container_cached.get("token_data")
            if isinstance(token_data, dict):
                _logger.debug("OAuth token served from container cache")
                return cast(dict[str, Any], token_data)
    except (ValueError, KeyError, TypeError) as e:
        _logger.debug("Container cache lookup failed: %s", str(e))

    # Fallback to DynamoDB cache
    try:
        table = _get_oauth_cache_client().Table(OAUTH_TOKEN_CACHE_TABLE)
        response = table.get_item(Key={"cache_key": cache_key})

        if "Item" in response:
            item = response["Item"]
            # Check if token is still valid (5 minute cache)
            if time.time() - item.get("timestamp", 0) < 300:
                token_data = item.get("token_data")
                if isinstance(token_data, dict):
                    # Also cache in container for next request
                    cache_config_in_container(
                        "oauth", f"token:{cache_key}", {"token_data": token_data}
                    )
                    _logger.debug("OAuth token served from DynamoDB cache")
                    return cast(dict[str, Any], token_data)

    except (ClientError, BotoCoreError) as e:
        _logger.warning("OAuth DynamoDB cache read failed: %s", str(e))

    return None


def _cache_oauth_token(cache_key: str, token_data: dict[str, Any]) -> None:
    """
    Cache OAuth token with dual-layer caching.

    Stores in both container cache (for immediate reuse) and DynamoDB
    (for persistence). This enhancement allows the oauth_gateway to benefit
    from shared caching infrastructure.
    """
    # Cache in container-level cache first (shared infrastructure)
    try:
        cache_config_in_container(
            "oauth", f"token:{cache_key}", {"token_data": token_data}
        )
        _logger.debug("OAuth token cached in container")
    except (ValueError, KeyError, TypeError) as e:
        _logger.warning("Container cache write failed: %s", str(e))

    # Also cache in DynamoDB for persistence
    try:
        table = _get_oauth_cache_client().Table(OAUTH_TOKEN_CACHE_TABLE)
        table.put_item(
            Item={
                "cache_key": cache_key,
                "token_data": token_data,
                "timestamp": time.time(),
                "ttl": int(time.time()) + 300,  # 5 minute TTL
            }
        )
        _logger.debug("OAuth token cached in DynamoDB")
    except (ClientError, BotoCoreError) as e:
        _logger.warning("OAuth DynamoDB cache write failed: %s", str(e))


# === MAIN LAMBDA HANDLER ===


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    🚪 AWS LAMBDA ENTRY POINT: Streamlined Security Gateway

    Handles both OAuth authentication and Smart Home proxy requests with
    shared security infrastructure for optimal performance and maintainability.
    """
    # Initialize request context
    correlation_id = extract_correlation_id(context)
    _logger.info("=== LAMBDA START (correlation: %s) ===", correlation_id)

    # 🛡️ SECURITY VALIDATION using shared infrastructure
    client_ip = event.get("headers", {}).get("X-Forwarded-For", "alexa-service")
    client_ip = client_ip.split(",")[0] if client_ip else "alexa-service"

    # Rate limiting for OAuth requests (HIGH security level)
    is_allowed, rate_limit_reason = _rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        SecurityEventLogger.log_rate_limit_violation(client_ip, rate_limit_reason)
        _logger.warning("Rate limit exceeded: %s", rate_limit_reason)
        return create_error_response(
            "rate_limited", "Too many requests", 429, correlation_id
        )

    # Basic request validation
    if not event:
        SecurityEventLogger.log_validation_failure(
            client_ip, "empty_event", "Empty event received"
        )
        return create_error_response(
            "invalid_request", "Empty request", 400, correlation_id
        )

    # Log security event
    SecurityEventLogger.log_security_event(
        "oauth_gateway_start",
        client_ip,
        f"OAuth gateway processing starting (correlation: {correlation_id})",
        "INFO",
    )

    try:
        # Detect request type and route accordingly
        request_type = _detect_request_type(event)
        _logger.info("Request type detected: %s", request_type)

        if request_type == "oauth":
            return _handle_oauth_flow(event, client_ip, correlation_id)
        if request_type == "smart_home":
            return _handle_smart_home_proxy(event, client_ip, correlation_id)

        SecurityEventLogger.log_validation_failure(
            client_ip,
            "unknown_request_type",
            f"Unknown request type: {request_type}",
        )
        return create_error_response(
            "invalid_request", "Unknown request type", 400, correlation_id
        )

    except (OSError, RuntimeError, ValueError) as e:
        SecurityEventLogger.log_security_event(
            "oauth_gateway_error",
            client_ip,
            f"Unexpected error: {str(e)}",
            "ERROR",
        )
        _logger.error("Unexpected error in lambda_handler: %s", str(e))
        return create_error_response(
            "internal_error", "Internal server error", 500, correlation_id
        )
    finally:
        _logger.info("=== LAMBDA END (correlation: %s) ===", correlation_id)


# === REQUEST TYPE DETECTION ===


def _detect_request_type(event: dict[str, Any]) -> str:
    """Detect whether this is an OAuth or Smart Home request."""
    # Check HTTP method and content type
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get(
        "http", {}
    ).get("method")
    content_type = event.get("headers", {}).get("content-type", "").lower()

    # OAuth requests are typically POST with form data
    if http_method == "POST" and "application/x-www-form-urlencoded" in content_type:
        return "oauth"

    # Smart Home requests contain Alexa directive structure
    body = event.get("body")
    if body:
        try:
            parsed_body = json.loads(body) if isinstance(body, str) else body

            # Check for Alexa Smart Home directive structure
            if isinstance(parsed_body, dict) and "directive" in parsed_body:
                directive = cast(dict[str, Any], parsed_body["directive"])
                if "header" in directive:
                    header = directive["header"]
                    if isinstance(header, dict) and "namespace" in header:
                        return "smart_home"
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Default to OAuth for compatibility
    return "oauth"


# === OAUTH AUTHENTICATION FLOW ===


def _handle_oauth_flow(
    event: dict[str, Any], client_ip: str, correlation_id: str
) -> dict[str, Any]:
    """Handle OAuth authentication flow with shared security validation."""
    SecurityEventLogger.log_security_event(
        "oauth_flow_start",
        client_ip,
        f"OAuth authentication flow starting (correlation: {correlation_id})",
        "INFO",
    )

    try:
        # Load OAuth configuration
        oauth_config = OAuthConfiguration.from_environment()

        # Validate and parse request body
        body = event.get("body", "")
        if isinstance(body, str):
            req_dict = urllib.parse.parse_qs(body.encode("utf-8"))
        else:
            req_dict = urllib.parse.parse_qs(body)

        # Security validation using shared infrastructure
        body_str = body if isinstance(body, str) else body.decode("utf-8")
        is_valid_size, size_reason = SecurityValidator.validate_request_size(
            len(body_str)
        )
        if not is_valid_size:
            SecurityEventLogger.log_validation_failure(
                client_ip, "request_size", size_reason
            )
            return create_error_response(
                "invalid_request", "Request too large", 400, correlation_id
            )

        # Check cache first for performance
        cache_key = _generate_oauth_cache_key(req_dict)
        if cache_key:
            cached_response = _get_cached_oauth_token(cache_key)
            if cached_response:
                SecurityEventLogger.log_security_event(
                    "oauth_cache_hit",
                    client_ip,
                    f"OAuth token served from cache (correlation: {correlation_id})",
                    "INFO",
                )
                return cached_response

        # Perform OAuth token exchange
        response = _perform_oauth_exchange(
            oauth_config, req_dict, client_ip, correlation_id
        )

        # Cache successful response
        if cache_key and response.get("statusCode") == 200:
            _cache_oauth_token(cache_key, response)

        SecurityEventLogger.log_oauth_success(client_ip, "home_assistant")
        return response

    except ValueError as e:
        SecurityEventLogger.log_validation_failure(client_ip, "oauth_config", str(e))
        return create_error_response("invalid_request", str(e), 400, correlation_id)
    except (OSError, RuntimeError) as e:
        SecurityEventLogger.log_security_event(
            "oauth_error",
            client_ip,
            f"OAuth flow error: {str(e)} (correlation: {correlation_id})",
            "ERROR",
        )
        return create_error_response(
            "internal_error", "OAuth processing failed", 500, correlation_id
        )


def _perform_oauth_exchange(
    config: OAuthConfiguration,
    req_dict: dict[bytes, list[bytes]],
    client_ip: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Perform the actual OAuth token exchange with Home Assistant."""
    # Create HTTP client with optimized settings
    http = create_http_client(config.verify_ssl, timeout_connect=5.0, timeout_read=15.0)

    # Build OAuth endpoint URL
    oauth_url = f"{config.base_url}/auth/token"

    # Prepare headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if config.cf_client_id and config.cf_client_secret:
        headers["CF-Access-Client-Id"] = config.cf_client_id
        headers["CF-Access-Client-Secret"] = config.cf_client_secret

    # Convert request dictionary back to form data
    form_data: dict[str, str] = {}
    for key, values in req_dict.items():
        if values:
            form_data[key.decode("utf-8")] = values[0].decode("utf-8")

    try:
        _logger.debug(
            "Making OAuth request to: %s (correlation: %s)", oauth_url, correlation_id
        )
        response = http.request(
            "POST",
            oauth_url,
            headers=headers,
            fields=form_data,
        )

        # Process response
        if response.status == 200:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": response.data.decode("utf-8"),
            }

        error_message = (
            response.data.decode("utf-8") if response.data else "OAuth request failed"
        )
        SecurityEventLogger.log_oauth_failure(
            client_ip, error_message, f"HTTP {response.status}"
        )
        return create_error_response(
            "invalid_grant", error_message, response.status, correlation_id
        )

    except urllib3.exceptions.TimeoutError:
        return create_error_response(
            "timeout", "OAuth request timeout", 503, correlation_id
        )
    except (OSError, RuntimeError, ValueError) as e:
        _logger.error("OAuth exchange error: %s", str(e))
        return create_error_response(
            "internal_error", "OAuth exchange failed", 500, correlation_id
        )


# === SMART HOME PROXY FLOW ===


def _handle_smart_home_proxy(
    event: dict[str, Any], client_ip: str, correlation_id: str
) -> dict[str, Any]:
    """Handle Smart Home proxy flow with CloudFlare headers."""
    SecurityEventLogger.log_security_event(
        "smart_home_proxy_start",
        client_ip,
        f"Smart Home proxy flow starting (correlation: {correlation_id})",
        "INFO",
    )

    try:
        # Load configuration
        config = OAuthConfiguration.from_environment()

        # Validate request using shared AlexaValidator
        body = event.get("body", "")
        if isinstance(body, str):
            try:
                alexa_event = json.loads(body)
            except json.JSONDecodeError:
                return create_error_response(
                    "invalid_request", "Invalid JSON", 400, correlation_id
                )
        else:
            alexa_event = body

        # Use shared AlexaValidator for directive validation
        directive, error = AlexaValidator.validate_directive(alexa_event)
        if error or directive is None:
            SecurityEventLogger.log_validation_failure(
                client_ip, "alexa_directive", "Invalid Alexa directive"
            )
            return error or create_error_response(
                "invalid_directive", "Invalid directive", 400, correlation_id
            )

        # Forward to Home Assistant with CloudFlare headers
        return _forward_to_home_assistant(
            config, alexa_event, client_ip, correlation_id
        )

    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as e:
        SecurityEventLogger.log_security_event(
            "smart_home_proxy_error",
            client_ip,
            f"Smart Home proxy error: {str(e)} (correlation: {correlation_id})",
            "ERROR",
        )
        return create_error_response(
            "internal_error", "Proxy processing failed", 500, correlation_id
        )


def _forward_to_home_assistant(
    config: OAuthConfiguration,
    alexa_event: dict[str, Any],
    client_ip: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Forward Smart Home request to Home Assistant with CloudFlare protection."""
    # Create HTTP client
    http = create_http_client(config.verify_ssl, timeout_connect=2.0, timeout_read=10.0)

    # Build Smart Home API endpoint
    api_url = f"{config.base_url}/api/alexa/smart_home"

    # Prepare headers
    headers = {"Content-Type": "application/json"}

    # Extract bearer token using shared AlexaValidator
    token, token_error = AlexaValidator.extract_auth_token(
        alexa_event, {}, debug_mode=bool(os.environ.get("DEBUG"))
    )
    if token_error or not token:
        return create_error_response(
            "unauthorized", "Invalid or missing authorization", 401, correlation_id
        )

    headers["Authorization"] = f"Bearer {token}"

    # Add CloudFlare headers if configured
    if config.cf_client_id and config.cf_client_secret:
        headers["CF-Access-Client-Id"] = config.cf_client_id
        headers["CF-Access-Client-Secret"] = config.cf_client_secret

    try:
        _logger.debug("Forwarding Smart Home request to: %s", api_url)
        response = http.request(
            "POST",
            api_url,
            headers=headers,
            body=json.dumps(alexa_event).encode("utf-8"),
        )

        SecurityEventLogger.log_security_event(
            "smart_home_proxy_success",
            client_ip,
            f"Smart Home request forwarded successfully "
            f"(status: {response.status}, correlation: {correlation_id})",
            "INFO",
        )

        return {
            "statusCode": response.status,
            "headers": {"Content-Type": "application/json"},
            "body": response.data.decode("utf-8"),
        }

    except urllib3.exceptions.TimeoutError:
        return create_error_response(
            "timeout", "Smart Home request timeout", 503, correlation_id
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as e:
        _logger.error("Smart Home proxy error: %s", str(e))
        return create_error_response(
            "internal_error", "Proxy request failed", 500, correlation_id
        )


# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯

# === UTILITY FUNCTIONS ===
# (All utility functions moved to shared_configuration.py for reuse)
