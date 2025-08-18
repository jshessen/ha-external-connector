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
import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add current directory to path for proper imports when run from different contexts
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

if TYPE_CHECKING:
    from deployment_manager import DeploymentManager

# Import deployment manager module at top level
try:
    import deployment_manager
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Script directory: {current_dir}")
    print("Note: This script should be run from the workspace root directory.")
    # Re-raise for proper error handling
    raise


def _validate_and_extract_string_dict(obj: Any) -> dict[str, str]:
    """Validate and extract a dictionary with string keys and values."""
    if not isinstance(obj, dict):
        raise ValueError("Object must be a dictionary")

    result: dict[str, str] = {}

    try:
        # Iterate over dictionary items with type ignore to satisfy Pylance
        for key, value in obj.items():  # type: ignore[misc]
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("All keys and values must be strings")
            result[key] = value

        return result
    except (TypeError, AttributeError) as e:
        raise ValueError(f"Failed to validate dictionary: {e}") from e


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
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("lambda_deployment.cli")

        # Parse custom function names
        custom_names = self._parse_custom_function_names(args)

        # Create deployment manager with custom names
        manager = deployment_manager.DeploymentManager(
            args.workspace, logger, custom_names
        )

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
  %(prog)s --package                                  Package all functions
  %(prog)s --package --function smart_home_bridge     Package specific function
  %(prog)s --deploy                                   Deploy all functions
  %(prog)s --deploy --function cloudflare_security_gateway
      Deploy single function
  %(prog)s --deploy --dry-run                         Test deployment of all functions
  %(prog)s --test --function smart_home_bridge        Test deployed function
  %(prog)s --validate                                 Validate deployment files
  %(prog)s --clean                                    Reset to development mode

Notes:
  - --function defaults to 'all' for --package and --deploy operations
  - --function is required for --test operations (cannot test all at once)
  - Use --dry-run to validate deployments without making AWS changes
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
            help="Package Lambda functions into ZIP files (defaults to all)",
        )
        group.add_argument(
            "--deploy",
            action="store_true",
            help="Deploy Lambda functions to AWS (defaults to all)",
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
                "Specify which function to operate on. "
                "Required for --test. Optional for --package and --deploy "
                "(defaults to 'all'). Available: smart_home_bridge, "
                "cloudflare_security_gateway, configuration_manager, all"
            ),
        )
        parser.add_argument(
            "--function-names",
            help=(
                "Custom AWS Lambda function names as JSON string. "
                'Example: \'{"cloudflare_security_gateway": "MyCustomName", '
                '"smart_home_bridge": "MyBridge"}\''
            ),
        )
        parser.add_argument(
            "--oauth-name",
            help=(
                "Custom AWS function name for cloudflare_security_gateway "
                "(overrides default 'CloudFlare-Security-Gateway')"
            ),
        )
        parser.add_argument(
            "--bridge-name",
            help=(
                "Custom AWS function name for smart_home_bridge "
                "(overrides default 'HomeAssistant')"
            ),
        )
        parser.add_argument(
            "--config-name",
            help=(
                "Custom AWS function name for configuration_manager "
                "(overrides default 'ConfigurationManager')"
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
        # Set default function to "all" for package and deploy operations
        if (args.package or args.deploy) and not args.function:
            args.function = "all"
            print("🎯 No function specified, defaulting to --function all")

        # Validate function argument for operations that require it
        if args.package or args.deploy or args.test:
            if not args.function:
                self.parser.error("--function is required with --test")

            # Validate function name
            available_functions = [
                "smart_home_bridge",
                "cloudflare_security_gateway",
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

    def _parse_custom_function_names(
        self, args: argparse.Namespace
    ) -> dict[str, str] | None:
        """
        Parse custom function names from CLI arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            Dictionary of custom function names or None if no custom names provided

        Raises:
            ValueError: If JSON parsing fails or function names are invalid
        """
        custom_names: dict[str, str] = {}

        # Parse JSON format names first (takes precedence)
        if args.function_names:
            try:
                json_data: Any = json.loads(args.function_names)
                if not isinstance(json_data, dict):
                    raise ValueError("--function-names must be a JSON object")

                # Validate and extract string dictionary
                validated_names = _validate_and_extract_string_dict(json_data)
                custom_names.update(validated_names)

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in --function-names: {e}") from e

        # Parse individual name arguments (lower precedence)
        if args.oauth_name:
            custom_names["cloudflare_security_gateway"] = args.oauth_name
        if args.bridge_name:
            custom_names["smart_home_bridge"] = args.bridge_name
        if args.config_name:
            custom_names["configuration_manager"] = args.config_name

        # Validate function name keys
        valid_keys = {
            "cloudflare_security_gateway",
            "smart_home_bridge",
            "configuration_manager",
        }
        invalid_keys = set(custom_names.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(
                f"Invalid function keys: {invalid_keys}. " f"Valid keys: {valid_keys}"
            )

        # Validate function name values (basic AWS Lambda naming rules)
        for function_key, function_name in custom_names.items():
            if not function_name:
                raise ValueError(
                    f"Function name for {function_key} must be a non-empty string"
                )
            if len(function_name) > 64:
                raise ValueError(
                    f"Function name '{function_name}' too long (max 64 characters)"
                )

        return custom_names if custom_names else None


def main() -> None:
    """Main entry point for the CLI."""
    cli = CLIHandler()
    cli.run()


if __name__ == "__main__":
    main()
