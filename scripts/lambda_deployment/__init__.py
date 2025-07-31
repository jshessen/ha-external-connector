"""
Enhanced Lambda Deployment System

This module provides a comprehensive, modular Lambda deployment system with
advanced marker processing, validation, and deployment generation capabilities.

The system includes:
- DeploymentManager: Main orchestrator for deployment workflows
- DeploymentMarkerSystem: Advanced marker processing and validation
- DeploymentValidationSystem: Comprehensive validation framework
- LambdaMarkerValidator: Standalone validation tool
- Performance-optimized import classification and processing
- Real-time progress feedback and detailed error reporting

Example usage:

    from scripts.lambda_deployment import DeploymentManager
    
    manager = DeploymentManager(
        source_dir="src/lambda_functions",
        deployment_dir="infrastructure/deployment"
    )
    
    results = manager.build_deployment(force_rebuild=True)
    print(f"Deployment success: {results['success']}")

For standalone validation:

    from scripts.lambda_deployment import LambdaMarkerValidator
    
    validator = LambdaMarkerValidator("src/lambda_functions")
    results = validator.validate_all_lambda_markers(verbose=True)
"""

from .deployment_manager import (
    DeploymentConfig,
    DeploymentManager,
    ImportGroup,
    ImportParser,
    ImportType,
    MarkerValidationResult,
)
from .marker_system import (
    DeploymentMarkerSystem,
    MarkerBlock,
    MarkerType,
    MarkerValidationIssue,
)
from .marker_validator import LambdaMarkerValidator
from .validation_system import (
    DeploymentValidationSystem,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    ValidationType,
)

__version__ = "2.0.0"
__author__ = "Enhanced Lambda Deployment System"

__all__ = [
    # Core deployment components
    "DeploymentManager",
    "DeploymentConfig",

    # Import processing
    "ImportGroup",
    "ImportParser",
    "ImportType",
    "MarkerValidationResult",

    # Marker system
    "DeploymentMarkerSystem",
    "MarkerBlock",
    "MarkerType",
    "MarkerValidationIssue",

    # Validation system
    "DeploymentValidationSystem",
    "ValidationIssue",
    "ValidationLevel",
    "ValidationResult",
    "ValidationType",

    # Standalone tools
    "LambdaMarkerValidator",
]
