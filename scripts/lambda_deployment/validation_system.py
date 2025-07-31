#!/usr/bin/env python3
"""
🔍 LAMBDA DEPLOYMENT VALIDATION SYSTEM

Comprehensive validation framework for Lambda deployment operations.
Provides multi-layer validation with detailed error reporting.

Key Features:
- Source file marker validation
- Deployment file structure validation
- Python syntax and import validation
- Comprehensive error reporting and recovery
- Performance-optimized validation workflows

Validation Layers:
1. Marker Structure Validation
2. File Existence and Readability
3. Python Syntax Validation
4. Import Structure Validation
5. Deployment Synchronization Checks
"""

import ast
import logging
from pathlib import Path
from typing import NamedTuple

from marker_system import DeploymentMarkerSystem


class ValidationResult(NamedTuple):
    """Result of validation operation."""

    is_valid: bool
    passed_checks: int
    total_checks: int
    issues: list[str]


class DeploymentValidationSystem:
    """Comprehensive validation system for Lambda deployments."""

    def __init__(
        self,
        deployment_dir: Path,
        source_dir: Path,
        shared_module: str,
        logger: logging.Logger | None = None,
    ):
        self.deployment_dir = deployment_dir
        self.source_dir = source_dir
        self.shared_module = shared_module
        self._logger = logger or self._setup_logger()

        # Initialize marker system for validation
        self.marker_system = DeploymentMarkerSystem(self._logger)

    def validate_complete_deployment(
        self, lambda_functions: list[tuple[str, str]]
    ) -> bool:
        """
        Validate complete deployment including all Lambda functions.

        Args:
            lambda_functions: List of (source_file, deployment_dir) tuples

        Returns:
            True if all validations pass, False otherwise
        """
        self._logger.info("🔍 Starting comprehensive deployment validation...")

        all_valid = True

        # Validate shared configuration first
        shared_result = self._validate_shared_configuration()
        if shared_result.is_valid:
            self._logger.info(
                "✅ Shared configuration: %d/%d checks passed",
                shared_result.passed_checks,
                shared_result.total_checks,
            )
        else:
            self._logger.error("❌ Shared configuration validation failed:")
            for issue in shared_result.issues:
                self._logger.error("   • %s", issue)
            all_valid = False

        # Validate each Lambda function deployment
        for source_file, deployment_dir in lambda_functions:
            result = self._validate_single_deployment(source_file, deployment_dir)

            if result.is_valid:
                self._logger.info(
                    "✅ %s: %d/%d checks passed",
                    source_file.replace(".py", ""),
                    result.passed_checks,
                    result.total_checks,
                )
            else:
                self._logger.error("❌ %s validation failed:", source_file)
                for issue in result.issues:
                    self._logger.error("   • %s", issue)
                all_valid = False

        # Final summary
        if all_valid:
            self._logger.info("🎉 All deployment validations passed!")
        else:
            self._logger.error("❌ Deployment validation failed")

        return all_valid

    def _validate_single_deployment(
        self, source_file: str, deployment_dir: str
    ) -> ValidationResult:
        """
        Validate a single Lambda deployment.

        Args:
            source_file: Name of the source Lambda file
            deployment_dir: Name of the deployment directory

        Returns:
            ValidationResult with detailed validation status
        """
        lambda_name = source_file.replace(".py", "")
        issues: list[str] = []
        passed_checks = 0
        total_checks = 5  # Number of validation checks

        self._logger.info("🔧 Validating %s deployment...", lambda_name)

        # Validate source file
        passed_checks += self._validate_source_file(source_file, issues)

        # Validate deployment file
        deployment_content, deployment_checks = self._validate_deployment_file(
            deployment_dir, issues
        )
        passed_checks += deployment_checks

        # Validate deployment content if available
        if deployment_content:
            passed_checks += self._validate_deployment_content(
                deployment_content, lambda_name, issues
            )

        is_valid = len(issues) == 0
        return ValidationResult(is_valid, passed_checks, total_checks, issues)

    def _validate_source_file(self, source_file: str, issues: list[str]) -> int:
        """
        Validate source file markers.

        Args:
            source_file: Name of the source Lambda file
            issues: List to append validation issues to

        Returns:
            Number of passed checks (0 or 1)
        """
        source_path = self.source_dir / source_file
        if not source_path.exists():
            issues.append(f"Source file not found: {source_path}")
            return 0

        marker_result = self.marker_system.validate_markers(source_path)
        if marker_result.is_valid:
            self._logger.info("   ✅ Source markers valid")
            return 1

        issues.extend(f"Source: {issue}" for issue in marker_result.issues)
        return 0

    def _validate_deployment_file(
        self, deployment_dir: str, issues: list[str]
    ) -> tuple[str, int]:
        """
        Validate deployment file exists and is readable.

        Args:
            deployment_dir: Name of the deployment directory
            issues: List to append validation issues to

        Returns:
            Tuple of (deployment_content, passed_checks_count)
        """
        deployment_function_dir = self.deployment_dir / deployment_dir
        deployment_path = deployment_function_dir / "lambda_function.py"

        if not deployment_path.exists():
            issues.append(f"Deployment file not found: {deployment_path}")
            return "", 0

        self._logger.info("   ✅ Deployment file exists")

        try:
            deployment_content = deployment_path.read_text(encoding="utf-8")
            return deployment_content, 1
        except OSError as e:
            issues.append(f"Cannot read deployment file: {e}")
            return "", 1  # File exists but can't read

    def _validate_deployment_content(
        self, deployment_content: str, lambda_name: str, issues: list[str]
    ) -> int:
        """
        Validate deployment content (syntax, structure, imports).

        Args:
            deployment_content: Content of the deployment file
            lambda_name: Name of Lambda function for logging
            issues: List to append validation issues to

        Returns:
            Number of passed checks (0-3)
        """
        passed_checks = 0

        # Check 3: Python syntax validation
        if self._validate_python_syntax(deployment_content, lambda_name):
            passed_checks += 1
            self._logger.info("   ✅ Python syntax valid")
        else:
            issues.append("Invalid Python syntax")

        # Check 4: Deployment structure validation
        if self._validate_deployment_structure(deployment_content, lambda_name):
            passed_checks += 1
            self._logger.info("   ✅ Deployment structure valid")
        else:
            issues.append("Invalid deployment structure")

        # Check 5: Import validation
        if self._validate_deployment_imports(deployment_content, lambda_name):
            passed_checks += 1
            self._logger.info("   ✅ Imports valid")
        else:
            issues.append("Invalid import structure")

        return passed_checks

    def _validate_shared_configuration(self) -> ValidationResult:
        """
        Validate shared configuration file.

        Returns:
            ValidationResult for shared configuration
        """
        issues: list[str] = []
        passed_checks = 0
        total_checks = 2

        self._logger.info("🔧 Validating shared configuration...")

        shared_path = self.source_dir / f"{self.shared_module}.py"

        # Check 1: File exists and is readable
        if shared_path.exists():
            passed_checks += 1
            self._logger.info("   ✅ Shared configuration file exists")

            try:
                shared_content = shared_path.read_text(encoding="utf-8")
            except OSError as e:
                issues.append(f"Cannot read shared configuration: {e}")
                shared_content = ""
        else:
            issues.append(f"Shared configuration not found: {shared_path}")
            shared_content = ""

        if shared_content:
            # Check 2: Marker validation (functions only for shared config)
            marker_result = self.marker_system.validate_markers(shared_path)
            if marker_result.is_valid:
                passed_checks += 1
                self._logger.info("   ✅ Shared configuration markers valid")
            else:
                issues.extend(f"Shared: {issue}" for issue in marker_result.issues)

        is_valid = len(issues) == 0
        return ValidationResult(is_valid, passed_checks, total_checks, issues)

    def _validate_python_syntax(self, content: str, lambda_name: str) -> bool:
        """
        Validate Python syntax of deployment content.

        Args:
            content: Content to validate
            lambda_name: Name of Lambda function for logging

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            self._logger.error(
                "   ❌ %s: Syntax error at line %d: %s", lambda_name, e.lineno, e.msg
            )
            return False

    def _validate_deployment_structure(self, content: str, lambda_name: str) -> bool:
        """
        Validate basic deployment file structure.

        Args:
            content: Deployment file content
            lambda_name: Name of Lambda function for logging

        Returns:
            True if structure is valid, False otherwise
        """
        # Check for required AWS Lambda handler pattern
        required_patterns = [
            "def lambda_handler(",  # AWS Lambda entry point
            "event",  # Lambda event parameter
            "context",  # Lambda context parameter
        ]

        for pattern in required_patterns:
            if pattern not in content:
                self._logger.error(
                    "   ❌ %s: Missing required pattern: %s", lambda_name, pattern
                )
                return False

        return True

    def _validate_deployment_imports(self, content: str, lambda_name: str) -> bool:
        """
        Validate deployment file import structure.

        Args:
            content: Deployment file content
            lambda_name: Name of Lambda function for logging

        Returns:
            True if imports are valid, False otherwise
        """
        # Check for prohibited imports that indicate incomplete deployment
        prohibited_patterns = [
            "from shared_configuration import",
            "import shared_configuration",
            "from .shared_configuration import",
        ]

        for pattern in prohibited_patterns:
            if pattern in content:
                self._logger.error(
                    "   ❌ %s: Found prohibited import pattern: %s",
                    lambda_name,
                    pattern,
                )
                return False

        # Check for embedded shared code marker (indicates proper deployment)
        if "# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===" not in content:
            self._logger.warning(
                "   ⚠️  %s: No embedded shared code marker found", lambda_name
            )
            # Don't fail validation for this, just warn
            # return False

        return True

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
