"""
Service Installer module for Home Assistant Lambda deployments.
Provides build, deploy, and configuration logic for AWS Lambda services.
"""

import os
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..platforms.aws.resource_manager import (
    AWSResourceManager,
    AWSResourceType,
    LambdaResourceSpec,
)
from ..utils import AWSError, HAConnectorLogger, ValidationError
from ..utils.constants import LAMBDA_ASSUME_ROLE_POLICY
from ..utils.manager import (
    ConfigurationManager,
    InstallationScenario,
    ResourceRequirement,
)


class ServiceType(str, Enum):
    """Supported service types"""

    ALEXA = "alexa"
    IOS_COMPANION = "ios_companion"
    CLOUDFLARE_PROXY = "cloudflare_proxy"
    GENERIC = "generic"


class ServiceConfig(BaseModel):
    """Configuration for a service deployment"""

    service_type: ServiceType = Field(..., description="Type of service to deploy")
    function_name: str = Field(..., description="Lambda function name")
    handler: str = Field(..., description="Lambda handler function")
    source_path: str = Field(..., description="Path to source code")
    runtime: str = Field(default="python3.11", description="Lambda runtime")
    timeout: int = Field(default=30, description="Function timeout in seconds")
    memory_size: int = Field(default=512, description="Memory size in MB")
    description: str | None = Field(default=None, description="Function description")
    environment_variables: dict[str, str] | None = Field(
        default=None, description="Environment variables"
    )
    create_url: bool = Field(
        default=False, description="Whether to create function URL"
    )
    url_auth_type: str = Field(default="NONE", description="Function URL auth type")
    role_arn: str | None = Field(
        default=None, description="IAM role ARN (will be created if not provided)"
    )


class DeploymentResult(BaseModel):
    """Result of a service deployment"""

    success: bool = Field(..., description="Whether deployment was successful")
    function_name: str = Field(..., description="Deployed function name")
    function_arn: str | None = Field(None, description="Function ARN")
    function_url: str | None = Field(None, description="Function URL if created")
    role_arn: str | None = Field(None, description="IAM role ARN used")
    errors: list[str] = Field(default_factory=list, description="Deployment errors")
    warnings: list[str] = Field(default_factory=list, description="Deployment warnings")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class ServiceInstaller:
    """Enhanced service installer with resource discovery and conflict resolution"""

    def __init__(
        self, region: str = "us-east-1", dry_run: bool = False, verbose: bool = False
    ):
        self.region = region
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = HAConnectorLogger("service_installer", verbose=verbose)
        self.aws_manager = AWSResourceManager(region)

        # Initialize Configuration Manager for enhanced resource discovery
        self.config_manager = ConfigurationManager()

        # Default service configurations
        self._default_configs: dict[ServiceType, dict[str, Any]] = {
            ServiceType.ALEXA: {
                "function_name": "ha-alexa-proxy",
                "handler": "smart_home_bridge.lambda_handler",
                "source_path": (
                    "src/ha_connector/integrations/alexa/lambda_functions/smart_home_bridge.py"
                ),
                "runtime": "python3.11",
                "description": "Home Assistant Alexa Smart Home Bridge",
                "timeout": 30,
                "memory_size": 512,
                "create_url": True,
            },
            ServiceType.IOS_COMPANION: {
                "function_name": "ha-ios-proxy",
                "handler": "ios_wrapper.lambda_handler",
                "source_path": "src/ios/ios_companion.py",
                "runtime": "python3.11",
                "description": "Home Assistant iOS Companion Proxy",
                "timeout": 30,
                "memory_size": 256,
                "create_url": True,
            },
            ServiceType.CLOUDFLARE_PROXY: {
                "function_name": "ha-cloudflare-cloudflare-security-gateway",
                "handler": "cloudflare_cloudflare_security_gateway.lambda_handler",
                "source_path": "src/aws/cloudflare_security_gateway.py",
                "runtime": "python3.11",
                "description": "Home Assistant CloudFlare CloudFlare Security Gateway",
                "timeout": 30,
                "memory_size": 256,
                "create_url": True,
            },
        }

    def get_default_config(self, service_type: ServiceType) -> dict[str, Any]:
        """Get default configuration for a service type"""
        config = self._default_configs.get(service_type, None)
        if config is None:
            return {}
        return config.copy()  # Return a copy to prevent mutations

    def create_deployment_package(
        self,
        source_path: str,
        output_path: str | None = None,
        include_dependencies: bool = True,
    ) -> str:
        """Create a deployment package from source code"""
        src_path = Path(source_path)
        if not src_path.exists():
            raise ValidationError(f"Source path does not exist: {src_path}")

        # Determine output path
        if output_path is None:
            output_path = f"/tmp/{src_path.stem}-deployment.zip"  # nosec B108
        out_path = Path(output_path)

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create deployment package: {out_path}")
            return str(out_path)

        self.logger.info(f"Creating deployment package: {out_path}")

        with zipfile.ZipFile(str(out_path), "w", zipfile.ZIP_DEFLATED) as zip_file:
            if src_path.is_file():
                # Single file
                zip_file.write(str(src_path), src_path.name)
            elif src_path.is_dir():
                # Directory - add all Python files
                for py_file in src_path.rglob("*.py"):
                    arc_name = py_file.relative_to(src_path)
                    zip_file.write(str(py_file), str(arc_name))

                # Add requirements if they exist
                if include_dependencies:
                    requirements_file = src_path / "requirements.txt"
                    if requirements_file.exists():
                        # This is a simplified approach - in practice you'd want to
                        # install dependencies into the package
                        self.logger.warning(
                            "Requirements.txt found but dependency "
                            "installation not implemented"
                        )

            # Add common utilities if they exist
            utils_path = Path(__file__).parent.parent / "utils.py"
            if utils_path.exists():
                zip_file.write(str(utils_path), "ha_connector_utils.py")

        self.logger.info(f"Created deployment package: {out_path}")
        return str(out_path)

    def create_iam_role(
        self,
        role_name: str,
        service_type: ServiceType,
    ) -> str:
        """Create IAM role for Lambda function"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create IAM role: {role_name}")
            return f"arn:aws:iam::123456789012:role/{role_name}"

        # Basic Lambda execution role policy
        assume_role_policy: dict[str, Any] = LAMBDA_ASSUME_ROLE_POLICY

        # Service-specific policies would go here
        role_spec: dict[str, Any] = {
            "resource_type": "role",
            "name": role_name,
            "assume_role_policy": assume_role_policy,
            "description": f"Lambda execution role for {service_type} service",
        }

        self.logger.info(f"Creating IAM role: {role_name}")
        result = self.aws_manager.create_resource(AWSResourceType.IAM, role_spec)

        if result.status == "error":
            raise AWSError(f"Failed to create IAM role: {', '.join(result.errors)}")

        # Extract ARN from result
        if result.resource and "Role" in result.resource:
            role_arn = str(result.resource["Role"]["Arn"])
            self.logger.info(f"Created IAM role: {role_arn}")
            return role_arn

        raise AWSError("Failed to get IAM role ARN from AWS response")

    def deploy_service(self, config: ServiceConfig) -> DeploymentResult:
        """Deploy a service to AWS Lambda"""
        self.logger.info(
            f"Starting deployment of {config.service_type} service: "
            f"{config.function_name}"
        )

        result = DeploymentResult(
            success=False,
            function_name=config.function_name,
            function_arn=None,
            function_url=None,
            role_arn=None,
        )

        try:
            # Create IAM role if not provided
            role_arn = config.role_arn
            if not role_arn:
                role_name = f"{config.function_name}-execution-role"
                role_arn = self.create_iam_role(role_name, config.service_type)
                result.role_arn = role_arn

            # Create deployment package
            package_path = self.create_deployment_package(config.source_path)

            # Create Lambda function specification
            lambda_spec = LambdaResourceSpec(
                function_name=config.function_name,
                handler=config.handler,
                role_arn=role_arn,
                package_path=package_path,
                runtime=config.runtime,
                timeout=config.timeout,
                memory_size=config.memory_size,
                description=config.description,
                environment_variables=config.environment_variables,
                create_url=config.create_url,
                url_auth_type=config.url_auth_type,
            )

            # Deploy to AWS
            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would deploy Lambda function: {config.function_name}"
                )
                result.success = True
                result.function_arn = (
                    f"arn:aws:lambda:{self.region}:123456789012:function:"
                    f"{config.function_name}"
                )
                result.metadata = {
                    "message": f"Would deploy Lambda function: {config.function_name}"
                }
                if config.create_url:
                    result.function_url = (
                        f"https://example.lambda-url.{self.region}.on.aws/"
                    )
            else:
                deploy_result = self.aws_manager.create_resource(
                    AWSResourceType.LAMBDA,
                    lambda_spec.model_dump(),
                )

                if deploy_result.status in ["created", "updated"]:
                    result.success = True

                    # Extract function details from AWS response
                    if deploy_result.resource:
                        function_config = deploy_result.resource.get(
                            "Configuration", {}
                        )
                        result.function_arn = function_config.get("FunctionArn")

                        # Extract function URL if created
                        function_url_config = function_config.get("FunctionUrl")
                        if function_url_config and "FunctionUrl" in function_url_config:
                            result.function_url = function_url_config["FunctionUrl"]

                    self.logger.success(f"Successfully deployed {config.function_name}")
                else:
                    result.errors = deploy_result.errors
                    self.logger.error(
                        f"Failed to deploy {config.function_name}: "
                        f"{', '.join(deploy_result.errors)}"
                    )

            # Clean up temporary package
            if os.path.exists(package_path) and not self.dry_run:
                os.unlink(package_path)

        except (ValidationError, AWSError, OSError, zipfile.BadZipFile) as e:
            result.errors.append(str(e))
            self.logger.error(f"Deployment failed: {str(e)}")

        return result

    def deploy_predefined_service(
        self,
        service_type: ServiceType,
        overrides: dict[str, Any] | None = None,
    ) -> DeploymentResult:
        """Deploy a predefined service type with optional overrides"""
        # Get default configuration
        default_config = self.get_default_config(service_type)
        if not default_config:
            raise ValidationError(
                f"No default configuration for service type: {service_type}"
            )

        # Apply overrides
        config_dict = {**default_config}
        if overrides:
            config_dict.update(overrides)

        config_dict["service_type"] = service_type

        # Create service config
        config = ServiceConfig(**config_dict)

        return self.deploy_service(config)

    def list_deployed_services(self) -> list[dict[str, Any]]:
        """List all deployed Lambda functions"""
        if self.dry_run:
            self.logger.info("[DRY RUN] Would list deployed services")
            return []

        # This would use AWS Lambda list-functions API
        # For now, return empty list as placeholder
        self.logger.info("Listing deployed services...")
        return []

    def plan_enhanced_installation(
        self, scenario: InstallationScenario
    ) -> dict[str, Any]:
        """Plan installation using Configuration Manager resource discovery"""
        self.logger.info(
            f"Planning enhanced installation for scenario: {scenario.value}"
        )

        # Initialize configuration for the scenario
        self.config_manager.init_config(scenario)

        # Define resource requirements based on scenario
        requirements: list[ResourceRequirement] = []

        if scenario in [InstallationScenario.DIRECT_ALEXA, InstallationScenario.ALL]:
            requirements.append(
                ResourceRequirement(
                    resource_type="lambda",
                    resource_id="ha-alexa-proxy",
                    description="Home Assistant Alexa Skills Proxy",
                )
            )

        if scenario in [InstallationScenario.CLOUDFLARE_IOS, InstallationScenario.ALL]:
            requirements.append(
                ResourceRequirement(
                    resource_type="lambda",
                    resource_id="ha-ios-proxy",
                    description="Home Assistant iOS Companion Proxy",
                )
            )

        # Use Configuration Manager for resource matching
        matched_resources = self.config_manager.match_resources_to_requirements(
            requirements
        )

        # Analyze conflicts and plan installation steps
        conflicts: list[dict[str, Any]] = []
        installation_steps: list[dict[str, Any]] = []
        user_decisions_needed: list[dict[str, Any]] = []

        # Check for conflicts and required user decisions
        for match in matched_resources:
            if match.exists:
                conflicts.append(
                    {
                        "resource": match.resource_id,
                        "issue": "Existing resource found",
                        "resource_type": match.resource_type,
                    }
                )
                user_decisions_needed.append(
                    {
                        "type": "conflict_resolution",
                        "message": (
                            f"Resource {match.resource_id} already exists. "
                            "Replace or update?"
                        ),
                        "options": ["replace", "update", "skip"],
                    }
                )

        # Plan installation steps for missing resources
        missing_requirements = [
            req
            for req in requirements
            if not any(
                match.resource_id == req.resource_id and match.exists
                for match in matched_resources
            )
        ]

        for requirement in missing_requirements:
            installation_steps.append(
                {
                    "action": "create",
                    "resource_type": requirement.resource_type,
                    "resource_id": requirement.resource_id,
                    "service_type": self._get_service_type_for_lambda(
                        requirement.resource_id
                    ),
                }
            )

        installation_plan = {
            "scenario": scenario.value,
            "region": self.region,
            "requirements": len(requirements),
            "matched_resources": len(matched_resources),
            "conflicts": conflicts,
            "installation_steps": installation_steps,
            "user_decisions_needed": user_decisions_needed,
        }

        plan_steps = len(installation_steps)
        self.logger.info(f"Installation plan created with {plan_steps} steps")
        return installation_plan

    def execute_enhanced_installation(
        self,
        installation_plan: dict[str, Any],
        user_choices: dict[str, str] | None = None,
    ) -> DeploymentResult:
        """Execute installation plan with user interaction handling"""
        self.logger.info("Executing enhanced installation plan...")

        user_choices = user_choices or {}
        results = DeploymentResult(
            success=True,
            function_name="enhanced-installation-batch",
            function_arn=None,
            function_url=None,
            role_arn=None,
        )

        # Handle user decisions for conflicts
        for decision in installation_plan.get("user_decisions_needed", []):
            resource_key = f"conflict_{decision.get('message', '').split()[1]}"
            user_choice = user_choices.get(resource_key, "skip")

            if user_choice == "skip":
                results.warnings.append(
                    "Skipped conflicted resource due to user choice"
                )
                continue
            if user_choice == "replace":
                results.warnings.append("Will replace existing resource")
            if user_choice == "update":
                results.warnings.append("Will update existing resource")

        # Execute installation steps
        for step in installation_plan.get("installation_steps", []):
            if step["action"] == "create":
                service_type = step["service_type"]
                resource_id = step["resource_id"]

                try:
                    # Deploy the service using existing methods
                    deploy_result = self.deploy_predefined_service(service_type)

                    if deploy_result.success:
                        results.metadata[f"deployed_{resource_id}"] = True
                        self.logger.success(f"Successfully deployed {resource_id}")
                    else:
                        results.errors.extend(deploy_result.errors)
                        results.warnings.extend(deploy_result.warnings)
                        results.success = False

                except (ValidationError, AWSError, OSError, KeyError) as e:
                    error_msg = f"Failed to deploy {resource_id}: {str(e)}"
                    results.errors.append(error_msg)
                    results.success = False
                    self.logger.error(error_msg)

        # Store summary in metadata
        if results.success:
            deployed_count = len(
                [k for k in results.metadata if k.startswith("deployed_")]
            )
            results.metadata["summary"] = (
                f"Enhanced installation completed successfully. "
                f"Deployed {deployed_count} services."
            )
        else:
            error_count = len(results.errors)
            results.metadata["summary"] = (
                f"Enhanced installation completed with {error_count} errors"
            )

        return results

    def _get_service_type_for_lambda(self, lambda_name: str) -> ServiceType:
        """Map Lambda function name to ServiceType"""
        if "alexa" in lambda_name.lower():
            return ServiceType.ALEXA
        if "ios" in lambda_name.lower():
            return ServiceType.IOS_COMPANION
        if "cloudflare" in lambda_name.lower():
            return ServiceType.CLOUDFLARE_PROXY
        return ServiceType.ALEXA  # Default fallback

    def remove_service(self, function_name: str) -> bool:
        """Remove a deployed service"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would remove service: {function_name}")
            return True

        self.logger.info(f"Removing service: {function_name}")
        result = self.aws_manager.delete_resource(AWSResourceType.LAMBDA, function_name)

        if result.status == "error":
            self.logger.error(f"Failed to remove service: {', '.join(result.errors)}")
            return False

        self.logger.success(f"Successfully removed service: {function_name}")
        return True


# Module-level singleton registry for ServiceInstaller instances
_service_installer_registry: dict[tuple[str, bool, bool], ServiceInstaller] = {}


def get_service_installer(
    region: str = "us-east-1",
    dry_run: bool = False,
    verbose: bool = False,
) -> ServiceInstaller:
    """Get or create singleton service installer instance"""
    key = (region, dry_run, verbose)

    if key not in _service_installer_registry:
        _service_installer_registry[key] = ServiceInstaller(
            region=region, dry_run=dry_run, verbose=verbose
        )

    return _service_installer_registry[key]
