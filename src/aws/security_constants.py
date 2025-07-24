"""Common security headers and constants for AWS Lambda functions."""

# Standard security headers for HTTP responses
SECURITY_HEADERS: dict[str, str] = {
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
}

# Sensitive data keywords for security filtering
SENSITIVE_KEYWORDS = [
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
