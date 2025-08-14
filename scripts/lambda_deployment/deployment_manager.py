#!/usr/bin/env python3
"""
🚀 LAMBDA DEPLOYMENT MANAGER

Core orchestrator for Lambda function deployment operations. Provides unified
interface for building, packaging, validating, and deploying Lambda functions.

Refactored for maintainability:
- Import management extracted to ImportManager
- AWS operations extracted to AWSDeploymentHandler
- CLI interface extracted to CLIHandler
- Core orchestration remains here with simplified responsibilities

Key Features:
- Build standalone deployment files with embedded shared code
- Orchestrate packaging, deployment, and validation operations
- Clean separation between development and deployment modes
- Integration with specialized handlers for complex operations

Usage:
    python scripts/lambda_deployment/deployment_manager.py --build
    python scripts/lambda_deployment/deployment_manager.py --package \
        --function smart_home_bridge
"""

import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

# Add current directory to path for proper imports when run from different contexts
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from aws_deployment_handler import AWSDeploymentHandler
    from import_manager import ImportManager
    from marker_system import DeploymentMarkerSystem, ExtractedContent
    from validation_system import DeploymentValidationSystem
except ImportError as e:
    # If running from VS Code or different context, provide helpful error
    print(f"Import error: {e}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Script directory: {current_dir}")
    print("Note: This script should be run from the workspace root directory.")
    print("Example: python scripts/lambda_deployment/deployment_manager.py --build")
    # Re-raise for proper error handling
    raise


@dataclass
class DeploymentConfig:
    """Configuration for Lambda deployment operations."""

    workspace_root: Path
    source_dir: Path
    deployment_dir: Path
    shared_module: str
    lambda_functions: list[tuple[str, str]]
    lambda_function_names: dict[str, str]  # deployment_dir -> AWS function name

    @classmethod
    def create(
        cls, workspace_root: str, custom_names: dict[str, str] | None = None
    ) -> "DeploymentConfig":
        """
        Create deployment configuration from workspace root.

        Args:
            workspace_root: Path to the workspace root directory
            custom_names: Optional custom AWS function names to override defaults
                         Format: {"cloudflare_security_gateway": "CustomName1",
                                  "smart_home_bridge": "CustomName2"}

        Returns:
            DeploymentConfig instance with default or custom function names
        """
        root = Path(workspace_root)

        # Default AWS function names
        default_function_names = {
            "cloudflare_security_gateway": "CloudFlare-Security-Gateway",
            "smart_home_bridge": "HomeAssistant",
            "configuration_manager": "ConfigurationManager",
        }

        # Merge custom names with defaults (custom names take precedence)
        function_names = default_function_names.copy()
        if custom_names:
            function_names.update(custom_names)

        return cls(
            workspace_root=root,
            source_dir=root / "src/ha_connector/integrations/alexa/lambda_functions",
            deployment_dir=root / "infrastructure/deployment",
            shared_module="shared_configuration",
            lambda_functions=[
                ("cloudflare_security_gateway.py", "cloudflare_security_gateway"),
                ("smart_home_bridge.py", "smart_home_bridge"),
                ("configuration_manager.py", "configuration_manager"),
            ],
            lambda_function_names=function_names,
        )


class DeploymentManager:
    """Main orchestrator for Lambda deployment operations."""

    def __init__(
        self,
        workspace_root: str,
        logger: logging.Logger | None = None,
        custom_function_names: dict[str, str] | None = None,
    ):
        self.config = DeploymentConfig.create(workspace_root, custom_function_names)
        self._logger = logger or self._setup_logger()

        # Initialize core systems
        self.marker_system = DeploymentMarkerSystem(self._logger)
        self.validation_system = DeploymentValidationSystem(
            self.config.deployment_dir,
            self.config.source_dir,
            self.config.shared_module,
            self._logger,
        )

        # Initialize specialized handlers
        self.import_manager = ImportManager()
        self.aws_handler = AWSDeploymentHandler(self.config, self._logger)

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
            deployment_function_dir = self.config.deployment_dir / deployment_dir
            if deployment_function_dir.exists():
                shutil.rmtree(deployment_function_dir)
                self._logger.info("🗑️  Removed %s", deployment_function_dir)

        self._logger.info("✅ Deployment cleanup complete")

    def package_function(self, function_name: str) -> bool:
        """
        Package a Lambda function into a deployment-ready ZIP file.

        Args:
            function_name: Name of the function to package (e.g., 'smart_home_bridge')

        Returns:
            True if packaging successful, False otherwise
        """
        return self.aws_handler.package_function(function_name)

    def deploy_function(self, function_name: str, dry_run: bool = False) -> bool:
        """
        Deploy a Lambda function to AWS.

        Args:
            function_name: Name of the function to deploy
                (e.g., 'smart_home_bridge' or 'all')
            dry_run: If True, validate but don't actually deploy

        Returns:
            True if deployment successful, False otherwise
        """
        return self.aws_handler.deploy_function(function_name, dry_run)

    def test_deployed_function(self, function_name: str) -> bool:
        """
        Test a deployed Lambda function.

        Args:
            function_name: Name of the function to test

        Returns:
            True if test successful, False otherwise
        """
        return self.aws_handler.test_deployed_function(function_name)

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

        # Add merged imports using ImportManager
        merged_imports = self.import_manager.merge_imports(
            lambda_content.imports, shared_content.imports
        )
        if merged_imports:
            sections.append(merged_imports)

        # Add embedded shared configuration classes
        if shared_content.configuration_classes:
            sections.extend(
                [
                    "# === EMBEDDED SHARED CONFIGURATION CLASSES (AUTO-GENERATED) ===",
                    "# This section contains shared configuration classes "
                    "embedded for deployment",
                    "",
                    shared_content.configuration_classes.strip(),
                ]
            )

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

        # Add Lambda-specific configuration classes (if any)
        if lambda_content.configuration_classes:
            sections.extend(
                [
                    "# === LAMBDA-SPECIFIC CONFIGURATION CLASSES ===",
                    "",
                    lambda_content.configuration_classes.strip(),
                ]
            )

        # Add Lambda-specific functions
        if lambda_content.functions:
            sections.append(lambda_content.functions.strip())

        return "\n\n".join(sections) + "\n"

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


# For backward compatibility, keep main() function here
def main() -> None:
    """Main entry point - implements basic CLI functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Lambda Deployment Manager")
    parser.add_argument("--build", action="store_true", help="Build deployment files")
    parser.add_argument("--package", help="Package specific function")
    parser.add_argument("--deploy", help="Deploy specific function")
    parser.add_argument("--function", help="Specify function name for package/deploy")

    args = parser.parse_args()

    # Get workspace root (assuming script is run from workspace root)
    workspace_root = str(Path.cwd())
    manager = DeploymentManager(workspace_root)

    if args.build:
        success = manager.build_deployment()
        sys.exit(0 if success else 1)
    elif args.package:
        success = manager.package_function(args.package)
        sys.exit(0 if success else 1)
    elif args.deploy:
        success = manager.deploy_function(args.deploy)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
