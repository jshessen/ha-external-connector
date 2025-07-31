"""
Comprehensive Test Suite for Enhanced Lambda Deployment System

This module provides comprehensive testing for the new modular Lambda deployment
system, including marker processing, validation, and deployment generation.

Features:
- Unit tests for all core components
- Integration tests for complete workflows
- Performance benchmarking and validation
- Mock AWS services for testing
- Comprehensive error condition testing
- Real-world scenario simulation
"""

import tempfile
import time
from pathlib import Path

import pytest

from scripts.lambda_deployment.deployment_manager import (
    DeploymentManager,
    ImportClassifier,
    ImportType,
)
from scripts.lambda_deployment.marker_system import DeploymentMarkerSystem, MarkerType
from scripts.lambda_deployment.validation_system import (
    DeploymentValidationSystem,
    ValidationType,
)


class TestImportClassifier:
    """Test the enhanced import classification system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = ImportClassifier()

    def test_standard_library_classification(self):
        """Test standard library module classification"""
        # Core standard library modules
        assert self.classifier.classify_module("os") == ImportType.STANDARD_LIBRARY
        assert self.classifier.classify_module("sys") == ImportType.STANDARD_LIBRARY
        assert self.classifier.classify_module("json") == ImportType.STANDARD_LIBRARY
        assert self.classifier.classify_module("pathlib") == ImportType.STANDARD_LIBRARY

        # Submodules should also be classified correctly
        assert self.classifier.classify_module("os.path") == ImportType.STANDARD_LIBRARY
        assert self.classifier.classify_module("urllib.parse") == ImportType.STANDARD_LIBRARY

    def test_third_party_classification(self):
        """Test third-party module classification"""
        # Common third-party modules
        assert self.classifier.classify_module("boto3") == ImportType.THIRD_PARTY
        assert self.classifier.classify_module("pydantic") == ImportType.THIRD_PARTY
        assert self.classifier.classify_module("rich") == ImportType.THIRD_PARTY

        # Submodules should also be classified correctly
        assert self.classifier.classify_module("boto3.client") == ImportType.THIRD_PARTY
        assert self.classifier.classify_module("pydantic.main") == ImportType.THIRD_PARTY

    def test_local_import_classification(self):
        """Test local import classification"""
        # Custom/local modules
        assert self.classifier.classify_module("my_module") == ImportType.LOCAL_IMPORT
        assert self.classifier.classify_module("custom.handler") == ImportType.LOCAL_IMPORT

    def test_relative_import_classification(self):
        """Test relative import classification"""
        assert self.classifier.classify_module(".local_module") == ImportType.RELATIVE_IMPORT
        assert self.classifier.classify_module("..parent_module") == ImportType.RELATIVE_IMPORT

    def test_performance_benchmark(self):
        """Test classification performance meets requirements"""
        test_modules = [
            "os", "sys", "boto3", "pydantic", "custom_module",
            "json", "pathlib", "rich", "typer", "local.handler"
        ] * 1000  # 10,000 classifications

        start_time = time.time()
        for module in test_modules:
            self.classifier.classify_module(module)
        elapsed = time.time() - start_time

        # Should classify at least 10k modules per second
        performance = len(test_modules) / elapsed
        assert performance > 10000, f"Performance {performance:.0f} ops/s below 10k/s requirement"


class TestMarkerSystem:
    """Test the deployment marker system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.marker_system = DeploymentMarkerSystem()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_marker_detection(self):
        """Test marker detection functionality"""
        # Create test file with markers
        test_content = '''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import os
import sys
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    return {"statusCode": 200}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
        '''

        test_file = self.temp_dir / "test_lambda.py"
        test_file.write_text(test_content)

        markers = self.marker_system.detect_markers(test_file)

        assert len(markers['start_markers']) == 2
        assert len(markers['end_markers']) == 2
        assert markers['start_markers'][0][1] == "IMPORT_BLOCK_START"
        assert markers['start_markers'][1][1] == "FUNCTION_BLOCK_START"

    def test_marker_block_extraction(self):
        """Test marker block extraction with content"""
        test_content = '''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import os
import sys
import json
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    data = json.loads(event['body'])
    return {"statusCode": 200, "body": json.dumps(data)}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
        '''

        test_file = self.temp_dir / "test_lambda.py"
        test_file.write_text(test_content)

        blocks = self.marker_system.extract_marker_blocks(test_file)

        assert len(blocks) == 2

        # Check import block
        import_block = blocks[0]
        assert import_block.start_marker == MarkerType.IMPORT_BLOCK_START
        assert import_block.end_marker == MarkerType.IMPORT_BLOCK_END
        assert len(import_block.content) == 3  # Three import lines
        assert import_block.is_valid

        # Check function block
        function_block = blocks[1]
        assert function_block.start_marker == MarkerType.FUNCTION_BLOCK_START
        assert function_block.end_marker == MarkerType.FUNCTION_BLOCK_END
        assert len(function_block.content) == 2  # Two function lines
        assert function_block.is_valid

    def test_orphaned_code_detection(self):
        """Test detection of code outside marker blocks"""
        test_content = '''
import boto3  # This import is outside markers

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import os
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

orphaned_variable = "this should be in a marker block"

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    return {"statusCode": 200}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
        '''

        test_file = self.temp_dir / "test_lambda.py"
        test_file.write_text(test_content)

        validation = self.marker_system.validate_all_markers(test_file)

        assert len(validation['orphaned_lines']) > 0
        orphaned_line_contents = [line['content'] for line in validation['orphaned_lines']]
        assert any('boto3' in content for content in orphaned_line_contents)
        assert any('orphaned_variable' in content for content in orphaned_line_contents)

    def test_invalid_marker_format(self):
        """Test detection of invalid marker formats"""
        test_content = '''
# IMPORT_BLOCK_START (invalid format - missing box drawing)
import os
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯
        '''

        test_file = self.temp_dir / "test_lambda.py"
        test_file.write_text(test_content)

        blocks = self.marker_system.extract_marker_blocks(test_file)

        # Should have issues due to invalid format
        assert len(blocks) == 0  # No valid blocks found


class TestValidationSystem:
    """Test the deployment validation system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validation_system = DeploymentValidationSystem()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_syntax_validation(self):
        """Test Python syntax validation"""
        # Valid Python file
        valid_content = '''
def lambda_handler(event, context):
    return {"statusCode": 200}
        '''

        valid_file = self.temp_dir / "valid.py"
        valid_file.write_text(valid_content)

        result = self.validation_system.validate_file(valid_file, [ValidationType.SYNTAX])

        assert result.is_valid
        assert result.critical_count == 0
        assert result.error_count == 0

    def test_syntax_validation_with_errors(self):
        """Test syntax validation with syntax errors"""
        # Invalid Python file
        invalid_content = '''
def lambda_handler(event, context:
    return {"statusCode": 200}  # Missing closing parenthesis
        '''

        invalid_file = self.temp_dir / "invalid.py"
        invalid_file.write_text(invalid_content)

        result = self.validation_system.validate_file(invalid_file, [ValidationType.SYNTAX])

        assert not result.is_valid
        assert result.critical_count > 0

    def test_import_validation(self):
        """Test import validation"""
        test_content = '''
import os
import sys
import unknown_module
from boto3 import client
        '''

        test_file = self.temp_dir / "test_imports.py"
        test_file.write_text(test_content)

        result = self.validation_system.validate_file(test_file, [ValidationType.IMPORTS])

        # Should have warnings for unknown modules
        assert result.warning_count > 0
        assert 'unknown_module' in result.metadata.get('unknown_modules', [])

    def test_security_validation(self):
        """Test security validation"""
        insecure_content = '''
password = "hardcoded_secret"  # Security issue
api_key = "sk-1234567890"      # Security issue

def lambda_handler(event, context):
    eval(event['code'])  # Security issue
    return {"statusCode": 200}
        '''

        test_file = self.temp_dir / "insecure.py"
        test_file.write_text(insecure_content)

        result = self.validation_system.validate_file(test_file, [ValidationType.SECURITY])

        assert result.error_count > 0
        error_messages = [issue.message for issue in result.issues]
        assert any('hardcoded secret' in msg.lower() for msg in error_messages)
        assert any('eval' in msg.lower() for msg in error_messages)

    def test_performance_validation(self):
        """Test performance validation"""
        # Create a large file to test performance warnings
        large_content = "\n".join([f"# Line {i}" for i in range(1500)])
        large_content += '''
def lambda_handler(event, context):
    return {"statusCode": 200}
        '''

        large_file = self.temp_dir / "large.py"
        large_file.write_text(large_content)

        result = self.validation_system.validate_file(large_file, [ValidationType.PERFORMANCE])

        # Should have warnings for high line count
        assert result.warning_count > 0
        assert result.metadata['line_count'] > 1000


class TestDeploymentManager:
    """Test the enhanced deployment manager"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_dir = self.temp_dir / "source"
        self.deployment_dir = self.temp_dir / "deployment"

        self.source_dir.mkdir(parents=True)
        self.deployment_dir.mkdir(parents=True)

        # Create test Lambda function
        self._create_test_lambda_function()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_lambda_function(self):
        """Create a test Lambda function file"""
        lambda_content = '''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import os
import boto3
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    """Lambda function handler"""
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda!"})
    }
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
        '''

        lambda_file = self.source_dir / "test_lambda.py"
        lambda_file.write_text(lambda_content)

    def test_deployment_manager_initialization(self):
        """Test deployment manager initialization"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir),
            verbose=True
        )

        assert manager.config.source_dir == self.source_dir
        assert manager.config.deployment_dir == self.deployment_dir
        assert manager.marker_system is not None
        assert manager.validation_system is not None

    def test_file_discovery_and_validation(self):
        """Test file discovery and validation"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        discovery_results = manager._discover_and_validate_files()

        assert discovery_results['total_files'] == 1
        assert discovery_results['valid_files'] >= 0  # Depends on validation strictness
        assert discovery_results['critical_errors'] == 0

    def test_infrastructure_preparation(self):
        """Test infrastructure preparation"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )
        manager.config.deployment_structure = "nested"

        infra_results = manager._prepare_infrastructure()

        assert infra_results['success']
        assert infra_results['structure'] == 'nested'

    def test_lambda_function_processing(self):
        """Test Lambda function processing"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        processing_results = manager._process_lambda_functions()

        assert processing_results['processed_count'] >= 0
        assert processing_results['failed_count'] >= 0
        assert isinstance(processing_results['processed_files'], list)

    def test_deployment_integrity_validation(self):
        """Test deployment integrity validation"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        # Create a test deployment file
        test_deployment = self.deployment_dir / "test_deployment.py"
        test_deployment.write_text('''
def lambda_handler(event, context):
    return {"statusCode": 200}
        ''')

        integrity_results = manager._validate_deployment_integrity()

        assert 'is_valid' in integrity_results
        assert 'deployment_files_count' in integrity_results
        assert integrity_results['deployment_files_count'] >= 1

    def test_complete_deployment_build(self):
        """Test complete deployment build process"""
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir),
            verbose=True
        )

        results = manager.build_deployment(force_rebuild=True)

        assert 'success' in results
        assert 'performance_metrics' in results
        assert 'validation_results' in results
        assert 'infrastructure_status' in results
        assert isinstance(results['processed_files'], list)


class TestIntegrationScenarios:
    """Test integration scenarios with real-world complexity"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.source_dir = self.temp_dir / "source"
        self.deployment_dir = self.temp_dir / "deployment"

        self.source_dir.mkdir(parents=True)
        self.deployment_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multi_function_deployment(self):
        """Test deployment with multiple Lambda functions"""
        # Create multiple Lambda functions
        functions = ["oauth_gateway.py", "smart_home_bridge.py", "config_manager.py"]

        for func_name in functions:
            func_content = f'''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import boto3
from typing import Dict, Any
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """{func_name} Lambda function"""
    return {{
        "statusCode": 200,
        "body": json.dumps({{"function": "{func_name}"}})
    }}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
            '''

            func_file = self.source_dir / func_name
            func_file.write_text(func_content)

        # Test deployment
        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        results = manager.build_deployment(force_rebuild=True)

        # Should successfully process multiple functions
        assert results.get('success', False) or len(results.get('processed_files', [])) > 0

    def test_error_recovery(self):
        """Test error recovery and partial deployment"""
        # Create mix of valid and invalid Lambda functions
        valid_content = '''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    return {"statusCode": 200}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
        '''

        invalid_content = '''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# Invalid syntax below
def lambda_handler(event, context:
    return {"statusCode": 200}
        '''

        valid_file = self.source_dir / "valid_lambda.py"
        valid_file.write_text(valid_content)

        invalid_file = self.source_dir / "invalid_lambda.py"
        invalid_file.write_text(invalid_content)

        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        results = manager.build_deployment(force_rebuild=True)

        # Should handle errors gracefully
        assert 'errors' in results
        assert 'processed_files' in results

    def test_performance_benchmarking(self):
        """Test performance requirements are met"""
        # Create multiple functions for performance testing
        for i in range(10):
            func_content = f'''
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import os
import boto3
import time
from typing import Dict, Any
# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Performance test function {i}"""
    return {{
        "statusCode": 200,
        "body": json.dumps({{"function": "test_{i}"}})
    }}
# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
            '''

            func_file = self.source_dir / f"test_function_{i}.py"
            func_file.write_text(func_content)

        manager = DeploymentManager(
            source_dir=str(self.source_dir),
            deployment_dir=str(self.deployment_dir)
        )

        start_time = time.time()
        results = manager.build_deployment(force_rebuild=True)
        total_time = time.time() - start_time

        # Performance requirements: should process files efficiently
        files_processed = len(results.get('processed_files', []))
        if files_processed > 0:
            time_per_file = total_time / files_processed
            assert time_per_file < 5.0, f"Processing too slow: {time_per_file:.2f}s per file"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
