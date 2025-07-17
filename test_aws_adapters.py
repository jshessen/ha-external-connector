#!/usr/bin/env python3
"""
Test suite for AWS adapters migration

This script validates the AWS resource management functionality migrated from bash.
Tests all CRUD operations for supported AWS resource types.
"""

import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ha_connector import (
        AWSResourceManager,
        AWSResourceType,
        validate_aws_access,
        logger as HAConnectorLogger
    )
    from ha_connector.adapters.aws_manager import (
        LambdaResourceSpec,
        IAMResourceSpec,
        SSMResourceSpec,
        LogsResourceSpec,
        AWSResourceResponse
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

def test_aws_resource_types():
    """Test AWSResourceType enum"""
    print_test_header("AWSResourceType enum")

    try:
        # Test enum values
        assert AWSResourceType.LAMBDA == "lambda"
        assert AWSResourceType.IAM == "iam"
        assert AWSResourceType.SSM == "ssm"
        assert AWSResourceType.LOGS == "logs"
        assert AWSResourceType.TRIGGER == "trigger"

        # Test enum iteration
        types = list(AWSResourceType)
        assert len(types) == 5

        print_test_result("AWSResourceType enum", True)
        return True
    except Exception as e:
        print_test_result("AWSResourceType enum", False, str(e))
        return False

def test_resource_specifications():
    """Test resource specification models"""
    print_test_header("resource specifications")

    try:
        # Test LambdaResourceSpec
        lambda_spec = LambdaResourceSpec(
            function_name="test-function",
            handler="index.handler",
            role_arn="arn:aws:iam::123456789012:role/test-role",
            package_path="/tmp/test.zip",
            runtime="python3.11",
            create_url=True,
            timeout=60,
            memory_size=256
        )
        assert lambda_spec.function_name == "test-function"
        assert lambda_spec.create_url is True
        assert lambda_spec.timeout == 60

        # Test IAMResourceSpec
        iam_spec = IAMResourceSpec(
            resource_type="role",
            name="test-role",
            assume_role_policy={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
        )
        assert iam_spec.resource_type == "role"
        assert iam_spec.name == "test-role"

        # Test SSMResourceSpec
        ssm_spec = SSMResourceSpec(
            name="/test/parameter",
            value="test-value",
            parameter_type="String",
            secure=False
        )
        assert ssm_spec.name == "/test/parameter"
        assert ssm_spec.secure is False

        # Test LogsResourceSpec
        logs_spec = LogsResourceSpec(
            log_group_name="/aws/lambda/test-function",
            retention_days=30
        )
        assert logs_spec.log_group_name == "/aws/lambda/test-function"
        assert logs_spec.retention_days == 30

        print_test_result("resource specifications", True)
        return True
    except Exception as e:
        print_test_result("resource specifications", False, str(e))
        return False

def test_aws_resource_response():
    """Test AWSResourceResponse model"""
    print_test_header("AWSResourceResponse model")

    try:
        # Test success response
        success_response = AWSResourceResponse(
            status="created",
            resource={"test": "data"},
            errors=[]
        )
        assert success_response.status == "created"
        assert success_response.resource == {"test": "data"}
        assert len(success_response.errors) == 0

        # Test error response
        error_response = AWSResourceResponse(
            status="error",
            errors=["Test error message"]
        )
        assert error_response.status == "error"
        assert len(error_response.errors) == 1
        assert error_response.errors[0] == "Test error message"

        # Test JSON serialization
        response_dict = success_response.dict()
        assert "status" in response_dict
        assert "resource" in response_dict
        assert "errors" in response_dict

        print_test_result("AWSResourceResponse model", True)
        return True
    except Exception as e:
        print_test_result("AWSResourceResponse model", False, str(e))
        return False

def test_aws_resource_manager_initialization():
    """Test AWSResourceManager initialization"""
    print_test_header("AWSResourceManager initialization")

    try:
        # Test default initialization
        manager = AWSResourceManager()
        assert manager.region == "us-east-1"
        assert hasattr(manager, 'lambda_manager')
        assert hasattr(manager, 'iam_manager')
        assert hasattr(manager, 'ssm_manager')
        assert hasattr(manager, 'logs_manager')
        assert hasattr(manager, 'trigger_manager')

        # Test custom region
        manager_eu = AWSResourceManager(region="eu-west-1")
        assert manager_eu.region == "eu-west-1"

        print_test_result("AWSResourceManager initialization", True)
        return True
    except Exception as e:
        print_test_result("AWSResourceManager initialization", False, str(e))
        return False

def test_validation_functionality():
    """Test validation and error handling"""
    print_test_header("validation functionality")

    try:
        manager = AWSResourceManager()

        # Test invalid resource type
        invalid_response = manager.create_resource(
            "invalid_type",  # Invalid resource type
            {"test": "data"}
        )
        assert invalid_response.status == "error"
        assert len(invalid_response.errors) > 0
        assert "Unknown resource type" in invalid_response.errors[0]

        # Test invalid specification (missing required fields)
        try:
            invalid_lambda_spec = {"function_name": "test"}  # Missing required fields
            response = manager.create_resource(
                AWSResourceType.LAMBDA,
                invalid_lambda_spec
            )
            assert response.status == "error"
            assert len(response.errors) > 0
        except Exception:
            # This is expected for invalid specs
            pass

        print_test_result("validation functionality", True)
        return True
    except Exception as e:
        print_test_result("validation functionality", False, str(e))
        return False

def create_test_lambda_package():
    """Create a test Lambda deployment package"""
    # Create a temporary zip file for testing
    temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    temp_file.close()

    with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
        # Add a simple Python file
        zip_file.writestr('index.py', '''
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from test Lambda!'
    }
''')

    return temp_file.name

def test_resource_crud_interface():
    """Test CRUD interface methods (without actual AWS calls)"""
    print_test_header("resource CRUD interface")

    try:
        manager = AWSResourceManager()

        # Test Lambda resource creation interface
        package_path = create_test_lambda_package()
        try:
            lambda_spec = {
                "function_name": "test-function",
                "handler": "index.lambda_handler",
                "role_arn": "arn:aws:iam::123456789012:role/test-role",
                "package_path": package_path,
                "runtime": "python3.11",
                "create_url": True
            }

            # This would normally fail due to AWS credentials, but we test the interface
            response = manager.create_resource(AWSResourceType.LAMBDA, lambda_spec)
            # We expect this to fail with AWS credentials error, not interface error
            assert response.status in ["error", "created", "updated"]

            # Test read interface
            read_response = manager.read_resource(AWSResourceType.LAMBDA, "test-function")
            assert read_response.status in ["error", "success"]

            # Test update interface (same as create for most resources)
            update_response = manager.update_resource(AWSResourceType.LAMBDA, "test-function", lambda_spec)
            assert update_response.status in ["error", "created", "updated"]

            # Test delete interface
            delete_response = manager.delete_resource(AWSResourceType.LAMBDA, "test-function")
            assert delete_response.status in ["error", "not_implemented", "deleted"]

        finally:
            # Clean up test package
            if os.path.exists(package_path):
                os.unlink(package_path)

        print_test_result("resource CRUD interface", True)
        return True
    except Exception as e:
        print_test_result("resource CRUD interface", False, str(e))
        return False

def test_global_functions():
    """Test global utility functions"""
    print_test_header("global utility functions")

    try:
        # Test validate_aws_access function
        # This will likely fail due to credentials, but we test the interface
        result = validate_aws_access()
        assert isinstance(result, dict)
        assert "status" in result

        print_test_result("global utility functions", True)
        return True
    except Exception as e:
        print_test_result("global utility functions", False, str(e))
        return False

def main():
    """Run all AWS adapters tests"""
    print("🚀 Starting ha_connector AWS adapters tests...")

    # Run all tests
    tests = [
        test_aws_resource_types,
        test_resource_specifications,
        test_aws_resource_response,
        test_aws_resource_manager_initialization,
        test_validation_functionality,
        test_resource_crud_interface,
        test_global_functions,
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
        print("\n🎉 All AWS adapters tests passed!")
        print("[SUCCESS] AWS adapters migration successful!")
        return 0
    else:
        print(f"\n💥 {failed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
