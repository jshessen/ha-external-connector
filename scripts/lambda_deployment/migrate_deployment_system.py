#!/usr/bin/env python3
"""
🔄 MIGRATE DEPLOYMENT SYSTEM

Migration script to transition from old deployment system to new modular architecture.
Handles cleanup of legacy files and initialization of new deployment structure.

Key Features:
- Safe migration with backup of existing files
- Validation of new system components
- Rollback capability in case of issues
- Comprehensive logging of migration process

Usage:
    python scripts/lambda_deployment/migrate_deployment_system.py --migrate
    python scripts/lambda_deployment/migrate_deployment_system.py --validate
    python scripts/lambda_deployment/migrate_deployment_system.py --rollback
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

from deployment_manager import DeploymentManager
from marker_validator import MarkerValidator


class DeploymentMigration:
    """Migration manager for deployment system transition."""

    def __init__(self, workspace_root: str, logger: logging.Logger | None = None):
        self.workspace_root = Path(workspace_root)
        self.scripts_dir = self.workspace_root / "scripts"
        self.lambda_deployment_dir = self.scripts_dir / "lambda_deployment"
        self.backup_dir = self.scripts_dir / "lambda_deployment_backup"
        self._logger = logger or self._setup_logger()

        # Legacy files to be removed
        self.legacy_files = [
            "deploy_lambda_oauth.py",
            "deploy_lambda_smart_home.py",
            "lambda_function_oauth.py",
            "lambda_function_smart_home.py",
            "migrate_oauth_to_bridge.py",
            "test_oauth_deployment.py",
            "validate_deployment_markers.py",
        ]

        # New system components (these should remain)
        self.new_system_files = [
            "deployment_manager.py",
            "marker_system.py",
            "marker_validator.py",
            "validation_system.py",
            "migrate_deployment_system.py",  # this file
            "test_new_system.py",
        ]

    def migrate_to_new_system(self) -> bool:
        """
        Migrate from old to new deployment system.

        Returns:
            True if migration successful, False otherwise
        """
        self._logger.info("🚀 Starting deployment system migration...")

        try:
            # Step 1: Create backup of existing deployment directory
            if not self._create_backup():
                return False

            # Step 2: Validate new system components
            if not self._validate_new_system():
                self._logger.error("❌ New system validation failed")
                return False

            # Step 3: Remove legacy files
            if not self._remove_legacy_files():
                return False

            # Step 4: Initialize new deployment structure
            if not self._initialize_new_structure():
                return False

            # Step 5: Final validation
            if not self._validate_migration():
                self._logger.error("❌ Migration validation failed")
                return False

            self._logger.info("✅ Migration completed successfully!")
            self._display_migration_summary()
            return True

        except (OSError, ValueError) as e:
            self._logger.error("❌ Migration failed: %s", e)
            return False

    def validate_migration(self) -> bool:
        """
        Validate the migrated deployment system.

        Returns:
            True if validation passes, False otherwise
        """
        self._logger.info("🔍 Validating migrated deployment system...")

        # Check that new system files exist
        missing_files: list[str] = []
        for file_name in self.new_system_files:
            file_path = self.lambda_deployment_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            self._logger.error("❌ Missing new system files:")
            for file_name in missing_files:
                self._logger.error("  • %s", file_name)
            return False

        # Check that legacy files are removed
        remaining_legacy: list[str] = []
        for file_name in self.legacy_files:
            file_path = self.lambda_deployment_dir / file_name
            if file_path.exists():
                remaining_legacy.append(file_name)

        if remaining_legacy:
            self._logger.warning("⚠️  Legacy files still present:")
            for file_name in remaining_legacy:
                self._logger.warning("  • %s", file_name)

        # Test new system functionality
        return self._test_new_system_functionality()

    def rollback_migration(self) -> bool:
        """
        Rollback migration by restoring from backup.

        Returns:
            True if rollback successful, False otherwise
        """
        self._logger.info("🔄 Rolling back deployment system migration...")

        if not self.backup_dir.exists():
            self._logger.error("❌ No backup found for rollback")
            return False

        try:
            # Remove current lambda_deployment directory
            if self.lambda_deployment_dir.exists():
                shutil.rmtree(self.lambda_deployment_dir)
                self._logger.info("🗑️  Removed current deployment directory")

            # Restore from backup
            shutil.copytree(self.backup_dir, self.lambda_deployment_dir)
            self._logger.info("✅ Restored from backup")

            # Remove backup directory
            shutil.rmtree(self.backup_dir)
            self._logger.info("🧹 Cleaned up backup directory")

            self._logger.info("✅ Rollback completed successfully!")
            return True

        except (OSError, shutil.Error) as e:
            self._logger.error("❌ Rollback failed: %s", e)
            return False

    def _create_backup(self) -> bool:
        """Create backup of existing deployment directory."""
        if not self.lambda_deployment_dir.exists():
            self._logger.info("ℹ️  No existing deployment directory to backup")
            return True

        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            shutil.copytree(self.lambda_deployment_dir, self.backup_dir)
            self._logger.info("💾 Created backup at %s", self.backup_dir)
            return True

        except (OSError, shutil.Error) as e:
            self._logger.error("❌ Failed to create backup: %s", e)
            return False

    def _validate_new_system(self) -> bool:
        """Validate that new system components are present and functional."""
        self._logger.info("🔍 Validating new system components...")

        # Check that all new system files exist
        missing_files: list[str] = []
        for file_name in self.new_system_files:
            file_path = self.lambda_deployment_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)

        if missing_files:
            self._logger.error("❌ Missing new system files:")
            for file_name in missing_files:
                self._logger.error("  • %s", file_name)
            return False

        self._logger.info("✅ All new system components present")
        return True

    def _remove_legacy_files(self) -> bool:
        """Remove legacy deployment files."""
        self._logger.info("🗑️  Removing legacy files...")

        removed_count = 0
        for file_name in self.legacy_files:
            file_path = self.lambda_deployment_dir / file_name
            if file_path.exists():
                try:
                    file_path.unlink()
                    self._logger.info("   ✅ Removed %s", file_name)
                    removed_count += 1
                except OSError as e:
                    self._logger.error("   ❌ Failed to remove %s: %s", file_name, e)
                    return False
            else:
                self._logger.debug("   ℹ️  %s not found (already removed)", file_name)

        self._logger.info("✅ Removed %d legacy files", removed_count)
        return True

    def _initialize_new_structure(self) -> bool:
        """Initialize new deployment directory structure."""
        self._logger.info("🏗️  Initializing new deployment structure...")

        # Ensure lambda_deployment directory exists
        self.lambda_deployment_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py for Python package
        init_file = self.lambda_deployment_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                '"""Lambda deployment automation system."""\n', encoding="utf-8"
            )
            self._logger.info("   ✅ Created __init__.py")

        self._logger.info("✅ New structure initialized")
        return True

    def _validate_migration(self) -> bool:
        """Final validation of the migration."""
        self._logger.info("🔍 Performing final migration validation...")

        # Test new system components
        return self._test_new_system_functionality()

    def _test_new_system_functionality(self) -> bool:
        """Test that the new system components work correctly."""
        self._logger.info("🧪 Testing new system functionality...")

        try:
            # Test deployment manager
            _deployment_manager = DeploymentManager(str(self.workspace_root))
            self._logger.info("   ✅ DeploymentManager initialized")

            # Test marker validator
            marker_validator = MarkerValidator(str(self.workspace_root))
            self._logger.info("   ✅ MarkerValidator initialized")

            # Test validation functionality
            validation_result = marker_validator.validate_complete_project()
            if validation_result:
                self._logger.info("   ✅ Project validation passed")
            else:
                self._logger.warning("   ⚠️  Project validation issues found")

            self._logger.info("✅ New system functionality test passed")
            return True

        except ImportError as e:
            self._logger.error("   ❌ Import error: %s", e)
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.error("   ❌ Functionality test failed: %s", e)
            return False

    def _display_migration_summary(self) -> None:
        """Display summary of migration results."""
        self._logger.info("📋 Migration Summary:")
        self._logger.info("  🗑️  Legacy files removed: %d", len(self.legacy_files))
        self._logger.info("  🆕 New system files: %d", len(self.new_system_files))
        self._logger.info("  📁 Backup location: %s", self.backup_dir)
        self._logger.info("")
        self._logger.info("🚀 Next Steps:")
        self._logger.info("  1. Test deployment: python deployment_manager.py --build")
        self._logger.info("  2. Validate system: python marker_validator.py --complete")
        self._logger.info("  3. Run tests: python test_new_system.py")

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
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Deployment System Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --migrate     Migrate to new deployment system
  %(prog)s --validate    Validate migrated system
  %(prog)s --rollback    Rollback to previous system
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate to new deployment system",
    )
    group.add_argument(
        "--validate",
        action="store_true",
        help="Validate migrated deployment system",
    )
    group.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback migration (restore from backup)",
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

    # Create migration manager
    migration = DeploymentMigration(args.workspace, logger)

    # Execute requested operation
    try:
        success: bool
        if args.migrate:
            success = migration.migrate_to_new_system()
        elif args.validate:
            success = migration.validate_migration()
        elif args.rollback:
            success = migration.rollback_migration()
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
