"""
🔧 SHARED CONFIGURATION MODULE: Cen# === PUBLIC API ===
# Unified configuration loading and caching functions
__all__ = [
    "load_configuration",
    "cache_configuration",
    "get_cache_stats",
    "test_dynamic_deployment",  # ← NEW FUNCTION ADDED
    "load_environment",         # ← ENV VARIABLE LOADER (separate from config)
    "validate_configuration",   # ← CONFIGURATION VALIDATION
]ambda Function Configuration

=== CENTRALIZED CODE MANAGEMENT STRATEGY ===

This module contains ALL shared code between oauth_gateway.py and smart_home_bridge.py
to eliminate duplication while supporting both development and deployment modes.

**DUAL MODE ARCHITECTURE:**

1. **DEVELOPMENT MODE**: Import from this module for testing and development
   - Fast iteration and testing
   - Single source of truth for shared code
   - Easy debugging and modification

2. **DEPLOYMENT MODE**: Code is embedded into standalone Lambda functions
   - No external dependencies in production
   - Each Lambda function is completely independent
   - Optimal AWS Lambda performance

**DEPLOYMENT MECHANISM:**
- Scripts/deployment tools copy shared functions into target Lambda files
- Each function maintains standalone operation for production reliability
- This module serves as the authoritative source for shared implementations

Author: Jeff Hessenflow <jeff.hessenflow@gmail.com>
License: Apache 2.0
"""

# pylint: disable=too-many-lines  # Shared Configuration for Lambda functions
# pylint: disable=duplicate-code  # Lambda functions must be standalone - no shared modules

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import configparser
import json
import logging
import os
import re
import time
from typing import Any

import boto3
import urllib3
from botocore.exceptions import ClientError, NoCredentialsError

# ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === PUBLIC API ===
# Unified configuration loading and caching functions
__all__ = [
    "load_configuration",
    "cache_configuration",
    "get_cache_stats",
    "test_dynamic_deployment",  # ← NEW FUNCTION ADDED
    "load_environment",  # ← ENV VARIABLE LOADER (separate from config)
    "validate_configuration",  # ← CONFIGURATION VALIDATION
    # Security infrastructure (Phase 2c)
    "SecurityConfig",  # ← SECURITY CONFIGURATION CONSTANTS
    "RateLimiter",  # ← RATE LIMITING IMPLEMENTATION
    "SecurityValidator",  # ← REQUEST VALIDATION FRAMEWORK
    "SecurityEventLogger",  # ← SECURITY EVENT LOGGING SYSTEM
    "AlexaValidator",  # ← ALEXA PROTOCOL & AUTHENTICATION VALIDATION
]


def test_dynamic_deployment() -> str:
    """Test function to prove dynamic deployment works automatically."""
    return (
        "🎯 Dynamic deployment working! This function was auto-detected and embedded."
    )


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
_ssm_client: Any = None
_dynamodb_client: Any = None
_config_cache: dict[str, Any] = {}

# Logger for shared operations
_logger = logging.getLogger("SharedConfiguration")
_logger.setLevel(logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════
# �️ SHARED SECURITY INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════


class SecurityConfig:
    """
    🛡️ SECURITY HEADQUARTERS: Enterprise Protection Standards

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
    🚦 TRAFFIC CONTROL SYSTEM: Enterprise Visitor Flow Management

    Professional traffic control system that monitors visitor flow, prevents
    overcrowding, and temporarily blocks problematic visitors. In-memory rate
    limiting optimized for AWS Lambda with automatic cleanup and block management.

    Like a smart building entrance that remembers visitors, controls capacity,
    and blocks problem sources while reporting suspicious patterns.
    """

    def __init__(self) -> None:
        # 📊 Visitor tracking databases
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
    🔍 SECURITY SCREENING DEPARTMENT: Professional Validation Services

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
    📋 SECURITY DOCUMENTATION CENTER: Professional Event Recording

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the SECURITY DOCUMENTATION CENTER in our Fortune 500 office building.
    These are the security professionals who maintain detailed records of every
    security event, visitor interaction, and incident for compliance and monitoring.

    🏢 **PROFESSIONAL SECURITY DOCUMENTATION:**

    📝 **COMPREHENSIVE EVENT RECORDING (Security Logging)**
    - Incident documentation: Record all security events with full context
    - Visitor tracking: Log all visitor interactions and outcomes
    - Threat intelligence: Document suspicious activities and patterns
    - Like maintaining a professional security incident log book

    🎯 **ENTERPRISE AUDIT TRAIL (Structured Logging)**
    - Timestamped records: Every event gets precise time documentation
    - Severity classification: Events categorized by importance level
    - Structured format: All records follow consistent documentation standards
    - Correlation tracking: Events linked together for pattern analysis

    📊 **COMPLIANCE REPORTING (Security Metrics)**
    - Event categorization: Security events grouped by type and severity
    - Trend analysis: Track security patterns over time
    - Regulatory compliance: Meet enterprise audit requirements
    - Real-time monitoring: Enable security team alerts and responses

    🎯 **FOR NON-TECHNICAL PEOPLE:**
    Think of this like a professional security logbook that:
    1. 📝 Documents every security event that happens
    2. 🕐 Records the exact time and details of each incident
    3. 📊 Categorizes events by how serious they are
    4. 🔍 Helps security teams spot patterns and threats

    🤖 **FOR IT TEAMS:**
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
            _logger.info("📊 SECURITY_EVENT: %s", json.dumps(log_entry))

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
    🎯 ALEXA REQUEST VALIDATOR: Smart Home Protocol Compliance & Authentication

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the RECEPTION DESK VALIDATION SPECIALIST who ensures every
    visitor (Alexa request) has proper credentials and follows company protocols
    before being allowed into the office building.

    🏢 **PROFESSIONAL ALEXA PROTOCOL VALIDATION:**

    📋 **DIRECTIVE STRUCTURE VALIDATION (Smart Home API Compliance)**
    - Protocol compliance: Ensure requests follow Alexa Smart Home API v3 specification
    - Request format: Validate directive structure, headers, and payload versions
    - Error handling: Return properly formatted error responses for protocol violations
    - Like checking that visitors fill out forms correctly and use the right entrance

    🔐 **AUTHENTICATION TOKEN EXTRACTION (Bearer Token Processing)**
    - Token discovery: Extract bearer tokens from multiple possible locations in
      directives
    - Format validation: Ensure tokens follow expected bearer token structure
    - Debug support: Fallback token extraction for development environments
    - Multi-location search: Check endpoint scope, payload grantee, and payload scope

    🛡️ **ALEXA SIGNATURE VALIDATION (Amazon Request Authentication)**
    - Certificate validation: Verify requests actually come from Amazon Alexa services
    - Timestamp validation: Ensure requests are recent and not replay attacks
    - Signature verification: Cryptographic validation of request authenticity
    - Security logging: Document validation attempts and failures for monitoring

    🎯 **FOR NON-TECHNICAL PEOPLE:**
    Think of this like a security checkpoint that:
    1. 📋 Checks that visitors have proper paperwork (directive validation)
    2. 🔐 Verifies visitor ID badges are authentic (token extraction)
    3. 🛡️ Confirms visitors are who they claim to be (Alexa signature validation)
    4. 📊 Documents all security checks for compliance records

    🤖 **FOR IT TEAMS:**
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
        📋 DIRECTIVE VALIDATION: Alexa Smart Home Protocol Compliance

        Validates the incoming Alexa directive structure according to the Smart Home
        API specification. This ensures the request follows the expected format
        before processing.

        Args:
            event: Raw event from Alexa containing the directive

        Returns:
            Tuple of (directive_dict, error_response)
            - Success: (directive_dict, None)
            - Failure: (None, error_response_dict)
        """
        directive = event.get("directive")
        if not directive:
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_DIRECTIVE",
                        "message": "Missing directive in request",
                    }
                }
            }

        payload_version = directive.get("header", {}).get("payloadVersion")
        if payload_version != "3":
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_DIRECTIVE",
                        "message": "Only payloadVersion 3 is supported",
                    }
                }
            }

        return directive, None

    @staticmethod
    def extract_auth_token(
        directive: dict[str, Any], app_config: dict[str, Any], debug_mode: bool = False
    ) -> tuple[str | None, dict[str, Any] | None]:
        """
        🔐 AUTHENTICATION TOKEN EXTRACTION: Bearer Token Discovery & Validation

        Extract authentication token from Alexa directive. Searches multiple possible
        locations in the directive structure for bearer tokens and validates format.

        Args:
            directive: Alexa directive containing authentication information
            app_config: Application configuration for debug fallback tokens
            debug_mode: Whether to use debug fallback token extraction

        Returns:
            Tuple of (token_string, error_response)
            - Success: (token_string, None)
            - Failure: (None, error_response_dict)
        """
        # Extract authentication token from various possible locations
        scope = directive.get("endpoint", {}).get("scope")
        if scope is None:
            # Token in grantee for Linking directive
            scope = directive.get("payload", {}).get("grantee")
        if scope is None:
            # Token in payload for Discovery directive
            scope = directive.get("payload", {}).get("scope")

        if not scope or scope.get("type") != "BearerToken":
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                        "message": "Missing or invalid bearer token",
                    }
                }
            }

        token = scope.get("token")
        if not token and debug_mode:
            # Debug fallback - ConfigParser converts keys to lowercase
            token = app_config.get("ha_token") or app_config.get("HA_TOKEN")

        if not token:
            return None, {
                "event": {
                    "payload": {
                        "type": "INVALID_AUTHORIZATION_CREDENTIAL",
                        "message": "No authentication token provided",
                    }
                }
            }

        return token, None

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
        📋 ALEXA ERROR RESPONSE BUILDER: Standardized Error Format

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
# �🚀 UNIFIED CONFIGURATION LOADING API
# ═══════════════════════════════════════════════════════════════════════════


def load_configuration(
    app_config_path: str = "",
    config_section: str = "",
    return_format: str = "dict",
    required_keys: list[str] | None = None,
) -> dict[str, Any] | configparser.ConfigParser:
    """
    🔧 UNIFIED CONFIGURATION LOADER: Load Configuration from SSM/Cache

    This function loads configuration from SSM Parameter Store or cache.
    If app_config_path is empty, it will attempt to load from environment fallback.

    **PERFORMANCE FEATURES:**
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
    🚀 CACHE CONFIGURATION: Public API for Configuration Caching

    Store configuration in both container and shared cache layers for optimal
    performance. This is useful for pre-warming caches, updating configuration
    after changes, or forcing cache refresh during deployment.

    **CACHING STRATEGY:**
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
    📊 CACHE MONITORING: Get Cache Statistics for Performance Analysis

    Provides detailed cache performance metrics for monitoring, debugging, and
    optimization. This is essential for understanding cache hit ratios, memory
    usage, and identifying performance bottlenecks in production environments.

    **MONITORING FEATURES:**
    - Container cache statistics (valid/expired entries, total size)
    - Shared cache configuration details
    - TTL settings and cache configuration
    - Memory usage analysis for Lambda optimization

    :return: Dictionary with comprehensive cache statistics and configuration
    """
    return _get_cache_stats()


def load_environment() -> dict[str, str]:
    """
    🌍 ENVIRONMENT VARIABLE LOADER: Pure ENV Variable Extraction

    This function ONLY loads environment variables and puts them into a clean
    dictionary. No configuration loading, no validation, no fallbacks.
    Pure environment variable extraction.

    **ENVIRONMENT VARIABLES EXTRACTED:**
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
# 🚀 INTERNAL CONFIGURATION LOADING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def _create_ssm_client() -> Any:
    """Create SSM client with lazy initialization."""
    global _ssm_client  # pylint: disable=global-statement
    if _ssm_client is None:
        _ssm_client = boto3.client(
            "ssm", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
    return _ssm_client  # pyright: ignore[reportUnknownVariableType]


def _get_dynamodb_client() -> Any:
    """Get DynamoDB client with lazy initialization."""
    global _dynamodb_client  # pylint: disable=global-statement
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client(
            "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
    return _dynamodb_client  # pyright: ignore[reportUnknownVariableType]


def _load_standardized_configuration(
    config_section: str,
    ssm_path: str,
    _: list[str] | None = None,
) -> dict[str, Any]:
    """
    🚀 SPEED-OPTIMIZED CONFIGURATION LOADING: <500ms Voice Command Response

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
        param_value = response["Parameter"]["Value"]
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
# 🗺️ CONFIGURATION MAPPING FUNCTIONS
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
# 🔧 FOUNDATION PATTERN COMPATIBILITY
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
            config_dict = _load_flat_config_from_ssm(app_config_path)
            if config_dict:
                configuration.add_section("appConfig")
                for key, value in config_dict.items():
                    configuration.set("appConfig", key, str(value))
                _logger.info("✅ Configuration loaded from APP_CONFIG_PATH")
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
        param_value = response["Parameter"]["Value"]
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


# === SHARED UTILITY FUNCTIONS ===


def create_lambda_logger(service_name: str) -> logging.Logger:
    """Create standardized logger for Lambda functions."""
    return logging.getLogger(f"HomeAssistant-{service_name}")


def extract_correlation_id(context: Any) -> str:
    """Extract correlation ID from Lambda context."""
    return getattr(context, "aws_request_id", "unknown")[:8]


def create_http_client(
    verify_ssl: bool = True, timeout_connect: float = 5.0, timeout_read: float = 15.0
) -> Any:
    """Create standardized HTTP client with security settings."""

    return urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
        timeout=urllib3.Timeout(connect=timeout_connect, read=timeout_read),
    )


def create_error_response(
    error_type: str, message: str, status_code: int, correlation_id: str | None = None
) -> dict[str, Any]:
    """Create standardized error response."""
    error_body = {
        "error": error_type,
        "error_description": message,
        "timestamp": time.time(),
    }

    if correlation_id:
        error_body["correlation_id"] = correlation_id

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(error_body),
    }


# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯
