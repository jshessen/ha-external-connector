---
description: "Security patterns and best practices for HA External Connector"
applyTo: "**/security/**/*.py,**/secrets/**/*.py,**/*security*.py"
---

# Security Patterns

## Secret Management

### Dynamic Secret Generation

```python
import secrets
from typing import Optional

def generate_secure_token(prefix: str = "", length: int = 32) -> str:
    """Generate cryptographically secure token."""
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}-{random_part}" if prefix else random_part

def generate_verification_token() -> str:
    """Generate verification token for external services."""
    return f"verify-{secrets.token_urlsafe(24)}"

class SecretManager:
    """Secure secret management for the application."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def get_secret(self, key: str, generate_if_missing: bool = False) -> Optional[str]:
        """Get secret with optional generation."""
        if key not in self._secrets and generate_if_missing:
            self._secrets[key] = generate_secure_token(length=32)
        return self._secrets.get(key)
```

### Prohibited Patterns (SECURITY VIOLATIONS)

```python
# ❌ NEVER: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # Security violation
SECRET_TOKEN = "hardcoded-secret"  # Security violation

# ❌ NEVER: Secrets in logs
logging.info(f"Using API key: {api_key}")  # Security violation

# ❌ NEVER: Secrets in error messages
raise ValueError(f"Invalid token: {secret_token}")  # Security violation
```

## Input Validation Patterns

### Command Injection Prevention

```python
import subprocess
import shlex
from typing import List

def safe_subprocess_execution(command: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Execute subprocess with security protections."""
    # Validate command components
    if not all(isinstance(arg, str) for arg in command):
        raise ValueError("All command arguments must be strings")

    # Use explicit argument list (never shell=True with user input)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Handle return codes explicitly
        )
        return result
    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"Command execution timeout: {e}")

def validate_file_path(file_path: str, allowed_directories: List[str]) -> bool:
    """Validate file path against directory traversal attacks."""
    import os.path

    # Resolve path to prevent directory traversal
    resolved_path = os.path.abspath(file_path)

    # Check if path is within allowed directories
    return any(
        resolved_path.startswith(os.path.abspath(allowed_dir))
        for allowed_dir in allowed_directories
    )
```

### Data Sanitization

```python
import re
from typing import Pattern

# Secure patterns for validation
SAFE_IDENTIFIER_PATTERN: Pattern[str] = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')
SAFE_FILENAME_PATTERN: Pattern[str] = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')

def sanitize_identifier(identifier: str) -> str:
    """Sanitize identifier for safe use in code generation."""
    if not SAFE_IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(f"Invalid identifier: {identifier}")
    return identifier

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not SAFE_FILENAME_PATTERN.match(filename):
        raise ValueError(f"Invalid filename: {filename}")
    if len(filename) > 255:
        raise ValueError("Filename too long")
    return filename
```

## Error Handling Security

### Secure Error Responses

```python
import logging
from typing import Dict, Any

class SecurityError(Exception):
    """Security-related error that requires special handling."""
    pass

def handle_security_error(error: Exception, context: str) -> Dict[str, Any]:
    """Handle security errors without exposing sensitive information."""
    # Log detailed error for security monitoring
    logging.error(
        f"Security error in {context}: {type(error).__name__}",
        extra={"context": context, "error_type": type(error).__name__}
    )

    # Return generic error response
    return {
        "status": "error",
        "message": "Access denied",
        "error_code": "SECURITY_ERROR"
    }

def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """Log security events for monitoring and alerting."""
    sanitized_details = {k: v for k, v in details.items() if k not in ["password", "token", "secret"]}
    logging.warning(
        f"Security event: {event_type}",
        extra={"event_type": event_type, "details": sanitized_details}
    )
```

## AWS Security Patterns

### IAM Policy Creation

```python
def create_least_privilege_policy(service_name: str, resources: List[str]) -> Dict[str, Any]:
    """Create IAM policy with least privilege principle."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    f"{service_name}:Get*",
                    f"{service_name}:List*",
                    f"{service_name}:Describe*"
                ],
                "Resource": resources
            }
        ]
    }

def validate_iam_policy(policy: Dict[str, Any]) -> bool:
    """Validate IAM policy for security best practices."""
    # Check for overly permissive policies
    for statement in policy.get("Statement", []):
        actions = statement.get("Action", [])
        if "*" in actions:
            logging.warning("Policy contains wildcard actions - review required")
            return False

        resources = statement.get("Resource", [])
        if "*" in resources:
            logging.warning("Policy contains wildcard resources - review required")
            return False

    return True
```

## Secure File Operations

### Temporary File Handling

```python
import tempfile
import os
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def secure_temp_directory() -> Iterator[str]:
    """Create secure temporary directory with proper cleanup."""
    temp_dir = tempfile.mkdtemp(prefix="ha-external-")
    try:
        # Set secure permissions (owner only)
        os.chmod(temp_dir, 0o700)
        yield temp_dir
    finally:
        # Secure cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def write_secure_file(file_path: str, content: str) -> None:
    """Write file with secure permissions."""
    # Create file with restrictive permissions
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Set secure permissions (owner read/write only)
    os.chmod(file_path, 0o600)
```

## Security Validation Requirements

- All user inputs must be validated and sanitized
- Never log sensitive information (secrets, tokens, passwords)
- Use type guards instead of assertions for security checks
- Implement proper timeout mechanisms for external calls
- Use secure random generation for all tokens and secrets
- Follow principle of least privilege for all AWS resources
- Validate all file operations against directory traversal
- Implement comprehensive error handling without information disclosure
