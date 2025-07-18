"""
Home Assistant External Connector.

A Python package for connecting self-hosted Home Assistant instances
to external cloud services like AWS Lambda, Alexa, CloudFlare, and iOS.
"""

from .adapters import (
    AWSIAMManager,
    AWSLambdaManager,
    AWSLogsManager,
    AWSResourceManager,
    AWSResourceType,
    AWSSSMManager,
    AWSTriggerManager,
    CloudFlareManager,
    CloudFlareResourceType,
)
from .config import (
    ConfigurationManager,
    InstallationScenario,
)
from .deployment import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentResult,
    DeploymentStrategy,
    ServiceConfig,
    ServiceInstaller,
    ServiceType,
    orchestrate_deployment,
)
from .utils import (
    AWSError,
    HAConnectorError,
    HAEnvironmentError,
    PrerequisiteError,
    ValidationError,
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

__version__ = "1.0.0"
__author__ = "Home Assistant External Connector Team"
__description__ = "Connect self-hosted Home Assistant to external cloud services"

# Package metadata
__all__ = [
    # Core utilities
    'logger',
    'HAConnectorError',
    'PrerequisiteError',
    'HAEnvironmentError',
    'ValidationError',
    'AWSError',
    'error_exit',

    # Validation functions
    'require_commands',
    'require_env',
    'validate_input',
    'sanitize_env_var',

    # File operations
    'safe_file_backup',
    'safe_file_write',
    'safe_file_append',

    # Command execution
    'safe_exec',

    # JSON utilities
    'validate_json',
    'extract_json_value',
    'process_json_secure',

    # AWS utilities
    'aws_region_check',
    'aws_credentials_check',
    'check_lambda_function_exists',

    # Configuration management
    'ConfigurationManager',
    'InstallationScenario',

    # AWS adapters
    'AWSResourceManager',
    'AWSResourceType',
    'AWSLambdaManager',
    'AWSIAMManager',
    'AWSSSMManager',
    'AWSLogsManager',
    'AWSTriggerManager',

    # CloudFlare adapters (moved to adapters module)
    'CloudFlareManager',
    'CloudFlareResourceType',

    # Deployment
    'ServiceInstaller',
    'ServiceType',
    'ServiceConfig',
    'DeploymentResult',
    'DeploymentManager',
    'DeploymentStrategy',
    'DeploymentConfig',
    'orchestrate_deployment',
]
