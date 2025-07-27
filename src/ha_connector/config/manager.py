"""Configuration and resource management for Home Assistant external connector."""

# pyright: reportUnknownVariableType=false

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - Only used for exception types with safe_exec wrapper
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NoReturn

from ..constants import DEFAULT_AWS_REGION, LAMBDA_ASSUME_ROLE_POLICY
from ..platforms.aws.resource_manager import AWSResourceType, get_aws_manager
from ..utils import HAConnectorError, logger, safe_exec
from .cloudflare_helpers import validate_cloudflare_domain_setup


def _assert_never(value: object) -> NoReturn:
    """Helper for exhaustive enum checking."""
    raise ValueError(
        f"Unsupported scenario: {value}. This indicates a bug in the code."
    )


class InstallationScenario(Enum):
    """Supported installation scenarios."""

    DIRECT_ALEXA = "direct_alexa"
    CLOUDFLARE_ALEXA = "cloudflare_alexa"
    CLOUDFLARE_IOS = "cloudflare_ios"
    ALL = "all"


@dataclass
class ConfigurationState:
    """Configuration state container."""

    scenario: InstallationScenario
    ha_base_url: str | None = None
    alexa_secret: str | None = None
    cf_client_id: str | None = None
    cf_client_secret: str | None = None
    aws_region: str = DEFAULT_AWS_REGION

    def __post_init__(self) -> None:
        """Initialize from environment variables if not provided."""
        if not self.ha_base_url:
            self.ha_base_url = os.getenv("HA_BASE_URL")
        if not self.alexa_secret:
            self.alexa_secret = os.getenv("ALEXA_SECRET")
        if not self.cf_client_id:
            self.cf_client_id = os.getenv("CF_CLIENT_ID")
        if not self.cf_client_secret:
            self.cf_client_secret = os.getenv("CF_CLIENT_SECRET")
        if not self.aws_region:
            self.aws_region = os.getenv("AWS_REGION", DEFAULT_AWS_REGION)


@dataclass
class ResourceRequirement:
    """Specification for a required AWS resource."""

    resource_type: str
    resource_id: str
    description: str | None = None


@dataclass
class MatchedResource:
    """Container for resource discovery results."""

    resource_type: str
    resource_id: str
    resource: dict[str, Any]
    exists: bool = False


@dataclass
class ResourceDiscoveryResult:
    """Results from AWS resource discovery."""

    found_resources: list[MatchedResource] = field(default_factory=list)
    missing_resources: list[ResourceRequirement] = field(default_factory=list)

    possible_resources: list[dict[str, Any]] = field(default_factory=list)


class ConfigurationManager:
    """Central configuration manager for Home Assistant external connector."""

    def __init__(self) -> None:
        self.config: ConfigurationState | None = None

    # Valid AWS regions for Alexa Smart Home
    ALEXA_VALID_REGIONS = ["us-east-1", "eu-west-1", "us-west-2"]

    def init_config(self, scenario: InstallationScenario) -> ConfigurationState:
        """Initialize configuration for a scenario."""
        logger.info(f"Initializing configuration for scenario: {scenario.value}")
        # Create fresh configuration state
        self.config = ConfigurationState(scenario=scenario)
        return self.config

    def validate_ha_base_url(self, url: str) -> bool:
        """Validate Home Assistant URL."""
        if not url:
            logger.error("HA_BASE_URL is required")
            return False

        if not url.startswith("https://"):
            logger.error(f"HA_BASE_URL must use HTTPS: {url}")
            return False

        return True

    def validate_alexa_config(self, secret: str | None = None) -> bool:
        """Validate Alexa configuration."""
        secret = secret or (self.config.alexa_secret if self.config else None)

        if not secret:
            logger.error("ALEXA_SECRET is required for Alexa integration")
            return False

        if len(secret) < 32:
            logger.error("ALEXA_SECRET must be at least 32 characters long")
            return False

        return True

    def validate_cloudflare_config(self) -> bool:
        """Validate CloudFlare configuration."""
        if not self.config:
            return False

        client_id = self.config.cf_client_id
        client_secret = self.config.cf_client_secret
        cf_api_token = os.getenv("CF_API_TOKEN")
        auto_setup = os.getenv("AUTO_SETUP_CLOUDFLARE", "false").lower() == "true"

        if not client_id and not cf_api_token and not auto_setup:
            logger.error("CloudFlare Access credentials or API token required")
            return False

        if client_id and not client_secret:
            logger.error("CF_CLIENT_SECRET required when CF_CLIENT_ID is provided")
            return False

        return True

    def validate_alexa_region(self, region: str) -> bool:
        """Validate AWS region for Alexa deployment."""
        if region not in self.ALEXA_VALID_REGIONS:
            logger.error(
                f"Alexa Skills must be deployed in a supported region: "
                f"{self.ALEXA_VALID_REGIONS}"
            )
            logger.error(f"Current region: {region}")
            return False

        return True

    def _validate_cloudflare_domain_setup(self, domain: str) -> None:
        """Validate CloudFlare domain setup.

        Args:
            domain: Domain to validate CloudFlare setup for

        Raises:
            ValueError: If validation fails
        """
        validate_cloudflare_domain_setup(domain)

    def check_prerequisites_for_scenario(self, scenario: InstallationScenario) -> bool:
        """Check prerequisites for a scenario."""
        # Check basic prerequisites using shutil.which instead of subprocess
        if not shutil.which("aws"):
            logger.error("AWS CLI is required but not installed")
            return False

        if not shutil.which("jq"):
            logger.error("jq is required but not installed")
            return False

        # Check AWS credentials using the AWS adapter
        if not self.check_aws_credentials():
            logger.error("AWS credentials not configured or invalid")
            return False

        # Scenario-specific prerequisites
        if scenario in [
            InstallationScenario.CLOUDFLARE_ALEXA,
            InstallationScenario.CLOUDFLARE_IOS,
        ]:
            cf_api_token = os.getenv("CF_API_TOKEN")
            cf_api_key = os.getenv("CF_API_KEY")
            auto_setup = os.getenv("AUTO_SETUP_CLOUDFLARE", "false").lower() == "true"
            if not cf_api_token and not cf_api_key and not auto_setup:
                logger.warning(
                    "CloudFlare API credentials not set - "
                    "some validations will be skipped"
                )

        return True

    def _validate_direct_alexa_scenario(self) -> bool:
        """Validate Direct Alexa Integration scenario."""
        logger.debug("Validating Direct Alexa Integration...")

        if not self.config:
            return False

        valid = True

        # Common validations
        if not self.validate_ha_base_url(self.config.ha_base_url or ""):
            valid = False

        # Alexa-specific validation
        if not self.validate_alexa_config():
            valid = False

        # Region validation for Alexa
        if not self.validate_alexa_region(self.config.aws_region):
            valid = False

        if valid:
            logger.success("Direct Alexa scenario validation passed")
        else:
            logger.error("Direct Alexa scenario validation failed")

        return valid

    def _validate_cloudflare_alexa_scenario(self) -> bool:
        """Validate CloudFlare-Proxied Alexa Integration scenario."""
        logger.debug("Validating CloudFlare-Proxied Alexa Integration...")

        valid = True

        # First validate direct Alexa requirements
        if not self._validate_direct_alexa_scenario():
            valid = False

        # Additional CloudFlare validation
        if not self.validate_cloudflare_config():
            valid = False

        # Validate existing CloudFlare Access setup if possible
        if (
            self.config
            and self.config.ha_base_url
            and (
                os.getenv("CF_API_TOKEN")
                or (os.getenv("CF_API_KEY") and os.getenv("CF_EMAIL"))
            )
        ):
            # Extract domain from URL
            ha_domain = self.config.ha_base_url.replace("https://", "").split("/")[0]
            logger.info(f"Validating existing CloudFlare Access setup for: {ha_domain}")

            # Basic CloudFlare Access validation
            try:
                self._validate_cloudflare_domain_setup(ha_domain)
                logger.info("CloudFlare Access validation completed")
            except (ValueError, ConnectionError, OSError) as e:
                logger.warning(f"CloudFlare Access validation warning: {e}")
                logger.info("This may be normal for manual CloudFlare setups")

        if valid:
            logger.success("CloudFlare Alexa scenario validation passed")
        else:
            logger.error("CloudFlare Alexa scenario validation failed")

        return valid

    def _validate_cloudflare_ios_scenario(self) -> bool:
        """Validate iOS Companion with CloudFlare scenario."""
        logger.debug("Validating iOS Companion with CloudFlare...")

        if not self.config:
            return False

        valid = True

        # Common validations
        if not self.validate_ha_base_url(self.config.ha_base_url or ""):
            valid = False

        # CloudFlare validation (iOS requires existing CloudFlare setup)
        if not self.validate_cloudflare_config():
            logger.error("CloudFlare Access setup required for iOS scenario")
            logger.error(
                "Either provide existing credentials or "
                "run CloudFlare Alexa scenario first"
            )
            valid = False

        if valid:
            logger.success("iOS CloudFlare scenario validation passed")
        else:
            logger.error("iOS CloudFlare scenario validation failed")

        return valid

    def validate_scenario_setup(
        self, scenario: InstallationScenario | None = None
    ) -> bool:
        """Main scenario validation entry point."""
        if not scenario:
            scenario = self.config.scenario if self.config else InstallationScenario.ALL

        if scenario == InstallationScenario.ALL:
            return self.validate_all_scenarios()

        logger.info(f"Validating setup for scenario: {scenario.value}")

        # Initialize config if not already done
        if not self.config or self.config.scenario != scenario:
            self.init_config(scenario)

        # Always check prerequisites first
        if not self.check_prerequisites_for_scenario(scenario):
            logger.error(f"Prerequisite check failed for scenario: {scenario.value}")
            return False

        # Run scenario-specific validation
        if scenario == InstallationScenario.DIRECT_ALEXA:
            return self._validate_direct_alexa_scenario()
        if scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            return self._validate_cloudflare_alexa_scenario()
        if scenario == InstallationScenario.CLOUDFLARE_IOS:
            return self._validate_cloudflare_ios_scenario()

        # This should never happen with current enum
        _assert_never(scenario)

    def validate_all_scenarios(self) -> bool:
        """Validate all scenarios."""
        all_passed = True
        supported_scenarios = [
            InstallationScenario.DIRECT_ALEXA,
            InstallationScenario.CLOUDFLARE_ALEXA,
            InstallationScenario.CLOUDFLARE_IOS,
        ]

        original_scenario = self.config.scenario if self.config else None

        for scenario in supported_scenarios:
            logger.info(f"Validating setup for scenario: {scenario.value}")

            # Initialize config for this scenario
            if not self.config or self.config.scenario != scenario:
                self.init_config(scenario)

            # Check prerequisites first
            if not self.check_prerequisites_for_scenario(scenario):
                logger.error(
                    f"Prerequisite check failed for scenario: {scenario.value}"
                )
                all_passed = False
                continue

            # Call specific validation method directly
            scenario_passed = False
            if scenario == InstallationScenario.DIRECT_ALEXA:
                scenario_passed = self._validate_direct_alexa_scenario()
            if scenario == InstallationScenario.CLOUDFLARE_ALEXA:
                scenario_passed = self._validate_cloudflare_alexa_scenario()
            if scenario == InstallationScenario.CLOUDFLARE_IOS:
                scenario_passed = self._validate_cloudflare_ios_scenario()

            if not scenario_passed:
                logger.error(f"Validation failed for scenario: {scenario.value}")
                all_passed = False

        # Restore original scenario
        if self.config and original_scenario is not None:
            self.config.scenario = original_scenario

        if all_passed:
            logger.success("Validation passed for all scenarios")
        else:
            logger.error("Validation failed for one or more scenarios")

        return all_passed

    def _collect_ha_url(self) -> str:
        """Collect Home Assistant URL interactively."""
        while True:
            url = input("Home Assistant base URL (must be HTTPS): ").strip()
            if self.validate_ha_base_url(url):
                if self.config:
                    self.config.ha_base_url = url
                return url

    def generate_secure_secret(self, length: int = 32) -> str:
        """Generate a secure random secret."""
        try:
            result = safe_exec(
                "Generate secure secret",
                ["openssl", "rand", "-base64", "48"],
                check=True,
            )
            # Clean up the output and truncate to desired length
            secret = (
                result.stdout.strip().replace("=", "").replace("+", "").replace("/", "")
            )
            return secret[:length]
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.error("Failed to generate secure secret: openssl command failed")
            raise HAConnectorError(
                "Secret generation failed - openssl not available"
            ) from exc
        except (AttributeError, TypeError) as exc:
            logger.error("Failed to generate secure secret: invalid result format")
            raise HAConnectorError("Secret generation failed - invalid format") from exc

    def _collect_alexa_config(self) -> None:
        """Collect Alexa configuration interactively."""
        if not self.config or self.config.alexa_secret:
            return

        while True:
            secret = input(
                "Alexa secret (32+ characters, press Enter to generate): "
            ).strip()
            if not secret:
                secret = self.generate_secure_secret(32)
                logger.info(f"Generated Alexa secret: {secret}")
                self.config.alexa_secret = secret
                break
            if len(secret) >= 32:
                self.config.alexa_secret = secret
                break

            logger.error("Alexa secret must be at least 32 characters")

    def _collect_cloudflare_config(self) -> None:
        """Collect CloudFlare configuration."""
        if not self.config or self.config.cf_client_id:
            return

        logger.info("CloudFlare configuration required")
        logger.info("You can either provide existing CloudFlare Access credentials")
        logger.info("or use CF_API_TOKEN for automatic setup")

        # Check if CF_API_TOKEN is available for auto-setup
        cf_api_token = os.getenv("CF_API_TOKEN")
        if cf_api_token:
            logger.info(
                "CF_API_TOKEN found - CloudFlare can be configured automatically"
            )
            auto_setup = (
                input("Use automatic CloudFlare setup? (y/N): ").strip().lower()
            )
            if auto_setup in ["y", "yes"]:
                logger.info(
                    "CloudFlare will be configured automatically during deployment"
                )
                return

        # Collect manual credentials
        logger.info("Collecting CloudFlare Access credentials manually")

        while True:
            client_id = input(
                "CloudFlare Client ID (from existing Access app): "
            ).strip()
            if client_id:
                self.config.cf_client_id = client_id
                break
            logger.error("CloudFlare Client ID is required")

        while True:
            client_secret = input("CloudFlare Client Secret: ").strip()
            if client_secret:
                self.config.cf_client_secret = client_secret
                break
            logger.error("CloudFlare Client Secret is required")

    def collect_config(self) -> None:
        """Collect configuration interactively."""
        if not self.config:
            self.init_config(InstallationScenario.ALL)

        if self.config:
            logger.info(f"Collecting configuration for {self.config.scenario.value}")

            # Collect HA URL if not set
            if not self.config.ha_base_url:
                self._collect_ha_url()

            # Scenario-specific configuration
            if self.config.scenario == InstallationScenario.DIRECT_ALEXA:
                self._collect_alexa_config()
            elif self.config.scenario == InstallationScenario.CLOUDFLARE_ALEXA:
                self._collect_alexa_config()
                self._collect_cloudflare_config()
            elif self.config.scenario == InstallationScenario.CLOUDFLARE_IOS:
                self._collect_cloudflare_config()

    def export_config(self) -> None:
        """Export configuration as environment variables."""
        if not self.config:
            return

        os.environ["HA_BASE_URL"] = self.config.ha_base_url or ""
        os.environ["ALEXA_SECRET"] = self.config.alexa_secret or ""
        os.environ["CF_CLIENT_ID"] = self.config.cf_client_id or ""
        os.environ["CF_CLIENT_SECRET"] = self.config.cf_client_secret or ""
        os.environ["AWS_REGION"] = self.config.aws_region

        logger.debug("Configuration exported to environment")

    def get_scenario_resource_requirements(
        self, scenario: InstallationScenario
    ) -> list[ResourceRequirement]:
        """Get required resources for a scenario."""
        if scenario in (
            InstallationScenario.DIRECT_ALEXA,
            InstallationScenario.CLOUDFLARE_ALEXA,
        ):
            return [
                ResourceRequirement(
                    "iam",
                    "ha-lambda-alexa",
                    "IAM role for Lambda execution",
                ),
                ResourceRequirement(
                    "lambda",
                    "ha-alexa-proxy",
                    "Lambda function for Alexa proxy",
                ),
                ResourceRequirement(
                    "ssm",
                    "/ha-alexa/config",
                    "SSM parameter for configuration",
                ),
            ]
        if scenario == InstallationScenario.CLOUDFLARE_IOS:
            return [
                ResourceRequirement(
                    "iam",
                    "ha-lambda-ios",
                    "IAM role for Lambda execution",
                ),
                ResourceRequirement(
                    "lambda",
                    "ha-ios-proxy",
                    "Lambda function for iOS proxy",
                ),
                ResourceRequirement(
                    "ssm",
                    "/ha-ios/config",
                    "SSM parameter for configuration",
                ),
                ResourceRequirement(
                    "url",
                    "ha-ios-proxy",
                    "Lambda function URL",
                ),
            ]

        return []

    def check_aws_resources_for_scenario(
        self, scenario: InstallationScenario
    ) -> ResourceDiscoveryResult:
        """Check existing AWS resources for a scenario."""
        logger.info(f"Checking AWS resources for scenario: {scenario.value}")

        # Get required resources
        required_resources = self.get_scenario_resource_requirements(scenario)
        result = ResourceDiscoveryResult()

        try:
            # Check each required resource
            for req_resource in required_resources:
                logger.debug(
                    f"Checking for {req_resource.resource_type}: "
                    f"{req_resource.resource_id}"
                )

                # Use AWS manager to check for resources
                # For now, we'll mark as not found since resource discovery
                # depends on specific AWS manager methods being available
                logger.debug(
                    f"Resource discovery for {req_resource.resource_type} "
                    "not yet implemented - assuming not found"
                )

                # Add to missing resources for now
                result.missing_resources.append(req_resource)
                logger.info(
                    f"❌ Missing {req_resource.resource_type}: "
                    f"{req_resource.resource_id}"
                )

        except (ValueError, ConnectionError, OSError) as e:
            logger.error(f"Error during AWS resource discovery: {e}")
            # Add all as missing if we can't check
            result.missing_resources.extend(required_resources)

        logger.info(
            f"Resource discovery complete: {len(result.found_resources)} found, "
            f"{len(result.missing_resources)} missing"
        )
        return result

    def get_aws_account_id(self) -> str:
        """Get AWS account ID using AWS adapter."""
        try:
            aws_manager = get_aws_manager()
            result = aws_manager.validate_aws_access()
            if result.status == "success" and result.resource:
                # result.resource contains the caller identity from STS
                return str(result.resource["Account"])

            raise HAConnectorError(
                "Failed to get AWS account ID - AWS credentials not available"
            )
        except Exception as exc:
            raise HAConnectorError(
                "Failed to get AWS account ID - AWS credentials not available"
            ) from exc

    def check_aws_credentials(self) -> bool:
        """Check AWS credentials using AWS adapter."""
        try:
            aws_manager = get_aws_manager()
            result = aws_manager.validate_aws_access()
            return result.status == "success"
        except (ImportError, AttributeError, TypeError) as exc:
            # Handle module import errors or unexpected structure changes
            logger.debug(f"AWS adapter error: {exc}")
            return False

    def check_tool_availability(self, tool: str) -> bool:
        """Check if a command-line tool is available using shutil.which."""
        return shutil.which(tool) is not None

    def build_resource_specs_for_scenario(
        self, scenario: InstallationScenario
    ) -> list[dict[str, Any]]:
        """Build resource specifications for deployment."""
        if not self.config:
            raise HAConnectorError("Configuration not initialized")

        specs: list[dict[str, Any]] = []

        # Get AWS account ID
        try:
            result = safe_exec(
                "Get AWS account ID",
                [
                    "aws",
                    "sts",
                    "get-caller-identity",
                    "--query",
                    "Account",
                    "--output",
                    "text",
                ],
                check=True,
            )
            account_id = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise HAConnectorError(
                "Failed to get AWS account ID - AWS CLI not available or not configured"
            ) from exc
        except (AttributeError, TypeError) as exc:
            raise HAConnectorError(
                "Failed to get AWS account ID - invalid result format"
            ) from exc

        if scenario == InstallationScenario.DIRECT_ALEXA:
            # IAM Role
            specs.append(
                {
                    "type": "iam",
                    "spec": {
                        "role_name": "ha-lambda-alexa",
                        "trust_policy": LAMBDA_ASSUME_ROLE_POLICY,
                    },
                }
            )

            # Lambda Function
            specs.append(
                {
                    "type": "lambda",
                    "spec": {
                        "function_name": "ha-alexa-proxy",
                        "runtime": "python3.11",
                        "handler": "alexa_wrapper.lambda_handler",
                        "role_arn": f"arn:aws:iam::{account_id}:role/ha-lambda-alexa",
                        "package_path": os.path.join(os.getcwd(), "alexa_wrapper.zip"),
                    },
                }
            )

            # SSM Parameter
            ssm_value = {
                "HA_BASE_URL": self.config.ha_base_url or "",
                "ALEXA_SECRET": self.config.alexa_secret or "",
            }
            specs.append(
                {
                    "type": "ssm",
                    "spec": {
                        "parameter_name": "/ha-alexa/config",
                        "parameter_value": ssm_value,
                        "parameter_type": "SecureString",
                    },
                }
            )

            # Function URL
            specs.append(
                {
                    "type": "url",
                    "spec": {"function_name": "ha-alexa-proxy", "auth_type": "NONE"},
                }
            )

        elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            # Same as direct Alexa but with CloudFlare configuration included

            # IAM Role
            specs.append(
                {
                    "type": "iam",
                    "spec": {
                        "role_name": "ha-lambda-alexa",
                        "trust_policy": LAMBDA_ASSUME_ROLE_POLICY,
                        "policies": [
                            (
                                "arn:aws:iam::aws:policy/service-role/"
                                "AWSLambdaBasicExecutionRole"
                            ),
                            "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
                        ],
                    },
                }
            )

            # Lambda Function
            specs.append(
                {
                    "type": "lambda",
                    "spec": {
                        "function_name": "ha-alexa-proxy",
                        "runtime": "python3.11",
                        "handler": "alexa_wrapper.lambda_handler",
                        "role_arn": f"arn:aws:iam::{account_id}:role/ha-lambda-alexa",
                        "package_path": os.path.join(os.getcwd(), "alexa_wrapper.zip"),
                    },
                }
            )

            # SSM Parameter with CloudFlare config
            ssm_value = {
                "HA_BASE_URL": self.config.ha_base_url or "",
                "ALEXA_SECRET": self.config.alexa_secret or "",
                "CF_CLIENT_ID": self.config.cf_client_id or "",
                "CF_CLIENT_SECRET": self.config.cf_client_secret or "",
            }
            specs.append(
                {
                    "type": "ssm",
                    "spec": {
                        "parameter_name": "/ha-alexa/config",
                        "parameter_value": ssm_value,
                        "parameter_type": "SecureString",
                    },
                }
            )

            # Function URL
            specs.append(
                {
                    "type": "url",
                    "spec": {"function_name": "ha-alexa-proxy", "auth_type": "NONE"},
                }
            )

        elif scenario == InstallationScenario.CLOUDFLARE_IOS:
            # iOS scenario with CloudFlare

            # IAM Role for iOS
            specs.append(
                {
                    "type": "iam",
                    "spec": {
                        "role_name": "ha-lambda-ios",
                        "trust_policy": LAMBDA_ASSUME_ROLE_POLICY,
                        "policies": [
                            (
                                "arn:aws:iam::aws:policy/service-role/"
                                "AWSLambdaBasicExecutionRole"
                            ),
                            "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
                        ],
                    },
                }
            )

            # Lambda Function for iOS
            specs.append(
                {
                    "type": "lambda",
                    "spec": {
                        "function_name": "ha-ios-proxy",
                        "runtime": "python3.11",
                        "handler": "ios_wrapper.lambda_handler",
                        "role_arn": f"arn:aws:iam::{account_id}:role/ha-lambda-ios",
                        "package_path": os.path.join(os.getcwd(), "ios_wrapper.zip"),
                    },
                }
            )

            # SSM Parameter for iOS with CloudFlare config
            ssm_value = {
                "HA_BASE_URL": self.config.ha_base_url or "",
                "CF_CLIENT_ID": self.config.cf_client_id or "",
                "CF_CLIENT_SECRET": self.config.cf_client_secret or "",
            }
            specs.append(
                {
                    "type": "ssm",
                    "spec": {
                        "parameter_name": "/ha-ios/config",
                        "parameter_value": ssm_value,
                        "parameter_type": "SecureString",
                    },
                }
            )

            # Function URL for iOS
            specs.append(
                {
                    "type": "url",
                    "spec": {"function_name": "ha-ios-proxy", "auth_type": "NONE"},
                }
            )

        return specs

    def discover_aws_resources(self) -> ResourceDiscoveryResult:
        """Discover existing AWS resources using CRUD operations.

        Returns:
            ResourceDiscoveryResult with found and missing resources
        """
        logger.info("🔍 Discovering existing AWS resources using CRUD interface...")

        try:
            aws_manager = get_aws_manager()
            result = ResourceDiscoveryResult()

            # Use scenario requirements to check for specific resources
            if self.config:
                requirements = self._get_scenario_requirements()

                for requirement in requirements:
                    discovered_resource = self._check_specific_resource(
                        aws_manager, requirement
                    )
                    if discovered_resource:
                        result.possible_resources.append(discovered_resource)

            logger.info(
                f"📋 Found {len(result.possible_resources)} existing AWS resources"
            )
            return result

        except (ImportError, AttributeError, ValueError, KeyError) as e:
            logger.error(f"❌ Resource discovery failed: {e}")
            return ResourceDiscoveryResult()

    def _check_specific_resource(
        self, aws_manager: Any, requirement: ResourceRequirement
    ) -> dict[str, Any] | None:
        """Check if a specific resource exists using CRUD read operations."""
        try:
            # Map requirement types to AWS resource types
            resource_type_map = {
                "iam": AWSResourceType.IAM,
                "lambda": AWSResourceType.LAMBDA,
                "ssm": AWSResourceType.SSM,
                "logs": AWSResourceType.LOGS,
                "url": AWSResourceType.TRIGGER,  # Function URLs are triggers
            }

            aws_resource_type = resource_type_map.get(requirement.resource_type)
            if not aws_resource_type:
                logger.debug(f"Unknown resource type: {requirement.resource_type}")
                return None

            # Try to read the specific resource
            response = aws_manager.read_resource(
                aws_resource_type, requirement.resource_id
            )

            if response.status == "success" and response.resource:
                logger.info(
                    f"✅ Found existing {requirement.resource_type}: "
                    f"{requirement.resource_id}"
                )
                return {
                    "resource_type": requirement.resource_type,
                    "resource_id": requirement.resource_id,
                    "arn": response.resource.get("Arn", ""),
                    "exists": True,
                    "details": response.resource,
                    "discovered_patterns": [requirement.resource_id],  # Exact match
                }

            logger.debug(
                f"Resource not found: {requirement.resource_type}:"
                f"{requirement.resource_id}"
            )
            return None

        except (ImportError, AttributeError, ValueError, KeyError) as e:
            logger.debug(f"Error checking resource {requirement.resource_id}: {e}")
            return None

    def match_resources_to_requirements(
        self, requirements: list[ResourceRequirement]
    ) -> list[MatchedResource]:
        """Match discovered resources to scenario requirements using CRUD operations.

        Args:
            requirements: List of required resources for the scenario

        Returns:
            List of matched resources that exist
        """
        logger.info("🔍 Matching requirements to existing resources...")

        matched_resources: list[MatchedResource] = []

        for requirement in requirements:
            # Use CRUD-based discovery to check if specific resource exists
            discovery_result = self.discover_aws_resources()

            # Look for exact matches first
            exact_match = None
            for possible_resource in discovery_result.possible_resources:
                if (
                    possible_resource["resource_type"] == requirement.resource_type
                    and possible_resource["resource_id"] == requirement.resource_id
                ):
                    exact_match = possible_resource
                    break

            if exact_match:
                matched_resources.append(
                    MatchedResource(
                        resource_type=requirement.resource_type,
                        resource_id=exact_match["resource_id"],
                        resource=exact_match,
                        exists=True,
                    )
                )
                logger.info(
                    f"✅ Found match for {requirement.resource_type}: "
                    f"{exact_match['resource_id']}"
                )
            else:
                logger.info(
                    f"❌ No match found for {requirement.resource_type}: "
                    f"{requirement.resource_id}"
                )

        return matched_resources

    def collect_config_with_discovery(self) -> None:
        """Collect configuration with automatic resource discovery."""
        if not self.config:
            logger.error("Configuration not initialized")
            return

        logger.info(
            "🚀 Starting enhanced configuration collection with resource discovery..."
        )

        # First collect basic configuration
        self.collect_config()

        # Then perform resource discovery
        if self.config.scenario != InstallationScenario.ALL:
            requirements = self._get_scenario_requirements()
            matched_resources = self.match_resources_to_requirements(requirements)

            if matched_resources:
                logger.info("💡 Found existing resources that could be reused:")
                for match in matched_resources:
                    logger.info(f"  • {match.resource_type}: {match.resource_id}")

                # Ask user if they want to use existing resources
                use_existing = (
                    input("Use existing resources where possible? (Y/n): ")
                    .strip()
                    .lower()
                )
                if use_existing in ["", "y", "yes"]:
                    self._apply_discovered_resources(matched_resources)
            else:
                logger.info("ℹ️  No existing resources found - will create new ones")

    def _get_scenario_requirements(self) -> list[ResourceRequirement]:
        """Get resource requirements for the current scenario."""
        if not self.config:
            return []

        requirements: list[ResourceRequirement] = []
        scenario = self.config.scenario

        if scenario in [
            InstallationScenario.DIRECT_ALEXA,
            InstallationScenario.CLOUDFLARE_ALEXA,
        ]:
            requirements.extend(
                [
                    ResourceRequirement(
                        "iam", "ha-lambda-alexa", "IAM role for Alexa Lambda"
                    ),
                    ResourceRequirement(
                        "lambda", "ha-alexa-proxy", "Lambda function for Alexa"
                    ),
                    ResourceRequirement(
                        "ssm", "/ha-alexa/config", "SSM parameter for Alexa config"
                    ),
                ]
            )

        if scenario in [InstallationScenario.CLOUDFLARE_IOS]:
            requirements.extend(
                [
                    ResourceRequirement(
                        "iam", "ha-lambda-ios", "IAM role for iOS Lambda"
                    ),
                    ResourceRequirement(
                        "lambda", "ha-ios-proxy", "Lambda function for iOS"
                    ),
                    ResourceRequirement(
                        "ssm", "/ha-ios/config", "SSM parameter for iOS config"
                    ),
                ]
            )

        return requirements

    def _apply_discovered_resources(
        self, matched_resources: list[MatchedResource]
    ) -> None:
        """Apply discovered resources to avoid creating duplicates."""
        logger.info("🔧 Applying discovered resources to configuration...")

        for match in matched_resources:
            logger.info(
                f"📌 Will reuse existing {match.resource_type}: {match.resource_id}"
            )

        # This could be enhanced to store the matched resources
        # for use during deployment. For now, we just log the matches

    # Ensure a list is always returned (dead code, remove)


# Global configuration manager instance
config_manager = ConfigurationManager()
