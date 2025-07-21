"""
🌐 CLOUDFLARE OAUTH GATEWAY: Secure Bridge for Alexa Authentication 🔐

=== WHAT THIS FILE DOES (In Plain English) ===

This file is like a "security checkpoint" that sits between Amazon Alexa and your
Home Assistant, but with a special twist - it handles CloudFlare protection and
OAuth authentication. Here's what happens when you link your Alexa account:

1. 📱 You open Alexa app and click "Link Account" for your smart home skill
2. 🌐 Alexa sends you to THIS CODE for OAuth authentication
3. 🔐 THIS CODE handles the OAuth "handshake" (like exchanging ID cards)
4. 🛡️ THIS CODE adds special CloudFlare headers (like a VIP pass)
5. 🏠 Your request gets forwarded to Home Assistant through CloudFlare
6. ✅ Home Assistant confirms your identity and grants access
7. 📱 Alexa app shows "Account successfully linked!"

=== THE COMPLETE ALEXA SKILL ECOSYSTEM: SECURITY GUARD & RECEPTIONIST TEAM ===

🏢 **HOW THESE TWO FILES WORK TOGETHER LIKE A PROFESSIONAL OFFICE**

Imagine your smart home system is like a prestigious corporate office building.
You have TWO key staff members working together to serve Alexa visitors:

👮 **SECURITY GUARD (THIS FILE - cloudflare_oauth_gateway.py)**
- 🏛️ **Job**: Guards the main entrance and handles visitor registration
- 🎫 **Location**: Main lobby entrance (OAuth authentication endpoint)
- 📋 **Responsibilities**:
  * Check visitor credentials when they first arrive
  * Issue temporary access badges (OAuth tokens)
  * Handle CloudFlare security clearance
  * Verify appointments and authority
  * Keep detailed security logs

💼 **EXECUTIVE RECEPTIONIST (voice_command_bridge.py)**
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
3. 🌐 Alexa redirects to: https://your-homeassistant.domain.com/auth/authorize
4. 👮 **SECURITY GUARD (OAuth Gateway)** receives the visitor
5. 🔐 Security Guard handles OAuth authentication with Home Assistant
6. 🎫 Security Guard issues temporary access badge (OAuth token)
7. 📋 Security Guard reports back to Alexa: "Credentials verified!"
8. ✅ Alexa app shows: "Account successfully linked!"

**PHASE 2: DAILY OPERATIONS (Voice Commands) - Receptionist Takes the Lead**
1. 🗣️ User says: "Alexa, turn on the kitchen lights"
2. 🌐 Alexa processes command → sends to AWS Lambda
3. 💼 **EXECUTIVE RECEPTIONIST (Voice Command Bridge)** receives the request
4. 🔍 Receptionist validates the access badge (checks OAuth token)
5. 📞 Receptionist translates request to Home Assistant language
6. 🏠 Receptionist forwards command to Home Assistant
7. 💡 Home Assistant turns on lights → sends confirmation
8. 📋 Receptionist translates response back to Alexa
9. 🗣️ Alexa responds: "OK"

**YOUR ALEXA SKILL CONFIGURATION MAPS TO THIS SYSTEM:**

🔗 **Account Linking Settings:**
- Web Authorization URI: https://your-homeassistant.domain.com/auth/authorize
  → This goes to the **SECURITY GUARD** for initial credential checking

- Access Token URI:
  https://your-oauth-gateway-lambda-url.us-east-1.on.aws/
  → This goes to the **SECURITY GUARD** for token exchange and refresh

📞 **Smart Home Endpoint:**
- Smart Home Endpoint: [Your Voice Command Bridge Lambda URL]
  → This goes to the **EXECUTIVE RECEPTIONIST** for daily operations

🔐 **Why You Need Both:**
- **Security Guard** specializes in high-security authentication tasks
- **Receptionist** specializes in fast, efficient daily operations
- **Security Guard** handles CloudFlare protection (which can be slow)
- **Receptionist** handles rapid voice commands (which need speed)
- **Security Guard** does complex OAuth flows (which need security expertise)
- **Receptionist** does simple token validation (which needs efficiency)

=== WHY THIS EXISTS ===

Think of this like a special translator that speaks three languages:
- 🗣️ Alexa Language: OAuth tokens and smart home directives
- 🛡️ CloudFlare Language: Special access headers and security tokens
- 🏠 Home Assistant Language: API calls and device commands

Without this bridge:
- Alexa can't get through CloudFlare's security (blocked as "suspicious")
- OAuth authentication would fail (no proper token exchange)
- Your smart home setup wouldn't work with CloudFlare protection

=== SECURITY FEATURES ===

This file provides multiple layers of security:
- 🔒 OAuth 2.0 Authentication: Industry standard secure login process
- 🛡️ CloudFlare Access Headers: Bypasses CloudFlare's bot protection
- 🚦 Rate Limiting: Prevents abuse and flooding attacks
- 📏 Request Size Limits: Prevents memory exhaustion attacks
- 🔍 Input Validation: Blocks malicious or malformed requests
- 📝 Security Event Logging: Records all suspicious activity
- 🎭 Sensitive Data Masking: Hides secrets in logs

=== FOR NON-TECHNICAL PEOPLE ===

Think of this like a sophisticated security guard at a corporate building:

🏢 **MAIN LOBBY (OAuth Gateway)**
- Checks visitor credentials (OAuth tokens)
- Issues temporary access badges (authentication)
- Verifies appointments (request validation)

🛡️ **SECURITY CHECKPOINT (CloudFlare Integration)**
- Adds special security clearance (CloudFlare headers)
- Escorts visitors through secured areas (proxy requests)
- Monitors for suspicious behavior (rate limiting)

🏠 **INNER OFFICE (Home Assistant)**
- Receives properly authenticated and authorized visitors
- Processes legitimate requests (smart home commands)
- Returns responses through the same secure channel

=== OAUTH FLOW EXPLANATION ===

OAuth is like a secure "introduction service" between Alexa and Home Assistant:

**STEP 1: AUTHORIZATION REQUEST** 🎫
- User clicks "Link Account" in Alexa app
- Alexa redirects to this gateway with a "please introduce me" request
- Gateway checks if Alexa is legitimate and redirects to Home Assistant

**STEP 2: USER CONSENT** ✅
- Home Assistant shows a login page to the user
- User enters their Home Assistant credentials
- User clicks "Allow Alexa to access my smart home"

**STEP 3: AUTHORIZATION CODE** 🎟️
- Home Assistant gives the user a temporary "introduction code"
- User's browser gets redirected back to this gateway with the code
- Gateway validates the code and prepares for token exchange

**STEP 4: TOKEN EXCHANGE** 🔑
- Alexa sends the introduction code to this gateway
- Gateway exchanges the code for permanent access tokens
- These tokens allow future smart home requests without re-authentication

**STEP 5: ONGOING ACCESS** 🔄
- All future Alexa requests include the access token
- Gateway validates tokens and adds CloudFlare headers
- Requests flow securely to Home Assistant

Author: Jeff Hessenflow <jeff.hessenflow@gmail.com>
Based on original work by: Jason Hu (awarecan)

Original Copyright and License:
  Copyright 2019 Jason Hu <awaregit at gmail.com>
  Licensed under the Apache License, Version 2.0
"""

import json
import logging
import os
import re
import time
from datetime import UTC, datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import boto3
import urllib3
from mypy_boto3_ssm import SSMClient
from urllib3.exceptions import HTTPError

if TYPE_CHECKING:
    pass  # Type checking imports can be added here if needed

# === CONFIGURATION SECTION ===
# These settings control how the OAuth gateway behaves

# Enable detailed logging for troubleshooting (shows more information in logs)
_enable_detailed_logging = bool(os.environ.get("DEBUG"))

# Set up our logging system (like a detailed security logbook)
_activity_logger = logging.getLogger("CloudFlareOAuthGateway")
_activity_logger.setLevel(logging.DEBUG if _enable_detailed_logging else logging.INFO)

# === SECURITY LIMITS ===
# These prevent abuse and ensure good performance

# Maximum size of incoming requests (10 megabytes)
# Prevents attackers from sending huge requests that could crash our function
MAXIMUM_REQUEST_SIZE_BYTES = 10 * 1024 * 1024

# Rate limiting settings - prevents abuse and DoS attacks
RATE_LIMITING_TIME_WINDOW_SECONDS = 60  # Count requests within last 60 seconds
MAXIMUM_REQUESTS_PER_IP_ADDRESS = 150  # Allow up to 150 requests per IP per minute

# Configuration caching - how long to remember loaded config (5 minutes)
# Reduces AWS API calls for better performance and lower costs
CONFIGURATION_CACHE_DURATION_SECONDS = 300

# === ENVIRONMENT SAFETY CHECK ===
# Make sure all required settings are available before starting


def verify_environment_configuration() -> None:
    """
    🔍 ENVIRONMENT VALIDATOR: Check Required Settings

    Like checking you have all necessary documents before traveling.
    Ensures all required environment variables are properly configured.

    Required Environment Variables:
    - APP_CONFIG_PATH: Path to secure configuration in AWS Parameter Store
    - ALLOWED_HA_BASE_URL: Allowlist of authorized Home Assistant URLs

    Raises:
        RuntimeError: If any required environment variables are missing
    """
    required_environment_variables = ["APP_CONFIG_PATH", "ALLOWED_HA_BASE_URL"]
    missing_variables = [
        var for var in required_environment_variables if not os.environ.get(var)
    ]

    if missing_variables:
        error_message = (
            f"Missing required environment variables: {', '.join(missing_variables)}. "
            "See deployment documentation for configuration details."
        )
        raise RuntimeError(error_message)


# Run the environment check when this file loads
verify_environment_configuration()

# Get environment configuration (guaranteed to exist after validation)
secure_config_storage_path = os.environ["APP_CONFIG_PATH"]
allowed_home_assistant_base_url = os.environ["ALLOWED_HA_BASE_URL"].strip().rstrip("/")

# === AWS SERVICE CLIENTS ===
# These provide secure access to AWS services

# SSM (Systems Manager Parameter Store) client for secure configuration retrieval
aws_parameter_store_client: SSMClient = boto3.client("ssm")  # pyright: ignore

# === SECURITY HEADERS ===
# These HTTP headers improve security by controlling browser behavior


def get_secure_response_headers() -> dict[str, str]:
    """
    🔒 SECURITY HEADER BUILDER: Create Secure HTTP Headers

    Like adding multiple locks and security systems to a building.
    Each header serves a specific security purpose to protect users.

    Returns:
        Dictionary of HTTP headers that enhance security
    """
    return {
        # Tell the client this is JSON data
        "Content-Type": "application/json",
        # CACHE CONTROL: Prevent caching of sensitive authentication data
        # Ensures secrets/tokens aren't stored in browser caches
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",  # Legacy cache prevention
        # CONTENT SECURITY: Prevent MIME type confusion attacks
        # Forces browsers to respect the declared content type
        "X-Content-Type-Options": "nosniff",
        # FRAME PROTECTION: Prevent clickjacking attacks
        # Stops this page from being embedded in malicious frames
        "X-Frame-Options": "DENY",
        # XSS PROTECTION: Enable browser's built-in XSS filtering
        "X-XSS-Protection": "1; mode=block",
        # HTTPS ENFORCEMENT: Force HTTPS for all future requests (1 year)
        # Ensures all communication remains encrypted
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        # REFERRER POLICY: Don't leak referrer information to other sites
        # Prevents information disclosure about user's browsing
        "Referrer-Policy": "no-referrer",
    }


# === GLOBAL STORAGE ===
# These store data in memory to improve performance and track security

# Rate limiting storage: Tracks request counts per IP address
# Resets when Lambda function restarts (which is normal AWS behavior)
_request_tracking_storage: dict[str, list[float]] = {}

# Configuration cache: Stores loaded config to reduce AWS API calls
# Format: {config_path: (config_data, timestamp)}
_configuration_cache: dict[str, tuple[dict[str, Any], float]] = {}


# === SECURITY AND VALIDATION FUNCTIONS ===


def validate_string_parameter_security(
    value: str, maximum_length: int = 512, allow_empty_values: bool = False
) -> bool:
    """
    🔍 STRING VALIDATOR: Check String Parameters for Security

    Like a security scanner that checks documents for dangerous content.
    Validates string inputs to prevent various types of security attacks.

    Args:
        value: The string to validate for security
        maximum_length: Maximum allowed length (prevents buffer overflow)
        allow_empty_values: Whether empty strings are acceptable

    Security Checks Performed:
    - Length validation: Prevents buffer overflow attacks
    - Content validation: Blocks XSS attack patterns
    - Character validation: Ensures safe character usage

    Returns:
        True if the string is safe to use, False if potentially dangerous
    """
    # Check for empty values if they're not allowed
    if not value and not allow_empty_values:
        _activity_logger.warning("🚨 Empty string provided where value required")
        return False

    # Check for excessive length (buffer overflow prevention)
    if len(value) > maximum_length:
        _activity_logger.warning(
            "🚨 String too long: %d characters (max: %d)", len(value), maximum_length
        )
        return False

    # Security check: Block dangerous characters that could be used for XSS attacks
    dangerous_character_patterns = [
        "<",
        ">",
        '"',
        "'",
        "&",
        "javascript:",
        "data:",
        "vbscript:",
        "onload=",
        "onerror=",
        "onclick=",
    ]

    value_lowercase = value.lower()
    for dangerous_pattern in dangerous_character_patterns:
        if dangerous_pattern in value_lowercase:
            _activity_logger.warning(
                "🚨 Dangerous pattern detected in string: %s", dangerous_pattern
            )
            return False

    return True  # String passed all security checks


def enforce_rate_limiting_protection(source_ip_address: str) -> bool:
    """
    🚦 RATE LIMITER: Prevent Request Flooding and DoS Attacks

    Like a bouncer at a club who tracks how many times each person
    has entered and blocks those who are being excessive.

    How It Works:
    1. Tracks request timestamps for each IP address
    2. Removes old timestamps outside the time window
    3. Counts recent requests within the current window
    4. Blocks IPs that exceed the maximum allowed requests
    5. Records the current request for future counting

    Args:
        source_ip_address: The IP address making the request

    Security Benefits:
    - Prevents DoS (Denial of Service) attacks
    - Limits resource consumption per IP address
    - Maintains service availability for legitimate users
    - Protects against automated abuse

    Returns:
        True if the request should be allowed, False if rate limit exceeded
    """
    current_timestamp = time.time()

    # Initialize tracking for new IP addresses
    if source_ip_address not in _request_tracking_storage:
        _request_tracking_storage[source_ip_address] = []
        _activity_logger.debug("📊 New IP address detected: %s", source_ip_address)

    # Remove old request timestamps that are outside our time window
    # This keeps only recent requests for accurate counting
    _request_tracking_storage[source_ip_address] = [
        request_timestamp
        for request_timestamp in _request_tracking_storage[source_ip_address]
        if current_timestamp - request_timestamp < RATE_LIMITING_TIME_WINDOW_SECONDS
    ]

    # Check if this IP has made too many requests recently
    recent_request_count = len(_request_tracking_storage[source_ip_address])
    if recent_request_count >= MAXIMUM_REQUESTS_PER_IP_ADDRESS:
        _activity_logger.warning(
            "🚨 Rate limit exceeded for IP %s: %d requests in %d seconds",
            source_ip_address,
            recent_request_count,
            RATE_LIMITING_TIME_WINDOW_SECONDS,
        )
        return False  # Block this request

    # Record this request timestamp and allow the request
    _request_tracking_storage[source_ip_address].append(current_timestamp)
    _activity_logger.debug(
        "✅ Rate limit check passed for IP %s: %d/%d requests",
        source_ip_address,
        recent_request_count + 1,
        MAXIMUM_REQUESTS_PER_IP_ADDRESS,
    )

    return True  # Request is allowed


def validate_request_size_protection(lambda_event: dict[str, Any]) -> bool:
    """
    📏 REQUEST SIZE VALIDATOR: Prevent Memory Exhaustion Attacks

    Like a postal service that weighs packages and rejects those
    that are too heavy for safe handling.

    Args:
        lambda_event: The AWS Lambda event containing the request data

    Security Protection:
    - Prevents memory exhaustion attacks via large payloads
    - Protects against DoS attacks using oversized requests
    - Ensures Lambda function stability and performance
    - Maintains reasonable resource usage

    Returns:
        True if request size is acceptable, False if too large
    """
    # Extract request body (where the main data is stored)
    request_body = lambda_event.get("body", "")

    # Calculate the size in bytes (handles unicode characters correctly)
    request_size_in_bytes = len(request_body.encode("utf-8"))

    # Check if the request exceeds our safety limit
    if request_size_in_bytes > MAXIMUM_REQUEST_SIZE_BYTES:
        _activity_logger.warning(
            "🚨 Request too large: %d bytes (max: %d bytes)",
            request_size_in_bytes,
            MAXIMUM_REQUEST_SIZE_BYTES,
        )
        return False  # Request is too large

    _activity_logger.debug(
        "✅ Request size check passed: %d bytes", request_size_in_bytes
    )

    return True  # Request size is acceptable


def sanitize_url_path_for_security(url_path: str) -> str:
    """
    🧹 URL PATH SANITIZER: Remove Dangerous Path Characters

    Like a security guard who checks that visitors aren't trying
    to access restricted areas by using sneaky path tricks.

    Security Protection:
    - Prevents directory traversal attacks (../../../etc/passwd)
    - Removes double slashes that could bypass security
    - Ensures paths are properly formatted
    - Blocks common path-based attack patterns

    Args:
        url_path: The URL path to clean and secure

    Returns:
        A sanitized version of the URL path that's safe to use
    """
    if not url_path:
        return "/"

    # Remove dangerous path traversal sequences
    sanitized_path = url_path.replace("..", "").replace("//", "/")

    # Remove any remaining dangerous patterns
    dangerous_patterns = ["\\", "%2e%2e", "%2f%2f", "~"]
    for pattern in dangerous_patterns:
        sanitized_path = sanitized_path.replace(pattern, "")

    # Ensure path starts with forward slash (proper URL format)
    if not sanitized_path.startswith("/"):
        sanitized_path = "/" + sanitized_path

    # Log if we had to make changes (potential attack attempt)
    if sanitized_path != url_path:
        _activity_logger.warning(
            "🧹 Path sanitized from '%s' to '%s'", url_path, sanitized_path
        )

    return sanitized_path


# === HTTP CONNECTION MANAGEMENT ===


@lru_cache(maxsize=2)
def create_optimized_http_connection_pool(
    pool_connections: int = 10, pool_maxsize: int = 20
) -> urllib3.PoolManager:
    """
    🌐 HTTP POOL MANAGER: Create Optimized Connection Pool

    Like a taxi dispatcher that keeps a fleet of taxis ready
    instead of calling a new taxi for each ride. This improves
    performance by reusing HTTP connections.

    Performance Benefits:
    - Reuses existing HTTP connections (faster than creating new ones)
    - Reduces network overhead and latency
    - Manages connection lifecycle automatically
    - Handles SSL/TLS handshakes efficiently

    Args:
        pool_connections: Number of connection pools to maintain
        pool_maxsize: Maximum connections per pool

    Returns:
        Configured HTTP connection pool manager
    """
    _activity_logger.debug(
        "🌐 Creating HTTP connection pool: %d pools, %d max connections",
        pool_connections,
        pool_maxsize,
    )

    return urllib3.PoolManager(
        num_pools=pool_connections,
        maxsize=pool_maxsize,
        # Connection timeout settings for good performance
        timeout=urllib3.Timeout(connect=2.0, read=10.0),
        # Retry configuration for reliability
        retries=urllib3.Retry(
            total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504]
        ),
    )


# === LOGGING AND MONITORING ===


def record_security_event_details(
    event_type: str,
    source_ip_address: str,
    additional_context: dict[str, Any] | None = None,
) -> None:
    """
    📝 SECURITY EVENT RECORDER: Log Security-Related Events

    Like a security guard writing detailed incident reports.
    Records all security-related events for monitoring and analysis.

    Args:
        event_type: Type of security event (rate_limit_exceeded, etc.)
        source_ip_address: IP address involved in the event
        additional_context: Extra details about the event

    Security Benefits:
    - Creates audit trail for security analysis
    - Helps identify attack patterns and sources
    - Enables proactive security response
    - Supports compliance and forensic investigation
    """
    security_event_record: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "source_ip": source_ip_address,
        "gateway_function": "cloudflare_oauth_gateway",
        "details": additional_context or {},
    }

    # Log as warning level so it appears in CloudWatch monitoring
    _activity_logger.warning("🚨 SECURITY EVENT: %s", json.dumps(security_event_record))


def record_performance_metrics_data(
    operation_name: str, duration_seconds: float, http_status_code: int
) -> None:
    """
    📊 PERFORMANCE METRICS RECORDER: Track Operation Performance

    Like a stopwatch coach who times all athletes to identify
    who needs improvement. Helps optimize gateway performance.

    Args:
        operation_name: Name of the operation being measured
        duration_seconds: How long the operation took
        http_status_code: HTTP status code of the result

    Performance Benefits:
    - Identifies slow operations that need optimization
    - Tracks success/failure rates
    - Enables performance trending and analysis
    - Supports capacity planning and scaling decisions
    """
    performance_metrics: dict[str, Any] = {
        "operation": operation_name,
        "duration_milliseconds": round(duration_seconds * 1000, 2),
        "status_code": http_status_code,
        "timestamp": datetime.now(UTC).isoformat(),
        "gateway_function": "cloudflare_oauth_gateway",
    }

    _activity_logger.info("📊 PERFORMANCE METRICS: %s", json.dumps(performance_metrics))


# === CONFIGURATION MANAGEMENT ===


class OAuthGatewayConfiguration:
    """
    ⚙️ CONFIGURATION MANAGER: Structured Access to Gateway Settings

    Like a well-organized filing cabinet that keeps all important
    documents in labeled folders for easy access.
    """

    def __init__(self, configuration_data: dict[str, Any]) -> None:
        """
        Initialize configuration with validation.

        Args:
            configuration_data: Dictionary containing all configuration settings
        """
        self._config_data = configuration_data
        self._validate_required_configuration()

    def _validate_required_configuration(self) -> None:
        """
        🔍 CONFIG VALIDATOR: Ensure All Required Settings Are Present

        Like a checklist before departing on a trip - makes sure
        we have everything we need before starting.
        """
        required_config_keys = [
            "HA_BASE_URL",  # Home Assistant URL
            "ALEXA_SECRET",  # Shared secret for Alexa authentication
            "CF_CLIENT_ID",  # CloudFlare Access client ID
            "CF_CLIENT_SECRET",  # CloudFlare Access client secret
        ]

        missing_keys = [
            key for key in required_config_keys if key not in self._config_data
        ]

        if missing_keys:
            error_message = (
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )
            _activity_logger.error(
                "❌ Configuration validation failed: %s", error_message
            )
            raise ValueError(error_message)

        _activity_logger.debug("✅ Configuration validation passed")

    @property
    def home_assistant_base_url(self) -> str:
        """Get the Home Assistant base URL."""
        return self._config_data["HA_BASE_URL"].strip().rstrip("/")

    @property
    def alexa_shared_secret(self) -> str:
        """Get the shared secret for Alexa authentication."""
        return self._config_data["ALEXA_SECRET"]

    @property
    def cloudflare_client_id(self) -> str:
        """Get the CloudFlare Access client ID."""
        return self._config_data["CF_CLIENT_ID"]

    @property
    def cloudflare_client_secret(self) -> str:
        """Get the CloudFlare Access client secret."""
        return self._config_data["CF_CLIENT_SECRET"]

    @property
    def home_assistant_token(self) -> str | None:
        """Get the Home Assistant token (optional fallback)."""
        return self._config_data.get("HA_TOKEN")

    def has_cloudflare_authentication(self) -> bool:
        """Check if CloudFlare authentication is properly configured."""
        return bool(self.cloudflare_client_id and self.cloudflare_client_secret)

    def has_home_assistant_token(self) -> bool:
        """Check if Home Assistant token fallback is available."""
        return bool(self.home_assistant_token)


class RequestProcessingContext:
    """
    📋 REQUEST CONTEXT: Centralized Request Processing Information

    Like a case file that contains all the information needed
    to process a specific request. Reduces parameter passing
    and makes the code easier to understand.
    """

    def __init__(
        self,
        gateway_config: OAuthGatewayConfiguration,
        *,
        http_method: str,
        api_endpoint_path: str,
        request_headers: dict[str, Any],
        request_body: str,
    ) -> None:
        """
        Initialize request context with all necessary information.

        Args:
            gateway_config: Gateway configuration object
            http_method: HTTP method (GET, POST, etc.)
            api_endpoint_path: API path being requested
            request_headers: HTTP headers from the request
            request_body: Request body content
        """
        self.config = gateway_config
        self.method = http_method
        self.path = api_endpoint_path
        self.headers = request_headers
        self.body = request_body
        self.start_time = time.time()

        # Determine request type based on path
        self.is_oauth_request = self._detect_oauth_request_type()

    def _detect_oauth_request_type(self) -> bool:
        """
        🕵️ REQUEST TYPE DETECTOR: Identify OAuth vs Regular Requests

        OAuth requests need special handling for token exchange,
        while regular requests are smart home commands.
        """
        oauth_path_patterns = ["/auth/token", "/oauth/token", "/token"]
        return any(pattern in self.path.lower() for pattern in oauth_path_patterns)

    def build_cloudflare_headers(self) -> dict[str, str]:
        """
        🛡️ CLOUDFLARE HEADER BUILDER: Create CloudFlare Access Headers

        Like creating a VIP pass that allows requests to bypass
        CloudFlare's security screening.
        """
        cloudflare_headers: dict[str, str] = {}

        if self.config.has_cloudflare_authentication():
            cloudflare_headers.update(
                {
                    "CF-Access-Client-Id": self.config.cloudflare_client_id,
                    "CF-Access-Client-Secret": self.config.cloudflare_client_secret,
                }
            )
            _activity_logger.debug("🛡️ CloudFlare headers added to request")
        else:
            _activity_logger.warning("⚠️ CloudFlare authentication not configured")

        return cloudflare_headers

    def get_processing_duration(self) -> float:
        """Get how long this request has been processing."""
        return time.time() - self.start_time


# === RESPONSE BUILDERS ===


class SecureResponseBuilder:
    """
    📤 RESPONSE BUILDER: Create Properly Formatted Gateway Responses

    Like a professional letter writer who ensures all correspondence
    follows proper format and includes necessary security measures.
    """

    @staticmethod
    def create_success_response(
        response_data: Any, http_status_code: int = 200
    ) -> dict[str, Any]:
        """
        Create a properly formatted success response.

        Args:
            response_data: The data to include in the response
            http_status_code: HTTP status code (default 200 = success)

        Returns:
            Formatted response ready for AWS Lambda to return
        """
        return {
            "statusCode": http_status_code,
            "headers": get_secure_response_headers(),
            "body": json.dumps(response_data),
        }

    @staticmethod
    def create_error_response(
        error_message: str, http_status_code: int = 400, log_level: str = "warning"
    ) -> dict[str, Any]:
        """
        Create a properly formatted error response with security measures.

        Args:
            error_message: Description of what went wrong
            http_status_code: HTTP error code (400, 500, etc.)
            log_level: How serious this error is ("warning" or "error")

        Returns:
            Formatted error response with security headers
        """
        # Remove sensitive information before logging or responding
        safe_error_message = SecureResponseBuilder._sanitize_error_message(
            error_message
        )

        # Log the error at the appropriate level
        if log_level == "warning":
            _activity_logger.warning("⚠️ Request error: %s", safe_error_message)
        else:
            _activity_logger.error("❌ Request error: %s", safe_error_message)

        return {
            "statusCode": http_status_code,
            "headers": get_secure_response_headers(),
            "body": json.dumps({"error": safe_error_message}),
        }

    @staticmethod
    def _sanitize_error_message(error_text: str) -> str:
        """
        🔒 ERROR MESSAGE SANITIZER: Remove Sensitive Information

        Like a redaction tool that blacks out classified information
        in documents before they're shared publicly.
        """
        sensitive_keywords_to_mask = [
            "bearer",
            "token",
            "secret",
            "authorization",
            "client_secret",
            "access_token",
            "refresh_token",
            "password",
            "key",
            "credential",
            "cf-access",
            "oauth",
            "session",
        ]

        sanitized_text = error_text
        for keyword in sensitive_keywords_to_mask:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            sanitized_text = pattern.sub("[🔒PROTECTED🔒]", sanitized_text)

        return sanitized_text


# === REQUEST EXECUTION ENGINE ===


class GatewayRequestExecutor:
    """
    🚀 REQUEST EXECUTOR: Handle HTTP Request Execution with Error Handling

    Like a skilled diplomat who handles all the complex negotiations
    between different parties (Alexa, CloudFlare, Home Assistant).
    """

    @staticmethod
    def execute_proxied_request(
        processing_context: RequestProcessingContext,
    ) -> dict[str, Any]:
        """
        🌉 PROXY EXECUTOR: Execute Request Through CloudFlare to Home Assistant

        This is the main execution engine that handles the actual
        forwarding of requests with proper CloudFlare headers.

        Args:
            processing_context: Complete context for request processing

        Returns:
            Response from Home Assistant (or error response)
        """
        operation_start_time = time.time()

        try:
            # Build the complete target URL
            target_url = GatewayRequestExecutor._build_target_url(processing_context)

            # Prepare headers with CloudFlare authentication
            proxy_headers = GatewayRequestExecutor._prepare_proxy_headers(
                processing_context
            )

            # Log the outgoing request (with sensitive data protected)
            GatewayRequestExecutor._log_outgoing_request(processing_context, target_url)

            # Execute the HTTP request
            http_response = GatewayRequestExecutor._execute_http_request(
                processing_context, target_url, proxy_headers
            )

            # Record performance metrics
            operation_duration = time.time() - operation_start_time
            record_performance_metrics_data(
                "proxy_request_execution", operation_duration, http_response.status
            )

            # Process and return the response
            return GatewayRequestExecutor._process_http_response(http_response)

        except HTTPError as http_error:
            # Handle HTTP-specific errors (connection issues, timeouts, etc.)
            operation_duration = time.time() - operation_start_time
            return GatewayRequestExecutor._handle_request_error(
                http_error, processing_context, operation_duration
            )

    @staticmethod
    def _build_target_url(processing_context: RequestProcessingContext) -> str:
        """Build the complete target URL for the request."""
        base_url = processing_context.config.home_assistant_base_url
        sanitized_path = sanitize_url_path_for_security(processing_context.path)

        target_url = f"{base_url}{sanitized_path}"
        _activity_logger.debug("🎯 Target URL built: %s", target_url)

        return target_url

    @staticmethod
    def _prepare_proxy_headers(
        processing_context: RequestProcessingContext,
    ) -> dict[str, str]:
        """Prepare headers for the proxied request."""
        proxy_headers = {
            "Content-Type": "application/json",
            "User-Agent": "CloudFlareOAuthGateway/1.0",
        }

        # Add CloudFlare authentication headers
        cloudflare_headers = processing_context.build_cloudflare_headers()
        proxy_headers.update(cloudflare_headers)

        # Copy relevant headers from original request
        headers_to_forward = ["authorization", "accept", "accept-language"]
        for header_name in headers_to_forward:
            if header_name in processing_context.headers:
                proxy_headers[header_name] = processing_context.headers[header_name]

        return proxy_headers

    @staticmethod
    def _log_outgoing_request(
        processing_context: RequestProcessingContext, target_url: str
    ) -> None:
        """Log outgoing request details (with sensitive data protected)."""
        if _enable_detailed_logging:
            _activity_logger.debug(
                "🌉 Proxying %s request to: %s", processing_context.method, target_url
            )
        else:
            _activity_logger.info("🌉 Proxying request to Home Assistant")

    @staticmethod
    def _execute_http_request(
        processing_context: RequestProcessingContext,
        target_url: str,
        proxy_headers: dict[str, str],
    ) -> Any:  # Changed from urllib3.HTTPResponse to Any for type compatibility
        """Execute the actual HTTP request."""
        http_pool = create_optimized_http_connection_pool()

        # Choose timeout based on request type (OAuth can be slower)
        timeout_seconds = 30.0 if processing_context.is_oauth_request else 10.0

        return http_pool.request(
            method=processing_context.method,
            url=target_url,
            headers=proxy_headers,
            body=(
                processing_context.body.encode("utf-8")
                if processing_context.body
                else None
            ),
            timeout=timeout_seconds,
            retries=False,  # We handle retries manually if needed
        )

    @staticmethod
    def _process_http_response(http_response: Any) -> dict[str, Any]:
        """Process the HTTP response from Home Assistant."""
        response_body = http_response.data.decode("utf-8")

        # Log successful responses in debug mode
        if _enable_detailed_logging:
            _activity_logger.debug(
                "✅ Home Assistant response: Status %d, Body: %s",
                http_response.status,
                (
                    response_body[:200] + "..."
                    if len(response_body) > 200
                    else response_body
                ),
            )

        # Parse JSON response if possible
        try:
            response_data = json.loads(response_body)
        except json.JSONDecodeError:
            # If not JSON, return as plain text
            response_data = {"response": response_body}

        return SecureResponseBuilder.create_success_response(
            response_data, http_response.status
        )

    @staticmethod
    def _handle_request_error(
        error: Exception,
        processing_context: RequestProcessingContext,  # pylint: disable=unused-argument
        operation_duration: float,
    ) -> dict[str, Any]:
        """Handle errors that occur during request execution."""
        error_message = str(error)

        # Log the error with appropriate detail level
        _activity_logger.exception(
            "❌ Request execution failed after %.2f seconds: %s",
            operation_duration,
            error_message,
        )

        # Record performance metrics for failed request
        record_performance_metrics_data(
            "proxy_request_execution", operation_duration, 500
        )

        # Determine appropriate error response
        if "timeout" in error_message.lower():
            return SecureResponseBuilder.create_error_response(
                "Request timeout - Home Assistant took too long to respond",
                504,
                "error",
            )
        if "connection" in error_message.lower():
            return SecureResponseBuilder.create_error_response(
                "Connection error - Unable to reach Home Assistant", 502, "error"
            )
        return SecureResponseBuilder.create_error_response(
            "Internal gateway error occurred", 500, "error"
        )


# === CONFIGURATION LOADING ===


def load_secure_gateway_configuration(
    parameter_store_path: str,
) -> dict[str, Any] | None:
    """
    🔐 CONFIGURATION LOADER: Retrieve Settings from AWS Parameter Store

    Like accessing a secure safe deposit box at a bank. Retrieves
    all configuration settings that are stored securely in AWS
    instead of being hardcoded in the application.

    Args:
        parameter_store_path: Path in AWS Parameter Store where config is stored

    Returns:
        Dictionary containing all configuration settings, or None if failed

    Security Benefits:
    - Configuration stored encrypted in AWS
    - No hardcoded secrets in source code
    - Centralized configuration management
    - Access controlled by AWS IAM policies
    """
    try:
        _activity_logger.info(
            "🔐 Loading secure configuration from: %s", parameter_store_path
        )

        # Retrieve all parameters from the specified path
        parameter_response = aws_parameter_store_client.get_parameters_by_path(
            Path=parameter_store_path,
            Recursive=False,  # Don't get sub-folders
            WithDecryption=True,  # Decrypt encrypted values
        )

        # Build configuration dictionary from parameters
        configuration_data: dict[str, Any] = {}
        for parameter in parameter_response.get("Parameters", []):
            parameter_name = parameter.get("Name", "").split("/")[-1]
            parameter_value = parameter.get("Value", "")

            # Try to parse as JSON, fall back to string
            try:
                configuration_data[parameter_name] = json.loads(parameter_value)
            except json.JSONDecodeError:
                configuration_data[parameter_name] = parameter_value

        _activity_logger.info(
            "✅ Successfully loaded configuration with %d parameters",
            len(configuration_data),
        )

        return configuration_data

    except (
        aws_parameter_store_client.exceptions.ParameterNotFound,
        aws_parameter_store_client.exceptions.ParameterVersionNotFound,
    ) as config_error:
        _activity_logger.error(
            "❌ Configuration parameters not found: %s", config_error
        )
        return None

    except (ValueError, TypeError, AttributeError) as data_error:
        _activity_logger.error("❌ Configuration data processing error: %s", data_error)
        return None


def load_cached_gateway_configuration(
    parameter_store_path: str,
) -> dict[str, Any] | None:
    """
    ⚡ CACHED CONFIGURATION LOADER: Fast Configuration with Caching

    Like keeping a photocopy of important documents in your desk
    instead of going to the filing cabinet every time. Improves
    performance by caching configuration in memory.

    Args:
        parameter_store_path: Path in AWS Parameter Store

    Returns:
        Cached configuration data or freshly loaded if cache expired

    Performance Benefits:
    - Reduces AWS Parameter Store API calls
    - Faster response times for subsequent requests
    - Lower AWS costs due to fewer API calls
    - Automatic cache expiration for security
    """
    current_time = time.time()

    # Check if we have cached configuration that's still valid
    if parameter_store_path in _configuration_cache:
        cached_config, cache_timestamp = _configuration_cache[parameter_store_path]
        cache_age = current_time - cache_timestamp

        if cache_age < CONFIGURATION_CACHE_DURATION_SECONDS:
            _activity_logger.debug(
                "⚡ Using cached configuration (age: %.1f seconds)", cache_age
            )
            return cached_config
        _activity_logger.debug(
            "🔄 Configuration cache expired (age: %.1f seconds)", cache_age
        )

    # Load fresh configuration from AWS
    fresh_configuration = load_secure_gateway_configuration(parameter_store_path)

    if fresh_configuration:
        # Cache the fresh configuration
        _configuration_cache[parameter_store_path] = (fresh_configuration, current_time)
        _activity_logger.debug("💾 Configuration cached for future use")

    return fresh_configuration


# === URL VALIDATION ===


def validate_home_assistant_url_security(target_url: str) -> bool:
    """
    🔍 URL VALIDATOR: Check Home Assistant URL Against Security Allowlist

    Like a guest list at an exclusive event. Ensures that we only
    send requests to authorized Home Assistant instances.

    Args:
        target_url: The URL being requested

    Security Benefits:
    - Prevents the gateway from being used to attack other websites
    - Ensures requests only go to authorized Home Assistant instances
    - Protects against Server-Side Request Forgery (SSRF) attacks
    - Maintains strict security boundaries

    Returns:
        True if URL is authorized, False if blocked
    """
    if not target_url:
        _activity_logger.warning("🚨 Empty URL provided for validation")
        return False

    # Normalize URLs for comparison
    target_url_normalized = target_url.strip().rstrip("/")
    allowed_url_normalized = allowed_home_assistant_base_url

    # Check if target URL matches or is a sub-path of allowed URL
    is_url_authorized = (
        target_url_normalized == allowed_url_normalized
        or target_url_normalized.startswith(allowed_url_normalized + "/")
    )

    if not is_url_authorized:
        _activity_logger.warning(
            "🚨 Unauthorized URL access attempted: %s (allowed: %s)",
            target_url_normalized,
            allowed_url_normalized,
        )
        return False

    _activity_logger.debug(
        "✅ URL authorization check passed: %s", target_url_normalized
    )
    return True


# === SENSITIVE DATA PROTECTION ===


def mask_sensitive_data_in_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """
    🎭 HEADER MASKER: Hide Sensitive Data in Headers for Logging

    Like using a black marker to redact classified information
    in documents before they're shared.
    """
    masked_headers: dict[str, Any] = {}
    sensitive_header_names = [
        "authorization",
        "cf-access-client-secret",
        "x-api-key",
        "cookie",
        "set-cookie",
        "x-auth-token",
    ]

    for header_name, header_value in headers.items():
        header_name_lower = header_name.lower()
        if any(
            sensitive_name in header_name_lower
            for sensitive_name in sensitive_header_names
        ):
            masked_headers[header_name] = "[🔒PROTECTED🔒]"
        else:
            masked_headers[header_name] = str(header_value)

    return masked_headers


def mask_sensitive_data_in_body(request_body: str) -> str:
    """
    🎭 BODY MASKER: Hide Sensitive Data in Request Bodies for Logging

    Protects authentication tokens, passwords, and other secrets
    from being exposed in log files.
    """
    if not request_body:
        return ""

    # List of sensitive field patterns to mask
    sensitive_patterns = [
        r'"(access_token|refresh_token|client_secret|password|secret)"\s*:\s*"[^"]*"',
        r'"token"\s*:\s*"[^"]*"',
        r'"authorization"\s*:\s*"[^"]*"',
    ]

    masked_body = request_body
    for pattern in sensitive_patterns:
        masked_body = re.sub(
            pattern,
            lambda m: m.group(0).split(":")[0] + ': "[🔒PROTECTED🔒]"',
            masked_body,
            flags=re.IGNORECASE,
        )

    return masked_body


# === MAIN REQUEST HANDLER ===


def lambda_handler(
    event: dict[str, Any], context: Any  # pylint: disable=unused-argument
) -> dict[str, Any]:
    """
    🚪 AWS LAMBDA ENTRY POINT: CloudFlare OAuth Gateway Main Handler

    This is the "front door" of our OAuth gateway. When Alexa needs
    to authenticate or when smart home requests need CloudFlare
    headers, AWS Lambda calls this function.

    Process Flow:
    1. 🔍 Extract request details from AWS Lambda event
    2. 🛡️ Perform security validation (rate limiting, size checks)
    3. 🔧 Load configuration from AWS Parameter Store
    4. 🏠 Validate Home Assistant URL authorization
    5. 🌉 Execute proxied request with CloudFlare headers
    6. 📤 Return response to Alexa

    Args:
        event: AWS Lambda event containing the HTTP request details
        context: AWS Lambda runtime context (contains request ID, etc.)

    Returns:
        HTTP response formatted for AWS API Gateway
    """
    request_start_time = time.time()

    _activity_logger.info("🎯 === NEW OAUTH GATEWAY REQUEST ===")

    try:
        # Extract request details from Lambda event
        request_context = extract_request_context_from_event(event)

        # Perform security validation
        security_check_result = perform_comprehensive_security_validation(
            event, request_context
        )
        if security_check_result:
            return security_check_result  # Security check failed

        # Load and validate configuration
        gateway_config = load_and_validate_gateway_configuration()
        if not gateway_config:
            return SecureResponseBuilder.create_error_response(
                "Gateway configuration error", 500, "error"
            )

        # Validate Home Assistant URL authorization
        if not validate_home_assistant_url_security(
            gateway_config.home_assistant_base_url
        ):
            record_security_event_details(
                "unauthorized_url_access", request_context.get("source_ip", "unknown")
            )
            return SecureResponseBuilder.create_error_response(
                "URL not authorized", 403, "error"
            )

        # Create processing context
        processing_context = RequestProcessingContext(
            gateway_config,
            http_method=request_context["method"],
            api_endpoint_path=request_context["path"],
            request_headers=request_context["headers"],
            request_body=request_context["body"],
        )

        # Execute the proxied request
        response = GatewayRequestExecutor.execute_proxied_request(processing_context)

        # Record successful completion
        total_duration = time.time() - request_start_time
        record_performance_metrics_data(
            "complete_gateway_request", total_duration, response["statusCode"]
        )

        _activity_logger.info("✅ === REQUEST COMPLETED SUCCESSFULLY ===")
        return response

    except (ValueError, TypeError, KeyError, AttributeError) as gateway_error:
        # Handle configuration or data processing errors
        total_duration = time.time() - request_start_time

        _activity_logger.error(
            "💥 Gateway configuration error after %.2f seconds: %s",
            total_duration,
            gateway_error,
        )

        record_performance_metrics_data("complete_gateway_request", total_duration, 500)

        return SecureResponseBuilder.create_error_response(
            "Internal gateway error occurred", 500, "error"
        )


# === HELPER FUNCTIONS ===


def extract_request_context_from_event(lambda_event: dict[str, Any]) -> dict[str, Any]:
    """
    📋 REQUEST EXTRACTOR: Extract Request Details from Lambda Event

    Like unpacking a carefully wrapped package to get to the
    contents inside. AWS Lambda wraps HTTP requests in a
    specific format that we need to unwrap.
    """
    # Extract HTTP method (GET, POST, etc.)
    http_method = lambda_event.get("httpMethod", "GET").upper()

    # Extract request path
    request_path = lambda_event.get("path", "/")

    # Extract headers (case-insensitive)
    request_headers = {}
    if "headers" in lambda_event:
        for header_name, header_value in lambda_event["headers"].items():
            request_headers[header_name.lower()] = header_value

    # Extract request body
    request_body = lambda_event.get("body", "")
    if request_body is None:
        request_body = ""

    # Extract source IP for security tracking
    source_ip = (
        lambda_event.get("requestContext", {})
        .get("identity", {})
        .get("sourceIp", "unknown")
    )

    return {
        "method": http_method,
        "path": request_path,
        "headers": request_headers,
        "body": request_body,
        "source_ip": source_ip,
    }


def perform_comprehensive_security_validation(
    lambda_event: dict[str, Any], request_context: dict[str, Any]
) -> dict[str, Any] | None:
    """
    🛡️ SECURITY VALIDATOR: Perform All Security Checks

    Like a comprehensive security screening at an airport.
    Performs multiple security checks to ensure the request
    is safe to process.

    Returns:
        None if all security checks pass
        Error response dict if any security check fails
    """
    source_ip = request_context.get("source_ip", "unknown")

    # Check rate limiting
    if not enforce_rate_limiting_protection(source_ip):
        record_security_event_details("rate_limit_exceeded", source_ip)
        return SecureResponseBuilder.create_error_response(
            "Too many requests - please slow down", 429, "warning"
        )

    # Check request size
    if not validate_request_size_protection(lambda_event):
        record_security_event_details("request_too_large", source_ip)
        return SecureResponseBuilder.create_error_response(
            "Request is too large", 413, "warning"
        )

    # Validate string parameters in headers
    for header_name, header_value in request_context.get("headers", {}).items():
        if not validate_string_parameter_security(str(header_value), 1024, True):
            record_security_event_details(
                "invalid_header_content", source_ip, {"header": header_name}
            )
            return SecureResponseBuilder.create_error_response(
                "Invalid header content detected", 400, "warning"
            )

    return None  # All security checks passed


def load_and_validate_gateway_configuration() -> OAuthGatewayConfiguration | None:
    """
    🔧 CONFIG LOADER: Load and Validate Gateway Configuration

    Like a quality control inspector who checks that all
    components are present and properly configured.

    Returns:
        Validated configuration object, or None if validation failed
    """
    try:
        # Load configuration from AWS Parameter Store
        config_data = load_cached_gateway_configuration(secure_config_storage_path)

        if not config_data:
            _activity_logger.error("❌ Failed to load gateway configuration")
            return None

        # Create and validate configuration object
        gateway_config = OAuthGatewayConfiguration(config_data)

        _activity_logger.debug("✅ Gateway configuration loaded and validated")
        return gateway_config

    except (ValueError, KeyError) as config_error:
        _activity_logger.error("❌ Configuration validation error: %s", config_error)
        return None

    except (TypeError, AttributeError) as data_error:
        _activity_logger.error("❌ Configuration data error: %s", data_error)
        return None


# === STARTUP VALIDATION ===
# These checks run when the Lambda function starts

_activity_logger.info("🚀 CloudFlare OAuth Gateway initializing...")

try:
    # Validate environment on startup
    verify_environment_configuration()
    _activity_logger.info("✅ Environment validation passed")

    # Test configuration loading
    test_config = load_cached_gateway_configuration(secure_config_storage_path)
    if test_config:
        _activity_logger.info("✅ Configuration loading test passed")
    else:
        _activity_logger.warning("⚠️ Configuration loading test failed")

    _activity_logger.info("🎯 CloudFlare OAuth Gateway ready for requests")

except Exception as startup_error:
    _activity_logger.exception("💥 Gateway startup failed: %s", startup_error)
    raise


# =============================================================================
# USAGE INSTRUCTIONS AND DEPLOYMENT NOTES
# =============================================================================

# 📚 CLOUDFLARE OAUTH GATEWAY DEPLOYMENT GUIDE
#
# === WHAT THIS GATEWAY DOES ===
#
# This Lambda function serves as a secure bridge between Alexa and Home Assistant,
# specifically designed to handle OAuth authentication flows and add CloudFlare
# Access headers to requests. It solves two main problems:
#
# 1. 🔐 OAuth Authentication: Alexa needs a proper OAuth flow to authenticate
#    with Home Assistant, including authorization codes and token exchanges.
#
# 2. 🛡️ CloudFlare Access: CloudFlare's bot protection blocks Alexa requests,
#    so this gateway adds the required headers to bypass protection.
#
# For complete deployment instructions, see the project documentation.
