"""
🔐 CLOUDFLARE SECURITY GATEWAY: Professional Building Security Services 👮

The Security Guard manages all visitor authentication and CloudFlare protection
for Alexa Smart Home account linking. Ensures only authorized visitors gain
access to the building through comprehensive security screening.

SECURITY GUARD RESPONSIBILITIES:
- Visitor Badge Validation: OAuth token exchange and verification
- CloudFlare Protection: Enterprise security screening and rate limiting
- Credential Verification: Home Assistant authentication and access control
- Incident Documentation: Security event logging and audit trails

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
from botocore.exceptions import ClientError

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import (
    OAuthConfigurationManager,
    OAuthRequestProcessor,
    OAuthSecurityValidator,
    PerformanceMonitor,
    RateLimiter,
    SecurityEventLogger,
    SecurityValidator,
    create_structured_logger,
    create_warmup_response,
    extract_correlation_id,
    handle_warmup_request,
    load_configuration_as_configparser,
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === SECURITY GUARD INITIALIZATION ===
_debug = bool(os.environ.get("DEBUG"))

# Security Guard logging setup
_logger = create_structured_logger("CloudFlareSecurityGateway")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize AWS SSM client for configuration access
client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]
_default_app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

# Initialize security components for visitor screening
_rate_limiter = RateLimiter()
_security_validator = SecurityValidator()
_security_logger = SecurityEventLogger()

# Initialize performance monitoring for security operations
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
    Security Guard Configuration Access: Load secure visitor credentials and settings.

    Retrieves authentication configuration through multi-tier caching for optimal
    security response times. Essential for OAuth token validation and CloudFlare
    protection settings.

    Returns:
        HAConfig instance with loaded security configuration
    """
    start_time = _performance_optimizer.start_timing("config_load")
    try:
        config = load_configuration_as_configparser(
            app_config_path=_default_app_config_path
        )

        # Configuration successfully loaded
        _performance_optimizer.record_cache_hit()
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.info("Security configuration loaded (%.1fms)", duration * 1000)
        return HAConfig(config)

    except Exception as e:
        duration = _performance_optimizer.end_timing("config_load", start_time)
        _logger.error(
            "Security configuration loading failed (%.1fms): %s", duration * 1000, e
        )
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
    Security Guard Entry Point: OAuth Authentication and CloudFlare Protection

    The main security checkpoint for Alexa account linking. Validates visitor
    credentials, processes OAuth token exchanges, and maintains comprehensive
    security monitoring for all authentication requests.

    SECURITY GUARD WORKFLOW:
    1. Visitor Screening: Rate limiting and security validation
    2. Credential Verification: Configuration loading and validation
    3. Request Processing: OAuth parameter extraction and validation
    4. Badge Issuance: OAuth token exchange with Home Assistant
    5. Incident Logging: Security event documentation and monitoring

    Target Response Time: <200ms for OAuth authentication
    """
    # Initialize request processing and correlation tracking
    correlation_id = extract_correlation_id(context)
    request_start = _performance_optimizer.start_timing("total_request")

    _logger.info("=== OAUTH LAMBDA START (correlation: %s) ===", correlation_id)
    _logger.debug("Event: %s", event)

    # 🔥 CONTAINER WARMING: Handle warmup requests from configuration manager
    if handle_warmup_request(event, correlation_id, "cloudflare_security_gateway"):
        return create_warmup_response("cloudflare_security_gateway", correlation_id)

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

    # 4. Badge Issuance: OAuth token exchange execution
    success_response, oauth_error = _execute_oauth_token_exchange(
        oauth_config, req_body, correlation_id
    )

    # 5. Incident Logging: Security documentation and monitoring
    total_duration = _performance_optimizer.end_timing("total_request", request_start)

    if oauth_error:
        _logger.warning(
            "Security Guard: Authentication failed in %.1fms (correlation: %s)",
            total_duration * 1000,
            correlation_id,
        )
        return oauth_error

    _logger.info(
        "Security Guard: Authentication completed in %.1fms (correlation: %s)",
        total_duration * 1000,
        correlation_id,
    )
    _logger.debug("Response: %s (correlation: %s)", success_response, correlation_id)
    _logger.info("=== OAUTH LAMBDA END (correlation: %s) ===", correlation_id)

    return success_response or {"error": "Unknown OAuth processing error"}


# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
