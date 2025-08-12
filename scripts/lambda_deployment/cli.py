#!/usr/bin/env python3
"""
⌨️ CLI HANDLER

Command-line interface for the Lambda Deployment Manager.
Extracted from deployment_manager.py to reduce complexity and improve maintainability.

Key Features:
- Argument parsing and validation
- Logging configuration
- Operation dispatch
- Error handling and user feedback
- Clean separation of CLI concerns from business logic
"""

import argparse
import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deployment_manager import DeploymentManager


class CLIHandler:
    """Handles command-line interface operations."""

    def __init__(self):
        """Initialize CLI handler."""
        self.parser = self._create_parser()

    def run(self) -> None:
        """Main entry point for CLI operations."""
        args = self.parser.parse_args()

        # Validate arguments
        if not self._validate_arguments(args):
            sys.exit(1)

        # Set up logging
        self._setup_logging(args.verbose)
        logger = logging.getLogger()

        # Import at runtime to avoid circular imports
        # pylint: disable-next=import-outside-toplevel
        from deployment_manager import DeploymentManager

        # Create deployment manager
        manager = DeploymentManager(args.workspace, logger)

        # Execute requested operation
        try:
            success = self._execute_operation(args, manager)
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

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            description=(
                "Lambda Deployment Manager - Complete Lambda Function "
                "Deployment Solution"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --build                                    Build deployment files
  %(prog)s --package --function smart_home_bridge     Package function for deployment
  %(prog)s --deploy --function oauth_gateway          Deploy single function
  %(prog)s --deploy --function all                    Deploy all functions
  %(prog)s --deploy --function all --dry-run          Test deployment without changes
  %(prog)s --test --function smart_home_bridge        Test deployed function
  %(prog)s --validate                                 Validate deployment files
  %(prog)s --clean                                    Reset to development mode
            """,
        )

        # Mutually exclusive operation group
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--build",
            action="store_true",
            help="Build deployment files with embedded shared code",
        )
        group.add_argument(
            "--package",
            action="store_true",
            help="Package Lambda function into deployment-ready ZIP file",
        )
        group.add_argument(
            "--deploy",
            action="store_true",
            help="Deploy Lambda function to AWS",
        )
        group.add_argument(
            "--test",
            action="store_true",
            help="Test a deployed Lambda function",
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

        # Additional arguments
        parser.add_argument(
            "--function",
            help=(
                "Specify which function to operate on "
                "(smart_home_bridge, oauth_gateway, configuration_manager, or all)"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate operation but don't make actual changes (deploy only)",
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

        return parser

    def _validate_arguments(self, args: argparse.Namespace) -> bool:
        """Validate parsed arguments."""
        # Validate function argument for operations that require it
        if args.package or args.deploy or args.test:
            if not args.function:
                self.parser.error(
                    "--function is required with --package, --deploy, or --test"
                )

            # Validate function name
            available_functions = [
                "smart_home_bridge",
                "oauth_gateway",
                "configuration_manager",
                "all",
            ]
            if args.test and args.function == "all":
                self.parser.error("--test cannot be used with --function all")
            if args.function not in available_functions:
                self.parser.error(
                    f"Invalid function: {args.function}. "
                    f"Available: {', '.join(available_functions)}"
                )

        return True

    def _setup_logging(self, verbose: bool) -> None:
        """Set up logging configuration."""
        if verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(levelname)s: %(message)s",
                force=True,  # Override any existing configuration
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(levelname)s: %(message)s",
                force=True,  # Override any existing configuration
            )

    def _execute_operation(
        self, args: argparse.Namespace, manager: "DeploymentManager"
    ) -> bool:
        """Execute the requested operation."""

        # Helper function for clean operation
        def clean_operation() -> bool:
            manager.clean_deployment()
            return True

        # Define operation dispatch table
        operations = {
            "build": manager.build_deployment,
            "package": lambda: manager.package_function(args.function),
            "deploy": lambda: manager.deploy_function(args.function, args.dry_run),
            "test": lambda: manager.test_deployed_function(args.function),
            "validate": manager.validate_deployment,
            "clean": clean_operation,
        }

        # Execute the first matching operation
        for operation_name, operation_func in operations.items():
            if getattr(args, operation_name, False):
                return operation_func()

        return False


def main() -> None:
    """Main entry point for the CLI."""
    cli = CLIHandler()
    cli.run()


if __name__ == "__main__":
    main()
