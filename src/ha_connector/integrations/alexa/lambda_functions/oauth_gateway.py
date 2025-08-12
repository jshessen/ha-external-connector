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

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import base64
import configparser
import json
import logging
import os
import urllib.parse
from typing import Any

import boto3
import urllib3
from botocore.exceptions import ClientError

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import (
    PerformanceOptimizer,
    RateLimiter,
    SecurityEventLogger,
    SecurityValidator,
    create_lambda_logger,
    extract_correlation_id,
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === LOGGING CONFIGURATION ===
_debug = bool(os.environ.get("DEBUG"))

# Use shared configuration logger instead of local setup
_logger = create_lambda_logger("OAuthGateway")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize boto3 client at global scope for connection reuse
client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]
app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

# ⚡ PHASE 2 SECURITY: Initialize security components at global scope
_rate_limiter = RateLimiter()
_security_validator = SecurityValidator()
_security_logger = SecurityEventLogger()

# ⚡ PHASE 1B PERFORMANCE: Initialize performance optimizer at global scope
_performance_optimizer = PerformanceOptimizer()

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
        # ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
        # ║                           🚀 TRANSFER-READY CODE 🚀                       ║
        # ║ 📋 BLOCK PURPOSE: Strategic 3-tier caching for <500ms OAuth responses    ║
        # ║ 🔄 TRANSFER STATUS: Ready for duplication across Lambda functions        ║
        # ║ ⚡ PERFORMANCE: Container 0-1ms | Shared 20-50ms | SSM 100-200ms         ║
        # ║                                                                           ║
        # ║ 🎯 USAGE PATTERN:                                                         ║
        # ║   1. Copy entire block between "BLOCK_START" and "BLOCK_END" markers     ║
        # ║   2. Update function prefixes as needed (e.g., _oauth_ → _bridge_)        ║
        # ║   3. Adjust cache keys and table names for target service                ║
        # ║   4. Maintain identical core functionality across Lambda functions       ║
        # ╚═══════════════════════════════════════════════════════════════════════════╝

        # Use enhanced configuration loading (fallback to legacy if needed)
        try:
            from .shared_configuration import load_configuration

            config = load_configuration(
                app_config_path=app_config_path,
                config_section="appConfig",
                return_format="configparser",
            )

            if isinstance(config, configparser.ConfigParser):
                _performance_optimizer.record_cache_hit()
                duration = _performance_optimizer.end_timing("config_load", start_time)
                _logger.info(
                    "✅ Enhanced configuration loaded (%.1fms)", duration * 1000
                )
                return HAConfig(config)

        except (ImportError, ValueError, RuntimeError) as e:
            _performance_optimizer.record_cache_miss()
            _logger.warning("Enhanced config loading failed, using fallback: %s", e)

        # ╭─────────────────── TRANSFER BLOCK END ───────────────────╮

        # Fallback to legacy configuration loading
        config = load_config(app_config_path)
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.warning("⚠️ Fallback configuration loaded (%.1fms)", duration * 1000)
        return HAConfig(config)

    except Exception as e:
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.error(
            "❌ Configuration loading failed (%.1fms): %s", duration * 1000, e
        )
        raise


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    # Initialize request context and performance tracking
    correlation_id = extract_correlation_id(context)
    request_start = _performance_optimizer.start_timing("total_request")

    _logger.info("=== OAUTH LAMBDA START (correlation: %s) ===", correlation_id)
    _logger.debug("Event: %s", event)

    # 🛡️ PHASE 2 SECURITY: Rate limiting and security validation
    client_ip = event.get("headers", {}).get("X-Forwarded-For", "alexa-service")
    client_ip = client_ip.split(",")[0] if client_ip else "alexa-service"

    # Check rate limiting
    is_allowed, rate_limit_reason = _rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        _logger.warning(
            "Rate limit exceeded for IP %s: %s (correlation: %s)",
            client_ip,
            rate_limit_reason,
            correlation_id,
        )
        _security_logger.log_security_event(
            "rate_limit_exceeded", client_ip, rate_limit_reason
        )
        return {
            "statusCode": 429,
            "body": json.dumps(
                {"error": "rate_limit_exceeded", "message": rate_limit_reason}
            ),
        }

    # Basic request validation
    request_size = len(json.dumps(event).encode("utf-8"))
    if not _security_validator.validate_request_size(request_size):
        _logger.warning(
            "Request size validation failed (correlation: %s)", correlation_id
        )
        _security_logger.log_security_event(
            "request_too_large", client_ip, "Request exceeds maximum size"
        )
        return {
            "statusCode": 413,
            "body": json.dumps(
                {"error": "request_too_large", "message": "Request too large"}
            ),
        }

    # Log security event for successful validation
    _security_logger.log_security_event(
        "request_validated",
        client_ip,
        f"OAuth request validated (correlation: {correlation_id})",
    )

    print("Loading config and creating persistence object...")
    app = get_app_config()

    app_config = app.get_config()["appConfig"]

    destination_url = app_config.get("HA_BASE_URL")
    cf_client_id = app_config.get("CF_CLIENT_ID")
    cf_client_secret = app_config.get("CF_CLIENT_SECRET")
    wrapper_secret = app_config.get("WRAPPER_SECRET")

    if not destination_url:
        raise ValueError("Please set BASE_URL parameter")
    destination_url = destination_url.strip("/")

    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED", timeout=urllib3.Timeout(connect=2.0, read=10.0)
    )

    # Get request body with proper validation
    event_body = event.get("body")
    if event_body is None:
        raise ValueError("Request body is missing")

    req_body = (
        base64.b64decode(event_body) if event.get("isBase64Encoded") else event_body
    )

    _logger.debug(req_body)

    req_dict = urllib.parse.parse_qs(req_body)
    client_secret = req_dict[b"client_secret"][0].decode("utf-8")

    # Validate wrapper secret
    if not wrapper_secret:
        _logger.error("WRAPPER_SECRET missing (correlation: %s)", correlation_id)
        raise ValueError("WRAPPER_SECRET is missing from configuration")

    if client_secret != wrapper_secret:
        _logger.error("Client secret mismatch (correlation: %s)", correlation_id)
        raise ValueError("Client secret mismatch")

    # Validate all required config values
    if not cf_client_id:
        _logger.error("CF_CLIENT_ID missing (correlation: %s)", correlation_id)
        raise ValueError("CF_CLIENT_ID is missing from configuration")
    if not cf_client_secret:
        _logger.error("CF_CLIENT_SECRET missing (correlation: %s)", correlation_id)
        raise ValueError("CF_CLIENT_SECRET is missing from configuration")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "CF-Access-Client-Id": str(cf_client_id),
        "CF-Access-Client-Secret": str(cf_client_secret),
    }

    response = http.request(
        "POST", f"{destination_url}/auth/token", headers=headers, body=req_body
    )

    if response.status >= 400:
        _logger.debug(
            "ERROR %s %s (correlation: %s)",
            response.status,
            response.data.decode("utf-8"),
            correlation_id,
        )
        # ⚡ PERFORMANCE: Log error response time
        total_duration = _performance_optimizer.end_timing(
            "total_request", request_start
        )
        _logger.warning(
            "⚠️ OAuth failed in %.1fms (correlation: %s)",
            total_duration * 1000,
            correlation_id,
        )
        return {
            "event": {
                "payload": {
                    "type": (
                        "INVALID_AUTHORIZATION_CREDENTIAL"
                        if response.status in (401, 403)
                        else f"INTERNAL_ERROR {response.status}"
                    ),
                    "message": response.data.decode("utf-8"),
                }
            }
        }

    # ⚡ PERFORMANCE: Log successful response time
    total_duration = _performance_optimizer.end_timing("total_request", request_start)
    _logger.info(
        "✅ OAuth completed in %.1fms (correlation: %s)",
        total_duration * 1000,
        correlation_id,
    )

    _logger.debug(
        "Response: %s (correlation: %s)", response.data.decode("utf-8"), correlation_id
    )
    _logger.info("=== OAUTH LAMBDA END (correlation: %s) ===", correlation_id)
    return json.loads(response.data.decode("utf-8"))


# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
