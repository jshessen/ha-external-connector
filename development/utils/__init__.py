"""
Home Assistant External Connector Utilities.

Core utilities and helpers for the HA External Connector development environment.
"""

# Export core utilities
from .helpers import (
    AWSError,
    HAConnectorError,
    HAConnectorLogger,
    HAEnvironmentError,
    PrerequisiteError,
    ValidationError,
    assert_never,
    aws_region_check,
    error_exit,
    extract_json_value,
    logger,
    process_json_secure,
    require_commands,
    require_env,
    safe_exec,
    safe_file_append,
    safe_file_backup,
    safe_file_write,
    sanitize_env_var,
    validate_input,
    validate_json,
)

__all__ = [
    # Loggers
    "HAConnectorLogger",
    "logger",
    # Exceptions
    "HAConnectorError",
    "ValidationError",
    "AWSError",
    "HAEnvironmentError",
    "PrerequisiteError",
    # Utilities
    "assert_never",
    "safe_exec",
    "error_exit",
    "require_commands",
    "require_env",
    "safe_file_backup",
    "safe_file_write",
    "safe_file_append",
    "validate_json",
    "validate_input",
    "extract_json_value",
    "process_json_secure",
    "sanitize_env_var",
    "aws_region_check",
]
