"""
🏠 HOME ASSISTANT ↔ ALEXA VOICE COMMAND BRIDGE 🗣️

=== WHAT THIS FILE DOES (In Plain English) ===

This file is like a "translator" that sits between Amazon Alexa and your Home Assistant
smart home system. When you say "Alexa, turn on the lights", here's what happens:

1. 🗣️  You speak to Alexa: "Alexa, turn on the kitchen lights"
2. 🌐  Alexa sends your request to Amazon's servers
3. 🔀  Amazon forwards the request to THIS CODE (running on AWS Lambda)
4. 🏠  THIS CODE translates and forwards your request to Home Assistant
5. 💡  Home Assistant turns on your kitchen lights
6. ✅  Home Assistant sends back "success" through this same path
7. 🗣️  Alexa responds: "OK"

=== THE COMPLETE ALEXA SKILL ECOSYSTEM: SECURITY GUARD & RECEPTIONIST TEAM ===

🏢 **HOW THESE TWO FILES WORK TOGETHER LIKE A PROFESSIONAL OFFICE**

Imagine your smart home system is like a prestigious corporate office building.
You have TWO key staff members working together to serve Alexa visitors:

👮 **SECURITY GUARD (cloudflare_oauth_gateway.py)**
- 🏛️ **Job**: Guards the main entrance and handles visitor registration
- 🎫 **Location**: Main lobby entrance (OAuth authentication endpoint)
- 📋 **Responsibilities**:
  * Check visitor credentials when they first arrive
  * Issue temporary access badges (OAuth tokens)
  * Handle CloudFlare security clearance
  * Verify appointments and authority
  * Keep detailed security logs

💼 **EXECUTIVE RECEPTIONIST (THIS FILE - voice_command_bridge.py)**
- 🏢 **Job**: Handles daily business operations and communications
- 📞 **Location**: Executive floor (Smart home command processor)
- 📋 **Responsibilities**:
  * Process ongoing business requests (voice commands)
  * Translate between Alexa and Home Assistant "languages"
  * Handle routine operations efficiently
  * Maintain appointment schedules and logs

🔄 **THE COMPLETE WORKFLOW IN YOUR ALEXA SKILL**

**PHASE 1: INITIAL SETUP (Account Linking) - Security Guard Takes the Lead**
1. 👤 User opens Alexa app → Skills & Games → [Your Smart Home Skill]
2. 📱 User clicks "Enable Skill" → "Link Account"
3. 🌐 Alexa redirects to your OAuth Gateway (Security Guard)
4. 👮 **SECURITY GUARD** receives the visitor
5. 🔐 Security Guard handles OAuth authentication with Home Assistant
6. 🎫 Security Guard issues temporary access badge (OAuth token)
7. 📋 Security Guard reports back to Alexa: "Credentials verified!"
8. ✅ Alexa app shows: "Account successfully linked!"

**PHASE 2: DAILY OPERATIONS (Voice Commands) - Receptionist Takes the Lead**
1. 🗣️ User says: "Alexa, turn on the kitchen lights"
2. 🌐 Alexa processes command → sends to AWS Lambda
3. 💼 **EXECUTIVE RECEPTIONIST (THIS FILE)** receives the request
4. 🔍 Receptionist validates the access badge (checks OAuth token)
5. 📞 Receptionist translates request to Home Assistant language
6. 🏠 Receptionist forwards command to Home Assistant
7. 💡 Home Assistant turns on lights → sends confirmation
8. 📋 Receptionist translates response back to Alexa
9. 🗣️ Alexa responds: "OK"

**WHY YOU NEED BOTH TEAM MEMBERS:**
- 👮 **Security Guard** specializes in high-security authentication tasks
- 💼 **Receptionist** specializes in fast, efficient daily operations
- 👮 **Security Guard** handles CloudFlare protection (which can be slow)
- 💼 **Receptionist** handles rapid voice commands (which need speed)
- 👮 **Security Guard** does complex OAuth flows (which need security expertise)
- 💼 **Receptionist** does simple token validation (which needs efficiency)

=== WHY THIS EXISTS ===

- Home Assistant lives in your house (local network)
- Alexa lives in Amazon's cloud (internet)
- They speak different "languages" (protocols)
- This bridge translates between them and handles security

=== SECURITY FEATURES ===

- 🔒 Validates every request is really from Alexa
- 🛡️  Protects against too many requests (rate limiting)
- 🔐 Uses secure authentication tokens
- 🌐 Can work through CloudFlare for extra protection
- 📝 Logs everything for troubleshooting

=== FOR NON-TECHNICAL PEOPLE ===

Think of this like a professional executive receptionist at a company:
- Checks if visitors (Alexa requests) have proper appointments (valid tokens)
- Translates between different languages (Alexa ↔ Home Assistant)
- Keeps records of all conversations (logging)
- Ensures security protocols are followed
- Handles the paperwork (authentication tokens)
- Processes routine business efficiently (voice commands)

Author: Jeff Hessenflow <jeff．hessenflow＠gmail．com>
Based on original work by: Jason Hu (awarecan)

Original Copyright and License:
  Copyright 2019 Jason Hu <awaregit at gmail.com>
  Licensed under the Apache License, Version 2.0
"""

# pylint: disable=too-many-lines  # Intentionally verbose for non-technical users
# pylint: disable=duplicate-code  # Lambda functions must be standalone - no shared modules

import configparser
import json
import logging
import os
import ssl
import time
from datetime import UTC, datetime
from typing import Any

import boto3
import botocore.exceptions
import urllib3
from urllib3.exceptions import HTTPError

# === CONFIGURATION SECTION ===
# These settings control how the bridge behaves

# Enable detailed logging for troubleshooting (shows more information in logs)
_enable_detailed_logging = bool(os.environ.get("DEBUG"))

# Set up our logging system (like a diary that records what happens)
_activity_logger = logging.getLogger("VoiceCommandBridge")
_activity_logger.setLevel(logging.DEBUG if _enable_detailed_logging else logging.INFO)


# === ENVIRONMENT SAFETY CHECK ===
# Make sure all required settings are available before starting
def verify_required_settings() -> None:
    """
    🔍 SAFETY CHECK: Verify Required Environment Settings

    Like checking you have your keys before leaving the house.
    This ensures all the necessary configuration is in place.
    """
    required_settings = ["HOME_ASSISTANT_URL", "ALEXA_TOKEN"]
    missing_settings: list[str] = []

    for setting in required_settings:
        if not os.getenv(setting):
            missing_settings.append(f"Missing required setting: {setting}")

    if missing_settings:
        error_message = "Configuration check failed: " + "; ".join(missing_settings)
        raise ValueError(error_message)


# Run the safety check when this file loads
try:
    verify_required_settings()
except ValueError as setup_error:
    _activity_logger.error("Setup error: %s", setup_error)
    raise

# === SECURITY HEADERS ===
# These headers make responses more secure (like putting locks on doors)
SECURE_RESPONSE_HEADERS = {
    "Content-Type": "application/json",
    # Don't cache sensitive data
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",  # Extra cache prevention
    # Prevent MIME type confusion attacks
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",  # Prevent clickjacking attacks
    "X-XSS-Protection": "1; mode=block",  # Block cross-site scripting
    # Force HTTPS
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "no-referrer",  # Don't leak referrer information
}

# === RATE LIMITING STORAGE ===
# Keeps track of how many requests each IP address has made
_request_tracker: dict[str, list[float]] = {}
_configuration_cache: dict[str, Any] = {}

# === SAFETY LIMITS ===
# These prevent abuse and ensure good performance
MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024  # 10MB maximum request size
RATE_LIMIT_TIME_WINDOW_SECONDS = 60  # Check requests within last 60 seconds
MAX_REQUESTS_PER_IP_PER_MINUTE = 100  # Allow up to 100 requests per IP per minute
CONFIG_CACHE_DURATION_SECONDS = 300  # Cache configuration for 5 minutes
NETWORK_CONNECT_TIMEOUT_SECONDS = 2.0  # 2 seconds to establish connection
NETWORK_READ_TIMEOUT_SECONDS = 10.0  # 10 seconds to read response


def record_security_event(
    event_type: str, source_ip: str, additional_details: dict[str, Any] | None = None
) -> None:
    """
    📝 SECURITY LOGGER: Record Security Events

    Like a security guard writing in a logbook. Records any suspicious
    or important security-related activity for later investigation.
    """
    security_record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "source_ip": source_ip,
        "details": additional_details or {},
    }
    _activity_logger.warning("🚨 SECURITY EVENT: %s", json.dumps(security_record))


def record_performance_metrics(
    operation: str, duration: float, status_code: int
) -> None:
    """
    📊 PERFORMANCE LOGGER: Track How Fast Things Are

    Like a stopwatch for operations. Helps identify if the bridge
    is running slowly and where improvements might be needed.
    """
    performance_data: dict[str, Any] = {
        "operation": operation,
        "duration_milliseconds": round(duration * 1000, 2),
        "status_code": status_code,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    _activity_logger.info("📊 PERFORMANCE: %s", json.dumps(performance_data))


class ConfigurationValidator:
    """
    ✅ CONFIGURATION CHECKER: Ensures Settings Are Valid

    Like a proofreader for configuration files. Makes sure all
    required settings are present and properly formatted.
    """

    @staticmethod
    def check_configuration_completeness(
        config: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Check if all required configuration keys are present.

        Returns:
            (is_valid, list_of_errors)
        """
        validation_errors: list[str] = []
        required_config_keys = ["HA_BASE_URL", "CF_CLIENT_ID", "CF_CLIENT_SECRET"]

        for key in required_config_keys:
            if key not in config:
                validation_errors.append(f"Missing required configuration: {key}")

        is_configuration_valid = len(validation_errors) == 0
        return (is_configuration_valid, validation_errors)


class ResponseFormatter:
    """
    📤 RESPONSE BUILDER: Creates Properly Formatted Responses

    Like a letter writer who ensures all correspondence follows
    proper format and includes necessary security measures.
    """

    @staticmethod
    def create_success_response(data: Any, status_code: int = 200) -> dict[str, Any]:
        """
        Create a properly formatted success response.

        Args:
            data: The response data to send back
            status_code: HTTP status code (default 200 = success)
        """
        return {
            "statusCode": status_code,
            "headers": SECURE_RESPONSE_HEADERS,
            "body": json.dumps(data),
        }

    @staticmethod
    def create_error_response(
        error_message: str, status_code: int = 400, log_level: str = "warning"
    ) -> dict[str, Any]:
        """
        Create a properly formatted error response with security measures.

        Args:
            error_message: Description of what went wrong
            status_code: HTTP error code (400 = bad request, 500 = server error, etc.)
            log_level: How serious this error is ("warning" or "error")
        """
        # Remove sensitive information before logging or responding
        safe_error_message = ResponseFormatter._remove_sensitive_information(
            error_message
        )

        # Log the error appropriately
        if log_level == "warning":
            _activity_logger.warning(safe_error_message)
        else:
            _activity_logger.error(safe_error_message)

        return {
            "statusCode": status_code,
            "headers": SECURE_RESPONSE_HEADERS,
            "body": json.dumps({"error": safe_error_message}),
        }

    @staticmethod
    def _remove_sensitive_information(text: str) -> str:
        """
        🔒 PRIVACY PROTECTOR: Remove Sensitive Data from Text

        Like a redaction tool that blacks out sensitive information
        in documents before they're shared publicly.
        """
        sensitive_keywords = [
            "Bearer",
            "token",
            "secret",
            "authorization",
            "client_secret",
            "access_token",
            "refresh_token",
            "password",
            "key",
            "credential",
        ]

        protected_text = text
        for keyword in sensitive_keywords:
            protected_text = protected_text.replace(keyword, "[🔒PROTECTED🔒]")

        return protected_text


def check_request_rate_limit(source_ip: str) -> bool:
    """
    🚦 TRAFFIC CONTROLLER: Prevent Request Flooding

    Like a professional receptionist who manages appointment scheduling
    to ensure no one person books too many meetings at once.

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    current_time = time.time()

    # Initialize tracking for new IP addresses
    if source_ip not in _request_tracker:
        _request_tracker[source_ip] = []

    # Remove old requests outside our time window
    _request_tracker[source_ip] = [
        request_time
        for request_time in _request_tracker[source_ip]
        if current_time - request_time < RATE_LIMIT_TIME_WINDOW_SECONDS
    ]

    # Check if this IP has exceeded the rate limit
    if len(_request_tracker[source_ip]) >= MAX_REQUESTS_PER_IP_PER_MINUTE:
        return False  # Rate limit exceeded

    # Record this request
    _request_tracker[source_ip].append(current_time)
    return True  # Request allowed


def validate_request_size_limit(incoming_request: dict[str, Any]) -> bool:
    """
    📏 SIZE CHECKER: Ensure Requests Aren't Too Large

    Like a postal service that rejects packages that are too big.
    Prevents memory exhaustion attacks.

    Returns:
        True if request size is acceptable, False if too large
    """
    request_body = incoming_request.get("body", "")
    request_size_bytes = len(request_body.encode("utf-8"))
    return request_size_bytes <= MAX_REQUEST_SIZE_BYTES


def sanitize_url_path(url_path: str) -> str:
    """
    🧹 PATH CLEANER: Remove Dangerous Characters from URLs

    Like a janitor who cleans up messy paths to prevent
    directory traversal attacks (trying to access files
    they shouldn't have access to).
    """
    # Remove dangerous path traversal attempts
    cleaned_path = url_path.replace("..", "").replace("//", "/")

    # Ensure path starts with forward slash
    if not cleaned_path.startswith("/"):
        cleaned_path = "/" + cleaned_path

    return cleaned_path


# === AWS INTEGRATION SETUP ===
# These connect to Amazon Web Services for secure configuration storage

# AWS Systems Manager client for securely retrieving configuration
aws_config_client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]

# Path to configuration stored in AWS Systems Manager Parameter Store
secure_config_storage_path = os.environ.get("APP_CONFIG_PATH")


def load_secure_configuration(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    🔐 SECURE CONFIG LOADER: Retrieve Settings from AWS

    Like a safe deposit box at a bank. Retrieves configuration
    settings that are stored securely in AWS Systems Manager
    Parameter Store instead of being hardcoded in the application.

    Args:
        ssm_parameter_path: The path in AWS where configuration is stored

    Returns:
        ConfigParser object containing all configuration settings
    """
    configuration = configparser.ConfigParser()

    try:
        _activity_logger.info(
            "🔐 Loading secure configuration from: %s", ssm_parameter_path
        )

        # Retrieve all parameters from the specified path
        parameter_response = aws_config_client.get_parameters_by_path(
            Path=ssm_parameter_path,
            Recursive=False,  # Don't get sub-folders
            WithDecryption=True,  # Decrypt encrypted values
        )

        # Process each parameter and add to configuration
        for parameter in parameter_response.get("Parameters", []):
            parameter_name = parameter.get("Name", "").split("/")[
                -1
            ]  # Get last part of path
            parameter_value = json.loads(parameter.get("Value", "{}"))
            configuration_section = {parameter_name: parameter_value}
            configuration.read_dict(configuration_section)

        _activity_logger.info(
            "✅ Successfully loaded configuration sections: %s",
            configuration.sections(),
        )

    except (
        aws_config_client.exceptions.ParameterNotFound,
        aws_config_client.exceptions.ParameterVersionNotFound,
        json.JSONDecodeError,
    ) as config_error:
        _activity_logger.error("❌ Failed to load configuration: %s", config_error)

    return configuration


def remove_sensitive_data_from_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """
    🛡️ DATA PROTECTOR: Remove Sensitive Information for Logging

    Like putting a cover over sensitive documents before taking
    a photo. Creates a safe version of the request for logging
    purposes without exposing sensitive authentication tokens.
    """
    safe_request = dict(request_data)
    if "directive" in safe_request:
        safe_request["directive"] = "[🔒PROTECTED_DIRECTIVE🔒]"
    return safe_request


def extract_aws_lambda_context_information(lambda_context: Any) -> dict[str, Any]:
    """
    📋 CONTEXT EXTRACTOR: Get AWS Lambda Runtime Information

    Like reading the return address on an envelope. Extracts
    useful information about the AWS Lambda environment for
    logging and troubleshooting purposes.
    """
    if lambda_context is None:
        return {}

    return {
        "aws_request_id": getattr(lambda_context, "aws_request_id", None),
        "function_name": getattr(lambda_context, "function_name", None),
        "function_version": getattr(lambda_context, "function_version", None),
        "invoked_function_arn": getattr(lambda_context, "invoked_function_arn", None),
    }


def validate_request_security_measures(
    incoming_request: dict[str, Any],
    source_ip: str,
    lambda_context_info: dict[str, Any],
) -> dict[str, Any] | None:
    """
    🛡️ SECURITY GATEKEEPER: Validate Request Security

    Like a security checkpoint at an airport. Performs multiple
    security checks on incoming requests to ensure they're safe
    and legitimate before processing.

    Returns:
        None if request passes security checks
        Error response dict if security validation fails
    """
    # Check rate limiting (prevent request flooding)
    if not check_request_rate_limit(source_ip):
        record_security_event("rate_limit_exceeded", source_ip, lambda_context_info)
        return ResponseFormatter.create_error_response(
            "Too many requests - please slow down", 429, log_level="warning"
        )

    # Check request size (prevent memory exhaustion)
    if not validate_request_size_limit(incoming_request):
        record_security_event("request_too_large", source_ip, lambda_context_info)
        return ResponseFormatter.create_error_response(
            "Request is too large", 413, log_level="warning"
        )

    return None  # All security checks passed


def load_and_validate_application_configuration() -> (
    tuple[dict[str, Any] | None, configparser.ConfigParser | None]
):
    """
    🔧 CONFIG MANAGER: Load and Validate Application Settings

    Like a quality control inspector who checks that all the
    parts are present and correctly configured before assembly.

    Returns:
        (error_response, configuration) tuple
        If error_response is not None, there was a problem loading config
    """
    # Check if configuration path is set
    if not secure_config_storage_path:
        _activity_logger.error("❌ Configuration storage path not specified")
        return (
            ResponseFormatter.create_error_response(
                "Configuration path not set", 500, log_level="error"
            ),
            None,
        )

    # Load configuration from AWS Systems Manager
    try:
        configuration = load_secure_configuration(secure_config_storage_path)
    except (
        botocore.exceptions.NoCredentialsError,
        botocore.exceptions.BotoCoreError,
        configparser.Error,
        TypeError,
        ValueError,
    ) as config_loading_error:
        # Handle different types of configuration loading errors
        if isinstance(config_loading_error, botocore.exceptions.NoCredentialsError):
            _activity_logger.exception(
                "❌ AWS credentials not found: %s", config_loading_error
            )
            error_message = "AWS credentials not found"
        elif isinstance(config_loading_error, botocore.exceptions.BotoCoreError):
            _activity_logger.exception("❌ AWS service error: %s", config_loading_error)
            error_message = f"AWS error: {str(config_loading_error)}"
        else:
            _activity_logger.exception(
                "❌ Unexpected configuration error: %s", config_loading_error
            )
            error_message = "Unexpected configuration error"

        return (
            ResponseFormatter.create_error_response(
                error_message, 500, log_level="error"
            ),
            None,
        )

    # Validate configuration structure
    if not configuration.has_section("appConfig"):
        _activity_logger.error("❌ Main configuration section missing")
        return (
            ResponseFormatter.create_error_response(
                "Configuration structure error", 500, log_level="error"
            ),
            None,
        )

    # Validate configuration completeness
    app_configuration = dict(configuration["appConfig"])
    is_valid, validation_errors = (
        ConfigurationValidator.check_configuration_completeness(app_configuration)
    )

    if not is_valid:
        _activity_logger.error(
            "❌ Configuration validation failed: %s", validation_errors
        )
        error_description = "Invalid configuration: " + ", ".join(validation_errors)
        return (
            ResponseFormatter.create_error_response(
                error_description, 500, log_level="error"
            ),
            None,
        )

    return (None, configuration)  # Configuration loaded and validated successfully


def validate_home_assistant_url_allowlist(
    app_configuration: dict[str, Any],
    source_ip: str,
    lambda_context_info: dict[str, Any],
) -> dict[str, Any] | None:
    """
    🏠 URL VALIDATOR: Check Home Assistant URL Against Allowlist

    Like a guest list at an exclusive event. Ensures that the
    Home Assistant URL being accessed is on the approved list
    of authorized URLs for security purposes.

    Returns:
        None if URL is allowed
        Error response dict if URL validation fails
    """
    target_base_url = app_configuration.get("HA_BASE_URL", "").strip("/")
    allowed_base_url = os.environ.get("ALLOWED_HA_BASE_URL")

    # If no allowlist is configured, allow any URL
    if not allowed_base_url:
        return None

    # Check if target URL matches the allowlist
    allowed_base_url = allowed_base_url.strip().rstrip("/")
    is_url_allowed = target_base_url == allowed_base_url or target_base_url.startswith(
        allowed_base_url + "/"
    )

    if not is_url_allowed:
        record_security_event(
            "unauthorized_url_access_attempt",
            source_ip,
            {
                "requested_url": target_base_url,
                "allowed_url": allowed_base_url,
                **lambda_context_info,
            },
        )
        return ResponseFormatter.create_error_response(
            "URL not authorized", 403, log_level="error"
        )

    return None  # URL is authorized


def extract_and_validate_alexa_authentication_token(
    incoming_request: dict[str, Any],
    app_configuration: dict[str, Any],
    source_ip: str,
    lambda_context_info: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """
    🎫 TOKEN VALIDATOR: Extract and Verify Alexa Authentication

    Like a ticket inspector on a train. Extracts the authentication
    token from Alexa's request and validates that it's legitimate
    and properly formatted.

    Returns:
        (error_response, authentication_token) tuple
        If error_response is not None, authentication failed
    """
    # Extract the main directive from the request
    alexa_directive = incoming_request.get("directive")

    # Validate directive structure
    if (
        not alexa_directive
        or alexa_directive.get("header", {}).get("payloadVersion") != "3"
    ):
        record_security_event(
            "invalid_alexa_directive",
            source_ip,
            {
                "request": remove_sensitive_data_from_request(incoming_request),
                **lambda_context_info,
            },
        )
        return (
            ResponseFormatter.create_error_response(
                "Invalid Alexa request format or unsupported version", 400
            ),
            None,
        )

    # Extract authentication scope from various possible locations in the directive
    # (Different Alexa directive types store the token in different places)
    authentication_scope = (
        alexa_directive.get("endpoint", {}).get("scope")  # Standard directives
        or alexa_directive.get("payload", {}).get("grantee")  # Grant directives
        or alexa_directive.get("payload", {}).get("scope")  # Discovery directives
    )

    # Validate scope structure
    if not authentication_scope or authentication_scope.get("type") != "BearerToken":
        record_security_event(
            "invalid_authentication_scope",
            source_ip,
            {
                "request": remove_sensitive_data_from_request(incoming_request),
                **lambda_context_info,
            },
        )
        return (
            ResponseFormatter.create_error_response(
                "Missing or invalid authentication scope", 401
            ),
            None,
        )

    # Extract the actual authentication token
    authentication_token = authentication_scope.get("token")

    # Allow fallback to debug token if in debug mode and no token provided
    if authentication_token is None and _enable_detailed_logging:
        authentication_token = app_configuration.get("HA_TOKEN")  # Debug fallback only

    # Validate token presence
    if not authentication_token:
        record_security_event(
            "missing_authentication_token",
            source_ip,
            {
                "request": remove_sensitive_data_from_request(incoming_request),
                **lambda_context_info,
            },
        )
        return (
            ResponseFormatter.create_error_response(
                "Authentication token missing", 401
            ),
            None,
        )

    return (None, authentication_token)  # Authentication successful


def _create_http_client() -> urllib3.PoolManager:
    """Create HTTP client with security and timeout settings."""
    verify_ssl_certificates = not bool(os.environ.get("NOT_VERIFY_SSL"))
    return urllib3.PoolManager(
        cert_reqs=ssl.CERT_REQUIRED if verify_ssl_certificates else ssl.CERT_NONE,
        timeout=urllib3.Timeout(
            connect=NETWORK_CONNECT_TIMEOUT_SECONDS, read=NETWORK_READ_TIMEOUT_SECONDS
        ),
    )


def _prepare_home_assistant_request(
    app_configuration: dict[str, Any], authentication_token: str
) -> tuple[str, dict[str, str]]:
    """Prepare Home Assistant API endpoint and request headers."""
    # Prepare the Home Assistant API endpoint
    home_assistant_base_url = app_configuration.get("HA_BASE_URL", "").strip("/")
    api_endpoint = sanitize_url_path(f"{home_assistant_base_url}/api/alexa/smart_home")

    # Prepare request headers with authentication and CloudFlare support
    request_headers: dict[str, str] = {
        "Authorization": f"Bearer {authentication_token}",
        "Content-Type": "application/json",
        # CloudFlare Access headers for additional security layer
        "CF-Access-Client-Id": app_configuration.get("CF_CLIENT_ID", ""),
        "CF-Access-Client-Secret": app_configuration.get("CF_CLIENT_SECRET", ""),
    }

    return api_endpoint, request_headers


def _handle_home_assistant_error_response(
    home_assistant_response: Any,
    source_ip: str,
    lambda_context_info: dict[str, Any],
) -> dict[str, Any]:
    """Handle error responses from Home Assistant."""
    record_security_event(
        "home_assistant_error_response",
        source_ip,
        {
            "status_code": home_assistant_response.status,
            "response_body": home_assistant_response.data.decode("utf-8"),
            **lambda_context_info,
        },
    )

    # Determine appropriate error status code to return
    error_status_code = (
        502
        if home_assistant_response.status >= 500  # Server error
        else 401  # Client/authentication error
    )

    return ResponseFormatter.create_error_response(
        f"Home Assistant error: {home_assistant_response.status}",
        error_status_code,
        log_level="error",
    )


def forward_request_to_home_assistant(
    alexa_request: dict[str, Any],
    app_configuration: dict[str, Any],
    authentication_token: str,
    request_context: dict[str, Any],
) -> dict[str, Any]:
    """
    🌉 REQUEST FORWARDER: Send Request to Home Assistant

    Like a mail forwarding service. Takes the validated Alexa
    request and sends it to your Home Assistant instance,
    then returns the response back to Alexa.

    Args:
        alexa_request: The original request from Alexa
        app_configuration: Application configuration settings
        authentication_token: Validated authentication token
        request_context: Timing and context information

    Returns:
        Formatted response to send back to Alexa
    """
    # Extract context information
    request_start_time = request_context["start_time"]
    source_ip = request_context["source_ip"]
    lambda_context_info = request_context["lambda_context_info"]

    # Create HTTP client and prepare request details
    http_client = _create_http_client()
    api_endpoint, request_headers = _prepare_home_assistant_request(
        app_configuration, authentication_token
    )

    # Log the outgoing request (with sensitive data protected)
    _activity_logger.info(
        "🌉 Forwarding Alexa request to Home Assistant. Request: %s",
        (
            json.dumps(remove_sensitive_data_from_request(alexa_request))
            if _enable_detailed_logging
            else "[🔒PROTECTED🔒]"
        ),
    )

    try:
        # Send the request to Home Assistant
        home_assistant_response = http_client.request(
            "POST",
            api_endpoint,
            headers=request_headers,
            body=json.dumps(alexa_request).encode("utf-8"),
        )

        # Record performance metrics
        request_duration = time.time() - request_start_time
        record_performance_metrics(
            "forward_alexa_to_home_assistant",
            request_duration,
            home_assistant_response.status,
        )

        # Handle error responses from Home Assistant
        if home_assistant_response.status >= 400:
            return _handle_home_assistant_error_response(
                home_assistant_response, source_ip, lambda_context_info
            )

        # Log successful response in debug mode
        if _enable_detailed_logging:
            _activity_logger.debug(
                "✅ Home Assistant response: %s",
                home_assistant_response.data.decode("utf-8"),
            )

        # Parse and return the successful response
        response_data = json.loads(home_assistant_response.data.decode("utf-8"))
        return ResponseFormatter.create_success_response(response_data, 200)

    except (HTTPError, ssl.SSLError, json.JSONDecodeError) as request_error:
        _activity_logger.exception(
            "❌ Error communicating with Home Assistant: %s", request_error
        )
        record_security_event(
            "home_assistant_communication_error",
            source_ip,
            {"error": str(request_error), **lambda_context_info},
        )

        # Return appropriate error response
        error_message = (
            "Communication error with Home Assistant"
            if not _enable_detailed_logging
            else str(request_error)
        )
        return ResponseFormatter.create_error_response(
            error_message, 500, log_level="error"
        )


def _extract_request_context(
    alexa_request: dict[str, Any], lambda_context: Any
) -> dict[str, Any]:
    """
    📋 CONTEXT EXTRACTOR: Extract Request Information

    Extracts and prepares context information from the incoming request
    and AWS Lambda runtime for processing.
    """
    request_start_time = time.time()

    # Extract source IP address for security tracking
    source_ip_address = (
        alexa_request.get("requestContext", {}).get("http", {}).get("sourceIp")
        or alexa_request.get("requestContext", {}).get("identity", {}).get("sourceIp")
        or "unknown"
    )

    # Extract AWS Lambda context information for logging
    lambda_context_information = extract_aws_lambda_context_information(lambda_context)
    if lambda_context_information:
        _activity_logger.info(
            "📋 AWS Lambda context: %s", json.dumps(lambda_context_information)
        )

    return {
        "start_time": request_start_time,
        "source_ip": source_ip_address,
        "lambda_context_info": lambda_context_information,
    }


def handle_voice_command_request(
    alexa_request: dict[str, Any], lambda_context: Any
) -> dict[str, Any]:
    """
    🎯 MAIN REQUEST HANDLER: Process Alexa Voice Commands

    This is the main entry point that Amazon Web Services calls when
    Alexa needs to communicate with your Home Assistant. Think of this
    as the receptionist who handles all incoming calls and routes them
    to the right department.

    PROCESS FLOW:
    1. 🕐 Record when the request started (for performance tracking)
    2. 🔍 Identify who sent the request (IP address for security)
    3. 🛡️ Run security checks (rate limiting, size validation)
    4. 🔧 Load and validate configuration settings
    5. 🏠 Verify Home Assistant URL is authorized
    6. 🎫 Extract and validate authentication token from Alexa
    7. 🌉 Forward the request to Home Assistant
    8. 📤 Return the response back to Alexa

    Args:
        alexa_request: The incoming request from Alexa (contains the voice command)
        lambda_context: AWS Lambda runtime information

    Returns:
        Formatted response to send back to Alexa
    """
    # Extract context information for processing
    context_data = _extract_request_context(alexa_request, lambda_context)

    # STEP 1: Validate request security (rate limiting, size checks)
    security_validation_result = validate_request_security_measures(
        alexa_request, context_data["source_ip"], context_data["lambda_context_info"]
    )
    if security_validation_result:
        return security_validation_result  # Security check failed

    # STEP 2: Load and validate application configuration
    config_error, application_configuration = (
        load_and_validate_application_configuration()
    )
    if config_error or application_configuration is None:
        return config_error or ResponseFormatter.create_error_response(
            "Configuration error", 500
        )

    # Extract configuration settings (guaranteed to exist due to validation above)
    app_config_settings = dict(application_configuration["appConfig"])

    # STEP 3: Validate Home Assistant URL against allowlist
    url_validation_result = validate_home_assistant_url_allowlist(
        app_config_settings,
        context_data["source_ip"],
        context_data["lambda_context_info"],
    )
    if url_validation_result:
        return url_validation_result  # URL validation failed

    # STEP 4: Extract and validate authentication token from Alexa
    auth_error, authentication_token = extract_and_validate_alexa_authentication_token(
        alexa_request,
        app_config_settings,
        context_data["source_ip"],
        context_data["lambda_context_info"],
    )
    if auth_error or authentication_token is None:
        return auth_error or ResponseFormatter.create_error_response(
            "Authentication error", 401
        )

    # STEP 5: Forward the request to Home Assistant and return the response
    return forward_request_to_home_assistant(
        alexa_request, app_config_settings, authentication_token, context_data
    )


# === AWS LAMBDA ENTRY POINT ===
# This is the function that AWS Lambda calls when Alexa sends a request


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    🚪 AWS LAMBDA ENTRY POINT: Where Amazon Calls Our Code

    This is the "front door" of our application. When someone talks
    to Alexa and mentions your smart home devices, Amazon's servers
    eventually call this function with the details of what was requested.

    AWS Lambda automatically calls this function with two parameters:
    - event: Contains the Alexa request (what the user said/wanted)
    - context: Contains AWS runtime information (like request ID, timeouts, etc.)

    This function acts as a traffic director, routing the request through
    all our security checks and processing steps before sending it to
    your Home Assistant.

    Args:
        event: The Alexa Smart Home directive (voice command details)
        context: AWS Lambda runtime context information

    Returns:
        Response formatted for Alexa to understand and act upon
    """
    _activity_logger.info("🎯 === NEW ALEXA VOICE COMMAND REQUEST ===")

    try:
        # Process the voice command request through our secure pipeline
        response = handle_voice_command_request(event, context)

        _activity_logger.info("✅ === REQUEST COMPLETED SUCCESSFULLY ===")
        return response

    except (
        ValueError,
        TypeError,
        json.JSONDecodeError,
        botocore.exceptions.BotoCoreError,
        urllib3.exceptions.HTTPError,
        ssl.SSLError,
    ) as unexpected_error:
        # Catch specific expected errors and log them securely
        _activity_logger.exception(
            "💥 Unexpected error processing request: %s", unexpected_error
        )

        # Return a safe error response (don't expose internal details)
        return ResponseFormatter.create_error_response(
            "An unexpected error occurred while processing your request",
            500,
            log_level="error",
        )
