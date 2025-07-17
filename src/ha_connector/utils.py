"""
Common utilities for Home Assistant External Connector.

This module provides shared functionality including logging, error handling,
input validation, and AWS utilities that are used across all components.
"""

import json
import logging
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess
import re


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[0;34m',    # Blue
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[0;31m', # Red
        'SUCCESS': '\033[0;32m',  # Green
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}[{record.levelname}]{self.COLORS['RESET']}"
        
        return super().format(record)


class HAConnectorLogger:
    """Enhanced logging system for HA Connector."""
    
    def __init__(self, 
                 name: str = "ha_connector",
                 log_file: Optional[str] = None,
                 verbose: bool = False,
                 max_log_size: int = 10 * 1024 * 1024):  # 10MB
        
        self.logger = logging.getLogger(name)
        self.verbose = verbose
        self.log_file = log_file or os.getenv('LOG_FILE', '/tmp/ha-connector.log')
        self.max_log_size = max_log_size
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level based on verbose flag
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Create file handler
        self._setup_file_handler()
        
        # Set formatters
        console_format = ColoredFormatter('%(levelname)s %(message)s')
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(console_format)
        self.file_handler.setFormatter(file_format)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(self.file_handler)
    
    def _setup_file_handler(self):
        """Setup file handler with rotation."""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotate log if too large
        if log_path.exists() and log_path.stat().st_size > self.max_log_size:
            backup_path = log_path.with_suffix(f'.old')
            shutil.move(str(log_path), str(backup_path))
        
        self.file_handler = logging.FileHandler(self.log_file, mode='a')
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message (custom level)."""
        # Create a custom success record
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, __file__, 0, message, (), None
        )
        record.levelname = 'SUCCESS'
        self.logger.handle(record)


# Global logger instance
logger = HAConnectorLogger(
    verbose=os.getenv('VERBOSE', 'false').lower() == 'true'
)


class HAConnectorError(Exception):
    """Base exception for HA Connector errors."""
    
    def __init__(self, message: str, context: Optional[str] = None, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.context = context
        self.exit_code = exit_code


class PrerequisiteError(HAConnectorError):
    """Error for missing prerequisites."""
    pass


class HAEnvironmentError(HAConnectorError):
    """Error for environment configuration issues."""
    pass


class ValidationError(HAConnectorError):
    """Error for input validation failures."""
    pass


def error_exit(message: str, exit_code: int = 1, context: Optional[str] = None):
    """Exit with error message and optional context."""
    logger.error(message)
    if context:
        logger.error(f"Context: {context}")
    
    logger.error(f"Operation failed. Check {logger.log_file} for details.")
    
    # Call cleanup if it exists
    if hasattr(sys.modules[__name__], 'cleanup'):
        try:
            cleanup()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    sys.exit(exit_code)


def require_commands(*commands: str) -> None:
    """Validate that required commands are available."""
    missing_commands = []
    
    for cmd in commands:
        if not shutil.which(cmd):
            missing_commands.append(cmd)
    
    if missing_commands:
        raise PrerequisiteError(
            f"Missing required commands: {', '.join(missing_commands)}",
            context="prerequisite_check"
        )


def require_env(*variables: str) -> None:
    """Validate that required environment variables are set."""
    missing_vars = []
    
    for var in variables:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise HAEnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}",
            context="environment_check"
        )


def safe_exec(description: str, 
              cmd: List[str], 
              dry_run: bool = None,
              check: bool = True) -> subprocess.CompletedProcess:
    """Execute command safely with dry-run support."""
    if dry_run is None:
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    if dry_run:
        logger.info(f"[DRY RUN] Would execute: {description}")
        logger.debug(f"[DRY RUN] Command: {' '.join(cmd)}")
        # Return a mock successful result for dry run
        return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')
    
    logger.debug(f"Executing: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        error_exit(
            f"Failed to execute: {description}",
            exit_code=e.returncode,
            context="command_execution"
        )


def safe_file_backup(file_path: Union[str, Path]) -> Optional[Path]:
    """Create a backup of a file if it exists."""
    file_path = Path(file_path)
    
    if file_path.exists():
        timestamp = int(datetime.now().timestamp())
        backup_path = file_path.with_suffix(f'.backup.{timestamp}')
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backed up {file_path} to {backup_path}")
        return backup_path
    
    return None


def safe_file_write(file_path: Union[str, Path], 
                   content: str, 
                   backup: bool = True,
                   dry_run: bool = None) -> None:
    """Write content to file safely with optional backup."""
    if dry_run is None:
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    file_path = Path(file_path)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would write to: {file_path}")
        return
    
    if backup:
        safe_file_backup(file_path)
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    logger.debug(f"Wrote to {file_path}")


def safe_file_append(file_path: Union[str, Path], 
                    content: str, 
                    backup: bool = True,
                    dry_run: bool = None) -> None:
    """Append content to file safely with optional backup."""
    if dry_run is None:
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    file_path = Path(file_path)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would append to: {file_path}")
        return
    
    if backup:
        safe_file_backup(file_path)
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open('a') as f:
        f.write(content)
    logger.debug(f"Appended to {file_path}")


def validate_json(json_string: str) -> bool:
    """Validate JSON string."""
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False


def extract_json_value(json_string: str, 
                      key_path: str, 
                      default: Any = None) -> Any:
    """Extract value from JSON using dot notation key path."""
    try:
        data = json.loads(json_string)
        
        # Navigate through key path
        keys = key_path.split('.')
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        
        return data
    except (json.JSONDecodeError, KeyError, TypeError):
        return default


def process_json_secure(json_input: str,
                       key_path: str,
                       default_value: Any = None,
                       max_length: int = 1024) -> Any:
    """Process JSON with security validation."""
    # Validate JSON structure first
    if not validate_json(json_input):
        logger.error("Invalid JSON provided")
        raise ValidationError("Invalid JSON format")
    
    # Extract value
    value = extract_json_value(json_input, key_path, default_value)
    
    # Validate length for string values
    if isinstance(value, str) and len(value) > max_length:
        logger.error(f"JSON value exceeds maximum length: {len(value)} > {max_length}")
        raise ValidationError(f"Value too long: {len(value)} > {max_length}")
    
    return value


def validate_input(input_value: str, 
                  input_type: str = "string",
                  max_length: int = 255) -> bool:
    """Validate and sanitize input based on type."""
    
    # Check length
    if len(input_value) > max_length:
        logger.error(f"Input exceeds maximum length of {max_length} characters")
        return False
    
    # Type-specific validation
    patterns = {
        'url': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$',
        'aws_region': r'^[a-z]{2}-[a-z]+-[0-9]+$',
        'service_name': r'^[a-z]+$',
        'string': r'^[^\x00-\x1f\x7f]*$'  # No control characters
    }
    
    if input_type in patterns:
        if not re.match(patterns[input_type], input_value):
            logger.error(f"Invalid {input_type} format: {input_value}")
            return False
    
    return True


def sanitize_env_var(var_name: str) -> str:
    """Sanitize environment variable value."""
    var_value = os.getenv(var_name, '')
    
    # Remove leading/trailing whitespace
    var_value = var_value.strip()
    
    # Convert to lowercase if applicable
    if var_name.endswith('_NAME'):
        var_value = var_value.lower()
    
    # Replace invalid characters (keep alphanumeric, underscore, dot, slash, dash)
    var_value = re.sub(r'[^a-z0-9_./-]', '', var_value)
    
    # Ensure non-empty value
    if not var_value:
        logger.error(f"Environment variable {var_name} cannot be empty")
        raise HAEnvironmentError(f"Empty environment variable: {var_name}")
    
    # Set the sanitized variable
    os.environ[var_name] = var_value
    logger.debug(f"Sanitized {var_name}")
    
    return var_value


def aws_region_check(region: Optional[str] = None) -> bool:
    """Validate AWS region."""
    region = region or os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        result = safe_exec(
            "Check AWS region",
            ['aws', 'ec2', 'describe-regions', '--region-names', region],
            check=True
        )
        logger.debug(f"AWS region validated: {region}")
        return True
    except Exception:
        logger.error(f"Invalid AWS region: {region}")
        return False


def aws_credentials_check() -> bool:
    """Validate AWS credentials."""
    try:
        result = safe_exec(
            "Check AWS credentials",
            ['aws', 'sts', 'get-caller-identity'],
            check=True
        )
        logger.debug("AWS credentials validated")
        return True
    except Exception:
        logger.error("AWS credentials not configured or invalid")
        return False


def check_lambda_function_exists(function_name: str, 
                                region: Optional[str] = None) -> bool:
    """Check if Lambda function exists."""
    region = region or os.getenv('AWS_REGION', 'us-east-1')
    
    logger.debug(f"Checking if Lambda function exists: {function_name} in {region}")
    
    try:
        result = safe_exec(
            f"Check Lambda function {function_name}",
            ['aws', 'lambda', 'get-function', 
             '--function-name', function_name, 
             '--region', region],
            check=True
        )
        logger.debug(f"Lambda function {function_name} exists")
        return True
    except Exception:
        logger.debug(f"Lambda function {function_name} does not exist")
        return False
