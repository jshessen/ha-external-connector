"""
Integration tests for Lambda Deployment System

Comprehensive integration tests that validate the complete deployment workflow,
performance optimizations, and end-to-end functionality.
"""

import tempfile
import time
from pathlib import Path

import pytest

from scripts.lambda_deployment.deployment_manager import (
    DeploymentManager,
    ImportClassifier,
    ImportParser,
    LambdaMarkerValidator,
)


class TestIntegrationDeploymentWorkflow:
    """Integration tests for complete deployment workflows"""

    @pytest.fixture(name="integration_environment")
    def integration_environment_fixture(self):
        """Create a complete integration test environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            source_dir = temp_path / "source"
            deployment_dir = temp_path / "deployment"
            lambda_functions_dir = source_dir / "lambda_functions"

            source_dir.mkdir()
            deployment_dir.mkdir()
            lambda_functions_dir.mkdir()

            # Create sample Lambda function with valid markers
            oauth_gateway = lambda_functions_dir / "oauth_gateway.py"
            oauth_content = '''"""OAuth Gateway Lambda Function"""

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import logging
import os
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
from .shared_configuration import (
    AlexaValidator,
    RateLimiter,
    SecurityValidator,
    load_configuration
)
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """OAuth Gateway Lambda handler"""
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared configuration
        config = load_configuration("oauth_gateway")
        validator = AlexaValidator()
        rate_limiter = RateLimiter()
        
        # Validate request
        if not validator.validate_request(event):
            return {"statusCode": 400, "body": "Invalid request"}
        
        # Check rate limits
        if not rate_limiter.check_limit(event.get("requestId", "")):
            return {"statusCode": 429, "body": "Rate limit exceeded"}
        
        # Process OAuth request
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "OAuth processed successfully"})
        }
        
    except Exception as e:
        logger.error("OAuth processing failed: %s", str(e))
        return {"statusCode": 500, "body": "Internal server error"}

# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
'''
            oauth_gateway.write_text(oauth_content)

            # Create shared configuration file
            shared_config = lambda_functions_dir / "shared_configuration.py"
            shared_content = '''"""Shared configuration module"""

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import logging
from typing import Dict, Any, Optional
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

class AlexaValidator:
    """Alexa request validator"""
    
    def validate_request(self, event: Dict[str, Any]) -> bool:
        """Validate Alexa request"""
        return isinstance(event, dict)

class RateLimiter:
    """Rate limiting functionality"""
    
    def check_limit(self, request_id: str) -> bool:
        """Check rate limits"""
        return True  # Always allow for testing

class SecurityValidator:
    """Security validation"""
    
    def validate_security(self, event: Dict[str, Any]) -> bool:
        """Validate security context"""
        return True

def load_configuration(service_name: str) -> Dict[str, Any]:
    """Load configuration for service"""
    return {
        "service": service_name,
        "timeout": 30,
        "memory": 256
    }

# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
'''
            shared_config.write_text(shared_content)

            yield {
                "temp_path": temp_path,
                "source_dir": source_dir,
                "deployment_dir": deployment_dir,
                "lambda_functions_dir": lambda_functions_dir,
                "oauth_gateway": oauth_gateway,
                "shared_config": shared_config
            }

    def test_complete_deployment_workflow(self, integration_environment):
        """Test complete deployment workflow from source to deployment"""
        env = integration_environment

        # Initialize deployment manager
        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"])
        )

        # Update manager configuration to only process existing files
        manager.config.lambda_functions = ["oauth_gateway.py"]

        # Process deployment
        results = manager.process_deployment(force_rebuild=True)

        # Validate results
        assert results["success"] is True
        assert len(results["processed_files"]) > 0
        assert "oauth_gateway.py" in results["processed_files"]
        assert len(results["errors"]) == 0

        # Check deployment file was created
        deployment_file = env["deployment_dir"] / "oauth_gateway.py"
        assert deployment_file.exists()

        # Validate deployment file content
        deployment_content = deployment_file.read_text()
        assert "=== EMBEDDED SHARED CODE (AUTO-GENERATED) ===" in deployment_content
        assert "class AlexaValidator:" in deployment_content
        assert "def lambda_handler" in deployment_content

        # Ensure shared imports are removed
        assert "from .shared_configuration import" not in deployment_content

    def test_deployment_with_import_analysis(self, integration_environment):
        """Test deployment with detailed import analysis"""
        env = integration_environment

        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"])
        )

        results = manager.process_deployment()

        # Check import analysis results
        assert "import_analysis" in results
        assert "oauth_gateway.py" in results["import_analysis"]

        import_analysis = results["import_analysis"]["oauth_gateway.py"]

        # Validate import categorization
        assert "standard_library" in import_analysis
        assert "third_party" in import_analysis
        assert "shared_config" in import_analysis

        # Check standard library imports
        std_imports = import_analysis["standard_library"]
        assert len(std_imports) > 0

        # Check shared config imports
        shared_imports = import_analysis["shared_config"]
        assert len(shared_imports) > 0

    def test_marker_validation_integration(self, integration_environment):
        """Test marker validation integration"""
        env = integration_environment

        validator = LambdaMarkerValidator(str(env["lambda_functions_dir"]))
        results = validator.validate_all_lambda_markers()

        # Should find oauth_gateway.py and shared_configuration.py
        assert len(results) >= 2
        assert "oauth_gateway.py" in results
        assert "shared_configuration.py" in results

        # Both should be valid (have proper markers)
        oauth_result = results["oauth_gateway.py"]
        assert oauth_result.is_valid is True
        assert len(oauth_result.missing_markers) == 0

    def test_error_handling_integration(self, integration_environment):
        """Test error handling in deployment workflow"""
        env = integration_environment

        # Create invalid source directory
        invalid_dir = env["temp_path"] / "invalid"

        manager = DeploymentManager(
            source_dir=str(invalid_dir),
            deployment_dir=str(env["deployment_dir"])
        )

        results = manager.process_deployment()

        # Should handle errors gracefully
        assert results["success"] is False
        assert len(results["errors"]) > 0
        assert len(results["processed_files"]) == 0


class TestPerformanceBenchmarks:
    """Performance benchmark tests for deployment optimizations"""

    def test_import_classification_performance(self):
        """Benchmark import classification performance"""
        classifier = ImportClassifier()

        # Test modules
        test_modules = [
            "os", "sys", "json", "time", "datetime", "logging",
            "boto3", "botocore", "pydantic", "typer", "click",
            "custom_module", "local_package", "unknown_module"
        ] * 100  # 1300 total classifications

        # Benchmark classification
        start_time = time.time()

        for module in test_modules:
            classifier.classify_module(module)

        elapsed = time.time() - start_time

        # Should be very fast (O(1) lookups)
        assert elapsed < 0.1  # Should complete in under 100ms

        # Calculate operations per second
        ops_per_second = len(test_modules) / elapsed
        assert ops_per_second > 10000  # Should handle 10k+ classifications per second

    def test_import_parsing_performance(self):
        """Benchmark import parsing performance"""
        # Create a file with many imports
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write many import statements
            for i in range(200):
                f.write(f"import module_{i}\n")
                f.write(f"from package_{i} import function_{i}\n")
                f.write(f"from .relative_{i} import Class_{i}\n")

            f.write("\ndef main(): pass\n")  # End with actual code
            temp_file = Path(f.name)

        try:
            parser = ImportParser("shared_configuration")

            # Benchmark parsing
            start_time = time.time()
            result = parser.parse_file_imports(temp_file)
            elapsed = time.time() - start_time

            # Should be fast even with many imports
            assert elapsed < 0.5  # Should complete in under 500ms
            assert isinstance(result, dict)
            assert len(result["standard_library"]) > 0

        finally:
            temp_file.unlink()

    def test_deployment_scaling_performance(self, integration_environment):
        """Test deployment performance with multiple files"""
        env = integration_environment

        # Create multiple Lambda function files
        function_count = 5
        for i in range(function_count):
            func_file = env["lambda_functions_dir"] / f"lambda_function_{i}.py"
            func_content = f'''"""Lambda function {i}"""

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import logging
import boto3
from .shared_configuration import load_configuration
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    """Handler for lambda function {i}"""
    config = load_configuration("lambda_{i}")
    return {{"statusCode": 200, "body": "Function {i} executed"}}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
'''
            func_file.write_text(func_content)

        # Update manager configuration
        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"])
        )

        # Override lambda functions list to include new files
        manager.config.lambda_functions = [
            f"lambda_function_{i}.py" for i in range(function_count)
        ] + ["oauth_gateway.py"]

        # Benchmark deployment
        start_time = time.time()
        results = manager.process_deployment()
        elapsed = time.time() - start_time

        # Should scale reasonably with multiple files
        assert elapsed < 5.0  # Should complete in under 5 seconds
        assert results["success"] is True
        assert len(results["processed_files"]) == function_count + 1  # +1 for oauth_gateway

        # Check performance metrics
        assert "performance_metrics" in results
        assert "total_time" in results["performance_metrics"]


class TestSecurityValidation:
    """Security validation tests"""

    def test_input_sanitization(self, integration_environment):
        """Test input sanitization and validation"""
        env = integration_environment

        # Test with invalid paths
        with pytest.raises(ValueError, match="Cannot create directory"):
            DeploymentManager(
                source_dir="/invalid\x00path",  # Null byte injection
                deployment_dir=str(env["deployment_dir"])
            )

    def test_file_operation_security(self, integration_environment):
        """Test secure file operations"""
        env = integration_environment

        # Create manager
        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"])
        )

        # Test with non-existent file
        non_existent = env["lambda_functions_dir"] / "non_existent.py"

        with pytest.raises(ValueError, match="Import parsing failed"):
            manager.import_parser.parse_file_imports(non_existent)

    def test_error_information_disclosure(self, integration_environment):
        """Test that errors don't disclose sensitive information"""
        env = integration_environment

        # Create file with syntax error
        invalid_file = env["lambda_functions_dir"] / "invalid.py"
        invalid_file.write_text("import json\nfrom .shared import (\n# Missing closing paren")

        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"])
        )

        # Should handle syntax errors gracefully
        with pytest.raises(ValueError, match="Import parsing failed"):
            manager.import_parser.parse_file_imports(invalid_file)


class TestDocumentationGeneration:
    """Test documentation and reporting generation"""

    def test_validation_report_generation(self, integration_environment):
        """Test comprehensive validation report generation"""
        env = integration_environment

        validator = LambdaMarkerValidator(str(env["lambda_functions_dir"]))
        results = validator.validate_all_lambda_markers()

        # Generate report manually (since we can't import the script function easily)
        report_data = {}
        for file_name, result in results.items():
            report_data[file_name] = {
                "valid": result.is_valid,
                "missing_markers": len(result.missing_markers),
                "orphaned_code": len(result.orphaned_code),
                "performance": result.performance_metrics
            }

        # Validate report data structure
        assert len(report_data) > 0
        assert "oauth_gateway.py" in report_data

        oauth_data = report_data["oauth_gateway.py"]
        assert "valid" in oauth_data
        assert "performance" in oauth_data

    def test_deployment_metrics_collection(self, integration_environment):
        """Test deployment metrics collection"""
        env = integration_environment

        manager = DeploymentManager(
            source_dir=str(env["lambda_functions_dir"]),
            deployment_dir=str(env["deployment_dir"]),
            verbose=True
        )

        results = manager.process_deployment()

        # Check metrics collection
        assert "performance_metrics" in results
        metrics = results["performance_metrics"]
        assert "total_time" in metrics
        assert metrics["total_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
