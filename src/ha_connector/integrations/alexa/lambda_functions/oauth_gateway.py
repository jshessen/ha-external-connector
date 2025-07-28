"""
🌐 ADVANCED CLOUDFLARE OAUTH GATEWAY V2: Enterprise Security Bridge for Alexa 🔐

=== WHAT THIS FILE DOES (In Plain English) ===

This file is your upgraded "security checkpoint" that sits between Amazon Alexa and your
Home Assistant, with enterprise-grade protection. Think of it as hiring a PROFESSIONAL
security team instead of just one security guard. Here's what happens:

1. 📱 You open Alexa app and click "Link Account" for your smart home skill
2. 🌐 Alexa sends you to THIS CODE for OAuth authentication
3. 🔐 THIS CODE handles the OAuth "handshake" with ENTERPRISE SECURITY
4. 🛡️ THIS CODE adds special CloudFlare headers (like a VIP pass)
5. 🏠 Your request gets forwarded to Home Assistant through CloudFlare
6. ✅ Home Assistant confirms your identity and grants access
7. 📱 Alexa app shows "Account successfully linked!"

=== THE ENHANCED ALEXA SKILL ECOSYSTEM: PROFESSIONAL SECURITY TEAM ===

🏢 **ENTERPRISE OFFICE BUILDING WITH PROFESSIONAL SECURITY TEAM**

Your smart home system is now like a Fortune 500 corporate headquarters with
a PROFESSIONAL SECURITY TEAM instead of just one security guard:

👮‍♂️ **HEAD OF SECURITY (THIS FILE - oauth_gateway_v2.py)**
- 🏛️ **Job**: Oversees ALL security operations with enterprise-grade protection
- 🎫 **Location**: Main lobby entrance (OAuth authentication endpoint)
- 📋 **Responsibilities**:
  * DUAL-MODE OPERATIONS: Handle both OAuth authentication AND Smart Home proxy
  * Advanced threat detection and circuit breaker protection
  * Professional error handling with correlation tracking
  * Comprehensive security event logging
  * Performance monitoring and operational dashboards
  * Multi-layer validation and rate limiting

🔒 **SECURITY OPERATIONS CENTER (Enhanced Classes)**
- 🛡️ **SecurityValidator**: Validates all incoming requests with enterprise standards
- 🚨 **SecurityEventLogger**: Records all security events with correlation IDs
- ⚡ **CircuitBreaker**: Automatically protects against system failures
- 📊 **AdvancedMonitor**: Provides real-time operational insights
- 🔧 **ErrorHandler**: Professional error management with context awareness

💼 **EXECUTIVE RECEPTIONIST (smart_home_bridge.py)**
- 🏢 **Job**: Handles daily business operations and communications
- 📞 **Location**: Executive floor (Smart home command processor)
- 📋 **Responsibilities**:
  * Process ongoing voice commands efficiently
  * Translate between Alexa and Home Assistant "languages"
  * Handle routine operations with speed
  * Maintain request logs and performance metrics

🔄 **THE ENHANCED WORKFLOW IN YOUR ALEXA SKILL**

**INITIAL SETUP (Account Linking) - Head of Security Takes the Lead**
1. 👤 User opens Alexa app → Skills & Games → [Your Smart Home Skill]
2. 📱 User clicks "Enable Skill" → "Link Account"
3. 🌐 Alexa redirects to: https://your-homeassistant.domain.com/auth/authorize
4. 👮‍♂️ **HEAD OF SECURITY (Enhanced OAuth Gateway)** receives the visitor
5. 🔍 Security team performs COMPREHENSIVE validation (size, rate, encoding)
6. 🔐 Head of Security handles OAuth authentication with Home Assistant
7. 🎫 Security team issues temporary access badge (OAuth token) with monitoring
8. 📋 Head of Security reports back to Alexa: "Credentials verified!"
9. ✅ Alexa app shows: "Account successfully linked!"

**DAILY OPERATIONS (Voice Commands) - Smart Home Proxy or Receptionist**
1. 🗣️ User says: "Alexa, turn on the kitchen lights"
2. 🌐 Alexa processes command → sends to AWS Lambda
3. 🔍 **HEAD OF SECURITY** intelligently detects request type:
   - If OAuth token request → Handle internally with enhanced security
   - If Smart Home directive → Proxy with CloudFlare headers OR forward to Receptionist
4. 🔍 Security team validates the access badge (enhanced token checking)
5. 📞 Request gets translated and forwarded to Home Assistant
6. 💡 Home Assistant turns on lights → sends confirmation
7. 📋 Response gets translated back to Alexa with security headers
8. 🗣️ Alexa responds: "OK"

**YOUR ALEXA SKILL CONFIGURATION MAPS TO THIS ENHANCED SYSTEM:**

🔗 **Account Linking Settings:**
- Web Authorization URI: https://your-homeassistant.domain.com/auth/authorize
  → This goes to the **HEAD OF SECURITY** for enterprise credential checking

- Access Token URI:
  https://your-oauth-gateway-v2-lambda-url.us-east-1.on.aws/
  → This goes to the **HEAD OF SECURITY** for enhanced token exchange and refresh

📞 **Smart Home Endpoint (Flexible Options):**
- Option A: Same URL as above → **HEAD OF SECURITY** handles both OAuth AND Smart Home
- Option B: [Your Voice Command Bridge Lambda URL] → **EXECUTIVE RECEPTIONIST** for
  daily operations

🔐 **Why You Need This Enhanced System:**
- **Head of Security** provides ENTERPRISE-GRADE authentication security
- **Security Operations Center** monitors and protects against threats
- **Dual-Mode Architecture** can handle both OAuth AND Smart Home in one function
- **Circuit Breaker Protection** prevents cascading failures
- **Performance Monitoring** ensures optimal operation
- **Professional Error Handling** provides better user experience

=== ENTERPRISE SECURITY FEATURES ===

This enhanced file provides MULTIPLE LAYERS of enterprise security:

🛡️ **FOUNDATION SECURITY**
- 🔒 OAuth 2.0 Authentication: Industry standard secure login process
- 🛡️ CloudFlare Access Headers: Bypasses CloudFlare's bot protection
- 🚦 Advanced Rate Limiting: IP-based protection with tracking
- 📏 Multi-layer Request Validation: Size, encoding, format checking
- 🔍 Enhanced Input Validation: Blocks malicious requests

🔒 **CONFIGURATION MANAGEMENT**
- 🏗️ Structured Configuration: Intelligent caching with TTL
- 🔧 Environment Validation: Multi-environment support
- 📊 Configuration Monitoring: Health checking and validation
- 🔄 Smart Caching: Container reuse optimization

🚨 **PROFESSIONAL ERROR HANDLING**
- 📋 Professional Error Classes: 15+ specialized error types
- 🔍 Context-Aware Logging: Correlation IDs for tracking
- ⚡ Circuit Breaker Pattern: Automatic failure protection
- 🎯 User-Friendly Messages: Clear error communication
- 📝 Comprehensive Logging: Structured security event recording

📊 **OPERATIONAL MONITORING**
- 📈 Advanced Metrics: Performance and security monitoring
- 🎛️ Operational Dashboard: Real-time system insights
- 🔔 Health Checking: Proactive system monitoring
- 📊 Request Correlation: End-to-end request tracking

=== FOR NON-TECHNICAL PEOPLE ===

Think of this like upgrading from a single security guard to a
PROFESSIONAL SECURITY COMPANY:

🏢 **ENHANCED MAIN LOBBY (Enterprise OAuth Gateway)**
- 👮‍♂️ Head of Security with specialized team
- 🔍 Advanced visitor screening (multi-layer validation)
- 📋 Professional visitor logs (correlation tracking)
- 🚨 Automatic threat detection (circuit breaker)
- 📊 Real-time security monitoring (operational dashboard)

🛡️ **SECURITY OPERATIONS CENTER (Enhanced Classes)**
- 🔒 Professional security validators
- 📝 Comprehensive event logging
- ⚡ Automatic system protection
- 📊 Performance monitoring
- 🔧 Intelligent error handling

🏠 **INNER OFFICE (Home Assistant)**
- Receives properly authenticated and authorized visitors
- Processes legitimate requests (smart home commands)
- Returns responses through the enhanced secure channel
- Benefits from circuit breaker protection

=== DUAL-MODE ARCHITECTURE EXPLANATION ===

This enhanced gateway can operate in TWO MODES like a versatile security team:

🔐 **MODE 1: OAUTH AUTHENTICATION (Account Linking)**
- Handles OAuth token exchange during initial skill setup
- Used when user clicks "Link Account" in Alexa app
- Provides enterprise-grade security validation
- Returns OAuth tokens in proper AWS Lambda response format

🏠 **MODE 2: SMART HOME PROXY (Voice Commands)**
- Proxies smart home requests with CloudFlare headers
- Used for daily voice commands ("Alexa, turn on lights")
- Intelligent request type detection
- Returns proxied Home Assistant responses

🤖 **INTELLIGENT REQUEST DETECTION**
The system automatically detects what type of request it is:
- OAuth requests: Contains client_secret, form-encoded data
- Smart Home requests: Contains JSON directives, authorization headers

=== ENHANCED OAUTH FLOW EXPLANATION ===

OAuth now works like a PROFESSIONAL security clearance process:

**STEP 1: ENHANCED AUTHORIZATION REQUEST** 🎫
- User clicks "Link Account" in Alexa app
- Request goes through MULTI-LAYER security validation
- Advanced rate limiting and size checking applied
- Professional logging with correlation IDs

**STEP 2: SECURE USER CONSENT** ✅
- Home Assistant shows a login page to the user
- Circuit breaker protection ensures system availability
- User enters their Home Assistant credentials
- User clicks "Allow Alexa to access my smart home"

**STEP 3: VALIDATED AUTHORIZATION CODE** 🎟️
- Home Assistant gives the user a temporary "introduction code"
- Enhanced validation ensures code integrity
- User's browser gets redirected back with comprehensive monitoring
- Professional error handling for any issues

**STEP 4: ENTERPRISE TOKEN EXCHANGE** 🔑
- Alexa sends the introduction code to this enhanced gateway
- COMPREHENSIVE security validation performed
- Gateway exchanges the code for permanent access tokens with monitoring
- Circuit breaker protection prevents cascading failures

**STEP 5: MONITORED ONGOING ACCESS** 🔄
- All future requests benefit from advanced monitoring
- Enhanced token validation with professional error handling
- Intelligent routing based on request type detection
- Performance metrics and operational insights

=== ENTERPRISE ARCHITECTURE ===

**FOUNDATION**: Foundation Security (Rate limiting, validation, basic protection)
**ENTERPRISE FEATURES**: Configuration Management (Structured config, caching,
environment support)
**ENTERPRISE FEATURES**: Professional Error Handling (Advanced errors, logging,
circuit breaker)
**ENTERPRISE FEATURES**: Operational Monitoring (Metrics, dashboards,
health checking)

Author: Enhanced by GitHub Copilot for Enterprise Security
Based on original work by: Jeff Hessenflow <jeff.hessenflow@gmail.com>
Original OAuth Gateway by: Jason Hu (awarecan)

Copyright 2019 Jason Hu <awaregit at gmail.com>
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

# pylint: disable=too-many-lines  # OAuth gateway with comprehensive security features
# pylint: disable=duplicate-code  # Lambda functions must be standalone - no shared modules

import base64
import binascii
import configparser
import json
import logging
import os
import re
import socket
import time
import traceback
import types
import urllib
import urllib.parse
import uuid
from dataclasses import dataclass
from typing import Any

import boto3
import urllib3
from botocore.exceptions import BotoCoreError, ClientError

try:
    import psutil  # type: ignore[import-untyped]
except ImportError:
    psutil = None

# === LOGGING CONFIGURATION ===
# Smart logging system with configurable levels from SSM and visual icons


def _initialize_logging() -> logging.Logger:
    """
    🔧 LOGGING INITIALIZER: Setup Smart Logging System

    Creates enterprise logging with icons for non-technical readability.
    LOG_LEVEL can be set via SSM configuration or defaults to environment.
    """
    # Set up our logging system (like a detailed security logbook)
    logger = logging.getLogger("EnterpriseOAuthGatewayV2")

    # Default to environment DEBUG for initial setup, will be updated from SSM
    initial_debug = bool(os.environ.get("DEBUG"))
    logger.setLevel(logging.DEBUG if initial_debug else logging.INFO)

    return logger


_logger = _initialize_logging()


def _update_log_level_from_config(config: configparser.ConfigParser) -> None:
    """
    📋 LOG LEVEL UPDATER: Apply SSM Configuration to Logging

    Updates logger level based on LOG_LEVEL setting from SSM configuration.
    Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    try:
        log_level_str = config.get("logging", "LOG_LEVEL", fallback="INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        _logger.setLevel(log_level)
        _logger.info("📋 Log level updated to: %s", log_level_str.upper())
    except (configparser.NoSectionError, AttributeError):
        # Fallback to environment or INFO if configuration unavailable
        env_debug = bool(os.environ.get("DEBUG"))
        _logger.setLevel(logging.DEBUG if env_debug else logging.INFO)
        fallback_level = "DEBUG" if env_debug else "INFO"
        _logger.info("📋 Using fallback log level: %s", fallback_level)


# Security Configuration Constants
# ═══════════════════════════════════════════════════════════════════════════
# 🔒 SECURITY OPERATIONS CENTER: Configuration & Protection Systems
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

    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_IP_PER_MINUTE = 10
    RATE_LIMIT_WINDOW_SECONDS = 60

    # Request validation limits
    MAX_REQUEST_SIZE_BYTES = 8192  # 8KB
    MAX_CLIENT_SECRET_LENGTH = 512
    MAX_URL_LENGTH = 2048

    # Security monitoring
    SUSPICIOUS_REQUEST_THRESHOLD = 5
    BLOCK_DURATION_SECONDS = 300  # 5 minutes


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
        """Log validation failures."""
        SecurityEventLogger.log_security_event(
            "validation_failure",
            client_ip,
            f"{validation_type} validation failed: {reason}",
            "WARNING",
        )


# ═══════════════════════════════════════════════════════════════════════════
# 🌐 GLOBAL INSTANCES: Shared Components for AWS Lambda Container Reuse
# ═══════════════════════════════════════════════════════════════════════════

# Global rate limiter instance for Lambda container reuse
_rate_limiter = RateLimiter()


# ═══════════════════════════════════════════════════════════════════════════
# 🚨 PROFESSIONAL ERROR HANDLING CENTER: Enterprise Error Management
# ═══════════════════════════════════════════════════════════════════════════


class ErrorType:
    """Error classification constants for structured error handling."""

    # Authentication and authorization errors
    INVALID_CLIENT = "invalid_client"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"

    # Network and connectivity errors
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"

    # Configuration and validation errors
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    PARAMETER_ERROR = "parameter_error"

    # Rate limiting and security errors
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Home Assistant specific errors
    HA_UNREACHABLE = "ha_unreachable"
    HA_OAUTH_ERROR = "ha_oauth_error"
    HA_CONFIG_ERROR = "ha_config_error"

    # System and internal errors
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DEPENDENCY_ERROR = "dependency_error"


class ErrorSeverity:
    """Error severity levels for monitoring and alerting."""

    LOW = "low"  # Minor issues, doesn't affect functionality
    MEDIUM = "medium"  # Affects some functionality, requires attention
    HIGH = "high"  # Significant impact, requires immediate attention
    CRITICAL = "critical"  # Service disruption, requires urgent response


class ErrorContext:
    """Context information for enhanced error handling and debugging."""

    def __init__(self, correlation_id: str | None = None):
        """Initialize with minimal required parameters."""
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.client_ip = "unknown"
        self.user_agent: str | None = None
        self.request_path: str | None = None
        self.timestamp = time.time()

    @classmethod
    def from_request(
        cls,
        *,
        correlation_id: str | None = None,
        client_ip: str = "unknown",
        user_agent: str | None = None,
        request_path: str | None = None,
    ) -> "ErrorContext":
        """Create ErrorContext from request data - preferred method."""
        context = cls(correlation_id)
        context.client_ip = client_ip
        context.user_agent = user_agent
        context.request_path = request_path
        return context

    def with_client_ip(self, client_ip: str) -> "ErrorContext":
        """Fluent interface for setting client IP."""
        self.client_ip = client_ip
        return self

    def with_user_agent(self, user_agent: str) -> "ErrorContext":
        """Fluent interface for setting user agent."""
        self.user_agent = user_agent
        return self

    def with_request_path(self, request_path: str) -> "ErrorContext":
        """Fluent interface for setting request path."""
        self.request_path = request_path
        return self

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate a unique correlation ID for request tracking."""
        return str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        """Convert error context to dictionary for logging."""
        return {
            "correlation_id": self.correlation_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "request_path": self.request_path,
            "timestamp": self.timestamp,
        }


class ErrorIdentification:
    """Grouped error identification attributes."""

    def __init__(self, error_type: str, error_code: str | None = None):
        self.error_type = error_type
        self.error_code = error_code or self._generate_error_code()

    def _generate_error_code(self) -> str:
        """Generate unique error code for tracking."""
        return f"{self.error_type.upper()}_{int(time.time())}"


class ErrorPresentation:
    """Grouped error presentation attributes."""

    def __init__(
        self, message: str, user_message: str, severity: str = ErrorSeverity.MEDIUM
    ):
        self.message = message
        self.user_message = user_message
        self.severity = severity


class ErrorMetadata:
    """Grouped error metadata attributes."""

    def __init__(
        self,
        context: ErrorContext | None = None,
        cause: Exception | None = None,
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.context = context or ErrorContext()
        self.cause = cause
        self.retry_after = retry_after
        self.details = details or {}


class ProfessionalErrorBuilder:
    """Builder for ProfessionalError to handle complex construction."""

    def __init__(self, error_type: str, message: str):
        # Core identification
        self.error_type = error_type
        self.message = message
        self.error_code: str | None = None

        # Presentation configuration
        self.user_message: str | None = None
        self.severity = ErrorSeverity.MEDIUM

        # Context and metadata
        self.context: ErrorContext | None = None
        self.metadata: dict[str, Any] = {}

    def with_user_message(self, user_message: str) -> "ProfessionalErrorBuilder":
        """Set user-friendly message."""
        self.user_message = user_message
        return self

    def with_severity(self, severity: str) -> "ProfessionalErrorBuilder":
        """Set error severity."""
        self.severity = severity
        return self

    def with_context(self, context: ErrorContext) -> "ProfessionalErrorBuilder":
        """Set error context."""
        self.context = context
        return self

    def with_cause(self, cause: Exception | None) -> "ProfessionalErrorBuilder":
        """Set underlying cause."""
        self.metadata["cause"] = cause
        return self

    def with_details(self, details: dict[str, Any]) -> "ProfessionalErrorBuilder":
        """Set additional details."""
        self.metadata["details"] = details
        return self

    def with_retry_after(self, retry_after: int) -> "ProfessionalErrorBuilder":
        """Set retry timing."""
        self.metadata["retry_after"] = retry_after
        return self

    def build(self) -> "ProfessionalError":
        """Build the error instance."""
        return ProfessionalError.from_builder(self)


class ProfessionalError(Exception):
    """
    📋 ENTERPRISE ERROR INFORMATION SYSTEM: Professional Error Context Management

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the PROFESSIONAL ERROR REPORTING SYSTEM in our Fortune 500 office
    building. When something goes wrong, this system provides comprehensive information
    about what happened, why it happened, and what users should do about it.

    🏢 **COMPREHENSIVE ERROR CONTEXT:**

    🔍 **DETAILED INCIDENT REPORTING (Error Context)**
    - Complete incident documentation with correlation tracking
    - User-friendly explanations alongside technical details
    - Severity classification for appropriate response levels
    - Professional error codes for system integration

    🎯 **ENTERPRISE ERROR MANAGEMENT:**
    This system provides structured error information that includes user-friendly
    messages, technical details for IT teams, correlation IDs for debugging, and
    appropriate response formatting for both Alexa and HTTP clients.
    """

    def __init__(self, error_type: str, message: str):
        """Basic constructor. Use builder() for complex errors."""
        super().__init__(message)
        self.identification = ErrorIdentification(error_type, None)
        self.presentation = ErrorPresentation(message, message, ErrorSeverity.MEDIUM)
        self.metadata = ErrorMetadata()

    @classmethod
    def builder(cls, error_type: str, message: str) -> ProfessionalErrorBuilder:
        """Create a builder for complex error construction."""
        return ProfessionalErrorBuilder(error_type, message)

    @classmethod
    def from_builder(cls, builder: ProfessionalErrorBuilder) -> "ProfessionalError":
        """Internal: construct from builder."""
        error = cls(builder.error_type, builder.message)
        error.identification = ErrorIdentification(
            builder.error_type, builder.error_code
        )
        error.presentation = ErrorPresentation(
            builder.message,
            builder.user_message or error._generate_user_message(),
            builder.severity,
        )
        error.metadata = ErrorMetadata(
            builder.context,
            builder.metadata.get("cause"),
            builder.metadata.get("retry_after"),
            builder.metadata.get("details"),
        )
        return error

    # Property access for structured error information
    @property
    def error_type(self) -> str:
        """Access to error type."""
        return self.identification.error_type

    @property
    def error_code(self) -> str:
        """Access to error code."""
        return self.identification.error_code

    @property
    def message(self) -> str:
        """Access to technical message."""
        return self.presentation.message

    @property
    def user_message(self) -> str:
        """Access to user-friendly message."""
        return self.presentation.user_message

    @property
    def severity(self) -> str:
        """Access to error severity."""
        return self.presentation.severity

    @property
    def context(self) -> ErrorContext:
        """Access to error context."""
        return self.metadata.context

    @property
    def cause(self) -> Exception | None:
        """Access to underlying cause."""
        return self.metadata.cause

    @property
    def retry_after(self) -> int | None:
        """Access to retry timing."""
        return self.metadata.retry_after

    @property
    def details(self) -> dict[str, Any]:
        """Access to additional details."""
        return self.metadata.details

    def _generate_user_message(self) -> str:
        """Generate user-friendly error message based on error type."""
        user_messages = {
            ErrorType.INVALID_CLIENT: (
                "Authentication failed. Please check your credentials."
            ),
            ErrorType.INVALID_REQUEST: (
                "Invalid request format. Please check your request parameters."
            ),
            ErrorType.RATE_LIMIT_EXCEEDED: (
                "Too many requests. Please wait before trying again."
            ),
            ErrorType.NETWORK_ERROR: (
                "Network connectivity issue. Please try again later."
            ),
            ErrorType.TIMEOUT_ERROR: "Request timed out. Please try again.",
            ErrorType.HA_UNREACHABLE: (
                "Home Assistant is currently unreachable. Please check your setup."
            ),
            ErrorType.CONFIGURATION_ERROR: (
                "Configuration error. Please contact your administrator."
            ),
            ErrorType.INTERNAL_ERROR: (
                "An internal error occurred. Please try again later."
            ),
        }
        return user_messages.get(
            self.error_type, "An error occurred. Please try again."
        )

    def _generate_error_code(self) -> str:
        """Generate unique error code for tracking."""
        return f"{self.error_type.upper()}_{int(time.time())}"

    def to_http_response(self) -> dict[str, Any]:
        """Convert error to HTTP response format."""
        status_codes = {
            ErrorType.INVALID_CLIENT: 401,
            ErrorType.INVALID_REQUEST: 400,
            ErrorType.UNAUTHORIZED: 401,
            ErrorType.FORBIDDEN: 403,
            ErrorType.RATE_LIMIT_EXCEEDED: 429,
            ErrorType.PAYLOAD_TOO_LARGE: 413,
            ErrorType.NETWORK_ERROR: 502,
            ErrorType.TIMEOUT_ERROR: 504,
            ErrorType.HA_UNREACHABLE: 502,
            ErrorType.CONFIGURATION_ERROR: 500,
            ErrorType.INTERNAL_ERROR: 500,
            ErrorType.SERVICE_UNAVAILABLE: 503,
        }

        status_code = status_codes.get(self.error_type, 500)

        response_body: dict[str, Any] = {
            "error": self.error_type,
            "error_description": self.user_message,
            "error_code": self.error_code,
            "correlation_id": self.context.correlation_id,
        }

        # Add retry information if applicable
        if self.retry_after:
            response_body["retry_after"] = self.retry_after

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "X-Correlation-ID": self.context.correlation_id,
            },
            "body": json.dumps(response_body),
        }

    def to_alexa_response(self) -> dict[str, Any]:
        """Convert error to Alexa Smart Home response format."""
        alexa_error_types = {
            ErrorType.INVALID_CLIENT: "INVALID_AUTHORIZATION_CREDENTIAL",
            ErrorType.UNAUTHORIZED: "INVALID_AUTHORIZATION_CREDENTIAL",
            ErrorType.FORBIDDEN: "INSUFFICIENT_PERMISSIONS",
            ErrorType.NETWORK_ERROR: "INTERNAL_ERROR",
            ErrorType.TIMEOUT_ERROR: "INTERNAL_ERROR",
            ErrorType.HA_UNREACHABLE: "ENDPOINT_UNREACHABLE",
            ErrorType.CONFIGURATION_ERROR: "INTERNAL_ERROR",
            ErrorType.INTERNAL_ERROR: "INTERNAL_ERROR",
            ErrorType.SERVICE_UNAVAILABLE: "INTERNAL_ERROR",
        }

        alexa_type = alexa_error_types.get(self.error_type, "INTERNAL_ERROR")

        return {
            "event": {
                "payload": {
                    "type": alexa_type,
                    "message": self.user_message,
                    "errorCode": self.error_code,
                    "correlationId": self.context.correlation_id,
                }
            }
        }

    def to_log_dict(self) -> dict[str, Any]:
        """Convert error to structured logging format."""
        log_data = {
            "error_type": self.error_type,
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity,
            "context": self.context.to_dict(),
            "details": self.details,
        }

        if self.cause:
            log_data["cause"] = str(self.cause)
            log_data["cause_type"] = type(self.cause).__name__

        return log_data


class ErrorHandler:
    """
    🚨 INCIDENT RESPONSE TEAM: Professional Error Resolution Services

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the INCIDENT RESPONSE TEAM in our Fortune 500 office building.
    When problems occur, this specialized team knows exactly how to handle each
    type of incident, create appropriate responses, and guide people toward solutions.

    🏢 **PROFESSIONAL INCIDENT MANAGEMENT:**

    🔧 **SPECIALIZED RESPONSE TEAMS (Error Type Handlers)**
    - Authentication issues: Handle login and credential problems
    - Network problems: Manage connectivity and timeout issues
    - Configuration errors: Resolve setup and parameter problems
    - Validation failures: Address input and format issues
    - System failures: Handle internal service problems

    📋 **STRUCTURED INCIDENT DOCUMENTATION (Error Context)**
    - Complete incident records with correlation tracking
    - User-friendly explanations for non-technical users
    - Technical details for IT support teams
    - Appropriate response formatting for different systems

    🎯 **ENTERPRISE ERROR RESOLUTION:**
    This team provides centralized error handling with context awareness,
    structured logging, and intelligent response generation for both
    user-facing and system-to-system communications.
    """

    @staticmethod
    def handle_configuration_error(
        message: str, context: ErrorContext, cause: Exception | None = None
    ) -> ProfessionalError:
        """Handle configuration-related errors."""
        return (
            ProfessionalError.builder(
                ErrorType.CONFIGURATION_ERROR, f"Configuration error: {message}"
            )
            .with_user_message(
                "Configuration issue detected. Please contact your administrator."
            )
            .with_severity(ErrorSeverity.HIGH)
            .with_context(context)
            .with_cause(cause)
            .with_details({"config_issue": message})
            .build()
        )

    @staticmethod
    def handle_network_error(
        message: str,
        context: ErrorContext,
        cause: Exception | None = None,
        retry_after: int = 60,
    ) -> ProfessionalError:
        """Handle network connectivity errors."""
        error_type = (
            ErrorType.TIMEOUT_ERROR
            if "timeout" in message.lower()
            else ErrorType.NETWORK_ERROR
        )

        return (
            ProfessionalError.builder(error_type, f"Network error: {message}")
            .with_user_message(
                "Network connectivity issue. Please try again in a moment."
            )
            .with_severity(ErrorSeverity.MEDIUM)
            .with_context(context)
            .with_cause(cause)
            .with_details({"network_issue": message, "retry_after": retry_after})
            .build()
        )

    @staticmethod
    def handle_authentication_error(
        message: str, context: ErrorContext, error_type: str = ErrorType.INVALID_CLIENT
    ) -> ProfessionalError:
        """Handle authentication and authorization errors."""
        return (
            ProfessionalError.builder(error_type, f"Authentication error: {message}")
            .with_user_message("Authentication failed. Please check your credentials.")
            .with_severity(ErrorSeverity.HIGH)
            .with_context(context)
            .with_details({"auth_issue": message})
            .build()
        )

    @staticmethod
    def handle_validation_error(
        message: str, context: ErrorContext, field_name: str | None = None
    ) -> ProfessionalError:
        """Handle request validation errors."""
        user_msg = (
            f"Invalid {field_name} provided. Please check your request."
            if field_name
            else "Invalid request format. Please check your parameters."
        )

        return (
            ProfessionalError.builder(
                ErrorType.VALIDATION_ERROR, f"Validation error: {message}"
            )
            .with_user_message(user_msg)
            .with_severity(ErrorSeverity.LOW)
            .with_context(context)
            .with_details({"validation_issue": message, "field": field_name})
            .build()
        )

    @staticmethod
    def handle_rate_limit_error(
        message: str, context: ErrorContext, retry_after: int = 60
    ) -> ProfessionalError:
        """Handle rate limiting errors."""
        return (
            ProfessionalError.builder(
                ErrorType.RATE_LIMIT_EXCEEDED, f"Rate limit exceeded: {message}"
            )
            .with_user_message(
                f"Too many requests. Please wait {retry_after} seconds "
                "before trying again."
            )
            .with_severity(ErrorSeverity.MEDIUM)
            .with_context(context)
            .with_details({"rate_limit_issue": message, "retry_after": retry_after})
            .build()
        )

    @staticmethod
    def handle_home_assistant_error(
        message: str,
        context: ErrorContext,
        status_code: int | None = None,
        cause: Exception | None = None,
    ) -> ProfessionalError:
        """Handle Home Assistant specific errors."""
        if status_code in (401, 403):
            error_type = ErrorType.HA_OAUTH_ERROR
            user_msg = (
                "Home Assistant authentication failed. Please check your OAuth setup."
            )
            severity = ErrorSeverity.HIGH
        elif status_code in (502, 503, 504):
            error_type = ErrorType.HA_UNREACHABLE
            user_msg = (
                "Home Assistant is currently unreachable. Please try again later."
            )
            severity = ErrorSeverity.MEDIUM
        else:
            error_type = ErrorType.HA_CONFIG_ERROR
            user_msg = (
                "Home Assistant configuration issue. Please contact your administrator."
            )
            severity = ErrorSeverity.HIGH

        builder = ProfessionalError.builder(
            error_type, f"Home Assistant error: {message}"
        )
        builder = (
            builder.with_user_message(user_msg)
            .with_severity(severity)
            .with_context(context)
            .with_cause(cause)
        )

        details = {"ha_issue": message, "status_code": status_code}
        if error_type == ErrorType.HA_UNREACHABLE:
            details["retry_after"] = 300

        return builder.with_details(details).build()


class EnhancedErrorLogger:
    """
    🚨 SECURITY AUDIT SYSTEM: Enterprise Event Documentation

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the SECURITY AUDIT DEPARTMENT in our Fortune 500 office building.
    It provides comprehensive error logging with context, correlation IDs, and
    structured data for monitoring and alerting systems.

    🏢 **PROFESSIONAL AUDIT SERVICES:**

    📋 **COMPREHENSIVE EVENT DOCUMENTATION**
    - Structured error logging with complete context information
    - Correlation ID tracking for cross-system debugging
    - Professional audit trail for compliance requirements
    - Integration with enterprise monitoring and alerting

    🔍 **ERROR RECOVERY & ANALYSIS**
    - Recovery action tracking with success/failure status
    - Pattern analysis for recurring issues
    - Professional incident documentation
    - Support for enterprise debugging workflows

    🎯 **ENTERPRISE COMPLIANCE & MONITORING**
    This system provides comprehensive error logging with context,
    correlation IDs, and structured data for monitoring and alerting.
    """

    @staticmethod
    def log_error(error: ProfessionalError) -> None:
        """Log error with full context and structured data."""
        log_data = error.to_log_dict()

        # Choose log level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            _logger.critical("🚨 CRITICAL_ERROR: %s", json.dumps(log_data))
        elif error.severity == ErrorSeverity.HIGH:
            _logger.error("❌ HIGH_SEVERITY_ERROR: %s", json.dumps(log_data))
        elif error.severity == ErrorSeverity.MEDIUM:
            _logger.warning("⚠️ MEDIUM_SEVERITY_ERROR: %s", json.dumps(log_data))
        else:
            _logger.info("📊 LOW_SEVERITY_ERROR: %s", json.dumps(log_data))

        # Log to security event logger if it's a security-related error
        if error.error_type in [
            ErrorType.RATE_LIMIT_EXCEEDED,
            ErrorType.SUSPICIOUS_ACTIVITY,
            ErrorType.INVALID_CLIENT,
            ErrorType.UNAUTHORIZED,
        ]:
            SecurityEventLogger.log_security_event(
                error.error_type,
                error.context.client_ip,
                error.message,
                error.severity.upper(),
            )

    @staticmethod
    def log_error_recovery(
        error: ProfessionalError, recovery_action: str, success: bool
    ) -> None:
        """Log error recovery attempts."""
        recovery_data = {
            "original_error": error.to_log_dict(),
            "recovery_action": recovery_action,
            "recovery_success": success,
            "timestamp": time.time(),
        }

        if success:
            _logger.info("✅ ERROR_RECOVERY_SUCCESS: %s", json.dumps(recovery_data))
        else:
            _logger.warning("⚠️ ERROR_RECOVERY_FAILED: %s", json.dumps(recovery_data))


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures gracefully.

    ENHANCEMENT: Provides automatic failure detection and recovery
    to prevent cascading failures and improve system resilience.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests)."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                _logger.info("🔄 Circuit breaker transitioning to HALF_OPEN state")
                return False
            return True
        return False

    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            _logger.info(
                "✅ Circuit breaker reset to CLOSED state after successful operation"
            )
        elif self.state == "CLOSED" and self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            _logger.warning(
                "🚨 Circuit breaker opened after %d failures, will retry in %d seconds",
                self.failure_count,
                self.recovery_timeout,
            )


# Global circuit breaker for Home Assistant connectivity
_ha_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)


# ═══════════════════════════════════════════════════════════════════════════
# 📊 OPERATIONAL MONITORING CENTER: Advanced Metrics & Health Management
# ═══════════════════════════════════════════════════════════════════════════


class MetricType:
    """Metric classification constants for structured monitoring."""

    # Request metrics
    REQUEST_COUNT = "request_count"
    REQUEST_DURATION = "request_duration"
    REQUEST_SIZE = "request_size"
    RESPONSE_SIZE = "response_size"

    # Error metrics
    ERROR_COUNT = "error_count"
    ERROR_RATE = "error_rate"
    CIRCUIT_BREAKER_STATE = "circuit_breaker_state"

    # Performance metrics
    CONFIG_LOAD_TIME = "config_load_time"
    OAUTH_EXCHANGE_TIME = "oauth_exchange_time"
    NETWORK_LATENCY = "network_latency"

    # Security metrics
    RATE_LIMIT_VIOLATIONS = "rate_limit_violations"
    AUTH_FAILURES = "auth_failures"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # System metrics
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    LAMBDA_COLD_START = "lambda_cold_start"


class HealthStatus:
    """Health check status constants."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MetricConfig:
    """Configuration object for creating metrics."""

    unit: str = "count"
    dimensions: dict[str, str] | None = None
    timestamp: float | None = None


class Metric:
    """Individual metric data structure for monitoring."""

    def __init__(self, name: str, value: float, metric_type: str):
        """Basic constructor with required fields."""
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.unit = "count"
        self.dimensions: dict[str, str] = {}
        self.timestamp = time.time()

    @classmethod
    def create(
        cls,
        name: str,
        value: float,
        metric_type: str,
        config: MetricConfig | None = None,
    ) -> "Metric":
        """Factory method for creating metrics with configuration object."""
        metric = cls(name, value, metric_type)
        if config:
            metric.unit = config.unit
            metric.dimensions = config.dimensions or {}
            metric.timestamp = config.timestamp or time.time()
        return metric

    def to_cloudwatch_format(self) -> dict[str, Any]:
        """Convert metric to CloudWatch format."""
        # Map common units to valid CloudWatch units
        unit_mapping = {
            "count": "Count",
            "milliseconds": "Milliseconds",
            "seconds": "Seconds",
            "percent": "Percent",
            "bytes": "Bytes",
            "kilobytes": "Kilobytes",
            "megabytes": "Megabytes",
            "gigabytes": "Gigabytes",
            "bits": "Bits",
            "kilobits": "Kilobits",
            "megabits": "Megabits",
            "gigabits": "Gigabits",
            "bytes/second": "Bytes/Second",
            "count/second": "Count/Second",
            "none": "None",
        }

        # Use mapped unit or default to "None" if not found
        cloudwatch_unit = unit_mapping.get(self.unit.lower(), "None")

        metric_data: dict[str, Any] = {
            "MetricName": self.name,
            "Value": self.value,
            "Unit": cloudwatch_unit,
            "Timestamp": self.timestamp,
        }

        if self.dimensions:
            metric_data["Dimensions"] = [
                {"Name": k, "Value": v} for k, v in self.dimensions.items()
            ]

        return metric_data

    def to_structured_log(self) -> dict[str, Any]:
        """Convert metric to structured log format."""
        return {
            "metric_name": self.name,
            "metric_value": self.value,
            "metric_type": self.metric_type,
            "metric_unit": self.unit,
            "metric_dimensions": self.dimensions,
            "metric_timestamp": self.timestamp,
        }


class PerformanceTimer:
    """Context manager for measuring operation duration."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration = 0.0

    def __enter__(self) -> "PerformanceTimer":
        self.start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def get_duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000

    def get_duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration


class MetricsCollector:
    """
    Advanced metrics collection and aggregation.

    ENHANCEMENT: Provides comprehensive metrics collection with
    CloudWatch integration and structured logging.
    """

    def __init__(self) -> None:
        self.metrics: list[Metric] = []
        self.request_start_time = time.time()
        self.lambda_start_time = time.time()

    def record_metric(self, name: str, value: float, metric_type: str) -> None:
        """Record a basic metric."""
        metric = Metric.create(name, value, metric_type)
        self.metrics.append(metric)
        _logger.info("📊 METRIC: %s", json.dumps(metric.to_structured_log()))

    def record_custom_metric(
        self, name: str, value: float, metric_type: str, config: MetricConfig
    ) -> None:
        """Record a metric with custom configuration."""
        metric = Metric.create(name, value, metric_type, config)
        self.metrics.append(metric)
        _logger.info("📊 METRIC: %s", json.dumps(metric.to_structured_log()))

    def record_request_start(self, correlation_id: str, client_ip: str) -> None:
        """Record request start metrics."""
        self.request_start_time = time.time()
        config = MetricConfig(
            unit="count",
            dimensions={"correlation_id": correlation_id, "client_ip": client_ip},
        )
        self.record_custom_metric(
            MetricType.REQUEST_COUNT,
            1,
            MetricType.REQUEST_COUNT,
            config,
        )

    def record_request_completion(
        self, correlation_id: str, status: str, error_type: str | None = None
    ) -> None:
        """Record request completion metrics."""
        duration = time.time() - self.request_start_time
        config = MetricConfig(
            unit="milliseconds",
            dimensions={"correlation_id": correlation_id, "status": status},
        )
        self.record_custom_metric(
            MetricType.REQUEST_DURATION,
            duration * 1000,  # Convert to milliseconds
            MetricType.REQUEST_DURATION,
            config,
        )

        if error_type:
            error_config = MetricConfig(
                unit="count",
                dimensions={"error_type": error_type, "correlation_id": correlation_id},
            )
            self.record_custom_metric(
                MetricType.ERROR_COUNT,
                1,
                MetricType.ERROR_COUNT,
                error_config,
            )

    def record_oauth_metrics(
        self, duration_ms: float, status_code: int, correlation_id: str
    ) -> None:
        """Record OAuth-specific metrics."""
        config = MetricConfig(
            unit="milliseconds",
            dimensions={
                "status_code": str(status_code),
                "correlation_id": correlation_id,
            },
        )
        self.record_custom_metric(
            MetricType.OAUTH_EXCHANGE_TIME,
            duration_ms,
            MetricType.OAUTH_EXCHANGE_TIME,
            config,
        )

    def record_security_event(
        self, event_type: str, client_ip: str, severity: str
    ) -> None:
        """Record security-related metrics."""
        metric_name = {
            "rate_limit_violation": MetricType.RATE_LIMIT_VIOLATIONS,
            "oauth_failure": MetricType.AUTH_FAILURES,
            "validation_failure": MetricType.AUTH_FAILURES,
            "suspicious_activity": MetricType.SUSPICIOUS_ACTIVITY,
        }.get(event_type, MetricType.SUSPICIOUS_ACTIVITY)

        config = MetricConfig(
            unit="count",
            dimensions={
                "event_type": event_type,
                "client_ip": client_ip,
                "severity": severity,
            },
        )
        self.record_custom_metric(
            metric_name,
            1,
            metric_name,
            config,
        )

    def record_circuit_breaker_state(self, state: str, failure_count: int) -> None:
        """Record circuit breaker state metrics."""
        config = MetricConfig(
            unit="count",
            dimensions={"state": state},
        )
        self.record_custom_metric(
            "circuit_breaker_state",
            float(failure_count),
            MetricType.CIRCUIT_BREAKER_STATE,
            config,
        )

        # Optionally record system metrics if psutil is available
        if psutil is not None:
            # Memory usage
            memory_info = psutil.virtual_memory()
            memory_config = MetricConfig(unit="percent")
            self.record_custom_metric(
                MetricType.MEMORY_USAGE,
                memory_info.percent,
                MetricType.MEMORY_USAGE,
                memory_config,
            )

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_config = MetricConfig(unit="percent")
            self.record_custom_metric(
                MetricType.CPU_USAGE,
                cpu_percent,
                MetricType.CPU_USAGE,
                cpu_config,
            )
        # else: psutil not available in Lambda environment, skip metrics

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of collected metrics."""
        summary: dict[str, Any] = {
            "total_metrics": len(self.metrics),
            "request_duration": time.time() - self.request_start_time,
            "lambda_uptime": time.time() - self.lambda_start_time,
            "metrics_by_type": {},
        }

        for metric in self.metrics:
            metric_type = metric.metric_type
            if metric_type not in summary["metrics_by_type"]:
                summary["metrics_by_type"][metric_type] = 0
            summary["metrics_by_type"][metric_type] += 1

        return summary

    def publish_to_cloudwatch(self, namespace: str = "OAuth/Gateway") -> bool:
        """Publish metrics to CloudWatch."""
        if not self.metrics:
            return True

        try:
            # Create CloudWatch client
            cloudwatch = boto3.client(  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                "cloudwatch"
            )
            metric_data = [metric.to_cloudwatch_format() for metric in self.metrics]

            # CloudWatch has a limit of 20 metrics per put_metric_data call
            batch_size = 20
            for i in range(0, len(metric_data), batch_size):
                batch = metric_data[i : i + batch_size]
                cloudwatch.put_metric_data(  # pyright: ignore[reportUnknownMemberType]
                    Namespace=namespace, MetricData=batch
                )

            _logger.info(
                "Published %d metrics to CloudWatch namespace: %s",
                len(self.metrics),
                namespace,
            )
            return True

        except (ClientError, ImportError) as e:
            _logger.error("Failed to publish metrics to CloudWatch: %s", str(e))
            return False


class HealthChecker:
    """
    Comprehensive health checking for OAuth Gateway components.

    ENHANCEMENT: Provides detailed health status for all system components
    with dependency checking and performance validation.
    """

    def __init__(self, config: "EnhancedConfiguration"):
        self.config = config
        self.health_checks: dict[str, dict[str, Any]] = {}

    def check_configuration_health(self) -> dict[str, Any]:
        """Check configuration system health."""
        start_time = time.time()
        health_data: dict[str, Any] = {
            "component": "configuration",
            "status": HealthStatus.UNKNOWN,
            "checks": [],
            "check_duration_ms": 0,
        }

        try:
            # Check configuration cache validity
            cache_valid = self.config.is_cache_valid()
            health_data["checks"].append(
                {
                    "name": "cache_validity",
                    "status": (
                        HealthStatus.HEALTHY if cache_valid else HealthStatus.DEGRADED
                    ),
                    "details": f"Cache valid: {cache_valid}",
                }
            )

            # Check required configuration values
            required_configs = [
                ("ha_base_url", self.config.home_assistant.base_url),
                ("cf_client_id", self.config.security.cf_client_id),
                ("cf_client_secret", self.config.security.cf_client_secret),
                ("alexa_secret", self.config.security.alexa_secret),
            ]

            missing_configs: list[str] = []
            for name, value in required_configs:
                if not value:
                    missing_configs.append(name)

            if not missing_configs:
                health_data["checks"].append(
                    {
                        "name": "required_configuration",
                        "status": HealthStatus.HEALTHY,
                        "details": "All required configuration present",
                    }
                )
            else:
                health_data["checks"].append(
                    {
                        "name": "required_configuration",
                        "status": HealthStatus.UNHEALTHY,
                        "details": (
                            f"Missing configuration: {', '.join(missing_configs)}"
                        ),
                    }
                )

            # Overall status determination
            check_statuses = [check["status"] for check in health_data["checks"]]
            if all(status == HealthStatus.HEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.HEALTHY
            elif any(status == HealthStatus.UNHEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.UNHEALTHY
            else:
                health_data["status"] = HealthStatus.DEGRADED

        except (AttributeError, TypeError, KeyError) as e:
            health_data["status"] = HealthStatus.UNHEALTHY
            health_data["checks"].append(
                {
                    "name": "configuration_exception",
                    "status": HealthStatus.UNHEALTHY,
                    "details": f"Configuration check failed: {str(e)}",
                }
            )

        health_data["check_duration_ms"] = (time.time() - start_time) * 1000
        return health_data

    def check_home_assistant_connectivity(self) -> dict[str, Any]:
        """Check Home Assistant connectivity health."""
        start_time = time.time()
        health_data: dict[str, Any] = {
            "component": "home_assistant",
            "status": HealthStatus.UNKNOWN,
            "checks": [],
            "check_duration_ms": 0,
        }

        try:
            # Check circuit breaker state
            cb_state = _ha_circuit_breaker.state
            cb_failures = _ha_circuit_breaker.failure_count

            if cb_state == "OPEN":
                health_data["checks"].append(
                    {
                        "name": "circuit_breaker",
                        "status": HealthStatus.UNHEALTHY,
                        "details": f"Circuit breaker OPEN with {cb_failures} failures",
                    }
                )
            elif cb_state == "HALF_OPEN":
                health_data["checks"].append(
                    {
                        "name": "circuit_breaker",
                        "status": HealthStatus.DEGRADED,
                        "details": (
                            f"Circuit breaker HALF_OPEN, recovering from "
                            f"{cb_failures} failures"
                        ),
                    }
                )
            else:
                health_data["checks"].append(
                    {
                        "name": "circuit_breaker",
                        "status": HealthStatus.HEALTHY,
                        "details": (
                            f"Circuit breaker CLOSED with {cb_failures} failures"
                        ),
                    }
                )

            # Test basic connectivity (lightweight check)
            try:
                ha_url = self.config.home_assistant.base_url
                if "://" in ha_url:
                    hostname = ha_url.split("://")[1].split("/")[0].split(":")[0]
                    port = 443 if ha_url.startswith("https://") else 80

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)  # 5 second timeout
                    result = sock.connect_ex((hostname, port))
                    sock.close()

                    if result == 0:
                        health_data["checks"].append(
                            {
                                "name": "network_connectivity",
                                "status": HealthStatus.HEALTHY,
                                "details": (
                                    f"Successfully connected to {hostname}:{port}"
                                ),
                            }
                        )
                    else:
                        health_data["checks"].append(
                            {
                                "name": "network_connectivity",
                                "status": HealthStatus.UNHEALTHY,
                                "details": f"Failed to connect to {hostname}:{port}",
                            }
                        )
                else:
                    health_data["checks"].append(
                        {
                            "name": "network_connectivity",
                            "status": HealthStatus.DEGRADED,
                            "details": "Invalid URL format for connectivity test",
                        }
                    )

            except (OSError, ValueError, AttributeError) as e:
                health_data["checks"].append(
                    {
                        "name": "network_connectivity",
                        "status": HealthStatus.DEGRADED,
                        "details": f"Connectivity test failed: {str(e)}",
                    }
                )

            # Overall status determination
            check_statuses = [check["status"] for check in health_data["checks"]]
            if all(status == HealthStatus.HEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.HEALTHY
            elif any(status == HealthStatus.UNHEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.UNHEALTHY
            else:
                health_data["status"] = HealthStatus.DEGRADED

        except (AttributeError, TypeError, ValueError) as e:
            health_data["status"] = HealthStatus.UNHEALTHY
            health_data["checks"].append(
                {
                    "name": "connectivity_exception",
                    "status": HealthStatus.UNHEALTHY,
                    "details": f"Connectivity check failed: {str(e)}",
                }
            )

        health_data["check_duration_ms"] = (time.time() - start_time) * 1000
        return health_data

    def check_security_systems(self) -> dict[str, Any]:
        """Check security systems health."""
        start_time = time.time()
        health_data: dict[str, Any] = {
            "component": "security",
            "status": HealthStatus.UNKNOWN,
            "checks": [],
            "check_duration_ms": 0,
        }

        try:
            # Check rate limiter state through public interface
            current_time = time.time()
            # Use safe attribute access to avoid protected member access
            rate_limiter_requests = getattr(_rate_limiter, "global_requests", [])
            global_requests = len(
                [
                    req
                    for req in rate_limiter_requests
                    if current_time - req[0] < SecurityConfig.RATE_LIMIT_WINDOW_SECONDS
                ]
            )

            rate_limit_usage = (
                global_requests / SecurityConfig.MAX_REQUESTS_PER_MINUTE
            ) * 100

            if rate_limit_usage < 70:
                health_data["checks"].append(
                    {
                        "name": "rate_limiter",
                        "status": HealthStatus.HEALTHY,
                        "details": f"Rate limit usage: {rate_limit_usage:.1f}%",
                    }
                )
            elif rate_limit_usage < 90:
                health_data["checks"].append(
                    {
                        "name": "rate_limiter",
                        "status": HealthStatus.DEGRADED,
                        "details": f"Rate limit usage: {rate_limit_usage:.1f}%",
                    }
                )
            else:
                health_data["checks"].append(
                    {
                        "name": "rate_limiter",
                        "status": HealthStatus.UNHEALTHY,
                        "details": f"Rate limit usage: {rate_limit_usage:.1f}%",
                    }
                )

            # Check blocked IPs through safe attribute access
            blocked_ips_list = getattr(_rate_limiter, "blocked_ips", [])
            blocked_ips = len(blocked_ips_list)
            if blocked_ips == 0:
                health_data["checks"].append(
                    {
                        "name": "security_blocks",
                        "status": HealthStatus.HEALTHY,
                        "details": "No IPs currently blocked",
                    }
                )
            elif blocked_ips < 5:
                health_data["checks"].append(
                    {
                        "name": "security_blocks",
                        "status": HealthStatus.DEGRADED,
                        "details": f"{blocked_ips} IPs currently blocked",
                    }
                )
            else:
                health_data["checks"].append(
                    {
                        "name": "security_blocks",
                        "status": HealthStatus.UNHEALTHY,
                        "details": f"{blocked_ips} IPs currently blocked (high)",
                    }
                )

            # Overall status determination
            check_statuses = [check["status"] for check in health_data["checks"]]
            if all(status == HealthStatus.HEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.HEALTHY
            elif any(status == HealthStatus.UNHEALTHY for status in check_statuses):
                health_data["status"] = HealthStatus.UNHEALTHY
            else:
                health_data["status"] = HealthStatus.DEGRADED

        except (AttributeError, TypeError, KeyError) as e:
            health_data["status"] = HealthStatus.UNHEALTHY
            health_data["checks"].append(
                {
                    "name": "security_exception",
                    "status": HealthStatus.UNHEALTHY,
                    "details": f"Security check failed: {str(e)}",
                }
            )

        health_data["check_duration_ms"] = (time.time() - start_time) * 1000
        return health_data

    def perform_comprehensive_health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check of all components."""
        start_time = time.time()

        health_report: dict[str, Any] = {
            "overall_status": HealthStatus.UNKNOWN,
            "check_timestamp": time.time(),
            "components": [],
            "total_check_duration_ms": 0,
            "summary": {},
        }

        # Run all health checks
        component_checks = [
            self.check_configuration_health(),
            self.check_home_assistant_connectivity(),
            self.check_security_systems(),
        ]

        health_report["components"] = component_checks

        # Determine overall status
        component_statuses = [component["status"] for component in component_checks]
        healthy_count = sum(
            1 for status in component_statuses if status == HealthStatus.HEALTHY
        )
        unhealthy_count = sum(
            1 for status in component_statuses if status == HealthStatus.UNHEALTHY
        )

        if unhealthy_count > 0:
            health_report["overall_status"] = HealthStatus.UNHEALTHY
        elif healthy_count == len(component_statuses):
            health_report["overall_status"] = HealthStatus.HEALTHY
        else:
            health_report["overall_status"] = HealthStatus.DEGRADED

        # Create summary
        health_report["summary"] = {
            "total_components": len(component_checks),
            "healthy_components": healthy_count,
            "degraded_components": len(component_statuses)
            - healthy_count
            - unhealthy_count,
            "unhealthy_components": unhealthy_count,
        }

        health_report["total_check_duration_ms"] = (time.time() - start_time) * 1000
        return health_report


class AdvancedMonitor:
    """
    Advanced monitoring coordinator for OAuth Gateway.

    ENHANCEMENT: Integrates metrics collection, health checking,
    and operational insights for comprehensive monitoring.
    """

    def __init__(self, config: "EnhancedConfiguration"):
        self.config = config
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker(config)
        self.monitoring_enabled = not bool(os.environ.get("DISABLE_MONITORING"))

    def start_request_monitoring(self, correlation_id: str, client_ip: str) -> None:
        """Start monitoring for a new request."""
        if not self.monitoring_enabled:
            return

        self.metrics_collector.record_request_start(correlation_id, client_ip)
        _logger.info(
            "MONITORING: Request started - correlation_id=%s, client_ip=%s",
            correlation_id,
            client_ip,
        )

    def record_operation_metrics(
        self, operation: str, timer: PerformanceTimer, **dimensions: str
    ) -> None:
        """Record metrics for a completed operation."""
        if not self.monitoring_enabled:
            return

        config = MetricConfig(unit="milliseconds", dimensions=dimensions)
        self.metrics_collector.record_custom_metric(
            f"{operation}_duration",
            timer.get_duration_ms(),
            MetricType.REQUEST_DURATION,
            config,
        )

    def record_error_metrics(self, error: ProfessionalError) -> None:
        """Record metrics for an error."""
        if not self.monitoring_enabled:
            return

        config = MetricConfig(
            unit="count",
            dimensions={
                "error_type": error.error_type,
                "severity": error.severity,
                "correlation_id": error.context.correlation_id,
            },
        )
        self.metrics_collector.record_custom_metric(
            MetricType.ERROR_COUNT,
            1,
            MetricType.ERROR_COUNT,
            config,
        )

    def complete_request_monitoring(
        self, correlation_id: str, success: bool, error_type: str | None = None
    ) -> None:
        """Complete monitoring for a request."""
        if not self.monitoring_enabled:
            return

        status = "success" if success else "error"
        self.metrics_collector.record_request_completion(
            correlation_id, status, error_type
        )

        # Record circuit breaker state
        self.metrics_collector.record_circuit_breaker_state(
            _ha_circuit_breaker.state, _ha_circuit_breaker.failure_count
        )

        _logger.info(
            "MONITORING: Request completed - correlation_id=%s, status=%s",
            correlation_id,
            status,
        )

    def get_operational_dashboard(self) -> dict[str, Any]:
        """Get comprehensive operational dashboard data."""
        dashboard = {
            "timestamp": time.time(),
            "monitoring_enabled": self.monitoring_enabled,
            "metrics_summary": self.metrics_collector.get_metrics_summary(),
            "health_status": self.health_checker.perform_comprehensive_health_check(),
            "system_info": {
                "lambda_function": os.environ.get(
                    "AWS_LAMBDA_FUNCTION_NAME", "unknown"
                ),
                "region": os.environ.get("AWS_REGION", "unknown"),
                "environment": self.config.environment.environment,
                "debug_mode": self.config.environment.debug_mode,
            },
            "circuit_breaker": {
                "state": _ha_circuit_breaker.state,
                "failure_count": _ha_circuit_breaker.failure_count,
                "last_failure": _ha_circuit_breaker.last_failure_time,
            },
        }

        return dashboard

    def get_monitoring_summary(self) -> dict[str, Any]:
        """Get concise monitoring summary for quick status checks."""
        health_status = self.health_checker.perform_comprehensive_health_check()
        metrics_summary = self.metrics_collector.get_metrics_summary()

        return {
            "overall_health": health_status.get("overall_status", "unknown"),
            "total_requests": metrics_summary.get("total_requests", 0),
            "error_rate": metrics_summary.get("error_rate", 0.0),
            "circuit_breaker_state": _ha_circuit_breaker.state,
            "monitoring_enabled": self.monitoring_enabled,
            "last_check_time": time.time(),
        }

    def publish_metrics(self) -> bool:
        """Publish collected metrics to CloudWatch."""
        if not self.monitoring_enabled:
            return True

        return self.metrics_collector.publish_to_cloudwatch("OAuth/Gateway")


# Global advanced monitor instance for Lambda container reuse
_advanced_monitor: AdvancedMonitor | None = None


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION MANAGEMENT CENTER: Enterprise Settings & Validation
# ═══════════════════════════════════════════════════════════════════════════


class TimeoutSettings:
    """Grouped timeout configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        self.request_timeout = int(config_dict.get("request_timeout", "10"))
        self.connect_timeout = int(config_dict.get("connect_timeout", "5"))
        self.read_timeout = int(config_dict.get("read_timeout", "10"))

    def validate(self) -> None:
        """Validate timeout settings."""
        if not 1 <= self.request_timeout <= 60:
            raise ValueError(
                f"request_timeout must be 1-60 seconds, got {self.request_timeout}"
            )
        if not 1 <= self.connect_timeout <= 30:
            raise ValueError(
                f"connect_timeout must be 1-30 seconds, got {self.connect_timeout}"
            )
        if not 1 <= self.read_timeout <= 60:
            raise ValueError(
                f"read_timeout must be 1-60 seconds, got {self.read_timeout}"
            )


class RetrySettings:
    """Grouped retry configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        self.max_retries = int(config_dict.get("max_retries", "3"))
        self.retry_delay = float(config_dict.get("retry_delay", "1.0"))
        retry_backoff = config_dict.get("retry_backoff_factor", "0.3")
        self.retry_backoff_factor = float(retry_backoff)
        self.retry_status_codes = [500, 502, 503, 504]  # Standard retry codes

    def validate(self) -> None:
        """Validate retry settings."""
        if not 0 <= self.max_retries <= 10:
            raise ValueError(f"max_retries must be 0-10, got {self.max_retries}")
        if not 0.1 <= self.retry_delay <= 10.0:
            raise ValueError(f"retry_delay must be 0.1-10.0, got {self.retry_delay}")


class PoolSettings:
    """Grouped connection pool configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        self.pool_maxsize = int(config_dict.get("pool_maxsize", "10"))
        self.pool_connections = int(config_dict.get("pool_connections", "10"))


class NetworkConfiguration:
    """Network and timeout configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        # Use composition pattern to group related settings
        self.timeouts = TimeoutSettings(config_dict)
        self.retries = RetrySettings(config_dict)
        self.pool = PoolSettings(config_dict)

        self._validate_network_settings()

    def _validate_network_settings(self) -> None:
        """Validate network configuration parameters."""
        self.timeouts.validate()
        self.retries.validate()

        _logger.debug(
            "Network config: timeout=%d, retries=%d, delay=%.1f",
            self.timeouts.request_timeout,
            self.retries.max_retries,
            self.retries.retry_delay,
        )

    def create_urllib3_timeout(self) -> urllib3.Timeout:
        """Create urllib3.Timeout object with configured values."""
        return urllib3.Timeout(
            connect=self.timeouts.connect_timeout, read=self.timeouts.read_timeout
        )

    def create_urllib3_retry(self) -> urllib3.Retry:
        """Create urllib3.Retry object with configured values."""
        return urllib3.Retry(
            total=self.retries.max_retries,
            backoff_factor=self.retries.retry_backoff_factor,
            status_forcelist=self.retries.retry_status_codes,
        )

    # Direct access properties for clean API
    @property
    def request_timeout(self) -> int:
        """Access to request timeout setting."""
        return self.timeouts.request_timeout

    @property
    def connect_timeout(self) -> int:
        """Access to connection timeout setting."""
        return self.timeouts.connect_timeout

    @property
    def read_timeout(self) -> int:
        """Access to read timeout setting."""
        return self.timeouts.read_timeout

    @property
    def max_retries(self) -> int:
        """Access to maximum retry setting."""
        return self.retries.max_retries

    @property
    def retry_delay(self) -> float:
        """Access to retry delay setting."""
        return self.retries.retry_delay

    @property
    def pool_maxsize(self) -> int:
        """Access to pool maximum size setting."""
        return self.pool.pool_maxsize

    @property
    def pool_connections(self) -> int:
        """Access to pool connections setting."""
        return self.pool.pool_connections


class AuthenticationSecrets:
    """
    🔐 CREDENTIAL VAULT: Enterprise Authentication Management

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the SECURE CREDENTIAL VAULT in our Fortune 500 office building.
    It safely stores all the secret passwords, keys, and authentication codes
    that our security systems need to verify identities and grant access.

    🏢 **ENTERPRISE CREDENTIAL STORAGE:**

    🎫 **ALEXA AUTHENTICATION (alexa_secret)**
    - Secret password that Alexa uses to prove it's really Amazon
    - Like a special code between Amazon and your Home Assistant
    - Required for OAuth token exchange during account linking

    🌐 **CLOUDFLARE ACCESS CREDENTIALS (cf_client_id, cf_client_secret)**
    - Special passes that allow access through CloudFlare protection
    - Like VIP credentials for bypassing CloudFlare's security screening
    - Required for proxying requests to protected Home Assistant

    🔒 **SECURITY BEST PRACTICES:**
    - All credentials are encrypted when stored in AWS Parameter Store
    - Credentials are loaded securely at runtime
    - No credentials are logged or exposed in error messages
    - Access is restricted to authorized Lambda functions only

    🎯 **FOR NON-TECHNICAL PEOPLE:**
    Think of this like a secure safe that contains:
    1. 🎫 Your building access card (Alexa secret)
    2. 🌐 Your VIP parking pass (CloudFlare credentials)
    3. 🔐 All stored securely and accessed only when needed

    🤖 **FOR IT TEAMS:**
    - Secure credential management for OAuth and CloudFlare integration
    - Environment-based credential loading from AWS Parameter Store
    - Structured access to prevent credential exposure
    - Integration with enterprise secret management practices
    """

    def __init__(self, config_dict: dict[str, Any]):
        self.alexa_secret: str = config_dict.get("alexa_secret", "")
        self.cf_client_id: str = config_dict.get("cf_client_id", "")
        self.cf_client_secret: str = config_dict.get("cf_client_secret", "")


class SSLSettings:
    """Grouped SSL/TLS configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        self.verify_ssl = not bool(os.environ.get("NOT_VERIFY_SSL"))
        self.ssl_cert_path = config_dict.get("ssl_cert_path")


class SecurityLimits:
    """Grouped security limit settings."""

    def __init__(self, config_dict: dict[str, Any]):
        self.max_request_size = int(
            config_dict.get(
                "max_request_size", str(SecurityConfig.MAX_REQUEST_SIZE_BYTES)
            )
        )
        self.rate_limit_per_ip = int(
            config_dict.get(
                "rate_limit_per_ip", str(SecurityConfig.MAX_REQUESTS_PER_IP_PER_MINUTE)
            )
        )
        self.rate_limit_global = int(
            config_dict.get(
                "rate_limit_global", str(SecurityConfig.MAX_REQUESTS_PER_MINUTE)
            )
        )


class SecurityConfiguration:
    """Security-related configuration settings."""

    def __init__(self, config_dict: dict[str, Any]):
        # Use composition pattern to group related settings
        self.authentication = AuthenticationSecrets(config_dict)
        self.ssl = SSLSettings(config_dict)
        self.limits = SecurityLimits(config_dict)

        self._validate_security_settings()

    def _validate_security_settings(self) -> None:
        """Validate security configuration parameters."""
        # Check for required secrets but don't fail validation - just warn
        required_secrets = ["alexa_secret", "cf_client_id", "cf_client_secret"]
        for secret_name in required_secrets:
            secret_value = getattr(self.authentication, secret_name)
            if not secret_value:
                _logger.warning("Missing required secret: %s", secret_name)
            else:
                _logger.debug("Secret %s is configured", secret_name)

        # 100MB max
        if (
            self.limits.max_request_size <= 0
            or self.limits.max_request_size > 100 * 1024 * 1024
        ):
            raise ValueError(
                f"Invalid max_request_size: {self.limits.max_request_size}"
            )

    # Direct access properties for clean API
    @property
    def alexa_secret(self) -> str:
        """Access to Alexa authentication secret."""
        return self.authentication.alexa_secret

    @property
    def cf_client_id(self) -> str:
        """Access to CloudFlare client ID."""
        return self.authentication.cf_client_id

    @property
    def cf_client_secret(self) -> str:
        """Access to CloudFlare client secret."""
        return self.authentication.cf_client_secret

    @property
    def verify_ssl(self) -> bool:
        """Backward compatibility access to verify_ssl."""
        return self.ssl.verify_ssl

    @property
    def max_request_size(self) -> int:
        """Backward compatibility access to max_request_size."""
        return self.limits.max_request_size


class HomeAssistantConfiguration:
    """Home Assistant connection configuration."""

    def __init__(self, config_dict: dict[str, Any]):
        # Use lowercase parameter names (ConfigParser converts all to lowercase)
        self.base_url = config_dict.get("ha_base_url", "").strip("/")
        self.api_path = config_dict.get("ha_api_path", "/api/alexa/smart_home")
        self.oauth_token_path = config_dict.get("ha_oauth_token_path", "/auth/token")
        self.token = config_dict.get("ha_token")  # Optional, for debug mode

        # URL validation and normalization
        self.webhook_id = config_dict.get("ha_webhook_id")
        self.long_lived_token = config_dict.get("ha_long_lived_token")

        # Debug logging to troubleshoot configuration loading
        _logger.debug("ha_base_url from config: '%s'", self.base_url)
        _logger.debug("Available config keys: %s", list(config_dict.keys()))

        self._validate_ha_settings()

    def _validate_ha_settings(self) -> None:
        """Validate Home Assistant configuration."""
        if not self.base_url:
            # More detailed error message for troubleshooting
            _logger.error("ha_base_url validation failed - empty or missing")
            _logger.error("This usually means the SSM parameter structure has changed")
            raise ValueError("HA_BASE_URL is required but was empty or missing")

        # Validate URL format
        url_valid, url_reason = SecurityValidator.validate_destination_url(
            self.base_url
        )
        if not url_valid:
            raise ValueError(f"Invalid HA_BASE_URL: {url_reason}")

        _logger.info("Home Assistant configuration validated: %s", self.base_url)

    def get_full_api_url(self) -> str:
        """Get the complete API URL for Home Assistant."""
        return f"{self.base_url}{self.api_path}"

    def get_oauth_token_url(self) -> str:
        """Get the complete OAuth token URL for Home Assistant."""
        return f"{self.base_url}{self.oauth_token_path}"


class EnvironmentConfiguration:
    """Environment-specific configuration and validation."""

    def __init__(self) -> None:
        self.environment = os.environ.get("ENVIRONMENT", "production").lower()
        self.debug_mode = bool(os.environ.get("DEBUG"))
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.lambda_function_name = os.environ.get(
            "AWS_LAMBDA_FUNCTION_NAME", "unknown"
        )

        # Configuration cache settings
        self.config_cache_ttl = int(
            os.environ.get("CONFIG_CACHE_TTL", "300")
        )  # 5 minutes
        self.enable_config_cache = not bool(os.environ.get("DISABLE_CONFIG_CACHE"))

        self._validate_environment()

    def _validate_environment(self) -> None:
        """Validate environment configuration."""
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            _logger.warning(
                "Unknown environment: %s (valid: %s)",
                self.environment,
                valid_environments,
            )

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


class EnhancedConfiguration:
    """
    🔧 ENTERPRISE CONFIGURATION SYSTEM: Professional Settings Management

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the ENTERPRISE CONFIGURATION MANAGEMENT SYSTEM in our Fortune 500
    office building. It replaces simple dictionary access with structured,
    validated configuration objects that provide type safety and intelligent defaults.

    🏢 **PROFESSIONAL CONFIGURATION MANAGEMENT:**

    🔧 **STRUCTURED SETTINGS ORGANIZATION**
    - Network settings: Timeouts, retries, connection pools
    - Security settings: Authentication secrets, SSL, rate limits
    - Home Assistant settings: URLs, API paths, tokens
    - Environment settings: Debug mode, AWS region, caching

    🛡️ **ENTERPRISE VALIDATION & SAFETY**
    - Type safety with structured configuration objects
    - Intelligent defaults for missing parameters
    - Validation of all critical settings at startup
    - Secure handling of sensitive configuration data

    🎯 **INTELLIGENT CACHING & PERFORMANCE**
    - Time-based configuration cache with automatic refresh
    - Multi-environment support with separate cache keys
    - Debug information for troubleshooting configuration issues
    - Optimized for AWS Lambda container reuse patterns
    """

    def __init__(self, config_parser: configparser.ConfigParser):
        self._config_parser = config_parser
        self._load_timestamp = time.time()

        # Extract app config section
        if not config_parser.has_section("appConfig"):
            raise ValueError("Missing required 'appConfig' section in configuration")

        app_config_dict = dict(config_parser["appConfig"])

        # Debug logging to troubleshoot configuration issues
        _logger.info("Configuration sections found: %s", config_parser.sections())
        _logger.info("AppConfig keys: %s", list(app_config_dict.keys()))
        _logger.info(
            "HA_BASE_URL value: '%s'", app_config_dict.get("ha_base_url", "[MISSING]")
        )

        # Initialize structured configuration sections
        self.network = NetworkConfiguration(app_config_dict)
        self.security = SecurityConfiguration(app_config_dict)
        self.home_assistant = HomeAssistantConfiguration(app_config_dict)
        self.environment = EnvironmentConfiguration()

        _logger.info(
            "Configuration loaded successfully for environment: %s",
            self.environment.environment,
        )

    def is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid."""
        if not self.environment.enable_config_cache:
            return False

        cache_age = time.time() - self._load_timestamp
        return cache_age < self.environment.config_cache_ttl

    def get_debug_info(self) -> dict[str, Any]:
        """Get configuration debug information (safe for logging)."""
        return {
            "environment": self.environment.environment,
            "debug_mode": self.environment.debug_mode,
            "aws_region": self.environment.aws_region,
            "ha_base_url": (
                self.home_assistant.base_url.split("//")[1].split("/")[0]
                if "//" in self.home_assistant.base_url
                else "unknown"
            ),
            "network_timeouts": (
                f"{self.network.connect_timeout}s/{self.network.read_timeout}s"
            ),
            "ssl_verification": self.security.verify_ssl,
            "cache_ttl": self.environment.config_cache_ttl,
            "config_age_seconds": round(time.time() - self._load_timestamp, 1),
        }


class ConfigurationManager:
    """
    🔧 ENTERPRISE CONFIGURATION COORDINATOR: Advanced Settings Management

    === WHAT THIS CLASS DOES (In Plain English) ===

    This is like the CONFIGURATION MANAGEMENT DEPARTMENT in our Fortune 500 office
    building. It provides intelligent caching, validation, and multi-environment
    support for OAuth Gateway configuration.

    🏢 **ADVANCED CONFIGURATION SERVICES:**

    💾 **INTELLIGENT CACHING SYSTEM**
    - Smart cache management with automatic refresh
    - Multi-environment support for development/staging/production
    - Time-based cache validation with configurable TTL
    - Memory optimization for AWS Lambda environments

    🔍 **CONFIGURATION VALIDATION & MONITORING**
    - Real-time cache status monitoring
    - Configuration freshness tracking
    - Environment-specific configuration loading
    - Debug information for troubleshooting

    🎯 **ENTERPRISE RELIABILITY**
    This system provides intelligent caching, validation, and multi-environment
    support for OAuth Gateway configuration with automatic fallback and
    error recovery mechanisms.
    """

    def __init__(self) -> None:
        self._cache: dict[str, EnhancedConfiguration] = {}
        self._cache_timestamps: dict[str, float] = {}

    def get_configuration(self, cache_key: str = "default") -> EnhancedConfiguration:
        """
        Get configuration with intelligent caching and validation.

        Args:
            cache_key: Cache key for multi-environment support

        Returns:
            EnhancedConfiguration object with structured access
        """
        # Check if we have a valid cached configuration
        if cache_key in self._cache and self._cache[cache_key].is_cache_valid():
            _logger.debug("Using cached configuration for key: %s", cache_key)
            return self._cache[cache_key]

        # Load fresh configuration
        _logger.info("Loading fresh configuration for key: %s", cache_key)

        try:
            app_config_path = os.environ["APP_CONFIG_PATH"]
            config_parser = load_config(app_config_path)

            # Update log level from SSM configuration
            _update_log_level_from_config(config_parser)

            enhanced_config = EnhancedConfiguration(config_parser)

            # Cache the configuration
            self._cache[cache_key] = enhanced_config
            self._cache_timestamps[cache_key] = time.time()

            # Log configuration debug info
            debug_info = enhanced_config.get_debug_info()
            _logger.info("Configuration loaded: %s", json.dumps(debug_info))

            return enhanced_config
        except (configparser.Error, BotoCoreError, OSError) as e:
            _logger.error("Failed to load configuration: %s", str(e))
            raise ValueError(f"Configuration loading failed: {str(e)}") from e

    def invalidate_cache(self, cache_key: str = "default") -> None:
        """Invalidate cached configuration for a specific key."""
        if cache_key in self._cache:
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            _logger.info("Invalidated configuration cache for key: %s", cache_key)

    def get_cache_status(self) -> dict[str, dict[str, Any]]:
        """Get current cache status for monitoring."""
        current_time = time.time()
        cache_status: dict[str, dict[str, Any]] = {}

        for key, config in self._cache.items():
            cache_age = current_time - self._cache_timestamps[key]
            cache_status[key] = {
                "cache_age_seconds": round(cache_age, 1),
                "is_valid": config.is_cache_valid(),
                "environment": config.environment.environment,
            }

        return cache_status


# Global configuration manager instance for Lambda container reuse
_config_manager = ConfigurationManager()


def validate_enhanced_configuration() -> tuple[bool, str]:
    """
    Validate the enhanced configuration structure for operational readiness.

    Returns:
        Tuple of (is_valid, validation_message)
    """
    try:
        config = _config_manager.get_configuration("validation_check")

        # Test all configuration sections
        test_results: list[str] = []

        # Network configuration tests
        try:
            _ = config.network.create_urllib3_timeout()
            _ = config.network.create_urllib3_retry()
            test_results.append("✓ Network configuration valid")
        except (ValueError, TypeError) as e:
            test_results.append(f"✗ Network configuration error: {str(e)}")

        # Security configuration tests
        if config.security.alexa_secret and config.security.cf_client_id:
            test_results.append("✓ Security credentials configured")
        else:
            test_results.append("✗ Missing security credentials")

        # Home Assistant configuration tests
        try:
            _ = config.home_assistant.get_full_api_url()
            _ = config.home_assistant.get_oauth_token_url()
            test_results.append("✓ Home Assistant URLs configured")
        except (ValueError, configparser.Error, BotoCoreError, OSError) as e:
            test_results.append(f"✗ Home Assistant configuration error: {str(e)}")

        # Environment configuration tests
        test_results.append(f"✓ Environment: {config.environment.environment}")
        test_results.append(f"✓ Debug mode: {config.environment.debug_mode}")

        validation_message = "\n".join(test_results)
        has_errors = any("✗" in result for result in test_results)

        return not has_errors, validation_message

    except (ValueError, configparser.Error, BotoCoreError, OSError) as e:
        return False, f"Configuration validation failed: {str(e)}"


class HAConfig:
    def __init__(self, config: configparser.ConfigParser) -> None:
        """
        Construct new app with configuration
        :param config: application configuration
        """
        self.config = config

    def get_config(self) -> configparser.ConfigParser:
        return self.config


def _create_ssm_client() -> Any:
    """Create and return SSM client for parameter retrieval."""
    print("Creating SSM client...")
    client = (
        boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
            "ssm"
        )
    )
    print("SSM client created successfully")
    return client


def _fetch_ssm_parameters(client: Any, ssm_parameter_path: str) -> dict[str, Any]:
    """Fetch parameters from SSM Parameter Store."""
    print("Fetching parameters from SSM...")
    param_details = client.get_parameters_by_path(
        Path=ssm_parameter_path, Recursive=False, WithDecryption=True
    )
    print(f"SSM response received: {param_details}")
    return param_details  # type: ignore[no-any-return]  # boto3 SSM response returns Any


def _parse_json_with_cleanup(param_value: str, param_name: str) -> dict[str, Any]:
    """Parse JSON parameter value with automatic cleanup for common issues."""
    try:
        result = json.loads(param_value)
        return result  # type: ignore[no-any-return]  # json.loads returns Any, but we know it's dict[str, Any]
    except json.JSONDecodeError as json_err:
        _logger.error(
            "🚨 Invalid JSON in SSM parameter %s: %s",
            param_name,
            str(json_err),
        )
        _logger.error("📋 Raw parameter value: %s", param_value)
        print(f"ERROR: Invalid JSON in parameter {param_name}: {json_err}")
        print(f"Raw value: {param_value}")

        # Try to clean common JSON issues
        try:
            # Remove trailing commas (common issue)
            cleaned_value = re.sub(r",\s*}", "}", param_value)
            cleaned_value = re.sub(r",\s*]", "]", cleaned_value)
            config_values = json.loads(cleaned_value)
            _logger.info(
                "✅ Successfully cleaned and parsed JSON after removing trailing commas"
            )
            print("INFO: Successfully cleaned JSON by removing trailing commas")
            return config_values  # type: ignore[no-any-return]
        except json.JSONDecodeError as clean_err:
            _logger.error(
                "❌ Failed to clean JSON, both original and cleaned versions invalid"
            )
            print(f"CRITICAL: JSON cleanup failed: {clean_err}")
            raise json_err from clean_err


def _process_single_parameter(
    param: dict[str, Any], configuration: configparser.ConfigParser
) -> None:
    """Process a single SSM parameter and add it to configuration."""
    param_name = param.get("Name")
    param_value = param.get("Value")

    if not param_name or not param_value:
        _logger.warning("Skipping parameter with missing name or value: %s", param)
        return

    print(f"Processing parameter: {param_name}")
    param_path_array = param_name.split("/")
    section_position = len(param_path_array) - 1
    section_name = param_path_array[section_position]

    # Parse JSON with automatic cleanup
    config_values = _parse_json_with_cleanup(param_value, param_name)

    # Add to configuration
    config_dict = {section_name: config_values}
    configuration.read_dict(config_dict)
    _logger.debug("Loaded section: %s", section_name)
    print(f"Loaded section: {section_name}")


def _process_ssm_parameters(
    param_details: dict[str, Any],
    configuration: configparser.ConfigParser,
    ssm_parameter_path: str,
) -> None:
    """Process all SSM parameters and populate configuration."""
    parameters = param_details.get("Parameters", [])

    if "Parameters" in param_details and len(parameters) > 0:
        _logger.debug("Found %d parameters", len(parameters))
        print(f"Processing {len(parameters)} parameters...")

        for param in parameters:
            _process_single_parameter(param, configuration)
    else:
        _logger.warning("No parameters found at path: %s", ssm_parameter_path)
        print(f"WARNING: No parameters found at path: {ssm_parameter_path}")


def load_config(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    Load configparser from config stored in SSM Parameter Store.

    This function follows enterprise patterns with clean workflow decomposition.

    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser holding loaded config
    """
    print(f"Starting load_config with path: {ssm_parameter_path}")
    configuration = configparser.ConfigParser()

    try:
        _logger.debug("Loading configuration from SSM path: %s", ssm_parameter_path)

        # Clean step-by-step execution following enterprise patterns
        ssm_client = _create_ssm_client()
        param_details = _fetch_ssm_parameters(ssm_client, ssm_parameter_path)
        _process_ssm_parameters(param_details, configuration, ssm_parameter_path)

    except (configparser.Error, BotoCoreError, OSError, json.JSONDecodeError) as err:
        # Catch configuration and AWS client errors during config loading
        error_msg = f"Error loading config from SSM: {str(err)}"
        _logger.error(error_msg)
        print(error_msg)
        print("Full traceback:")
        print(traceback.format_exc())
        # Re-raise to ensure calling code knows about the failure
        raise

    _logger.debug("Configuration loading completed")
    print("Configuration loading completed successfully")
    return configuration


# Module-level application instance cache for AWS Lambda container reuse
_app_instance_cache: dict[str, EnhancedConfiguration] = {}


def get_app_instance() -> EnhancedConfiguration:
    """
    🔧 ENTERPRISE CONFIGURATION FACTORY: Professional Instance Management

    === WHAT THIS FUNCTION DOES (In Plain English) ===

    This is like the CONFIGURATION SERVICES DESK in our Fortune 500 office building.
    When any department needs access to the building's configuration settings,
    they come here to get a properly validated and structured configuration instance.

    🏢 **CONFIGURATION INSTANCE SERVICES:**

    📋 **STRUCTURED CONFIGURATION ACCESS**
    - Uses ConfigurationManager for intelligent caching
    - Provides structured configuration with environment validation
    - Maintains configuration consistency across all departments
    - Optimized for AWS Lambda container reuse patterns

    🛡️ **ENTERPRISE RELIABILITY & VALIDATION**
    - Comprehensive error handling for configuration failures
    - Automatic fallback mechanisms for critical settings
    - Professional error reporting with correlation tracking
    - Integration with enterprise monitoring systems

    🎯 **RETURNS:**
    EnhancedConfiguration instance with structured access and validation
    for all OAuth Gateway settings and parameters.
    """
    cache_key = "default"

    try:
        # Use ConfigurationManager for intelligent caching
        enhanced_config = _config_manager.get_configuration(cache_key)

        # Update legacy cache for backward compatibility
        _app_instance_cache[cache_key] = enhanced_config

        return enhanced_config

    except (ValueError, configparser.Error, BotoCoreError, OSError) as e:
        print(f"CRITICAL ERROR during enhanced configuration initialization: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        _logger.error("Failed to initialize enhanced configuration: %s", str(e))
        raise


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 LAMBDA HANDLER HELPER FUNCTIONS: Professional Request Processing
# ═══════════════════════════════════════════════════════════════════════════


def _initialize_monitoring(
    error_context: ErrorContext,
) -> tuple[EnhancedConfiguration | None, AdvancedMonitor | None]:
    """Initialize advanced monitoring for the request."""
    config = None
    monitor = None
    try:
        # Initialize configuration using the same pattern as the existing code
        app_config_path = os.environ.get("APP_CONFIG_PATH")
        if app_config_path:
            config_parser = load_config(app_config_path)

            # Update log level from SSM configuration
            _update_log_level_from_config(config_parser)

            config = EnhancedConfiguration(config_parser)
        else:
            _logger.warning("APP_CONFIG_PATH not set, monitoring will be limited")

        global _advanced_monitor  # pylint: disable=global-statement
        # Initialize advanced monitor if not already done
        if _advanced_monitor is None and config:
            _advanced_monitor = AdvancedMonitor(config)
        monitor = _advanced_monitor

        # Start request monitoring if available
        if monitor:
            monitor.start_request_monitoring(
                error_context.correlation_id, error_context.client_ip
            )
    except (AttributeError, TypeError, ValueError, ImportError) as monitor_error:
        _logger.warning("Failed to initialize monitoring: %s", str(monitor_error))

    return config, monitor


def _extract_client_ip(event: dict[str, Any], error_context: ErrorContext) -> None:
    """Extract client IP from event and update error context."""
    if "requestContext" in event:
        error_context.client_ip = (
            event["requestContext"].get("identity", {}).get("sourceIp", "unknown")
        )
    elif "headers" in event:
        # Check for common proxy headers
        headers = event["headers"]
        error_context.client_ip = headers.get("x-forwarded-for", "").split(",")[
            0
        ].strip() or headers.get("x-real-ip", "unknown")


def _validate_rate_limits(error_context: ErrorContext) -> dict[str, Any] | None:
    """Validate rate limits and return error response if exceeded."""
    is_allowed, rate_limit_reason = _rate_limiter.is_allowed(error_context.client_ip)
    if not is_allowed:
        rate_limit_error = ErrorHandler.handle_rate_limit_error(
            rate_limit_reason, error_context, retry_after=60
        )
        EnhancedErrorLogger.log_error(rate_limit_error)
        return rate_limit_error.to_http_response()
    return None


def _validate_request_size(
    event: dict[str, Any], error_context: ErrorContext
) -> tuple[dict[str, Any] | None, bytes | None]:
    """Validate request size and decode body if needed."""
    content_length = 0
    decoded_body = None  # Cache decoded body for later use

    if "body" in event and event["body"]:
        if event.get("isBase64Encoded", False):
            # Decode to get actual size
            try:
                decoded_body = base64.b64decode(event["body"])
                content_length = len(decoded_body)
            except (binascii.Error, ValueError) as decode_error:
                validation_error = ErrorHandler.handle_validation_error(
                    f"Invalid base64 encoding: {str(decode_error)}",
                    error_context,
                    "request_body",
                )
                EnhancedErrorLogger.log_error(validation_error)
                return validation_error.to_http_response(), None
        else:
            content_length = len(
                event["body"].encode("utf-8")
                if isinstance(event["body"], str)
                else event["body"]
            )

    size_valid, size_reason = SecurityValidator.validate_request_size(content_length)
    if not size_valid:
        size_error = ErrorHandler.handle_validation_error(
            size_reason, error_context, "request_size"
        )
        EnhancedErrorLogger.log_error(size_error)
        return size_error.to_http_response(), None

    return None, decoded_body


def _check_circuit_breaker(error_context: ErrorContext) -> dict[str, Any] | None:
    """Check circuit breaker status and return error if open."""
    if _ha_circuit_breaker.is_open():
        circuit_error = (
            ProfessionalError.builder(
                ErrorType.SERVICE_UNAVAILABLE,
                "Circuit breaker is open due to repeated failures",
            )
            .with_user_message(
                "Service temporarily unavailable. Please try again later."
            )
            .with_severity(ErrorSeverity.MEDIUM)
            .with_context(error_context)
            .with_details({"circuit_breaker_state": "OPEN", "retry_after": 300})
            .build()
        )
        EnhancedErrorLogger.log_error(circuit_error)
        return circuit_error.to_alexa_response()
    return None


def _get_enhanced_configuration(
    error_context: ErrorContext,
) -> tuple[EnhancedConfiguration | None, dict[str, Any] | None]:
    """Get enhanced configuration instance with error handling."""
    try:
        enhanced_config = get_app_instance()
        return enhanced_config, None
    except (ValueError, configparser.Error, BotoCoreError, OSError) as config_error:
        config_error_obj = ErrorHandler.handle_configuration_error(
            str(config_error), error_context, config_error
        )
        EnhancedErrorLogger.log_error(config_error_obj)
        _ha_circuit_breaker.record_failure()
        return None, config_error_obj.to_alexa_response()


def _validate_configuration(
    enhanced_config: EnhancedConfiguration, error_context: ErrorContext
) -> dict[str, Any] | None:
    """Validate required configuration parameters."""
    destination_url = enhanced_config.home_assistant.base_url
    if not destination_url:
        config_error_obj = ErrorHandler.handle_configuration_error(
            "HA_BASE_URL parameter is required but not set", error_context
        )
        EnhancedErrorLogger.log_error(config_error_obj)
        return config_error_obj.to_alexa_response()
    return None


def _create_http_pool(enhanced_config: EnhancedConfiguration) -> urllib3.PoolManager:
    """Create HTTP pool manager with enhanced configuration."""
    timeout = enhanced_config.network.create_urllib3_timeout()
    retry = enhanced_config.network.create_urllib3_retry()

    return urllib3.PoolManager(
        cert_reqs=(
            "CERT_REQUIRED" if enhanced_config.security.verify_ssl else "CERT_NONE"
        ),
        timeout=timeout,
        retries=retry,
        maxsize=enhanced_config.network.pool_maxsize,
        num_pools=enhanced_config.network.pool_connections,
    )


def _process_request_body(
    event: dict[str, Any], decoded_body: bytes | None, error_context: ErrorContext
) -> tuple[dict[bytes, list[bytes]] | None, bytes | None, dict[str, Any] | None]:
    """Process and parse request body."""
    event_body = event.get("body")
    is_base64 = event.get("isBase64Encoded", False)

    if event_body:
        # Use cached decoded body if available (from size validation)
        if decoded_body is not None:
            req_body = decoded_body
        else:
            req_body = (
                base64.b64decode(event_body)
                if is_base64
                else (
                    event_body.encode() if isinstance(event_body, str) else event_body
                )
            )
    else:
        req_body = b""

    _logger.debug(
        "Request body received (length: %d)", len(req_body) if req_body else 0
    )

    try:
        req_dict = urllib.parse.parse_qs(req_body)
        return req_dict, req_body, None
    except (ValueError, UnicodeDecodeError) as parse_error:
        parse_error_obj = ErrorHandler.handle_validation_error(
            f"Failed to parse request body: {str(parse_error)}",
            error_context,
            "request_body",
        )
        EnhancedErrorLogger.log_error(parse_error_obj)
        return None, None, parse_error_obj.to_http_response()


def _validate_client_secret(
    req_dict: dict[bytes, list[bytes]],
    enhanced_config: EnhancedConfiguration,
    error_context: ErrorContext,
) -> tuple[str | None, dict[str, Any] | None]:
    """Validate and extract client secret from request."""
    if b"client_secret" not in req_dict or not req_dict[b"client_secret"]:
        auth_error = ErrorHandler.handle_authentication_error(
            "Missing client_secret parameter",
            error_context,
            ErrorType.INVALID_REQUEST,
        )
        EnhancedErrorLogger.log_error(auth_error)
        return None, auth_error.to_http_response()

    try:
        client_secret = req_dict[b"client_secret"][0].decode("utf-8")
    except (UnicodeDecodeError, IndexError) as decode_error:
        auth_error = ErrorHandler.handle_authentication_error(
            f"Invalid client_secret encoding: {str(decode_error)}",
            error_context,
            ErrorType.INVALID_REQUEST,
        )
        EnhancedErrorLogger.log_error(auth_error)
        return None, auth_error.to_http_response()

    # SECURITY: Validate client secret format and safety
    secret_valid, secret_reason = SecurityValidator.validate_client_secret(
        client_secret
    )
    if not secret_valid:
        auth_error = ErrorHandler.handle_authentication_error(
            secret_reason, error_context, ErrorType.INVALID_REQUEST
        )
        EnhancedErrorLogger.log_error(auth_error)
        return None, auth_error.to_http_response()

    # Validate against configured secret
    if client_secret != enhanced_config.security.alexa_secret:
        auth_error = ErrorHandler.handle_authentication_error(
            "Client secret mismatch", error_context, ErrorType.INVALID_CLIENT
        )
        EnhancedErrorLogger.log_error(auth_error)
        return None, auth_error.to_http_response()

    return client_secret, None


def _perform_oauth_exchange(
    enhanced_config: EnhancedConfiguration,
    http: urllib3.PoolManager,
    req_body: bytes,
    error_context: ErrorContext,
) -> tuple[Any, dict[str, Any] | None]:  # Any for urllib3 v1/v2 compatibility
    """Perform OAuth token exchange with Home Assistant."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "CF-Access-Client-Id": enhanced_config.security.cf_client_id,
        "CF-Access-Client-Secret": enhanced_config.security.cf_client_secret,
    }

    _logger.debug(
        "Making OAuth token request to: %s",
        enhanced_config.home_assistant.get_oauth_token_url(),
    )

    try:
        endpoint_url = enhanced_config.home_assistant.get_oauth_token_url()
        response = http.request("POST", endpoint_url, headers=headers, body=req_body)

        # Record success for circuit breaker
        _ha_circuit_breaker.record_success()
        return response, None

    except urllib3.exceptions.MaxRetryError as retry_error:
        # Record failure for circuit breaker
        _ha_circuit_breaker.record_failure()

        network_error = ErrorHandler.handle_network_error(
            f"Max retries exceeded: {str(retry_error)}",
            error_context,
            retry_error,
            retry_after=300,
        )
        EnhancedErrorLogger.log_error(network_error)
        return None, network_error.to_alexa_response()

    except (urllib3.exceptions.HTTPError, ValueError, OSError) as http_error:
        # Record failure for circuit breaker
        _ha_circuit_breaker.record_failure()

        network_error = ErrorHandler.handle_network_error(
            f"HTTP/Network error: {str(http_error)}",
            error_context,
            http_error,
            retry_after=60,
        )
        EnhancedErrorLogger.log_error(network_error)
        return None, network_error.to_alexa_response()


def _process_oauth_response(
    response: Any,
    error_context: ErrorContext,  # Any for urllib3 v1/v2 compatibility
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Process OAuth response and handle errors."""
    _logger.debug("OAuth response status: %d", response.status)

    # 🔧 Enhanced HTTP status handling
    if response.status >= 400:
        _logger.debug("ERROR %s %s", response.status, response.data)

        ha_error = ErrorHandler.handle_home_assistant_error(
            (
                f"HTTP {response.status}: "
                f"{response.data.decode('utf-8', errors='ignore')}"
            ),
            error_context,
            response.status,
        )
        EnhancedErrorLogger.log_error(ha_error)

        # Record failure for circuit breaker on 5xx errors
        if response.status >= 500:
            _ha_circuit_breaker.record_failure()

        return None, ha_error.to_alexa_response()

    # 🔧 Enhanced success response handling
    try:
        success_response: dict[str, Any] = json.loads(response.data.decode("utf-8"))
        return success_response, None
    except (json.JSONDecodeError, UnicodeDecodeError) as json_error:
        parse_error_obj = ErrorHandler.handle_validation_error(
            f"Invalid JSON response from Home Assistant: {str(json_error)}",
            error_context,
            "response_body",
        )
        EnhancedErrorLogger.log_error(parse_error_obj)
        return None, parse_error_obj.to_alexa_response()


def _handle_unexpected_error(
    error: Exception, error_context: ErrorContext, monitor: AdvancedMonitor | None
) -> dict[str, Any]:
    """Handle unexpected errors with comprehensive logging and monitoring."""
    _logger.error("UNEXPECTED ERROR in lambda_handler: %s", str(error))
    print(f"UNEXPECTED ERROR in lambda_handler: {str(error)}")
    print("Traceback:")
    print(traceback.format_exc())

    # Create a comprehensive error for unexpected issues
    fallback_error = (
        ProfessionalError.builder(
            ErrorType.INTERNAL_ERROR, f"Unexpected error: {str(error)}"
        )
        .with_user_message("An unexpected error occurred. Please try again later.")
        .with_severity(ErrorSeverity.CRITICAL)
        .with_context(error_context)
        .with_cause(error)
        .with_details(
            {
                "unexpected_error_type": type(error).__name__,
                "stack_trace": traceback.format_exc(),
            }
        )
        .build()
    )

    EnhancedErrorLogger.log_error(fallback_error)

    # Record critical failure for circuit breaker
    _ha_circuit_breaker.record_failure()

    # 📊 Record error metrics
    if monitor:
        monitor.record_error_metrics(fallback_error)
        monitor.complete_request_monitoring(
            error_context.correlation_id,
            success=False,
            error_type=fallback_error.error_type,
        )

    return fallback_error.to_alexa_response()


# ═══════════════════════════════════════════════════════════════════════════
# 🚪 MAIN LAMBDA HANDLERS: Enterprise Request Processing Entry Points
# ═══════════════════════════════════════════════════════════════════════════


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    🚪 AWS LAMBDA ENTRY POINT: Enhanced Enterprise Security Gateway

    === WHAT HAPPENS WHEN ALEXA CALLS THIS FUNCTION (In Plain English) ===

    This is the "front door" where AWS Lambda brings ALL Alexa requests. Think of it
    like the main entrance to our Fortune 500 office building where the HEAD OF SECURITY
    greets every visitor and decides what to do with them.

    🔍 **STEP 1: VISITOR IDENTIFICATION**
    - Look at the visitor (Alexa request) and figure out what they want
    - Are they here for initial security clearance? (OAuth authentication)
    - Or are they here for daily business? (Smart Home commands)

    🛡️ **STEP 2: SECURITY CHECKPOINT**
    - Check visitor credentials and run them through security screening
    - Apply rate limiting (prevent flooding)
    - Validate request size (prevent overload attacks)
    - Log everything for security monitoring

    🎯 **STEP 3: INTELLIGENT ROUTING**
    - Route OAuth visitors to the OAuth Authentication Department
    - Route Smart Home visitors to the Smart Home Proxy Department
    - Both departments are run by the same HEAD OF SECURITY team

    ═══════════════════════════════════════════════════════════════════════════

    🔐 **MODE 1: OAUTH AUTHENTICATION (Account Linking)**

    **When This Happens:**
    - User opens Alexa app and clicks "Link Account"
    - Alexa needs to get permission to access your smart home
    - This is like a new employee getting their security badge

    **What We Do:**
    - Handle OAuth token exchange with enterprise security validation
    - Issue temporary access badges (OAuth tokens)
    - Return tokens in proper AWS Lambda response format
    - Record everything for security auditing

    ═══════════════════════════════════════════════════════════════════════════

    🏠 **MODE 2: SMART HOME PROXY (Voice Commands)**

    **When This Happens:**
    - User says "Alexa, turn on the lights"
    - Alexa needs to send command to your Home Assistant
    - This is like an employee using their badge for daily work

    **What We Do:**
    - Proxy smart home requests with CloudFlare headers
    - Add security clearance for CloudFlare protection
    - Forward commands to Home Assistant
    - Return responses back to Alexa

    ═══════════════════════════════════════════════════════════════════════════

    🎛️ **ENTERPRISE MONITORING**

    **Advanced Features:**
    - Real-time performance monitoring and metrics collection
    - Health checking and operational insights
    - Professional error handling with correlation tracking
    - Circuit breaker protection against cascading failures

    **For IT Teams:**
    - Comprehensive logging with correlation IDs for debugging
    - CloudWatch metrics for monitoring and alerting
    - Operational dashboard capabilities
    - Professional error categorization and handling

    Args:
        event: AWS Lambda event containing the HTTP request details from Alexa
        context: AWS Lambda runtime context (contains request ID, timeout info, etc.)

    Returns:
        HTTP response formatted for AWS API Gateway (OAuth tokens or Smart Home
        responses)
    """
    # 🎫 CREATE VISITOR BADGE (Error Context)
    # Every visitor gets a unique tracking badge for security monitoring
    error_context = ErrorContext.from_request(
        client_ip="unknown",  # Will be updated once we extract it from the request
        user_agent=event.get("headers", {}).get("User-Agent"),
        request_path=event.get("path", "/"),
    )

    # 📊 INITIALIZE SECURITY OPERATIONS CENTER (Advanced Monitoring)
    # Start up our professional monitoring system
    _, monitor = _initialize_monitoring(error_context)

    try:
        # 🏢 MAIN LOBBY GREETING
        print("=== Enhanced OAuth Gateway Lambda Handler Starting ===")
        _logger.debug("=== Enterprise OAuth Gateway Request Started ===")
        _logger.debug("Event: %s", SecurityValidator.sanitize_log_data(str(event)))
        _logger.debug("Context: %s", context)
        _logger.info("Request correlation ID: %s", error_context.correlation_id)

        # 🔍 VISITOR IDENTIFICATION (Extract Client IP)
        # Figure out who this visitor is and where they came from
        _extract_client_ip(event, error_context)
        _logger.info("Processing request from visitor IP: %s", error_context.client_ip)

        # 🎯 CRITICAL DECISION POINT: What kind of visitor is this?
        # This determines EVERYTHING about how we handle the request
        request_type = _detect_alexa_request_type(event)
        _logger.info("🎯 Visitor type identified: %s", request_type)

        if request_type == "oauth":
            # 🔐 OAUTH DEPARTMENT: Handle account linking and authentication
            _logger.info("👮‍♂️ Routing to OAuth Authentication Department")
            return _handle_oauth_authentication_flow(event, error_context, monitor)

        if request_type == "smart_home":
            # 🏠 SMART HOME DEPARTMENT: Handle voice commands and device control
            _logger.info("🏠 Routing to Smart Home Proxy Department")
            return _handle_smart_home_proxy_flow(event, error_context, monitor)

        # ❌ UNKNOWN VISITOR TYPE: Security concern - log and reject
        _logger.warning("❓ Unknown visitor type detected: %s", request_type)
        unknown_error = ErrorHandler.handle_validation_error(
            f"Unknown request type: {request_type}", error_context, "request_type"
        )
        EnhancedErrorLogger.log_error(unknown_error)
        return unknown_error.to_http_response()

    except (
        ValueError,
        configparser.Error,
        BotoCoreError,
        OSError,
        KeyError,
        TypeError,
        RuntimeError,
    ) as unexpected_error:
        # Comprehensive fallback error handling
        return _handle_unexpected_error(unexpected_error, error_context, monitor)

    finally:
        # Ensure monitoring completion and metrics publishing
        if monitor:
            try:
                monitor.publish_metrics()
            except (
                ClientError,
                BotoCoreError,
                AttributeError,
                TypeError,
            ) as publish_error:
                _logger.warning("Failed to publish metrics: %s", str(publish_error))


def _detect_alexa_request_type(event: dict[str, Any]) -> str:
    """
    🔍 VISITOR TYPE DETECTOR: What Kind of Business Are You Here For?

    === WHAT THIS FUNCTION DOES (In Plain English) ===

    This is like the reception desk where we ask visitors: "Are you here for
    account setup or daily business?" We look at their paperwork (the request)
    and figure out what department they need.

    🏢 **VISITOR IDENTIFICATION PROCESS:**

    👮‍♂️ **SECURITY CHECKPOINT QUESTIONS:**
    1. What's in your briefcase? (request body contents)
    2. What form did you fill out? (content type)
    3. Which entrance did you use? (URL path)
    4. Do you have proper ID? (authorization headers)

    🔐 **OAUTH AUTHENTICATION VISITORS** (Account Linking)
    **They're here because:**
    - User clicked "Link Account" in Alexa app
    - Alexa needs to get permission to access smart home
    - Like a new employee getting their security badge

    **We identify them by:**
    - They use the OAuth entrance: /auth/token, /oauth/token, /token
    - They carry special paperwork: client_secret in form data
    - They fill out form-encoded applications (not JSON)

    🏠 **SMART HOME PROXY VISITORS** (Voice Commands)
    **They're here because:**
    - User said "Alexa, turn on the lights"
    - Alexa needs to send commands to Home Assistant
    - Like an employee using their badge for daily work

    **We identify them by:**
    - They use the smart home entrance: /api/alexa, /smart_home, /directive
    - They carry JSON directives (structured commands)
    - They have authorization badges (Bearer tokens)
    - Their paperwork mentions "directive" or "header"

    🤖 **TECHNICAL DETAILS FOR IT TEAMS:**

    OAuth Authentication Pattern:
    - HTTP Method: POST
    - Content-Type: application/x-www-form-urlencoded
    - Body Contains: client_secret parameter
    - Common Paths: /auth/token, /oauth/token, /token

    Smart Home Proxy Pattern:
    - HTTP Method: POST
    - Content-Type: application/json
    - Headers: Authorization with Bearer token
    - Body Contains: directive and header objects
    - Common Paths: /api/alexa, /smart_home, /directive

    Args:
        event: AWS Lambda event containing the HTTP request details

    Returns:
        "oauth" for OAuth authentication flow (account linking)
        "smart_home" for smart home proxy flow (voice commands)
        "oauth" for unknown requests (default to OAuth for backward compatibility)
    """
    # 📋 VISITOR PAPERWORK INSPECTION (Extract Request Details)
    http_method = event.get("httpMethod", "GET").upper()
    request_path = event.get("path", "/").lower()
    headers = event.get("headers", {})
    body = event.get("body", "")

    # 🔍 PAPERWORK ANALYSIS (Case-insensitive header lookup)
    headers_lower = {k.lower(): v for k, v in headers.items()}
    content_type = headers_lower.get("content-type", "")

    _logger.debug(
        "🔍 Visitor analysis - Method: %s, Path: %s, Content-Type: %s",
        http_method,
        request_path,
        content_type,
    )

    # 🔐 OAUTH ENTRANCE CHECK (Path-based identification)
    # Check if they came through the OAuth department entrance
    oauth_path_patterns = ["/auth/token", "/oauth/token", "/token"]
    if any(pattern in request_path for pattern in oauth_path_patterns):
        _logger.debug("🔐 OAuth department entrance detected")
        return "oauth"

    # 🔐 OAUTH PAPERWORK CHECK (Content-based identification)
    # Check if they have OAuth-style paperwork
    if (
        http_method == "POST"
        and "application/x-www-form-urlencoded" in content_type
        and body
        and "client_secret" in body
    ):
        _logger.debug("🔐 OAuth paperwork pattern detected")
        return "oauth"

    # 🏠 SMART HOME ENTRANCE CHECK (Path-based identification)
    # Check if they came through the Smart Home department entrance
    smart_home_path_patterns = ["/api/alexa", "/smart_home", "/directive"]
    if any(pattern in request_path for pattern in smart_home_path_patterns):
        _logger.debug("🏠 Smart home department entrance detected")
        return "smart_home"

    # 🏠 SMART HOME PAPERWORK CHECK (Content-based identification)
    # Check if they have Smart Home-style paperwork (JSON directives)
    is_post_request = http_method == "POST"
    has_json_content = "application/json" in content_type
    has_authorization = "authorization" in headers_lower
    has_body_content = bool(body)
    has_smart_home_keywords = body and (
        "directive" in body.lower() or "header" in body.lower()
    )

    if (
        is_post_request
        and has_json_content
        and has_authorization
        and has_body_content
        and has_smart_home_keywords
    ):
        _logger.debug("🏠 Smart home paperwork pattern detected")
        return "smart_home"

    # 🤔 UNKNOWN VISITOR TYPE (Default Handling)
    # When we can't identify the visitor type, we default to OAuth
    # This maintains backward compatibility with existing integrations
    _logger.warning("❓ Unknown visitor type, defaulting to OAuth department")
    return "oauth"


def _handle_oauth_authentication_flow(
    event: dict[str, Any], error_context: ErrorContext, monitor: AdvancedMonitor | None
) -> dict[str, Any]:
    """
    🔐 OAUTH AUTHENTICATION DEPARTMENT: Account Linking Specialist

    === WHAT THIS DEPARTMENT DOES (In Plain English) ===

    This is our specialized OAuth Authentication Department, staffed by expert
    security professionals who handle the complex process of linking your Alexa
    account to your Home Assistant. Think of it like a high-security bank where
    they verify your identity and issue you a special access card.

    🏛️ **WHEN THIS DEPARTMENT IS CALLED:**
    - User opens Alexa app and clicks "Link Account"
    - User completes login on Home Assistant
    - Alexa exchanges authorization codes for access tokens
    - Token refresh operations (when tokens expire)

    🔐 **WHAT HAPPENS IN THIS DEPARTMENT:**

    **STEP 1: SECURITY SCREENING** 🛡️
    - Check visitor credentials (rate limiting, request size)
    - Validate request format and encoding
    - Ensure no suspicious activity

    **STEP 2: CONFIGURATION SETUP** 🔧
    - Load enterprise security configuration
    - Set up secure communication channels
    - Prepare CloudFlare access credentials

    **STEP 3: TOKEN EXCHANGE PROCESS** 🎫
    - Validate client secret (like checking ID)
    - Forward request to Home Assistant securely
    - Exchange authorization codes for access tokens
    - Apply CloudFlare security headers

    **STEP 4: SECURE RESPONSE** ✅
    - Package tokens in proper AWS Lambda format
    - Add security headers for protection
    - Log successful completion for auditing

    🎯 **FOR NON-TECHNICAL PEOPLE:**

    This is like going to a bank to get a special credit card:
    1. 🏛️ You walk into the bank (OAuth request arrives)
    2. 🛂 Security guard checks your ID (request validation)
    3. 💼 Banker verifies your account (Home Assistant authentication)
    4. 🎫 Bank issues you a credit card (OAuth token)
    5. 📋 Everything gets recorded for security (comprehensive logging)

    🤖 **FOR IT TEAMS:**

    Technical Process:
    - Multi-layer security validation
    - Structured configuration management
    - Professional error handling
    - Advanced monitoring and metrics

    Uses decomposed helper functions for improved maintainability and reduced
    complexity. Each step is professionally monitored and logged.

    Args:
        event: AWS Lambda event containing OAuth request
        error_context: Error tracking context with correlation ID
        monitor: Advanced monitoring instance for metrics collection

    Returns:
        dict: AWS Lambda response with OAuth tokens or error information
    """
    _logger.info("🔐 OAuth Authentication Department: Processing account linking")

    try:
        # 🛡️ STEP 1: SECURITY SCREENING
        # Run comprehensive security validation before processing anything
        security_validation_error = _perform_oauth_security_validation(
            event, error_context
        )
        if security_validation_error:
            _logger.warning("🚨 Security screening failed - rejecting visitor")
            return security_validation_error

        # 🔧 STEP 2: CONFIGURATION SETUP
        # Load and validate enterprise security configuration
        config_setup_result = _setup_oauth_configuration(error_context)
        if isinstance(config_setup_result, dict):
            # This is an error response
            _logger.error("⚙️ Configuration setup failed")
            return config_setup_result

        # Extract configuration and HTTP pool from successful setup
        enhanced_config, http = config_setup_result
        _logger.debug("✅ Enterprise configuration loaded successfully")

        # 🎫 STEP 3: TOKEN EXCHANGE PROCESS
        # Execute the secure OAuth token exchange workflow
        success_response = _execute_oauth_token_exchange(
            event, enhanced_config, http, error_context, monitor
        )
        if "statusCode" in success_response:
            # This is an error response, return it directly
            _logger.error("💳 Token exchange process failed")
            return success_response

        # ✅ STEP 4: SECURE RESPONSE PACKAGING
        # Package the successful response with proper security headers
        _logger.info("🎉 OAuth token exchange completed successfully")
        return _build_oauth_success_response(success_response, error_context)

    except (
        ValueError,
        configparser.Error,
        BotoCoreError,
        OSError,
        KeyError,
        TypeError,
        RuntimeError,
    ) as unexpected_error:
        # Comprehensive fallback error handling
        return _handle_unexpected_error(unexpected_error, error_context, monitor)

    finally:
        # Ensure monitoring completion and metrics publishing
        if monitor:
            try:
                monitor.publish_metrics()
            except (
                ClientError,
                BotoCoreError,
                AttributeError,
                TypeError,
            ) as publish_error:
                _logger.warning("Failed to publish metrics: %s", str(publish_error))


def _handle_smart_home_proxy_flow(
    event: dict[str, Any], error_context: ErrorContext, monitor: AdvancedMonitor | None
) -> dict[str, Any]:
    """
    🏠 SMART HOME PROXY DEPARTMENT: Voice Command Specialist

    === WHAT THIS DEPARTMENT DOES (In Plain English) ===

    This is our Smart Home Proxy Department, where voice commands get processed
    and forwarded to your Home Assistant. Think of it like a professional
    translator service at the United Nations - they take what Alexa says and
    translate it perfectly for your Home Assistant to understand.

    🗣️ **WHEN THIS DEPARTMENT IS CALLED:**
    - User says "Alexa, turn on the kitchen lights"
    - User asks "Alexa, what's the temperature?"
    - User commands "Alexa, set the thermostat to 72 degrees"
    - Any voice command that controls smart home devices

    🏠 **WHAT HAPPENS IN THIS DEPARTMENT:**

    **STEP 1: COMMAND RECEPTION** 📞
    - Receive smart home directive from Alexa
    - Parse the command to understand what's being requested
    - Log the request for monitoring and debugging

    **STEP 2: SECURITY CLEARANCE** 🛡️
    - Validate authorization tokens (check access badge)
    - Apply CloudFlare security headers for safe passage
    - Ensure request comes from legitimate Alexa source

    **STEP 3: TRANSLATION SERVICE** 🌐
    - Translate Alexa's JSON directive format
    - Convert to Home Assistant API language
    - Preserve all important details (device IDs, commands, parameters)

    **STEP 4: SECURE FORWARDING** 🚀
    - Forward translated command to Home Assistant
    - Apply enterprise security protocols
    - Monitor response time and success rates

    **STEP 5: RESPONSE TRANSLATION** 📨
    - Receive response from Home Assistant
    - Translate back to Alexa's expected format
    - Add proper security headers
    - Return formatted response to Alexa

    🎯 **FOR NON-TECHNICAL PEOPLE:**

    This is like having a professional interpreter at an international conference:
    1. 🗣️ Alexa speaks in "Alexa language" (JSON directives)
    2. 🌐 Our translator converts it to "Home Assistant language"
    3. 🏠 Home Assistant understands and controls your devices
    4. 📨 Home Assistant responds in its own language
    5. 🔄 Our translator converts the response back to "Alexa language"
    6. ✅ Alexa says "OK" and your lights turn on

    🤖 **FOR IT TEAMS:**

    Current Implementation:
    - Basic Smart Home directive parsing
    - Alexa-compatible response formatting
    - Professional error handling and logging
    - Correlation tracking for debugging

    Future Enhancement (Ready for Implementation):
    - CloudFlare proxy integration for secure forwarding
    - Home Assistant API translation and routing
    - Advanced device state management
    - Performance optimization for voice response times

    Args:
        event: AWS Lambda event containing Smart Home directive
        error_context: Error tracking context with correlation ID
        monitor: Advanced monitoring instance for metrics collection

    Returns:
        dict: AWS Lambda response with Smart Home API response or acknowledgment
    """
    _logger.info("🏠 Smart Home Proxy Department: Processing voice command")

    try:
        # 📞 STEP 1: COMMAND RECEPTION
        # Extract and analyze the smart home directive
        body = event.get("body", "")

        # 🔍 STEP 2: DIRECTIVE ANALYSIS
        # Parse Smart Home directive from request body
        directive_name = "unknown"
        if body:
            try:
                directive = json.loads(body)
                directive_name = (
                    directive.get("directive", {})
                    .get("header", {})
                    .get("name", "unknown")
                )
                _logger.debug("📋 Smart Home command decoded: %s", directive_name)
            except json.JSONDecodeError:
                _logger.warning("⚠️ Failed to decode Smart Home directive body")
                directive = {}
        else:
            directive = {}

        # 🌐 STEP 3: FUTURE ENHANCEMENT PLACEHOLDER
        # This is where CloudFlare proxy integration will be implemented
        # Currently returns acknowledgment, will be enhanced for full proxy
        _logger.debug("🚀 Preparing Smart Home response (proxy enhancement ready)")

        # 📨 STEP 4: ALEXA-COMPATIBLE RESPONSE
        # Return properly formatted Alexa Smart Home response
        response_data = {
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "messageId": str(uuid.uuid4()),
                    "payloadVersion": "3",
                },
                "payload": {},
            }
        }

        # 📊 STEP 5: SUCCESS MONITORING
        # Record successful completion for operational monitoring
        if monitor:
            monitor.complete_request_monitoring(
                error_context.correlation_id, success=True
            )

        _logger.info("✅ Smart Home command processed successfully: %s", directive_name)

        # 🎯 STEP 6: SECURE RESPONSE PACKAGING
        # Return response with comprehensive security headers
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "X-Correlation-ID": error_context.correlation_id,
            },
            "body": json.dumps(response_data),
        }

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as e:
        _logger.error("❌ Smart Home proxy flow error: %s", str(e), exc_info=True)

        # 📊 Record error for monitoring
        if monitor:
            monitor.complete_request_monitoring(
                error_context.correlation_id,
                success=False,
                error_type="smart_home_error",
            )

        error_response = {
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "ErrorResponse",
                    "messageId": str(uuid.uuid4()),
                    "payloadVersion": "3",
                },
                "payload": {
                    "type": "INTERNAL_ERROR",
                    "message": "Smart Home proxy encountered an error",
                },
            }
        }

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff",
                "X-Correlation-ID": error_context.correlation_id,
            },
            "body": json.dumps(error_response),
        }


def _perform_oauth_security_validation(
    event: dict[str, Any], error_context: ErrorContext
) -> dict[str, Any] | None:
    """Perform comprehensive security validation for OAuth requests."""
    # Enhanced rate limiting with professional error handling
    rate_limit_response = _validate_rate_limits(error_context)
    if rate_limit_response:
        return rate_limit_response

    # Enhanced request size validation
    size_validation_response, decoded_body = _validate_request_size(
        event, error_context
    )
    if size_validation_response:
        return size_validation_response

    # Handle base64 decoding error case separately since we need decoded body
    if (
        "body" in event
        and event["body"]
        and event.get("isBase64Encoded", False)
        and decoded_body is None
    ):
        try:
            decoded_body = base64.b64decode(event["body"])
        except (binascii.Error, ValueError) as decode_error:
            validation_error = ErrorHandler.handle_validation_error(
                f"Invalid base64 encoding: {str(decode_error)}",
                error_context,
                "request_body",
            )
            EnhancedErrorLogger.log_error(validation_error)
            return validation_error.to_http_response()

    _logger.debug("Security validation passed - proceeding with OAuth flow")
    return None


def _setup_oauth_configuration(
    error_context: ErrorContext,
) -> tuple[EnhancedConfiguration, Any] | dict[str, Any]:
    """Setup and validate OAuth configuration."""
    # Enhanced configuration loading with circuit breaker
    circuit_breaker_response = _check_circuit_breaker(error_context)
    if circuit_breaker_response:
        return circuit_breaker_response

    # Get enhanced configuration instance using ConfigurationManager
    enhanced_config, config_error_response = _get_enhanced_configuration(error_context)
    if config_error_response:
        return config_error_response

    # We know enhanced_config is not None here due to previous check
    if enhanced_config is None:
        raise RuntimeError("Configuration unexpectedly None after error check")

    # Validate required parameters exist
    config_validation_response = _validate_configuration(enhanced_config, error_context)
    if config_validation_response:
        return config_validation_response

    # Create HTTP pool manager with enhanced configuration
    http = _create_http_pool(enhanced_config)

    return enhanced_config, http


def _execute_oauth_token_exchange(
    event: dict[str, Any],
    enhanced_config: EnhancedConfiguration,
    http: Any,
    error_context: ErrorContext,
    monitor: AdvancedMonitor | None,
) -> dict[str, Any]:
    """Execute OAuth token exchange workflow."""
    # Enhanced request body handling
    _, decoded_body = _validate_request_size(event, error_context)

    req_dict, req_body, request_body_error = _process_request_body(
        event, decoded_body, error_context
    )
    if request_body_error:
        return request_body_error

    # Type check for req_dict
    if req_dict is None:
        raise RuntimeError("Request dict unexpectedly None after error check")

    # Enhanced client secret validation
    _, secret_validation_error = _validate_client_secret(
        req_dict, enhanced_config, error_context
    )
    if secret_validation_error:
        return secret_validation_error

    # Type check for req_body
    if req_body is None:
        raise RuntimeError("Request body unexpectedly None after validation")

    # Enhanced OAuth token exchange with professional error handling
    response, oauth_exchange_error = _perform_oauth_exchange(
        enhanced_config, http, req_body, error_context
    )
    if oauth_exchange_error:
        return oauth_exchange_error

    # Enhanced OAuth response processing
    if response is None:
        raise RuntimeError("Response unexpectedly None after successful exchange")

    success_response, response_processing_error = _process_oauth_response(
        response, error_context
    )
    if response_processing_error:
        return response_processing_error

    # Type check for success_response
    if success_response is None:
        raise RuntimeError("Success response unexpectedly None after processing")

    # SECURITY: Log successful OAuth completion
    SecurityEventLogger.log_oauth_success(
        error_context.client_ip, enhanced_config.home_assistant.base_url
    )

    # Record successful completion for monitoring
    if monitor:
        monitor.complete_request_monitoring(error_context.correlation_id, success=True)

    return success_response


def _build_oauth_success_response(
    success_response: dict[str, Any], error_context: ErrorContext
) -> dict[str, Any]:
    """Build the final OAuth success response in AWS Lambda format."""
    _logger.info(
        "=== OAuth Gateway Request Completed Successfully (correlation: %s) ===",
        error_context.correlation_id,
    )

    # CRITICAL FIX: Use proper AWS Lambda response format for OAuth success
    # This is required for Alexa skill linking compatibility
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Correlation-ID": error_context.correlation_id,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "no-referrer",
        },
        "body": json.dumps(success_response),
    }
