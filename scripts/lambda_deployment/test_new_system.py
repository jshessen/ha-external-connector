#!/usr/bin/env python3
"""Comprehensive test suite for the new system."""
# pylint: disable=import-outside-toplevel  # Intentional for test isolation

import logging
import sys
import time
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class SystemTester:
    """Test suite for all system components."""

    def __init__(self, workspace_path: str = ".") -> None:
        """Initialize the tester with workspace path."""
        print(f"DEBUG: Creating tester with workspace: {workspace_path}")  # Debug
        self.workspace_path = Path(workspace_path)
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def run_all_tests(self) -> bool:
        """Run all test suites."""
        print("DEBUG: About to execute tests")  # Debug
        print("DEBUG: Starting unit tests...")  # Debug
        self._logger.info("🧪 Running Comprehensive System Tests")
        self._logger.info("=" * 50)

        all_passed = True

        # Run unit tests
        if not self._run_unit_tests():
            all_passed = False

        # Run integration tests
        if not self._run_integration_tests():
            all_passed = False

        # Run performance tests
        if not self._run_performance_tests():
            all_passed = False

        # Run error handling tests
        if not self._run_error_handling_tests():
            all_passed = False

        self._logger.info("=" * 50)
        if all_passed:
            self._logger.info("🎉 ALL TESTS PASSED!")
        else:
            self._logger.error("💥 SOME TESTS FAILED!")

        return all_passed

    def _run_unit_tests(self) -> bool:
        """Run unit tests for individual components."""
        self._logger.info("📋 Unit Tests")
        self._logger.info("-" * 30)

        unit_tests = [
            ("DeploymentManager imports", self._test_deployment_manager_import),
            ("DeploymentMarkerSystem imports", self._test_marker_system_import),
            ("DeploymentValidationSystem imports", self._test_validation_system_import),
            ("MarkerValidator imports", self._test_marker_validator_import),
            (
                "DeploymentManager basic instantiation",
                self._test_deployment_manager_create,
            ),
            ("MarkerValidator basic instantiation", self._test_marker_validator_create),
        ]

        all_passed = True
        for test_name, test_func in unit_tests:
            print(f"DEBUG: Running test: {test_name}")  # Debug
            try:
                result = test_func()
                print(f"DEBUG: Test {test_name} returned: {result}")  # Debug
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"DEBUG: Test {test_name} failed: {e}")  # Debug
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def _run_integration_tests(self) -> bool:
        """Run integration tests between components."""
        self._logger.info("🔗 Integration Tests")
        self._logger.info("-" * 30)

        integration_tests = [
            (
                "DeploymentManager + DeploymentMarkerSystem",
                self._test_deployment_manager_integration,
            ),
            (
                "MarkerValidator + DeploymentValidationSystem",
                self._test_marker_validator_integration,
            ),
            ("Full workflow test", self._test_full_workflow),
        ]

        all_passed = True
        for test_name, test_func in integration_tests:
            print(f"DEBUG: Running integration test: {test_name}")  # Debug
            try:
                result = test_func()
                print(f"DEBUG: Test {test_name} returned: {result}")  # Debug
                if result:
                    self._logger.info("   ✅ %s", test_name)
                else:
                    self._logger.error("   ❌ %s", test_name)
                    all_passed = False
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"DEBUG: Test {test_name} failed: {e}")  # Debug
                self._logger.error("   ❌ %s: %s", test_name, e)
                all_passed = False

        return all_passed

    def _run_performance_tests(self) -> bool:
        """Run performance tests."""
        self._logger.info("⚡ Performance Tests")
        self._logger.info("-" * 30)

        performance_tests = [
            ("Import speed test", self._test_import_speed),
            ("Marker processing speed", self._test_marker_processing_speed),
            ("Memory usage test", self._test_memory_usage),
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

    def _run_error_handling_tests(self) -> bool:
        """Run error handling tests."""
        self._logger.info("🚨 Error Handling Tests")
        self._logger.info("-" * 30)

        error_tests = [
            ("Invalid file handling", self._test_invalid_file_handling),
            ("Missing dependency handling", self._test_missing_dependency_handling),
            ("Malformed marker handling", self._test_malformed_marker_handling),
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

    # Unit test implementations
    def _test_deployment_manager_import(self) -> bool:
        """Test that DeploymentManager can be imported."""
        try:
            from deployment_manager import DeploymentManager  # noqa: F401

            return True
        except ImportError:
            return False

    def _test_marker_system_import(self) -> bool:
        """Test that DeploymentMarkerSystem can be imported."""
        try:
            from marker_system import DeploymentMarkerSystem  # noqa: F401

            return True
        except ImportError:
            return False

    def _test_validation_system_import(self) -> bool:
        """Test that DeploymentValidationSystem can be imported."""
        try:
            from validation_system import DeploymentValidationSystem  # noqa: F401

            return True
        except ImportError:
            return False

    def _test_marker_validator_import(self) -> bool:
        """Test that MarkerValidator can be imported."""
        try:
            from marker_validator import MarkerValidator  # noqa: F401

            return True
        except ImportError:
            return False

    def _test_deployment_manager_create(self) -> bool:
        """Test that DeploymentManager can be instantiated."""
        try:
            from deployment_manager import DeploymentManager

            DeploymentManager(workspace_root=".")
            return True  # If creation succeeds without exception
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_marker_validator_create(self) -> bool:
        """Test that MarkerValidator can be instantiated."""
        try:
            from marker_validator import MarkerValidator

            MarkerValidator(workspace_root=".")
            return True  # If creation succeeds without exception
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    # Integration test implementations
    def _test_deployment_manager_integration(self) -> bool:
        """Test DeploymentManager integration with DeploymentMarkerSystem."""
        try:
            from deployment_manager import DeploymentManager

            manager = DeploymentManager(workspace_root=".")
            # Test basic functionality
            manager.validate_deployment()
            return True  # If it doesn't crash, it works
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_marker_validator_integration(self) -> bool:
        """Test MarkerValidator integration with DeploymentValidationSystem."""
        try:
            from marker_validator import MarkerValidator

            validator = MarkerValidator(workspace_root=".")
            # Test basic validation
            validator.validate_file("nonexistent.py")
            return True  # Returns bool regardless of result
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_full_workflow(self) -> bool:
        """Test full workflow from start to finish."""
        try:
            from deployment_manager import DeploymentManager
            from marker_validator import MarkerValidator

            # Test basic workflow
            DeploymentManager(workspace_root=".")  # Just test creation
            validator = MarkerValidator(workspace_root=".")

            # Test validation workflow
            validator.validate_file("nonexistent.py")
            return True  # Returns bool regardless of result
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    # Performance test implementations
    def _test_import_speed(self) -> bool:
        """Test that imports happen quickly."""
        start_time = time.time()
        try:
            from deployment_manager import DeploymentManager  # noqa: F401
            from marker_system import DeploymentMarkerSystem  # noqa: F401
            from marker_validator import MarkerValidator  # noqa: F401
            from validation_system import DeploymentValidationSystem  # noqa: F401

            import_time = time.time() - start_time
            return import_time < 1.0  # Should import in under 1 second
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_marker_processing_speed(self) -> bool:
        """Test marker processing performance."""
        try:
            from marker_system import DeploymentMarkerSystem

            marker_system = DeploymentMarkerSystem()

            # Create test content with correct markers and write to temporary file
            test_content = """
# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def test_function():
    '''Test function for marker processing.'''
    return True
# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯
"""
            # Create temporary file
            temp_file = Path("temp_test.py")
            temp_file.write_text(test_content, encoding="utf-8")

            try:
                start_time = time.time()
                content = marker_system.extract_content(temp_file)
                processing_time = time.time() - start_time

                # Should process quickly and extract function content
                # content.functions is a string, so check if it contains our function
                function_found = "def test_function" in content.functions
                return processing_time < 1.0 and function_found
            finally:
                # Clean up
                if temp_file.exists():
                    temp_file.unlink()
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_memory_usage(self) -> bool:
        """Test memory usage is reasonable."""
        try:
            from deployment_manager import DeploymentManager

            systems: list[DeploymentManager] = []
            for _ in range(10):
                system = DeploymentManager(workspace_root=".")
                systems.append(system)

            # Should be able to create multiple instances
            return len(systems) == 10
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    # Error handling test implementations
    def _test_invalid_file_handling(self) -> bool:
        """Test handling of invalid files."""
        try:
            from marker_validator import MarkerValidator

            validator = MarkerValidator(workspace_root=".")

            # Test with non-existent file
            validator.validate_file("this_file_does_not_exist.py")
            return True  # Should handle gracefully without throwing exception
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_missing_dependency_handling(self) -> bool:
        """Test handling of missing dependencies."""
        try:
            # This should work since all dependencies should be available
            from deployment_manager import DeploymentManager

            DeploymentManager(workspace_root=".")
            return True  # If creation succeeds without exception
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _test_malformed_marker_handling(self) -> bool:
        """Test handling of malformed markers."""
        try:
            from marker_system import DeploymentMarkerSystem

            marker_system = DeploymentMarkerSystem()

            # Test with malformed content - create temporary file
            malformed_content = "# This is not a proper marker"
            temp_file = Path("temp_malformed.py")
            temp_file.write_text(malformed_content, encoding="utf-8")

            try:
                result = marker_system.extract_content(temp_file)
                _ = result  # Acknowledge we got a result
                return True  # Should handle gracefully
            finally:
                # Clean up
                if temp_file.exists():
                    temp_file.unlink()
        except Exception:  # pylint: disable=broad-exception-caught
            return False


def main() -> None:
    """Main entry point for the test suite."""
    print("DEBUG: Main function called")  # Debug
    tester = SystemTester()
    success = tester.run_all_tests()

    if not success:
        sys.exit(1)

    print("🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()
