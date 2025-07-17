"""
Deployment Package

This package provides deployment automation for Home Assistant External Connector services.
Replaces the bash deployment scripts with a modern Python implementation.
"""

from .service_installer import (
    ServiceInstaller,
    ServiceType,
    ServiceConfig,
    DeploymentResult,
    deploy_service,
)

from .cloudflare_manager import (
    CloudFlareManager,
    CloudFlareConfig,
    AccessApplicationConfig,
    create_access_application,
)

from .deploy_manager import (
    DeploymentManager,
    DeploymentStrategy,
    DeploymentConfig,
    orchestrate_deployment,
)

__all__ = [
    "ServiceInstaller",
    "ServiceType",
    "ServiceConfig",
    "DeploymentResult",
    "deploy_service",
    "CloudFlareManager",
    "CloudFlareConfig",
    "AccessApplicationConfig",
    "create_access_application",
    "DeploymentManager",
    "DeploymentStrategy",
    "DeploymentConfig",
    "orchestrate_deployment",
]
