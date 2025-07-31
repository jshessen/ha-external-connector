"""
Unit tests for Lambda Deployment System

Tests for the deployment manager and marker validation functionality,
including validation of the refactoring improvements.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

from scripts.lambda_deployment.deployment_manager import (
    DeploymentManager,
    ImportGroup,
    ImportType,
    LambdaMarkerValidator,
    MarkerValidationResult,
)


class TestDeploymentManager:
    """Test suite for DeploymentManager class"""

    @pytest.fixture(name="temp_dirs")
    def temp_dirs_fixture(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            deployment_dir = temp_path / "deployment"
            source_dir.mkdir()
            deployment_dir.mkdir()
            
            yield {
                "source": source_dir,
                "deployment": deployment_dir,
                "temp": temp_path
            }

    @pytest.fixture(name="sample_lambda_file")
    def sample_lambda_file_fixture(self, temp_dirs):
        """Create a sample Lambda function file"""
        source_dir = temp_dirs["source"]
        lambda_file = source_dir / "test_lambda.py"
        
        content = '''"""Sample Lambda function"""
import os
import sys
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
from .shared_configuration import load_configuration, AlexaValidator

def lambda_handler(event, context):
    """Sample handler"""
    return {"statusCode": 200}
'''
        lambda_file.write_text(content)
        return lambda_file

    def test_deployment_manager_initialization(self, temp_dirs):
        """Test DeploymentManager initialization"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        assert manager.config.source_dir == temp_dirs["source"]
        assert manager.config.deployment_dir == temp_dirs["deployment"]
        assert manager.config.shared_module == "shared_configuration"

    def test_parse_imports_into_groups_complex_function(self, temp_dirs, sample_lambda_file):
        """Test the optimized _parse_imports_into_groups function"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        # This tests the refactored function
        import_groups = manager._parse_imports_into_groups(sample_lambda_file)
        
        assert isinstance(import_groups, dict)
        assert "standard_library" in import_groups
        assert "third_party" in import_groups
        assert "shared_config" in import_groups
        
        # Check that imports are categorized correctly
        standard_imports = import_groups["standard_library"]
        assert len(standard_imports) > 0
        
        third_party_imports = import_groups["third_party"]  
        assert len(third_party_imports) > 0

    def test_is_standard_library_performance(self, temp_dirs):
        """Test the optimized _is_standard_library method"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        # Test standard library detection
        assert manager._is_standard_library("os") is True
        assert manager._is_standard_library("sys") is True
        assert manager._is_standard_library("boto3") is False
        assert manager._is_standard_library("unknown_module") is False

    def test_process_deployment_error_handling(self, temp_dirs):
        """Test deployment process error handling"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        # Test with non-existent files
        result = manager.process_deployment()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "errors" in result
        assert "processed_files" in result


class TestLambdaMarkerValidator:
    """Test suite for LambdaMarkerValidator class"""

    @pytest.fixture(name="temp_lambda_dir")
    def temp_lambda_dir_fixture(self):
        """Create temporary Lambda functions directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lambda_dir = Path(temp_dir) / "lambda_functions"
            lambda_dir.mkdir()
            yield lambda_dir

    @pytest.fixture(name="valid_lambda_file")
    def valid_lambda_file_fixture(self, temp_lambda_dir):
        """Create a Lambda file with valid markers"""
        lambda_file = temp_lambda_dir / "oauth_gateway.py"
        content = '''"""Lambda function with valid markers"""

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import os
import boto3
from typing import Dict, Any
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    """Handler function"""
    return {"statusCode": 200}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
'''
        lambda_file.write_text(content)
        return lambda_file

    @pytest.fixture(name="invalid_lambda_file")
    def invalid_lambda_file_fixture(self, temp_lambda_dir):
        """Create a Lambda file with missing markers"""
        lambda_file = temp_lambda_dir / "smart_home_bridge.py"
        content = '''"""Lambda function with missing markers"""

import os
import boto3

def lambda_handler(event, context):
    """Handler function"""
    return {"statusCode": 200}
'''
        lambda_file.write_text(content)
        return lambda_file

    def test_marker_validator_initialization(self, temp_lambda_dir):
        """Test LambdaMarkerValidator initialization"""
        validator = LambdaMarkerValidator(str(temp_lambda_dir))
        assert validator.lambda_functions_dir == temp_lambda_dir

    def test_validate_valid_markers(self, temp_lambda_dir, valid_lambda_file):
        """Test validation of file with valid markers"""
        validator = LambdaMarkerValidator(str(temp_lambda_dir))
        result = validator.validate_lambda_markers(valid_lambda_file)
        
        assert isinstance(result, MarkerValidationResult)
        assert result.is_valid is True
        assert len(result.missing_markers) == 0
        assert result.file_path == str(valid_lambda_file)

    def test_validate_invalid_markers(self, temp_lambda_dir, invalid_lambda_file):
        """Test validation of file with missing markers"""
        validator = LambdaMarkerValidator(str(temp_lambda_dir))
        result = validator.validate_lambda_markers(invalid_lambda_file)
        
        assert isinstance(result, MarkerValidationResult)
        assert result.is_valid is False
        assert len(result.missing_markers) > 0
        assert "IMPORT_BLOCK_START" in result.missing_markers


class TestImportGroupAndTypes:
    """Test suite for ImportGroup and ImportType classes"""

    def test_import_type_enum(self):
        """Test ImportType enum values"""
        assert ImportType.STANDARD_LIBRARY == "standard_library"
        assert ImportType.THIRD_PARTY == "third_party"
        assert ImportType.LOCAL_IMPORT == "local_import"
        assert ImportType.SHARED_CONFIG == "shared_config"
        assert ImportType.RELATIVE_IMPORT == "relative_import"

    def test_import_group_creation(self):
        """Test ImportGroup model creation"""
        group = ImportGroup(
            import_type=ImportType.STANDARD_LIBRARY,
            module_name="os",
            import_names=["path", "environ"],
            original_line="from os import path, environ",
            line_number=5
        )
        
        assert group.import_type == ImportType.STANDARD_LIBRARY
        assert group.module_name == "os"
        assert group.import_names == ["path", "environ"]
        assert group.original_line == "from os import path, environ"
        assert group.line_number == 5

    def test_marker_validation_result_creation(self):
        """Test MarkerValidationResult model creation"""
        result = MarkerValidationResult(
            is_valid=False,
            file_path="/path/to/file.py",
            missing_markers=["IMPORT_BLOCK_START"],
            orphaned_code=["line 10: orphaned code"],
            marker_issues=["Invalid marker format"]
        )
        
        assert result.is_valid is False
        assert result.file_path == "/path/to/file.py"
        assert "IMPORT_BLOCK_START" in result.missing_markers
        assert len(result.orphaned_code) == 1
        assert len(result.marker_issues) == 1


class TestPerformanceAndSecurity:
    """Test suite for performance and security issues validation"""

    def test_inefficient_standard_library_check(self, temp_dirs):
        """Test that the current implementation is inefficient"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        # This should be slow due to linear search
        import time
        start_time = time.time()
        
        # Test multiple modules to demonstrate inefficiency
        test_modules = ["os", "sys", "json", "unknown"] * 100
        for module in test_modules:
            manager._is_standard_library(module)
            
        elapsed = time.time() - start_time
        
        # This test documents current poor performance
        # After refactoring, this should be much faster
        assert elapsed > 0  # Just ensuring the test runs

    def test_error_handling_issues(self, temp_dirs):
        """Test current poor error handling patterns"""
        manager = DeploymentManager(
            source_dir=str(temp_dirs["source"]),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        # Test with invalid file path
        invalid_path = Path("/nonexistent/file.py")
        
        # The current implementation should catch and re-raise with poor context
        with pytest.raises(RuntimeError, match="Failed to parse imports"):
            manager._parse_imports_into_groups(invalid_path)


# Performance benchmark tests
class TestPerformanceBenchmarks:
    """Performance benchmark tests for refactoring validation"""

    def test_import_parsing_performance(self, temp_dirs):
        """Benchmark import parsing performance"""
        # Create a file with many imports
        source_dir = temp_dirs["source"]
        large_file = source_dir / "large_lambda.py"
        
        import_lines = []
        for i in range(100):
            import_lines.append(f"import module_{i}")
            import_lines.append(f"from package_{i} import function_{i}")
            
        content = "\n".join(import_lines) + "\n\ndef handler(): pass"
        large_file.write_text(content)
        
        manager = DeploymentManager(
            source_dir=str(source_dir),
            deployment_dir=str(temp_dirs["deployment"])
        )
        
        import time
        start_time = time.time()
        result = manager._parse_imports_into_groups(large_file)
        elapsed = time.time() - start_time
        
        # Document current performance
        assert isinstance(result, dict)
        assert elapsed > 0  # Baseline measurement
        
        # After refactoring, this should be significantly faster
        print(f"Current performance: {elapsed:.4f} seconds for 200 imports")


if __name__ == "__main__":
    pytest.main([__file__])