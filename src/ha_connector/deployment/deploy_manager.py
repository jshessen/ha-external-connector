
"""
Deployment Manager Module

Orchestrated deployment automation for Home Assistant AWS Lambda functions.
Modern Python implementation for automated deployments.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..adapters import AWSResourceType
from ..adapters.cloudflare_manager import AccessApplicationSpec, CloudFlareManager
from ..utils import HAConnectorLogger, ValidationError
from .service_installer import DeploymentResult, ServiceInstaller, ServiceType


class DeploymentStrategy(str, Enum):
    """Deployment strategies"""
    ROLLING = "rolling"
    BLUE_GREEN = "blue-green"
    CANARY = "canary"
    IMMEDIATE = "immediate"


class DeploymentConfig(BaseModel):
    """Configuration for orchestrated deployment"""
    environment: str = Field(
        ..., description="Deployment environment (dev, staging, prod)"
    )
    version: str = Field(..., description="Version to deploy")
    strategy: DeploymentStrategy = Field(
        default=DeploymentStrategy.ROLLING, description="Deployment strategy"
    )
    services: list[ServiceType] = Field(..., description="Services to deploy")
    region: str = Field(default="us-east-1", description="AWS region")
    dry_run: bool = Field(default=False, description="Dry run mode")
    verbose: bool = Field(default=False, description="Verbose logging")
    skip_tests: bool = Field(default=False, description="Skip tests")
    force: bool = Field(default=False, description="Force deployment")
    rollback_on_failure: bool = Field(
        default=True, description="Rollback on failure"
    )
    health_check_timeout: int = Field(
        default=300, description="Health check timeout in seconds"
    )
    cloudflare_setup: bool = Field(
        default=False, description="Set up CloudFlare Access"
    )
    cloudflare_domain: str | None = Field(
        None, description="CloudFlare domain for setup"
    )
    service_overrides: dict[str, dict[str, Any]] | None = Field(
        None, description="Per-service configuration overrides"
    )
    tags: dict[str, str] | None = Field(None, description="Deployment tags")


class DeploymentManager:
    """Orchestrated deployment manager"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = HAConnectorLogger("deployment_manager", verbose=config.verbose)
        self.service_installer = ServiceInstaller(
            region=config.region,
            dry_run=config.dry_run,
            verbose=config.verbose
        )
        self.deployment_results: list[DeploymentResult] = []
        self.start_time = None
        self.end_time = None

    def validate_deployment_config(self) -> None:
        """Validate deployment configuration"""
        self.logger.info("Validating deployment configuration")

        # Validate environment
        valid_environments = ["dev", "staging", "prod"]
        if self.config.environment not in valid_environments:
            raise ValidationError(
                f"Invalid environment: {self.config.environment}. "
                f"Must be one of: {valid_environments}"
            )

        # Validate version format (simple semver check)
        version_parts = self.config.version.split('.')
        if len(version_parts) < 2 or not all(part.isdigit() for part in version_parts):
            raise ValidationError(
                f"Invalid version format: {self.config.version}. "
                "Expected: x.y.z"
            )

        # Validate services
        if not self.config.services:
            raise ValidationError("No services specified for deployment")

        # Validate CloudFlare setup requirements
        if self.config.cloudflare_setup and not self.config.cloudflare_domain:
            raise ValidationError(
                "CloudFlare domain required when cloudflare_setup is enabled"
            )

        self.logger.info("✓ Deployment configuration validated")

    def pre_deployment_checks(self) -> bool:
        """Run pre-deployment checks"""
        self.logger.info("Running pre-deployment checks")

        checks_passed = True

        # Check AWS connectivity using resource manager
        try:
            # Try to read a non-existent Lambda function to check connectivity
            _ = self.service_installer.aws_manager.read_resource(
                AWSResourceType.LAMBDA, "nonexistent-function-for-connectivity-check"
            )
            self.logger.info("✓ AWS access validated")
        except (KeyError, AttributeError, RuntimeError) as e:
            self.logger.error(f"AWS access check failed: {str(e)}")
            checks_passed = False

        # Check CloudFlare credentials if needed
        if self.config.cloudflare_setup:
            try:
                cf_manager = CloudFlareManager()
                cf_manager.get_account_id()  # Test API access
                self.logger.info("✓ CloudFlare access validated")
            except (KeyError, AttributeError, RuntimeError) as e:
                self.logger.error(f"CloudFlare access check failed: {str(e)}")
                checks_passed = False

        # Additional environment-specific checks
        if self.config.environment == "prod" and not self.config.force:
            if self.config.skip_tests:
                self.logger.warning(
                    "⚠ Skipping tests in production deployment"
                )
            if self.config.dry_run:
                self.logger.info(
                    "ℹ Production deployment in dry-run mode"
                )

        return checks_passed

    def deploy_service_with_strategy(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any] | None = None
    ) -> DeploymentResult:
        """Deploy a service using the configured strategy"""
        self.logger.info(
            f"Deploying {service_type} using {self.config.strategy} strategy"
        )

        # Prepare service overrides
        final_overrides = {}
        if (self.config.service_overrides and
                service_type in self.config.service_overrides):
            final_overrides.update(self.config.service_overrides[service_type])
        if overrides:
            final_overrides.update(overrides)

        # Add environment-specific configuration
        final_overrides.update({
            "environment_variables": {
                "ENVIRONMENT": self.config.environment,
                "VERSION": self.config.version,
                **(final_overrides.get("environment_variables", {}))
            }
        })

        # Add tags
        if self.config.tags:
            final_overrides["tags"] = {
                **self.config.tags,
                "Environment": self.config.environment,
                "Version": self.config.version,
                "Service": service_type
            }

        # Deploy based on strategy
        if self.config.strategy == DeploymentStrategy.IMMEDIATE:
            return self._deploy_immediate(service_type, final_overrides)
        elif self.config.strategy == DeploymentStrategy.ROLLING:
            return self._deploy_rolling(service_type, final_overrides)
        elif self.config.strategy == DeploymentStrategy.BLUE_GREEN:
            return self._deploy_blue_green(service_type, final_overrides)
        elif self.config.strategy == DeploymentStrategy.CANARY:
            return self._deploy_canary(service_type, final_overrides)
        else:
            raise ValidationError(
                f"Unsupported deployment strategy: {self.config.strategy}"
            )

    def _deploy_immediate(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any]
    ) -> DeploymentResult:
        """Deploy service immediately"""
        return self.service_installer.deploy_predefined_service(
            service_type, overrides
        )

    def _deploy_rolling(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any]
    ) -> DeploymentResult:
        """Deploy service with rolling strategy"""
        # For Lambda functions, rolling deployment is essentially immediate
        # with health checks
        result = self.service_installer.deploy_predefined_service(
            service_type, overrides
        )

        if result.success and not self.config.dry_run:
            # Perform health check
            if self._health_check_service(result.function_name):
                self.logger.info(
                    f"✓ Health check passed for {service_type}"
                )
            else:
                result.success = False
                result.errors.append("Health check failed")
                self.logger.error(
                    f"✗ Health check failed for {service_type}"
                )

        return result

    def _deploy_blue_green(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any]
    ) -> DeploymentResult:
        """Deploy service with blue-green strategy"""
        # For this implementation, we'll create a new version and switch alias
        # This is a simplified version - full blue-green would require more
        # infrastructure

        # Add version suffix for blue-green deployment
        function_name = overrides.get('function_name', f'ha-{service_type}')
        overrides["function_name"] = f"{function_name}-{self.config.version}"

        result = self.service_installer.deploy_predefined_service(
            service_type, overrides
        )

        if result.success:
            self.logger.info(
                f"✓ Blue-green deployment completed for {service_type}"
            )

        return result

    def _deploy_canary(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any]
    ) -> DeploymentResult:
        """Deploy service with canary strategy"""
        # For this implementation, we'll deploy with a canary suffix
        # Real canary deployments would require weighted routing

        self.logger.info(
            f"Starting canary deployment for {service_type}"
        )

        # Deploy canary version
        canary_overrides = {**overrides}
        function_name = overrides.get('function_name', f'ha-{service_type}')
        canary_overrides["function_name"] = f"{function_name}-canary"

        canary_result = self.service_installer.deploy_predefined_service(
            service_type, canary_overrides
        )

        if canary_result.success and not self.config.dry_run:
            # Run canary health checks
            self.logger.info(
                "Running canary health checks..."
            )
            if self._health_check_service(canary_result.function_name):
                self.logger.info(
                    "✓ Canary health checks passed, promoting to production"
                )
                # Deploy production version
                return self.service_installer.deploy_predefined_service(
                    service_type, overrides
                )
            else:
                canary_result.success = False
                canary_result.errors.append("Canary health check failed")
                self.logger.error(
                    "✗ Canary health checks failed, aborting deployment"
                )

        return canary_result

    def _health_check_service(self, function_name: str) -> bool:
        """Perform health check on deployed service"""
        if self.config.dry_run:
            self.logger.info(
                f"[DRY RUN] Would perform health check on {function_name}"
            )
            return True

        self.logger.info(
            f"Performing health check on {function_name}"
        )

        # Simple health check - verify function exists and is active
        try:
            result = self.service_installer.aws_manager.read_resource(
                AWSResourceType.LAMBDA,
                function_name
            )

            # Use hasattr to check for 'exists' or fallback to 'resource' presence
            exists = getattr(result, 'exists', None)
            if exists is not None:
                exists_flag = exists
            else:
                exists_flag = bool(getattr(result, 'resource', None))

            if exists_flag and result.resource:
                function_config = result.resource.get('Configuration', {})
                state = function_config.get('State', 'Unknown')

                if state == 'Active':
                    return True
                self.logger.warning(
                    f"Function {function_name} state: {state}"
                )
                return False
            self.logger.error(
                f"Function {function_name} not found"
            )
            return False

        except (KeyError, AttributeError, RuntimeError) as e:
            self.logger.error(
                f"Health check failed for {function_name}: {str(e)}"
            )
            return False

    def setup_cloudflare_access(self) -> dict[str, Any]:
        """Set up CloudFlare Access for deployed Lambda functions (resource-oriented)"""
        if not self.config.cloudflare_setup:
            return {}

        self.logger.info(
            f"Setting up CloudFlare Access for {self.config.cloudflare_domain}"
        )

        try:
            with CloudFlareManager() as cf_manager:
                # Use resource-oriented CRUD pattern
                account_id = cf_manager.get_account_id()
                domain = self.config.cloudflare_domain
                if not isinstance(domain, str) or not domain:
                    raise ValidationError(
                        "CloudFlare domain must be a non-empty string."
                    )
                app_spec = AccessApplicationSpec(
                    name=f"Home Assistant {self.config.environment.title()}",
                    domain=domain,
                    subdomain=None,
                    cors_headers=None,
                    tags=None,
                )
                result = cf_manager.access_manager.create_or_update(
                    app_spec, account_id
                )

                if getattr(result, 'status', None) == "success":
                    self.logger.success(
                        f"✓ CloudFlare Access configured: {domain}"
                    )
                else:
                    self.logger.error(
                        "CloudFlare Access setup failed: "
                        f"{getattr(result, 'errors', None)}"
                    )
                # Always return a dict
                if hasattr(result, 'dict'):
                    return result.dict()
                if isinstance(result, dict):
                    return result
                return {"result": str(result)}

        except (KeyError, AttributeError, RuntimeError) as e:
            self.logger.error(
                f"CloudFlare setup failed: {str(e)}"
            )
            raise

    def rollback_deployment(self) -> bool:
        """Rollback failed deployment"""
        if not self.config.rollback_on_failure:
            return False

        self.logger.warning(
            "Rolling back deployment..."
        )

        # For this implementation, rollback removes the deployed functions
        # In a real system, you'd restore previous versions
        rollback_success = True

        for result in self.deployment_results:
            if result.success:
                try:
                    self.service_installer.remove_service(result.function_name)
                    self.logger.info(
                        f"✓ Rolled back {result.function_name}"
                    )
                except (KeyError, AttributeError, RuntimeError) as e:
                    self.logger.error(
                        f"✗ Failed to rollback {result.function_name}: {str(e)}"
                    )
                    rollback_success = False

        return rollback_success

    def execute_deployment(self) -> dict[str, Any]:
        """Execute the complete deployment process"""
        self.start_time = time.time()

        try:
            self.logger.info(
                f"🚀 Starting {self.config.strategy} deployment"
            )
            self.logger.info(
                f"Environment: {self.config.environment}"
            )
            self.logger.info(
                f"Version: {self.config.version}"
            )
            self.logger.info(
                f"Services: {', '.join(self.config.services)}"
            )

            # Validate configuration
            self.validate_deployment_config()

            # Run pre-deployment checks
            if not self.pre_deployment_checks():
                if not self.config.force:
                    raise ValidationError(
                        "Pre-deployment checks failed. Use --force to override."
                    )
                else:
                    self.logger.warning(
                        "⚠ Pre-deployment checks failed but forced deployment continues"
                    )

            # Deploy services
            lambda_urls = {}

            for service_type in self.config.services:
                result = self.deploy_service_with_strategy(service_type)
                self.deployment_results.append(result)

                if result.success:
                    self.logger.success(
                        f"✓ Successfully deployed {service_type}"
                    )
                    if result.function_url:
                        lambda_urls[service_type] = result.function_url
                else:
                    self.logger.error(
                        f"✗ Failed to deploy {service_type}: "
                        f"{', '.join(result.errors)}"
                    )
                    if self.config.rollback_on_failure:
                        self.rollback_deployment()
                    raise ValidationError(
                        f"Service deployment failed: {service_type}"
                    )

            # Set up CloudFlare Access if requested
            cloudflare_result = {}
            if self.config.cloudflare_setup and lambda_urls:
                cloudflare_result = self.setup_cloudflare_access()

            self.end_time = time.time()
            deployment_time = self.end_time - self.start_time

            self.logger.success(
                f"🎉 Deployment completed successfully in {deployment_time:.2f} seconds"
            )

            return {
                "success": True,
                "environment": self.config.environment,
                "version": self.config.version,
                "strategy": self.config.strategy,
                "deployment_time": deployment_time,
                "services": [result.dict() for result in self.deployment_results],
                "lambda_urls": lambda_urls,
                "cloudflare": cloudflare_result,
                "errors": [],
            }

        except ValidationError as e:
            self.end_time = time.time()
            self.logger.error(f"💥 Deployment failed: {str(e)}")

            return {
                "success": False,
                "environment": self.config.environment,
                "version": self.config.version,
                "strategy": self.config.strategy,
                "deployment_time": (
                    self.end_time - self.start_time
                ) if self.start_time else 0,
                "services": [result.dict() for result in self.deployment_results],
                "errors": [str(e)],
            }


def orchestrate_deployment(config: DeploymentConfig) -> dict[str, Any]:
    """Convenience function to orchestrate a deployment"""
    manager = DeploymentManager(config)
    return manager.execute_deployment()
