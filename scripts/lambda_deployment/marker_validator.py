#!/usr/bin/env python3
"""
🔍 MARKER VALIDATOR - Standalone Validation Tool

Validate Lambda deployment markers in source files. This tool provides
comprehensive validation reporting for development workflow.

Key Features:
- Standalone validation without deployment build
- Detailed reporting of marker issues
- Support for individual files or complete projects
- Development workflow integration

Usage:
    python scripts/lambda_deployment/marker_validator.py \
        --file cloudflare_security_gateway.py
    python scripts/lambda_deployment/marker_validator.py --all
    python scripts/lambda_deployment/marker_validator.py --shared-config
"""

import argparse
import logging
import sys
from pathlib import Path

from scripts.lambda_deployment.marker_system import (
    DeploymentMarkerSystem,
    ExtractedContent,
    MarkerValidationResult,
)


class MarkerValidator:
    """Standalone marker validation tool."""

    def __init__(self, workspace_root: str, logger: logging.Logger | None = None):
        self.workspace_root = Path(workspace_root)
        self.source_dir = (
            self.workspace_root / "src/ha_connector/integrations/alexa/lambda_functions"
        )
        self._logger = logger or self._setup_logger()
        self.marker_system = DeploymentMarkerSystem(self._logger)

    def validate_file(self, file_path: str) -> bool:
        """
        Validate markers in a specific file.

        Args:
            file_path: Path to the file to validate (relative to source dir)

        Returns:
            True if validation passes, False otherwise
        """
        target_path = self.source_dir / file_path
        if not target_path.exists():
            self._logger.error("❌ File not found: %s", target_path)
            return False

        self._logger.info("🔍 Validating markers in %s", file_path)
        result = self.marker_system.validate_markers(target_path)

        if result.is_valid:
            self._logger.info("✅ Validation passed")
            self._display_validation_summary(result)
        else:
            self._logger.error("❌ Validation failed")
            self._display_validation_errors(result)

        return result.is_valid

    def validate_all_lambda_functions(self) -> bool:
        """
        Validate markers in all Lambda function files.

        Returns:
            True if all validations pass, False otherwise
        """
        lambda_files = ["cloudflare_security_gateway.py", "smart_home_bridge.py"]
        self._logger.info("🔍 Validating all Lambda function markers...")

        all_valid = True
        for file_name in lambda_files:
            file_path = self.source_dir / file_name
            if not file_path.exists():
                self._logger.warning("⚠️  File not found: %s", file_name)
                continue

            result = self.marker_system.validate_markers(file_path)
            if result.is_valid:
                self._logger.info("✅ %s: Validation passed", file_name)
            else:
                self._logger.error("❌ %s: Validation failed", file_name)
                self._display_validation_errors(result)
                all_valid = False

        return all_valid

    def validate_shared_config(self) -> bool:
        """
        Validate markers in shared configuration file.

        Returns:
            True if validation passes, False otherwise
        """
        shared_path = self.source_dir / "shared_configuration.py"
        if not shared_path.exists():
            self._logger.warning("⚠️  Shared configuration file not found")
            return True  # Not an error if file doesn't exist

        self._logger.info("🔍 Validating shared configuration markers...")
        result = self.marker_system.validate_markers(shared_path)

        if result.is_valid:
            self._logger.info("✅ Shared configuration: Validation passed")
        else:
            self._logger.error("❌ Shared configuration: Validation failed")
            self._display_validation_errors(result)

        return result.is_valid

    def validate_complete_project(self) -> bool:
        """
        Validate markers across the entire project.

        Returns:
            True if all validations pass, False otherwise
        """
        self._logger.info("🔍 Validating complete project...")

        results = [
            self.validate_all_lambda_functions(),
            self.validate_shared_config(),
        ]

        success = all(results)
        if success:
            self._logger.info("✅ Complete project validation passed")
        else:
            self._logger.error("❌ Project validation failed")

        return success

    def extract_content_preview(self, file_path: str) -> bool:
        """
        Extract and preview content from a file without building.

        Args:
            file_path: Path to the file (relative to source dir)

        Returns:
            True if extraction successful, False otherwise
        """
        target_path = self.source_dir / file_path
        if not target_path.exists():
            self._logger.error("❌ File not found: %s", target_path)
            return False

        self._logger.info("📋 Extracting content preview from %s", file_path)
        content = self.marker_system.extract_content(target_path)

        self._display_content_preview(content)
        return True

    def _display_validation_summary(self, result: MarkerValidationResult) -> None:
        """Display summary of successful validation."""
        self._logger.info("📊 Validation Summary:")
        self._logger.info(
            "  • Found %d valid marker positions", len(result.marker_positions)
        )
        for marker_type in result.marker_positions:
            self._logger.info("    - %s", marker_type)

    def _display_validation_errors(self, result: MarkerValidationResult) -> None:
        """Display detailed validation errors."""
        self._logger.error("❌ Validation Issues:")
        for issue in result.issues:
            self._logger.error("  • %s", issue)

        if result.marker_positions:
            self._logger.info("✅ Valid markers found:")
            for marker_type in result.marker_positions:
                self._logger.info("  • %s", marker_type)

    def _display_content_preview(self, content: ExtractedContent) -> None:
        """Display preview of extracted content."""
        self._logger.info("📋 Extracted Content Preview:")

        self._preview_header_section(content.header)
        self._preview_imports_section(content.imports)
        self._preview_configuration_section(content.configuration_classes)
        self._preview_functions_section(content.functions)

    def _preview_header_section(self, header: str) -> None:
        """Display preview of header section."""
        if not header:
            return

        lines = header.split("\n")
        preview_lines = lines[:3]
        self._logger.info("  Header: %d lines", len(lines))
        for line in preview_lines:
            self._logger.info("    %s", line.strip()[:60])
        if len(lines) > 3:
            self._logger.info("    ... (+%d more lines)", len(lines) - 3)

    def _preview_imports_section(self, imports: str) -> None:
        """Display preview of imports section."""
        if not imports:
            return

        import_lines = [
            line.strip()
            for line in imports.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        self._logger.info("  Imports: %d statements", len(import_lines))
        for imp in import_lines[:3]:
            self._logger.info("    %s", imp)
        if len(import_lines) > 3:
            self._logger.info("    ... (+%d more imports)", len(import_lines) - 3)

    def _preview_configuration_section(self, configuration_classes: str) -> None:
        """Display preview of configuration classes section."""
        if not configuration_classes:
            return

        config_lines = configuration_classes.split("\n")
        self._logger.info("  Configuration Classes: %d lines", len(config_lines))
        self._display_section_preview(config_lines, 10)

    def _preview_functions_section(self, functions: str) -> None:
        """Display preview of functions section."""
        if not functions:
            return

        func_lines = functions.split("\n")
        self._logger.info("  Functions: %d lines", len(func_lines))
        self._display_section_preview(func_lines, 10)

    def _display_section_preview(self, lines: list[str], threshold: int) -> None:
        """Display preview of lines with a threshold for showing '...' message."""
        preview_count = 0
        for line in lines:
            if line.strip() and preview_count < 3:
                self._logger.info("    %s", line.strip()[:60])
                preview_count += 1
        if len(lines) > threshold:
            self._logger.info("    ... (+%d more lines)", len(lines) - threshold)

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
    """Main entry point for the marker validator."""
    parser = argparse.ArgumentParser(
        description="Lambda Deployment Marker Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file cloudflare_security_gateway.py      Validate specific file
  %(prog)s --all                        Validate all Lambda functions
  %(prog)s --shared-config              Validate shared configuration
  %(prog)s --complete                   Validate entire project
  %(prog)s --preview cloudflare_security_gateway.py   Preview extracted content
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        metavar="FILE",
        help="Validate markers in specific file",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Validate all Lambda function files",
    )
    group.add_argument(
        "--shared-config",
        action="store_true",
        help="Validate shared configuration file",
    )
    group.add_argument(
        "--complete",
        action="store_true",
        help="Validate complete project",
    )
    group.add_argument(
        "--preview",
        metavar="FILE",
        help="Preview extracted content from file",
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

    # Create validator
    validator = MarkerValidator(args.workspace, logger)

    # Execute requested operation
    try:
        success = False  # Initialize success variable
        if args.file:
            success = validator.validate_file(args.file)
        elif args.all:
            success = validator.validate_all_lambda_functions()
        elif args.shared_config:
            success = validator.validate_shared_config()
        elif args.complete:
            success = validator.validate_complete_project()
        elif args.preview:
            success = validator.extract_content_preview(args.preview)
        else:
            parser.error("No action specified")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except (OSError, ValueError, ImportError) as e:
        logger.error("Operation failed: %s", e)
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
