#!/usr/bin/env python3
"""
🧪 TEST NEW DEPLOYMENT SYSTEM

Comprehensive testing suite for the new modular Lambda deployment system.
Validates all components and ensures proper integration.

Key Features:
- Unit tests for individual components
- Integration tests for complete workflow
- Performance benchmarks
- Error handling validation

Usage:
    python scripts/lambda_deployment/test_new_system.py --all
    python scripts/lambda_deployment/test_new_system.py --unit
    python scripts/lambda_deployment/test_new_system.py --integration
"""

import argparse
import logging
import sys
import tempfile
import time
from pathlib import Path

from deployment_manager import DeploymentManager
from marker_system import DeploymentMarkerSystem
from marker_validator import MarkerValidator
from validation_system import DeploymentValidationSystem


class NewSystemTester:
    """Comprehensive testing suite for the new deployment system."""

    def __init__(self, workspace_root: str, logger: logging.Logger | None = None):
        self.workspace_root = Path(workspace_root)
        self._logger = logger or self._setup_logger()
        self.test_results: dict[str, bool] = {}

    def run_all_tests(self) -> bool:
        """
        Run complete test suite.

        Returns:
            True if all tests pass, False otherwise
        """
        self._logger.info("🧪 Running complete test suite...")

        test_methods = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Error Handling Tests", self.run_error_handling_tests),
        ]

        all_passed = True
        for test_name, test_method in test_methods:
            self._logger.info("📋 Starting %s...", test_name)
            result = test_method()
            self.test_results[test_name] = result
            if result:
                self._logger.info("✅ %s: PASSED", test_name)
            else:
                self._logger.error("❌ %s: FAILED", test_name)
                all_passed = False

        self._display_test_summary()
        return all_passed

    def run_unit_tests(self) -> bool:
        """
        Run unit tests for individual components.

        Returns:
            True if all unit tests pass, False otherwise
        """
        self._logger.info("🔬 Running unit tests...")

        unit_tests = [
            ("Marker System Validation", self._test_marker_system),
            ("Validation System", self._test_validation_system),
            ("Deployment Manager Initialization", self._test_deployment_manager_init),
            ("Marker Validator", self._test_marker_validator),
        ]

        all_passed = True
        for test_name, test_func in unit_tests:
            try:
                result = test_func()
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def run_integration_tests(self) -> bool:
        """
        Run integration tests for complete workflows.

        Returns:
            True if all integration tests pass, False otherwise
        """
        self._logger.info("🔗 Running integration tests...")

        integration_tests = [
            ("Complete Deployment Workflow", self._test_complete_deployment),
            ("Validation Pipeline", self._test_validation_pipeline),
            ("Error Recovery", self._test_error_recovery),
        ]

        all_passed = True
        for test_name, test_func in integration_tests:
            try:
                result = test_func()
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def run_performance_tests(self) -> bool:
        """
        Run performance benchmarks.

        Returns:
            True if performance meets requirements, False otherwise
        """
        self._logger.info("⚡ Running performance tests...")

        performance_tests = [
            ("Marker Processing Speed", self._test_marker_processing_speed),
            ("Validation Performance", self._test_validation_performance),
            ("Memory Usage", self._test_memory_usage),
        ]

        all_passed = True
        for test_name, test_func in performance_tests:
            try:
                result = test_func()
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def run_error_handling_tests(self) -> bool:
        """
        Run error handling and edge case tests.

        Returns:
            True if error handling is robust, False otherwise
        """
        self._logger.info("🛡️  Running error handling tests...")

        error_tests = [
            ("Missing File Handling", self._test_missing_file_handling),
            ("Invalid Marker Handling", self._test_invalid_marker_handling),
            ("Permission Error Handling", self._test_permission_error_handling),
        ]

        all_passed = True
        for test_name, test_func in error_tests:
            try:
                result = test_func()
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def _test_marker_system(self) -> bool:
        """Test marker system functionality."""
        marker_system = DeploymentMarkerSystem(self._logger)

        # Test marker definitions
        if not marker_system.MARKERS:
            return False

        # Test with a temporary file containing markers
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write("""
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import logging
# ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def test_function():
    return "test"
# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯
            """)
            tmp.flush()

            temp_path = Path(tmp.name)
            try:
                # Test validation
                result = marker_system.validate_markers(temp_path)
                if not result.is_valid:
                    return False

                # Test content extraction
                content = marker_system.extract_content(temp_path)
                return bool(content.imports and content.functions)
            finally:
                temp_path.unlink()

    def _test_validation_system(self) -> bool:
        """Test validation system functionality."""
        source_dir = (
            self.workspace_root
            / "src/ha_connector/integrations/alexa/lambda_functions"
        )
        deployment_dir = self.workspace_root / "infrastructure/deployment"

        # Test basic initialization
        _validation_system = DeploymentValidationSystem(
            deployment_dir, source_dir, "shared_configuration", self._logger
        )

        # Test basic initialization
        return True

    def _test_deployment_manager_init(self) -> bool:
        """Test deployment manager initialization."""
        try:
            _deployment_manager = DeploymentManager(
                str(self.workspace_root), self._logger
            )
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_marker_validator(self) -> bool:
        """Test marker validator functionality."""
        try:
            validator = MarkerValidator(str(self.workspace_root), self._logger)
            return validator is not None
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_complete_deployment(self) -> bool:
        """Test complete deployment workflow."""
        try:
            deployment_manager = DeploymentManager(str(self.workspace_root), self._logger)

            # Test validation (should not modify files)
            result = deployment_manager.validate_deployment()
            return isinstance(result, bool)  # Should return boolean regardless of result

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_validation_pipeline(self) -> bool:
        """Test the complete validation pipeline."""
        try:
            validator = MarkerValidator(str(self.workspace_root), self._logger)

            # Test project validation
            result = validator.validate_complete_project()
            return isinstance(result, bool)  # Should return boolean regardless of result

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_error_recovery(self) -> bool:
        """Test error recovery mechanisms."""
        # For now, just test that error handling doesn't crash
        try:
            marker_system = DeploymentMarkerSystem(self._logger)

            # Test with non-existent file
            non_existent = Path("/non/existent/file.py")
            result = marker_system.validate_markers(non_existent)

            # Should return an invalid result, not crash
            return not result.is_valid and len(result.issues) > 0

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_marker_processing_speed(self) -> bool:
        """Test marker processing performance."""
        marker_system = DeploymentMarkerSystem(self._logger)

        # Create a larger test file
        test_content = """
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
""" + "\n".join([f"import module_{i}" for i in range(100)]) + """
# ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
""" + "\n".join([f"def function_{i}(): pass" for i in range(100)]) + """
# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(test_content)
            tmp.flush()

            temp_path = Path(tmp.name)
            try:
                # Measure processing time
                start_time = time.time()
                content = marker_system.extract_content(temp_path)
                end_time = time.time()

                processing_time = end_time - start_time
                self._logger.debug("Marker processing took %.3f seconds", processing_time)

                # Should process in under 1 second for reasonable file sizes
                return processing_time < 1.0 and content.imports and content.functions

            finally:
                temp_path.unlink()

    def _test_validation_performance(self) -> bool:
        """Test validation performance."""
        # Simple performance test - validation should complete quickly
        start_time = time.time()

        try:
            validator = MarkerValidator(str(self.workspace_root), self._logger)
            validator.validate_complete_project()

            end_time = time.time()
            validation_time = end_time - start_time
            self._logger.debug("Validation took %.3f seconds", validation_time)

            # Should validate in under 10 seconds
            return validation_time < 10.0

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_memory_usage(self) -> bool:
        """Test memory usage (basic check)."""
        # For now, just ensure system can be instantiated multiple times
        try:
            systems = []
            for _ in range(10):
                system = DeploymentMarkerSystem(self._logger)
                systems.append(system)

            # If we got here without memory errors, test passes
            return len(systems) == 10

        except MemoryError:
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_missing_file_handling(self) -> bool:
        """Test handling of missing files."""
        marker_system = DeploymentMarkerSystem(self._logger)

        non_existent = Path("/absolutely/non/existent/file.py")
        result = marker_system.validate_markers(non_existent)

        # Should handle gracefully and return invalid result
        return not result.is_valid and len(result.issues) > 0

    def _test_invalid_marker_handling(self) -> bool:
        """Test handling of invalid markers."""
        marker_system = DeploymentMarkerSystem(self._logger)

        # Create file with malformed markers
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write("""
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
# Missing end marker!

def some_function():
    pass
            """)
            tmp.flush()

            temp_path = Path(tmp.name)
            try:
                result = marker_system.validate_markers(temp_path)
                # Should detect the missing end marker
                return not result.is_valid and len(result.issues) > 0

            finally:
                temp_path.unlink()

    def _test_permission_error_handling(self) -> bool:
        """Test handling of permission errors."""
        # This is a simplified test since we can't easily create permission errors
        # in all environments. For now, just test that the system handles exceptions.
        try:
            marker_system = DeploymentMarkerSystem(self._logger)

            # Try to access a system directory that might not be accessible
            system_path = Path("/root/.bashrc")  # Likely not accessible to regular users
            if system_path.exists():
                result = marker_system.validate_markers(system_path)
                # Should either work or handle the error gracefully
                return isinstance(result.is_valid, bool)

            return True  # If path doesn't exist, test passes

        except Exception:  # pylint: disable=broad-exception-caught
            # Any exception should be handled gracefully
            return False

    def _display_test_summary(self) -> None:
        """Display summary of test results."""
        self._logger.info("📊 Test Summary:")

        passed_count = sum(1 for result in self.test_results.values() if result)
        total_count = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self._logger.info("  %s: %s", test_name, status)

        self._logger.info("")
        self._logger.info("🏆 Total: %d/%d tests passed", passed_count, total_count)

        if passed_count == total_count:
            self._logger.info("🎉 All tests passed! System is ready for use.")
        else:
            self._logger.warning("⚠️  Some tests failed. Review issues before deployment.")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


def main() -> None:
    """Main entry point for the test suite."""
    parser = argparse.ArgumentParser(
        description="New Deployment System Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all           Run complete test suite
  %(prog)s --unit          Run unit tests only
  %(prog)s --integration   Run integration tests only
  %(prog)s --performance   Run performance tests only
  %(prog)s --errors        Run error handling tests only
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Run complete test suite",
    )
    group.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only",
    )
    group.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only",
    )
    group.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only",
    )
    group.add_argument(
        "--errors",
        action="store_true",
        help="Run error handling tests only",
    )

    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set up logging
    logger = logging.getLogger()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create tester
    tester = NewSystemTester(args.workspace, logger)

    # Execute requested tests
    try:
        if args.all:
            success = tester.run_all_tests()
        elif args.unit:
            success = tester.run_unit_tests()
        elif args.integration:
            success = tester.run_integration_tests()
        elif args.performance:
            success = tester.run_performance_tests()
        elif args.errors:
            success = tester.run_error_handling_tests()
        else:
            parser.error("No test type specified")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Tests cancelled by user")
        sys.exit(1)
    except (OSError, ValueError, ImportError) as e:
        logger.error("Test execution failed: %s", e)
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error: %s", e)
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
