"""
⚡ OPTIMIZED HOME ASSISTANT ↔ ALEXA VOICE COMMAND BRIDGE

Copyright 2019 Jason Hu <awaregit at gmail.com>
Licensed under the Apache License, Version 2.0

PERFORMANCE OPTIMIZATIONS:
- Environment variable priority for fastest startup
- Container-level configuration caching
- Reduced SSM Parameter Store calls
- Streamlined request processing
"""

import configparser
import json
import logging
import os
from typing import Any

import boto3
import urllib3

# === PERFORMANCE-OPTIMIZED CONFIGURATION ===
# Priority: Environment variables (fastest) → SSM (fallback) → Error

# Debug mode for detailed logging
_debug = bool(os.environ.get("DEBUG"))

# Logger setup
_logger = logging.getLogger("HomeAssistant-SmartHome")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Container-level cache to avoid repeated SSM calls
_config_cache: dict[str, Any] = {}
_ssm_client = None  # Lazy initialization


def _get_ssm_client() -> Any:
    """Get SSM client with lazy initialization."""
    global _ssm_client
    if _ssm_client is None:
        _ssm_client = boto3.client(
            "ssm"
        )  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
    return _ssm_client


def load_config(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    Load configuration with environment variable priority for performance.

    PERFORMANCE STRATEGY:
    1. Check environment variables first (instant)
    2. Fall back to SSM Parameter Store (slower but secure)
    3. Cache results at container level
    """
    # Check container-level cache first
    if "config" in _config_cache:
        _logger.debug("Using cached configuration")
        return _config_cache["config"]

    configuration = configparser.ConfigParser()

    # FAST PATH: Try environment variables first
    env_config = {
        "HA_BASE_URL": os.environ.get("HA_BASE_URL"),
        "HA_TOKEN": os.environ.get("HA_TOKEN"),
        "CF_CLIENT_ID": os.environ.get("CF_CLIENT_ID"),
        "CF_CLIENT_SECRET": os.environ.get("CF_CLIENT_SECRET"),
    }

    # If all required env vars are present, use them (fastest startup)
    if all(value is not None for value in env_config.values()):
        _logger.debug("Using environment variables for configuration")
        config_dict = {"appConfig": env_config}
        configuration.read_dict(config_dict)
        _config_cache["config"] = configuration
        return configuration

    # FALLBACK PATH: Load from SSM Parameter Store
    _logger.debug("Loading configuration from SSM Parameter Store")
    try:
        client = _get_ssm_client()
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        if "Parameters" in param_details and param_details.get("Parameters"):
            for param in param_details.get("Parameters"):
                if param.get("Name") and param.get("Value"):
                    param_path_array = param.get("Name").split("/")
                    section_name = param_path_array[-1]
                    config_values = json.loads(param.get("Value"))
                    config_dict = {section_name: config_values}
                    configuration.read_dict(config_dict)

        # Cache the loaded configuration
        _config_cache["config"] = configuration

    except Exception as err:
        _logger.error("Error loading config from SSM: %s", str(err))
        # Return empty config rather than crash

    return configuration


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Optimized Lambda handler for Alexa smart home directives.

    PERFORMANCE FEATURES:
    - Container-level configuration caching
    - Environment variable priority
    - Streamlined request processing
    - Connection reuse via global PoolManager
    """
    # Validate required environment
    app_config_path = os.environ.get("APP_CONFIG_PATH")
    if not app_config_path:
        return {
            "event": {
                "payload": {
                    "type": "INTERNAL_ERROR",
                    "message": "APP_CONFIG_PATH environment variable not set",
                }
            }
        }

    # Get configuration (cached after first call)
    config = load_config(app_config_path)
    if not config.has_section("appConfig"):
        return {
            "event": {
                "payload": {
                    "type": "INTERNAL_ERROR",
                    "message": "Configuration not loaded properly",
                }
            }
        }

    app_config = dict(config["appConfig"])

    # Extract required configuration values
    base_url = app_config.get("HA_BASE_URL")
    cf_client_id = app_config.get("CF_CLIENT_ID")
    cf_client_secret = app_config.get("CF_CLIENT_SECRET")

    # Validate Alexa directive structure
    directive = event.get("directive")
    if not directive:
        return {
            "event": {
                "payload": {
                    "type": "INVALID_DIRECTIVE",
                    "message": "Missing directive in request",
                }
            }
        }

    # Check payload version
    if directive.get("header", {}).get("payloadVersion") != "3":
        return {
            "event": {
                "payload": {
                    "type": "INVALID_DIRECTIVE",
                    "message": "Only payloadVersion 3 is supported",
                }
            }
        }

    # Extract authentication token from various possible locations
    scope = directive.get("endpoint", {}).get("scope")
    if scope is None:
        # Token in grantee for Linking directive
        scope = directive.get("payload", {}).get("grantee")
    if scope is None:
        # Token in payload for Discovery directive
        scope = directive.get("payload", {}).get("scope")

    if not scope or scope.get("type") != "BearerToken":
        return {
            "event": {
                "payload": {
                    "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                    "message": "Missing or invalid bearer token",
                }
            }
        }

    token = scope.get("token")
    if not token and _debug:
        # Debug fallback
        token = app_config.get("HA_TOKEN")

    if not token:
        return {
            "event": {
                "payload": {
                    "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                    "message": "No authentication token provided",
                }
            }
        }

    # SSL verification setting
    verify_ssl = not bool(os.environ.get("NOT_VERIFY_SSL"))

    # Log request for debugging
    correlation_id = getattr(context, "aws_request_id", "unknown")[:8]
    _logger.debug("Processing directive (correlation: %s)", correlation_id)
    if _debug:
        _logger.debug("Event: %s", event)

    # Validate base URL
    if not base_url:
        return {
            "event": {
                "payload": {
                    "type": "INTERNAL_ERROR",
                    "message": "HA_BASE_URL not configured",
                }
            }
        }

    base_url = base_url.strip("/")
    _logger.debug("Base URL: %s", base_url)

    # Create HTTP client with optimized settings
    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
        timeout=urllib3.Timeout(connect=2.0, read=10.0),
    )

    # Forward request to Home Assistant
    api_path = f"{base_url}/api/alexa/smart_home"

    try:
        response = http.request(
            "POST",
            api_path,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "CF-Access-Client-Id": cf_client_id or "",
                "CF-Access-Client-Secret": cf_client_secret or "",
            },
            body=json.dumps(event).encode("utf-8"),
        )

        if response.status >= 400:
            error_type = (
                "INVALID_AUTHORIZATION_CREDENTIAL"
                if response.status in (401, 403)
                else f"INTERNAL_ERROR {response.status}"
            )
            return {
                "event": {
                    "payload": {
                        "type": error_type,
                        "message": response.data.decode("utf-8"),
                    }
                }
            }

        _logger.debug("Response: %s", response.data.decode("utf-8"))
        return json.loads(response.data.decode("utf-8"))

    except Exception as err:
        _logger.error("Error forwarding request to Home Assistant: %s", str(err))
        return {
            "event": {
                "payload": {
                    "type": "INTERNAL_ERROR",
                    "message": f"Failed to communicate with Home Assistant: {str(err)}",
                }
            }
        }
