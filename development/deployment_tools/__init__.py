"""
Deployment Package

This package provides deployment automation for Home Assistant External Connector
services. Modern Python implementation for automated deployments.
"""

from .deploy_manager import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentStrategy,
    orchestrate_deployment,
)
from .service_installer import (
    DeploymentResult,
    ServiceConfig,
    ServiceInstaller,
    ServiceType,
)

__all__ = [
    # Service installer
    "ServiceInstaller",
    "ServiceType",
    "ServiceConfig",
    "DeploymentResult",
    # Deployment orchestration
    "DeploymentManager",
    "DeploymentStrategy",
    "DeploymentConfig",
    "orchestrate_deployment",
]
