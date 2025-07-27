"""
Utilities package for Home Assistant External Connector.

This package provides common utilities and helper functions used throughout
the Home Assistant External Connector project.
"""

from .helpers import (
    AWSError,
    HAConnectorError,
    HAConnectorLogger,
    HAEnvironmentError,
    PrerequisiteError,
    ValidationError,
    assert_never,
    aws_credentials_check,
    aws_region_check,
    check_lambda_function_exists,
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
    "AWSError",
    "HAConnectorError",
    "HAConnectorLogger",
    "HAEnvironmentError",
    "PrerequisiteError",
    "ValidationError",
    "assert_never",
    "aws_credentials_check",
    "aws_region_check",
    "check_lambda_function_exists",
    "error_exit",
    "extract_json_value",
    "logger",
    "process_json_secure",
    "require_commands",
    "require_env",
    "safe_exec",
    "safe_file_append",
    "safe_file_backup",
    "safe_file_write",
    "sanitize_env_var",
    "validate_input",
    "validate_json",
]
