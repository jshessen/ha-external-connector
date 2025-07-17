"""
Configuration Manager for Home Assistant External Connector.

This module centralizes configuration collection, validation, and state management
for different installation scenarios (direct_alexa, cloudflare_alexa, cloudflare_ios).
"""

import os
import re
import json
import subprocess
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ..utils import (
    logger,
    HAConnectorError,
    ValidationError,
    validate_input,
    safe_exec,
    extract_json_value,
    aws_credentials_check,
    aws_region_check
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
    ha_base_url: Optional[str] = None
    alexa_secret: Optional[str] = None
    cf_client_id: Optional[str] = None
    cf_client_secret: Optional[str] = None
    aws_region: str = "us-east-1"
    
    def __post_init__(self):
        """Initialize from environment variables if not provided."""
        if not self.ha_base_url:
            self.ha_base_url = os.getenv('HA_BASE_URL')
        if not self.alexa_secret:
            self.alexa_secret = os.getenv('ALEXA_SECRET')
        if not self.cf_client_id:
            self.cf_client_id = os.getenv('CF_CLIENT_ID')
        if not self.cf_client_secret:
            self.cf_client_secret = os.getenv('CF_CLIENT_SECRET')
        if not self.aws_region:
            self.aws_region = os.getenv('AWS_REGION', 'us-east-1')


@dataclass
class ResourceRequirement:
    """Specification for a required AWS resource."""
    resource_type: str
    resource_id: str
    description: Optional[str] = None


@dataclass
class MatchedResource:
    """Container for resource discovery results."""
    resource_type: str
    resource_id: str
    resource: Dict[str, Any]
    exists: bool = False


@dataclass
class ResourceDiscoveryResult:
    """Results from AWS resource discovery."""
    found_resources: List[MatchedResource] = field(default_factory=list)
    missing_resources: List[ResourceRequirement] = field(default_factory=list)
    possible_resources: List[Dict[str, Any]] = field(default_factory=list)


class ConfigurationManager:
    """Central configuration manager for HA Connector."""
    
    # Valid AWS regions for Alexa Smart Home
    ALEXA_VALID_REGIONS = ["us-east-1", "eu-west-1", "us-west-2"]
    
    # Resource patterns for possible matches
    IAM_PATTERNS = {
        "ha-lambda-alexa": r"alexa|homeassistant|home.assistant|lambda.*execution",
        "ha-lambda-ios": r"ios|companion|wrapper|lambda.*execution"
    }
    
    LAMBDA_PATTERNS = {
        "ha-alexa-proxy": r"homeassistant|home.assistant|alexa|smarthome|smart.home",
        "ha-ios-proxy": r"ios|companion|wrapper|home.assistant|homeassistant"
    }
    
    SSM_PATTERNS = {
        "/ha-alexa/config": r"alexa.*config|alexa.*app|/ha-alexa/",
        "/ha-ios/config": r"ios.*config|ios.*app|/ha-ios/"
    }
    
    def __init__(self, scenario: Optional[InstallationScenario] = None):
        """Initialize configuration manager."""
        self.config = None
        if scenario:
            self.init_config(scenario)
    
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
        
        if not url.startswith('https://'):
            logger.error(f"HA_BASE_URL must use HTTPS: {url}")
            return False
        
        return True
    
    def validate_alexa_config(self, secret: Optional[str] = None) -> bool:
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
        cf_api_token = os.getenv('CF_API_TOKEN')
        auto_setup = os.getenv('AUTO_SETUP_CLOUDFLARE', 'false').lower() == 'true'
        
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
            logger.error(f"Alexa Skills must be deployed in a supported region: {self.ALEXA_VALID_REGIONS}")
            logger.error(f"Current region: {region}")
            return False
        
        return True
    
    def check_prerequisites_for_scenario(self, scenario: InstallationScenario) -> bool:
        """Check prerequisites for a scenario."""
        # Check basic prerequisites
        try:
            result = subprocess.run(['aws', '--version'], 
                                  capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("AWS CLI is required but not installed")
            return False
        
        try:
            result = subprocess.run(['jq', '--version'], 
                                  capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("jq is required but not installed")
            return False
        
        # Check AWS credentials
        if not aws_credentials_check():
            logger.error("AWS credentials not configured or invalid")
            return False
        
        # Scenario-specific prerequisites
        if scenario in [InstallationScenario.CLOUDFLARE_ALEXA, InstallationScenario.CLOUDFLARE_IOS]:
            cf_api_token = os.getenv('CF_API_TOKEN')
            cf_api_key = os.getenv('CF_API_KEY')
            auto_setup = os.getenv('AUTO_SETUP_CLOUDFLARE', 'false').lower() == 'true'
            
            if not cf_api_token and not cf_api_key and not auto_setup:
                logger.warning("CloudFlare API credentials not set - some validations will be skipped")
        
        return True
    
    def validate_direct_alexa_scenario(self) -> bool:
        """Validate Direct Alexa Integration scenario."""
        logger.debug("Validating Direct Alexa Integration...")
        
        if not self.config:
            return False
        
        valid = True
        
        # Common validations
        if not self.validate_ha_base_url(self.config.ha_base_url or ''):
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
    
    def validate_cloudflare_alexa_scenario(self) -> bool:
        """Validate CloudFlare-Proxied Alexa Integration scenario."""
        logger.debug("Validating CloudFlare-Proxied Alexa Integration...")
        
        valid = True
        
        # First validate direct Alexa requirements
        if not self.validate_direct_alexa_scenario():
            valid = False
        
        # Additional CloudFlare validation
        if not self.validate_cloudflare_config():
            valid = False
        
        # Validate existing CloudFlare Access setup if possible
        if (self.config and self.config.ha_base_url and 
            (os.getenv('CF_API_TOKEN') or (os.getenv('CF_API_KEY') and os.getenv('CF_EMAIL')))):
            
            # Extract domain from URL
            ha_domain = self.config.ha_base_url.replace('https://', '').split('/')[0]
            
            logger.info(f"Validating existing CloudFlare Access setup for: {ha_domain}")
            # Note: CloudFlare validation would be implemented in a separate module
            logger.warning("CloudFlare Access validation not yet implemented in Python version")
        
        if valid:
            logger.success("CloudFlare Alexa scenario validation passed")
        else:
            logger.error("CloudFlare Alexa scenario validation failed")
        
        return valid
    
    def validate_cloudflare_ios_scenario(self) -> bool:
        """Validate iOS Companion with CloudFlare scenario."""
        logger.debug("Validating iOS Companion with CloudFlare...")
        
        if not self.config:
            return False
        
        valid = True
        
        # Common validations
        if not self.validate_ha_base_url(self.config.ha_base_url or ''):
            valid = False
        
        # CloudFlare validation (iOS requires existing CloudFlare setup)
        if not self.validate_cloudflare_config():
            logger.error("CloudFlare Access setup required for iOS scenario")
            logger.error("Either provide existing credentials or run CloudFlare Alexa scenario first")
            valid = False
        
        if valid:
            logger.success("iOS CloudFlare scenario validation passed")
        else:
            logger.error("iOS CloudFlare scenario validation failed")
        
        return valid
    
    def validate_scenario_setup(self, scenario: Optional[InstallationScenario] = None) -> bool:
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
            return self.validate_direct_alexa_scenario()
        elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            return self.validate_cloudflare_alexa_scenario()
        elif scenario == InstallationScenario.CLOUDFLARE_IOS:
            return self.validate_cloudflare_ios_scenario()
        else:
            logger.error(f"Unknown scenario: {scenario}")
            return False
    
    def validate_all_scenarios(self) -> bool:
        """Validate all scenarios."""
        all_passed = True
        supported_scenarios = [
            InstallationScenario.DIRECT_ALEXA,
            InstallationScenario.CLOUDFLARE_ALEXA,
            InstallationScenario.CLOUDFLARE_IOS
        ]
        
        original_scenario = self.config.scenario if self.config else None
        
        for scenario in supported_scenarios:
            logger.info(f"Validating setup for scenario: {scenario.value}")
            if not self.validate_scenario_setup(scenario):
                logger.error(f"Validation failed for scenario: {scenario.value}")
                all_passed = False
        
        # Restore original scenario
        if original_scenario:
            self.config.scenario = original_scenario
        
        if all_passed:
            logger.success("Validation passed for all scenarios")
        else:
            logger.error("Validation failed for one or more scenarios")
        
        return all_passed
    
    def collect_ha_url(self) -> str:
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
                ['openssl', 'rand', '-base64', '48'],
                check=True
            )
            # Clean up the output and truncate to desired length
            secret = result.stdout.strip().replace('=', '').replace('+', '').replace('/', '')
            return secret[:length]
        except Exception:
            logger.error("Failed to generate secure secret")
            raise HAConnectorError("Secret generation failed")
    
    def collect_alexa_config(self) -> None:
        """Collect Alexa configuration interactively."""
        if not self.config or self.config.alexa_secret:
            return
        
        while True:
            secret = input("Alexa secret (32+ characters, press Enter to generate): ").strip()
            if not secret:
                secret = self.generate_secure_secret(32)
                logger.info(f"Generated Alexa secret: {secret}")
                self.config.alexa_secret = secret
                break
            elif len(secret) >= 32:
                self.config.alexa_secret = secret
                break
            else:
                logger.error("Alexa secret must be at least 32 characters")
    
    def collect_cloudflare_config(self) -> None:
        """Collect CloudFlare configuration."""
        if not self.config or self.config.cf_client_id:
            return
        
        logger.info("CloudFlare configuration required")
        # This would integrate with cloudflare_config module when implemented
        logger.warning("CloudFlare configuration collection not yet implemented in Python version")
        logger.info("Please set CF_CLIENT_ID and CF_CLIENT_SECRET environment variables")
    
    def collect_config(self) -> None:
        """Collect configuration interactively."""
        if not self.config:
            self.init_config(InstallationScenario.ALL)
        
        logger.info(f"Collecting configuration for {self.config.scenario.value}")
        
        # Collect HA URL if not set
        if not self.config.ha_base_url:
            self.collect_ha_url()
        
        # Scenario-specific configuration
        if self.config.scenario == InstallationScenario.DIRECT_ALEXA:
            self.collect_alexa_config()
        elif self.config.scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            self.collect_alexa_config()
            self.collect_cloudflare_config()
        elif self.config.scenario == InstallationScenario.CLOUDFLARE_IOS:
            self.collect_cloudflare_config()
    
    def export_config(self) -> None:
        """Export configuration as environment variables."""
        if not self.config:
            return
        
        os.environ['HA_BASE_URL'] = self.config.ha_base_url or ''
        os.environ['ALEXA_SECRET'] = self.config.alexa_secret or ''
        os.environ['CF_CLIENT_ID'] = self.config.cf_client_id or ''
        os.environ['CF_CLIENT_SECRET'] = self.config.cf_client_secret or ''
        os.environ['AWS_REGION'] = self.config.aws_region
        
        logger.debug("Configuration exported to environment")
    
    def get_scenario_resource_requirements(self, scenario: InstallationScenario) -> List[ResourceRequirement]:
        """Get required resources for a scenario."""
        if scenario == InstallationScenario.DIRECT_ALEXA:
            return [
                ResourceRequirement("iam", "ha-lambda-alexa", "IAM role for Lambda execution"),
                ResourceRequirement("lambda", "ha-alexa-proxy", "Lambda function for Alexa proxy"),
                ResourceRequirement("ssm", "/ha-alexa/config", "SSM parameter for configuration")
            ]
        elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            return [
                ResourceRequirement("iam", "ha-lambda-alexa", "IAM role for Lambda execution"),
                ResourceRequirement("lambda", "ha-alexa-proxy", "Lambda function for Alexa proxy"),
                ResourceRequirement("ssm", "/ha-alexa/config", "SSM parameter for configuration")
            ]
        elif scenario == InstallationScenario.CLOUDFLARE_IOS:
            return [
                ResourceRequirement("iam", "ha-lambda-ios", "IAM role for Lambda execution"),
                ResourceRequirement("lambda", "ha-ios-proxy", "Lambda function for iOS proxy"),
                ResourceRequirement("ssm", "/ha-ios/config", "SSM parameter for configuration"),
                ResourceRequirement("url", "ha-ios-proxy", "Lambda function URL")
            ]
        else:
            return []
    
    def check_aws_resources_for_scenario(self, scenario: InstallationScenario) -> ResourceDiscoveryResult:
        """Check existing AWS resources for a scenario."""
        logger.info(f"Checking AWS resources for scenario: {scenario.value}")
        
        # Get required resources
        required_resources = self.get_scenario_resource_requirements(scenario)
        
        # This would use AWS managers/adapters when implemented
        logger.warning("AWS resource discovery not yet fully implemented in Python version")
        logger.info("This would check for existing IAM roles, Lambda functions, and SSM parameters")
        
        # Return empty result for now
        return ResourceDiscoveryResult()
    
    def build_resource_specs_for_scenario(self, scenario: InstallationScenario) -> List[Dict[str, Any]]:
        """Build resource specifications for deployment."""
        if not self.config:
            raise HAConnectorError("Configuration not initialized")
        
        specs = []
        
        # Get AWS account ID
        try:
            result = safe_exec(
                "Get AWS account ID",
                ['aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text'],
                check=True
            )
            account_id = result.stdout.strip()
        except Exception:
            raise HAConnectorError("Failed to get AWS account ID")
        
        if scenario == InstallationScenario.DIRECT_ALEXA:
            # IAM Role
            specs.append({
                "type": "iam",
                "spec": {
                    "role_name": "ha-lambda-alexa",
                    "trust_policy": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    }
                }
            })
            
            # Lambda Function
            specs.append({
                "type": "lambda",
                "spec": {
                    "function_name": "ha-alexa-proxy",
                    "runtime": "python3.11",
                    "handler": "alexa_wrapper.lambda_handler",
                    "role_arn": f"arn:aws:iam::{account_id}:role/ha-lambda-alexa",
                    "package_path": os.path.join(os.getcwd(), "alexa_wrapper.zip")
                }
            })
            
            # SSM Parameter
            ssm_value = {
                "HA_BASE_URL": self.config.ha_base_url or "",
                "ALEXA_SECRET": self.config.alexa_secret or ""
            }
            specs.append({
                "type": "ssm",
                "spec": {
                    "parameter_name": "/ha-alexa/config",
                    "parameter_value": ssm_value,
                    "parameter_type": "SecureString"
                }
            })
            
            # Function URL
            specs.append({
                "type": "url",
                "spec": {
                    "function_name": "ha-alexa-proxy",
                    "auth_type": "NONE"
                }
            })
        
        elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
            # Similar to direct_alexa but with CloudFlare config
            # Implementation would be similar with additional CF parameters
            logger.warning("CloudFlare Alexa resource specs not yet implemented")
        
        elif scenario == InstallationScenario.CLOUDFLARE_IOS:
            # iOS scenario resources
            logger.warning("CloudFlare iOS resource specs not yet implemented")
        
        return specs


# Global configuration manager instance
config_manager = ConfigurationManager()
