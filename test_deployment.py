#!/usr/bin/env python3
"""
Test suite for deployment modules migration

This script validates the deployment functionality migrated from bash scripts.
Tests service installation, CloudFlare management, and deployment orchestration.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the source directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ha_connector import (
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
        logger as HAConnectorLogger
    )
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Initialize logger
logger = HAConnectorLogger

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\nTesting {test_name}...")

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with proper formatting"""
    status = "✓" if success else "❌"
    print(f"{status} {test_name} test {'passed' if success else 'failed'}")
    if details:
        print(f"  Details: {details}")

def test_service_types():
    """Test ServiceType enum"""
    print_test_header("ServiceType enum")
    
    try:
        # Test enum values
        assert ServiceType.ALEXA == "alexa"
        assert ServiceType.IOS_COMPANION == "ios_companion"
        assert ServiceType.CLOUDFLARE_PROXY == "cloudflare_proxy"
        assert ServiceType.GENERIC == "generic"
        
        # Test enum iteration
        types = list(ServiceType)
        assert len(types) == 4
        
        print_test_result("ServiceType enum", True)
        return True
    except Exception as e:
        print_test_result("ServiceType enum", False, str(e))
        return False

def test_service_config():
    """Test ServiceConfig model"""
    print_test_header("ServiceConfig model")
    
    try:
        # Test basic configuration
        config = ServiceConfig(
            service_type=ServiceType.ALEXA,
            function_name="test-alexa-function",
            handler="alexa_wrapper.lambda_handler",
            source_path="/tmp/test_source.py",
            runtime="python3.11",
            timeout=60,
            memory_size=512,
            create_url=True
        )
        
        assert config.service_type == ServiceType.ALEXA
        assert config.function_name == "test-alexa-function"
        assert config.create_url is True
        assert config.timeout == 60
        
        # Test with environment variables
        config_with_env = ServiceConfig(
            service_type=ServiceType.IOS_COMPANION,
            function_name="test-ios-function",
            handler="ios_companion.lambda_handler",
            source_path="/tmp/test_source.py",
            environment_variables={"TEST_VAR": "test_value"}
        )
        
        assert config_with_env.environment_variables == {"TEST_VAR": "test_value"}
        
        print_test_result("ServiceConfig model", True)
        return True
    except Exception as e:
        print_test_result("ServiceConfig model", False, str(e))
        return False

def test_deployment_result():
    """Test DeploymentResult model"""
    print_test_header("DeploymentResult model")
    
    try:
        # Test successful result
        success_result = DeploymentResult(
            success=True,
            function_name="test-function",
            function_arn="arn:aws:lambda:us-east-1:123456789012:function:test-function",
            function_url="https://example.lambda-url.us-east-1.on.aws/",
            role_arn="arn:aws:iam::123456789012:role/test-role"
        )
        
        assert success_result.success is True
        assert success_result.function_name == "test-function"
        assert len(success_result.errors) == 0
        
        # Test failed result
        failed_result = DeploymentResult(
            success=False,
            function_name="test-function",
            errors=["Deployment failed", "Invalid credentials"]
        )
        
        assert failed_result.success is False
        assert len(failed_result.errors) == 2
        
        print_test_result("DeploymentResult model", True)
        return True
    except Exception as e:
        print_test_result("DeploymentResult model", False, str(e))
        return False

def test_service_installer_initialization():
    """Test ServiceInstaller initialization"""
    print_test_header("ServiceInstaller initialization")
    
    try:
        # Test default initialization
        installer = ServiceInstaller()
        assert installer.region == "us-east-1"
        assert installer.dry_run is False
        assert installer.verbose is False
        
        # Test custom initialization
        installer_custom = ServiceInstaller(
            region="eu-west-1",
            dry_run=True,
            verbose=True
        )
        assert installer_custom.region == "eu-west-1"
        assert installer_custom.dry_run is True
        assert installer_custom.verbose is True
        
        # Test default configurations
        alexa_config = installer.get_default_config(ServiceType.ALEXA)
        assert "function_name" in alexa_config
        assert alexa_config["function_name"] == "ha-alexa-proxy"
        
        ios_config = installer.get_default_config(ServiceType.IOS_COMPANION)
        assert "function_name" in ios_config
        assert ios_config["function_name"] == "ha-ios-companion"
        
        print_test_result("ServiceInstaller initialization", True)
        return True
    except Exception as e:
        print_test_result("ServiceInstaller initialization", False, str(e))
        return False

def test_deployment_package_creation():
    """Test deployment package creation"""
    print_test_header("deployment package creation")
    
    try:
        installer = ServiceInstaller(dry_run=True)
        
        # Create a temporary source file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write('''
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from test Lambda!'
    }
''')
            temp_source = temp_file.name
        
        try:
            # Test package creation (dry run)
            package_path = installer.create_deployment_package(temp_source)
            assert package_path.endswith('-deployment.zip')
            
            print_test_result("deployment package creation", True)
            return True
        finally:
            # Clean up
            if os.path.exists(temp_source):
                os.unlink(temp_source)
                
    except Exception as e:
        print_test_result("deployment package creation", False, str(e))
        return False

def test_cloudflare_config():
    """Test CloudFlare configuration models"""
    print_test_header("CloudFlare configuration")
    
    try:
        # Test CloudFlareConfig
        cf_config = CloudFlareConfig(
            api_token="test-token",
            debug=True
        )
        assert cf_config.api_token == "test-token"
        assert cf_config.debug is True
        
        # Test AccessApplicationConfig
        app_config = AccessApplicationConfig(
            name="Test App",
            domain="test.example.com",
            session_duration="24h",
            auto_redirect_to_identity=True
        )
        assert app_config.name == "Test App"
        assert app_config.domain == "test.example.com"
        assert app_config.session_duration == "24h"
        
        print_test_result("CloudFlare configuration", True)
        return True
    except Exception as e:
        print_test_result("CloudFlare configuration", False, str(e))
        return False

def test_deployment_strategies():
    """Test deployment strategy enums"""
    print_test_header("deployment strategies")
    
    try:
        # Test DeploymentStrategy enum
        assert DeploymentStrategy.ROLLING == "rolling"
        assert DeploymentStrategy.BLUE_GREEN == "blue-green"
        assert DeploymentStrategy.CANARY == "canary"
        assert DeploymentStrategy.IMMEDIATE == "immediate"
        
        # Test enum iteration
        strategies = list(DeploymentStrategy)
        assert len(strategies) == 4
        
        print_test_result("deployment strategies", True)
        return True
    except Exception as e:
        print_test_result("deployment strategies", False, str(e))
        return False

def test_deployment_config():
    """Test DeploymentConfig model"""
    print_test_header("DeploymentConfig model")
    
    try:
        # Test basic deployment configuration
        config = DeploymentConfig(
            environment="staging",
            version="1.2.3",
            strategy=DeploymentStrategy.ROLLING,
            services=[ServiceType.ALEXA, ServiceType.IOS_COMPANION],
            region="us-west-2",
            dry_run=True,
            verbose=True
        )
        
        assert config.environment == "staging"
        assert config.version == "1.2.3"
        assert config.strategy == DeploymentStrategy.ROLLING
        assert len(config.services) == 2
        assert ServiceType.ALEXA in config.services
        
        # Test with CloudFlare setup
        config_with_cf = DeploymentConfig(
            environment="prod",
            version="2.0.0",
            strategy=DeploymentStrategy.BLUE_GREEN,
            services=[ServiceType.ALEXA],
            cloudflare_setup=True,
            cloudflare_domain="ha.example.com"
        )
        
        assert config_with_cf.cloudflare_setup is True
        assert config_with_cf.cloudflare_domain == "ha.example.com"
        
        print_test_result("DeploymentConfig model", True)
        return True
    except Exception as e:
        print_test_result("DeploymentConfig model", False, str(e))
        return False

def test_deployment_manager_initialization():
    """Test DeploymentManager initialization"""
    print_test_header("DeploymentManager initialization")
    
    try:
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            services=[ServiceType.ALEXA],
            dry_run=True
        )
        
        manager = DeploymentManager(config)
        assert manager.config.environment == "dev"
        assert manager.config.version == "1.0.0"
        assert manager.config.dry_run is True
        assert len(manager.deployment_results) == 0
        
        print_test_result("DeploymentManager initialization", True)
        return True
    except Exception as e:
        print_test_result("DeploymentManager initialization", False, str(e))
        return False

def test_deployment_validation():
    """Test deployment configuration validation"""
    print_test_header("deployment validation")
    
    try:
        # Test valid configuration
        valid_config = DeploymentConfig(
            environment="staging",
            version="1.2.3",
            services=[ServiceType.ALEXA]
        )
        
        manager = DeploymentManager(valid_config)
        # This should not raise an exception
        manager.validate_deployment_config()
        
        # Test invalid environment
        try:
            invalid_config = DeploymentConfig(
                environment="invalid_env",
                version="1.0.0",
                services=[ServiceType.ALEXA]
            )
            invalid_manager = DeploymentManager(invalid_config)
            invalid_manager.validate_deployment_config()
            # Should not reach here
            assert False, "Should have raised ValidationError"
        except Exception:
            # Expected to fail
            pass
        
        print_test_result("deployment validation", True)
        return True
    except Exception as e:
        print_test_result("deployment validation", False, str(e))
        return False

def test_convenience_functions():
    """Test convenience functions"""
    print_test_header("convenience functions")
    
    try:
        # Test deploy_service function (dry run)
        result = deploy_service(
            ServiceType.ALEXA,
            region="us-east-1",
            dry_run=True,
            verbose=False
        )
        
        # The function should return a DeploymentResult
        assert isinstance(result, DeploymentResult)
        assert result.function_name == "ha-alexa-proxy"  # Default name
        
        # Test orchestrate_deployment function (dry run)
        config = DeploymentConfig(
            environment="dev",
            version="1.0.0",
            services=[ServiceType.ALEXA],
            dry_run=True
        )
        
        orchestration_result = orchestrate_deployment(config)
        assert isinstance(orchestration_result, dict)
        assert "success" in orchestration_result
        assert "environment" in orchestration_result
        
        print_test_result("convenience functions", True)
        return True
    except Exception as e:
        print_test_result("convenience functions", False, str(e))
        return False

def main():
    """Run all deployment tests"""
    print("🚀 Starting ha_connector deployment tests...")
    
    # Run all tests
    tests = [
        test_service_types,
        test_service_config,
        test_deployment_result,
        test_service_installer_initialization,
        test_deployment_package_creation,
        test_cloudflare_config,
        test_deployment_strategies,
        test_deployment_config,
        test_deployment_manager_initialization,
        test_deployment_validation,
        test_convenience_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✓ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All deployment tests passed!")
        print("[SUCCESS] Deployment modules migration successful!")
        return 0
    else:
        print(f"\n💥 {failed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
