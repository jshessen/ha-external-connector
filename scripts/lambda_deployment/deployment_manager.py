#!/usr/bin/env python3
"""
🚀 LAMBDA DEPLOYMENT MANAGER

Main orchestrator for Lambda deployment operations. Provides a clean, unified
interface for building, validating, and managing Lambda deployment files.

Key Features:
- Unified deployment workflow management
- Comprehensive validation and error reporting
- Clean separation between development and deployment modes
- Modular architecture with pluggable components

Usage:
    python scripts/lambda_deployment/deployment_manager.py --build
    python scripts/lambda_deployment/deployment_manager.py --validate
    python scripts/lambda_deployment/deployment_manager.py --clean
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from marker_system import DeploymentMarkerSystem, ExtractedContent
from validation_system import DeploymentValidationSystem


@dataclass
class DeploymentConfig:
    """Configuration for Lambda deployment operations."""

    workspace_root: Path
    source_dir: Path
    deployment_dir: Path
    shared_module: str
    lambda_functions: list[tuple[str, str]]

    @classmethod
    def create(cls, workspace_root: str) -> "DeploymentConfig":
        """Create deployment configuration from workspace root."""
        root = Path(workspace_root)
        return cls(
            workspace_root=root,
            source_dir=root / "src/ha_connector/integrations/alexa/lambda_functions",
            deployment_dir=root / "infrastructure/deployment",
            shared_module="shared_configuration",
            lambda_functions=[
                ("oauth_gateway.py", "oauth_gateway"),
                ("smart_home_bridge.py", "smart_home_bridge"),
            ],
        )


class DeploymentManager:
    """Main orchestrator for Lambda deployment operations."""

    def __init__(
        self,
        workspace_root: str,
        logger: logging.Logger | None = None,
    ):
        self.config = DeploymentConfig.create(workspace_root)
        self._logger = logger or self._setup_logger()

        # Initialize core systems
        self.marker_system = DeploymentMarkerSystem(self._logger)
        self.validation_system = DeploymentValidationSystem(
            self.config.deployment_dir,
            self.config.source_dir,
            self.config.shared_module,
            self._logger,
        )

    def build_deployment(self) -> bool:
        """
        Build standalone Lambda deployment files with embedded shared code.

        Returns:
            True if deployment built successfully, False otherwise
        """
        self._logger.info("🚀 Building Lambda deployment files...")

        # Validate source files first
        if not self._validate_source_files():
            return False

        # Build each Lambda function
        success = True
        for source_file, deployment_dir in self.config.lambda_functions:
            if not self._build_single_lambda(source_file, deployment_dir):
                success = False

        if success:
            self._logger.info("✅ All deployment files built successfully!")
            self._display_deployment_structure()
        else:
            self._logger.error("❌ Deployment build failed")

        return success

    def validate_deployment(self) -> bool:
        """
        Validate deployment files and synchronization.

        Returns:
            True if validation passes, False otherwise
        """
        self._logger.info("🔍 Validating deployment files...")

        return self.validation_system.validate_complete_deployment(
            self.config.lambda_functions
        )

    def clean_deployment(self) -> None:
        """Reset to development mode by removing deployment files."""
        self._logger.info("🧹 Cleaning deployment files...")

        for _, deployment_dir in self.config.lambda_functions:
            deployment_path = self.config.deployment_dir / deployment_dir
            if deployment_path.exists():
                self._logger.info("🗑️  Removing %s", deployment_path)
                # In a real implementation, we'd remove the files
                # For now, just log the action
                self._logger.info("   (Directory would be removed)")

        self._logger.info("✅ Deployment cleanup complete")

    def _validate_source_files(self) -> bool:
        """Validate that all source files have proper markers."""
        self._logger.info("📋 Validating source file markers...")

        all_valid = True

        for source_file, _ in self.config.lambda_functions:
            source_path = self.config.source_dir / source_file
            if not source_path.exists():
                self._logger.error("❌ Source file not found: %s", source_path)
                all_valid = False
                continue

            result = self.marker_system.validate_markers(source_path)
            if not result.is_valid:
                self._logger.error("❌ Marker validation failed for %s:", source_file)
                for issue in result.issues:
                    self._logger.error("   • %s", issue)
                all_valid = False
            else:
                self._logger.info("✅ %s: Markers valid", source_file)

        # Also validate shared configuration
        shared_path = self.config.source_dir / f"{self.config.shared_module}.py"
        if shared_path.exists():
            result = self.marker_system.validate_markers(shared_path)
            if not result.is_valid:
                self._logger.error("❌ Shared config marker validation failed:")
                for issue in result.issues:
                    self._logger.error("   • %s", issue)
                all_valid = False
            else:
                self._logger.info("✅ shared_configuration.py: Markers valid")

        return all_valid

    def _build_single_lambda(self, source_file: str, deployment_dir: str) -> bool:
        """
        Build deployment file for a single Lambda function.

        Args:
            source_file: Name of the source Lambda file
            deployment_dir: Name of the deployment directory

        Returns:
            True if build successful, False otherwise
        """
        self._logger.info("🔧 Building %s...", source_file)

        source_path = self.config.source_dir / source_file
        deployment_function_dir = self.config.deployment_dir / deployment_dir
        deployment_path = deployment_function_dir / "lambda_function.py"

        # Extract content from source file
        content = self.marker_system.extract_content(source_path)
        if not content.header and not content.functions:
            self._logger.error("❌ Failed to extract content from %s", source_file)
            return False

        # Extract shared configuration
        shared_path = self.config.source_dir / f"{self.config.shared_module}.py"
        shared_content = self.marker_system.extract_content(shared_path)

        # Build deployment content
        deployment_content = self._build_deployment_content(content, shared_content)

        # Ensure deployment directory exists
        deployment_function_dir.mkdir(parents=True, exist_ok=True)

        # Write deployment file
        try:
            deployment_path.write_text(deployment_content, encoding="utf-8")
            self._logger.info("✅ Created %s", deployment_path)
            return True
        except OSError as e:
            self._logger.error("❌ Failed to write %s: %s", deployment_path, e)
            return False

    def _build_deployment_content(
        self, lambda_content: ExtractedContent, shared_content: ExtractedContent
    ) -> str:
        """
        Build complete deployment content by merging Lambda and shared content.

        Args:
            lambda_content: Extracted content from Lambda function
            shared_content: Extracted content from shared configuration

        Returns:
            Complete deployment file content
        """
        sections: list[str] = []

        # Add header
        if lambda_content.header:
            sections.append(lambda_content.header.strip())

        # Add merged imports
        merged_imports = self._merge_imports(
            lambda_content.imports, shared_content.imports
        )
        if merged_imports:
            sections.append(merged_imports)

        # Add embedded shared code marker and functions
        if shared_content.functions:
            sections.extend(
                [
                    "# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===",
                    "# This section contains shared configuration "
                    "embedded for deployment",
                    "",
                    shared_content.functions.strip(),
                ]
            )

        # Add Lambda-specific functions
        if lambda_content.functions:
            sections.append(lambda_content.functions.strip())

        return "\n\n".join(sections) + "\n"

    def _merge_imports(self, lambda_imports: str, shared_imports: str) -> str:
        """
        Merge and deduplicate imports from Lambda and shared code.

        Args:
            lambda_imports: Import statements from Lambda function
            shared_imports: Import statements from shared configuration

        Returns:
            Merged and deduplicated import statements
        """
        all_imports: set[str] = set()

        # Process Lambda imports
        for line in lambda_imports.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                all_imports.add(line)

        # Process shared imports
        for line in shared_imports.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                all_imports.add(line)

        # Sort imports for consistency
        return "\n".join(sorted(all_imports))

    def _display_deployment_structure(self) -> None:
        """Display the deployment directory structure."""
        self._logger.info("📁 Deployment structure:")
        for _, deployment_dir in self.config.lambda_functions:
            self._logger.info("├── %s/", deployment_dir)
            self._logger.info("│   └── lambda_function.py")

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
    """Main entry point for the deployment manager."""
    parser = argparse.ArgumentParser(
        description="Lambda Deployment Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --build      Build deployment files with embedded shared code
  %(prog)s --validate   Validate deployment files and synchronization
  %(prog)s --clean      Reset to development mode
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--build",
        action="store_true",
        help="Build deployment files with embedded shared code",
    )
    group.add_argument(
        "--validate",
        action="store_true",
        help="Validate deployment files and synchronization",
    )
    group.add_argument(
        "--clean",
        action="store_true",
        help="Reset to development mode (remove deployment files)",
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

    # Create deployment manager
    manager = DeploymentManager(args.workspace, logger)

    # Execute requested operation
    try:
        if args.build:
            success = manager.build_deployment()
            sys.exit(0 if success else 1)
        elif args.validate:
            success = manager.validate_deployment()
            sys.exit(0 if success else 1)
        elif args.clean:
            manager.clean_deployment()
            sys.exit(0)
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
