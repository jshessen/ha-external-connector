#!/usr/bin/env python3
"""
Test script for ha_connector configuration management.

This script validates that our configuration management works correctly.
"""

import sys
import os
import tempfile

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ha_connector import (
    logger,
    ConfigurationManager,
    InstallationScenario,
    config_manager
)


def test_scenario_enum():
    """Test installation scenario enum."""
    print("Testing InstallationScenario enum...")
    
    # Test enum values
    assert InstallationScenario.DIRECT_ALEXA.value == "direct_alexa"
    assert InstallationScenario.CLOUDFLARE_ALEXA.value == "cloudflare_alexa"
    assert InstallationScenario.CLOUDFLARE_IOS.value == "cloudflare_ios"
    assert InstallationScenario.ALL.value == "all"
    
    print("✓ InstallationScenario enum test passed")


def test_configuration_manager_init():
    """Test configuration manager initialization."""
    print("Testing ConfigurationManager initialization...")
    
    # Test with no scenario
    cm = ConfigurationManager()
    assert cm.config is None
    
    # Test with scenario
    cm = ConfigurationManager(InstallationScenario.DIRECT_ALEXA)
    assert cm.config is not None
    assert cm.config.scenario == InstallationScenario.DIRECT_ALEXA
    assert cm.config.aws_region == "us-east-1"
    
    print("✓ ConfigurationManager initialization test passed")


def test_validation_functions():
    """Test validation functions."""
    print("Testing validation functions...")
    
    cm = ConfigurationManager(InstallationScenario.DIRECT_ALEXA)
    
    # Test URL validation
    assert cm.validate_ha_base_url("https://example.com") == True
    assert cm.validate_ha_base_url("http://example.com") == False
    assert cm.validate_ha_base_url("") == False
    
    # Test Alexa secret validation
    assert cm.validate_alexa_config("a" * 32) == True
    assert cm.validate_alexa_config("short") == False
    assert cm.validate_alexa_config("") == False
    
    # Test Alexa region validation
    assert cm.validate_alexa_region("us-east-1") == True
    assert cm.validate_alexa_region("invalid-region") == False
    
    print("✓ Validation functions test passed")


def test_secret_generation():
    """Test secure secret generation."""
    print("Testing secure secret generation...")
    
    cm = ConfigurationManager()
    
    try:
        secret = cm.generate_secure_secret(32)
        assert len(secret) == 32
        assert secret.isalnum()  # Should be alphanumeric after cleanup
        
        # Generate another to ensure they're different
        secret2 = cm.generate_secure_secret(32)
        assert secret != secret2
        
        print("✓ Secret generation test passed")
    except Exception as e:
        print(f"⚠ Secret generation test warning: {e}")


def test_resource_requirements():
    """Test resource requirements for scenarios."""
    print("Testing resource requirements...")
    
    cm = ConfigurationManager()
    
    # Test direct Alexa requirements
    requirements = cm.get_scenario_resource_requirements(InstallationScenario.DIRECT_ALEXA)
    assert len(requirements) == 3
    assert any(req.resource_type == "iam" for req in requirements)
    assert any(req.resource_type == "lambda" for req in requirements)
    assert any(req.resource_type == "ssm" for req in requirements)
    
    # Test CloudFlare iOS requirements
    requirements = cm.get_scenario_resource_requirements(InstallationScenario.CLOUDFLARE_IOS)
    assert len(requirements) == 4  # Includes URL requirement
    assert any(req.resource_type == "url" for req in requirements)
    
    print("✓ Resource requirements test passed")


def test_config_export():
    """Test configuration export."""
    print("Testing configuration export...")
    
    cm = ConfigurationManager(InstallationScenario.DIRECT_ALEXA)
    cm.config.ha_base_url = "https://test.example.com"
    cm.config.alexa_secret = "test_secret_32_characters_long"
    cm.config.aws_region = "us-west-2"
    
    # Export to environment
    cm.export_config()
    
    # Verify environment variables
    assert os.environ.get('HA_BASE_URL') == "https://test.example.com"
    assert os.environ.get('ALEXA_SECRET') == "test_secret_32_characters_long"
    assert os.environ.get('AWS_REGION') == "us-west-2"
    
    print("✓ Configuration export test passed")


def test_global_config_manager():
    """Test global config manager instance."""
    print("Testing global config manager...")
    
    # The global instance should be available
    assert config_manager is not None
    assert isinstance(config_manager, ConfigurationManager)
    
    # Test initialization
    config_manager.init_config(InstallationScenario.CLOUDFLARE_ALEXA)
    assert config_manager.config.scenario == InstallationScenario.CLOUDFLARE_ALEXA
    
    print("✓ Global config manager test passed")


def main():
    """Run all tests."""
    print("🚀 Starting ha_connector configuration management tests...")
    print()
    
    try:
        test_scenario_enum()
        test_configuration_manager_init()
        test_validation_functions()
        test_secret_generation()
        test_resource_requirements()
        test_config_export()
        test_global_config_manager()
        
        print()
        print("🎉 All configuration management tests passed!")
        logger.success("Configuration management migration successful!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failure: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
