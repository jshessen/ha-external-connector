"""
Home Assistant External Connector.

A Python package for connecting self-hosted Home Assistant instances
to external cloud services like AWS Lambda, Alexa, CloudFlare, and iOS.
"""

from .utils import (
    # Logger and error handling
    logger,
    HAConnectorError,
    PrerequisiteError,
    HAEnvironmentError,
    ValidationError,
    AWSError,
    error_exit,

    # Validation and requirements
    require_commands,
    require_env,
    validate_input,
    sanitize_env_var,

    # File operations
    safe_file_backup,
    safe_file_write,
    safe_file_append,

    # Command execution
    safe_exec,

    # JSON utilities
    validate_json,
    extract_json_value,
    process_json_secure,

    # AWS utilities
    aws_region_check,
    aws_credentials_check,
    check_lambda_function_exists,
)

from .config import (
    ConfigurationManager,
    InstallationScenario,
)

from .adapters import (
    AWSResourceManager,
    AWSResourceType,
    AWSLambdaManager,
    AWSIAMManager,
    AWSSSMManager,
    AWSLogsManager,
    AWSTriggerManager,
    validate_aws_access,
)

from .deployment import (
    ServiceInstaller,
    ServiceType,
    ServiceConfig,
    DeploymentResult,
    deploy_service,
    CloudFlareManager,
    CloudFlareConfig,
    AccessApplicationConfig,
    create_access_application,
    DeploymentManager,
    DeploymentStrategy,
    DeploymentConfig,
    orchestrate_deployment,
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
    'validate_aws_access',

    # Deployment
    'ServiceInstaller',
    'ServiceType',
    'ServiceConfig',
    'DeploymentResult',
    'deploy_service',
    'CloudFlareManager',
    'CloudFlareConfig',
    'AccessApplicationConfig',
    'create_access_application',
    'DeploymentManager',
    'DeploymentStrategy',
    'DeploymentConfig',
    'orchestrate_deployment',
]
