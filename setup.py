#!/usr/bin/env python3
"""Simple setup script to initialize the project."""

import logging
import subprocess  # nosec B404
import sys
import time
from pathlib import Path

# Setup configuration
SETUP_CONFIG: dict[str, int | str | set[str]] = {
    "timeout": 300,  # Command timeout in seconds
    "log_level": "INFO",
    "allowed_commands": {
        "poetry",
        "python",
        "python3",
        "pip",
        "pre-commit",
        "pytest",
        "mypy",
        "black",
        "ruff",
        "bandit",
    },
}


# Configure logging for setup operations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def validate_command(cmd: str) -> None:
    """Validate that command is safe to execute."""
    command_parts = cmd.strip().split()
    if not command_parts:
        raise ValueError("Empty command not allowed")

    base_command = command_parts[0]
    allowed_commands = SETUP_CONFIG["allowed_commands"]
    if not isinstance(allowed_commands, set):
        raise TypeError(
            f"Expected set for allowed_commands, got {type(allowed_commands)}"
        )
    if base_command not in allowed_commands:
        raise ValueError(
            f"Command '{base_command}' not in allowed list: {allowed_commands}"
        )


def run_command(
    cmd: str, check: bool = True, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with timeout protection.

    Args:
        cmd: Command to execute
        check: Whether to raise exception on non-zero exit
        timeout: Maximum execution time in seconds

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command is not in allowed list
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    # Validate command before execution
    validate_command(cmd)

    # Use configured timeout if none provided
    if timeout is None:
        timeout = SETUP_CONFIG["timeout"]  # type: ignore[assignment]

    logging.info("Executing: %s", cmd)
    start_time = time.perf_counter()

    try:
        # nosec B602 - shell=True needed for setup commands like "poetry install"
        result = subprocess.run(  # nosec B602
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logging.error("Command timed out after %ss: %s", timeout, cmd)
        raise

    elapsed = time.perf_counter() - start_time
    logging.info(
        "Command completed in %.2fs with exit code %s", elapsed, result.returncode
    )

    if check and result.returncode != 0:
        logging.error("Command failed: %s", cmd)
        logging.error("STDOUT: %s", result.stdout)
        logging.error("STDERR: %s", result.stderr)
        sys.exit(1)

    return result


def check_prerequisites() -> None:
    """Check that required tools are installed."""
    logging.info("🔍 Checking prerequisites...")

    # Check if poetry is installed
    poetry_check = run_command("poetry --version", check=False)
    if poetry_check.returncode != 0:
        logging.error("❌ Poetry not found. Please install Poetry first:")
        logging.error("   curl -sSL https://install.python-poetry.org | python3 -")
        sys.exit(1)

    logging.info("✅ Poetry found")


def install_dependencies() -> None:
    """Install project dependencies."""
    logging.info("📦 Installing dependencies...")
    run_command("poetry install")


def setup_development_tools() -> None:
    """Setup development tools and hooks."""
    logging.info("🔧 Setting up pre-commit hooks...")
    run_command("poetry run pre-commit install")


def create_initial_tests(project_root: Path) -> None:
    """Create initial test structure and files."""
    logging.info("🧪 Creating initial test structure...")

    test_dir = project_root / "tests" / "unit"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_initial.py"

    if not test_file.exists():
        test_content = '''"""Initial test file.

import pytest


def test_project_structure():
    """Test that the project structure is correct."""
    import ha_connector
    assert ha_connector.__version__ == "0.1.0"


def test_imports():
    """Test that basic imports work."""
    from ha_connector.models import InstallationScenario
    from ha_connector.config import Settings
    # Test enum values
    assert InstallationScenario.DIRECT_ALEXA == "direct_alexa"
    assert InstallationScenario.CLOUDFLARE_ALEXA == "cloudflare_alexa"
    assert InstallationScenario.CLOUDFLARE_IOS == "cloudflare_ios"
    # Test settings instantiation
    settings = Settings()
    assert settings.aws_region == "us-east-1"
    assert settings.log_level == "INFO"
'''
        test_file.write_text(test_content)
        logging.info("Created initial test file: %s", test_file)


def run_quality_checks() -> None:
    """Run initial code quality checks."""
    logging.info("🔍 Running code quality checks...")

    # Run initial tests
    logging.info("🧪 Running initial tests...")
    run_command("poetry run python -m pytest tests/unit/test_initial.py -v")

    # Check code quality (non-blocking for initial setup)
    logging.info("🔍 Running type checking...")
    run_command(
        "poetry run mypy --install-types --non-interactive src/ha_connector/",
        check=False,
    )


def print_next_steps() -> None:
    """Print helpful next steps for the user."""
    logging.info("✅ Project initialization complete!")
    print("\n📖 Next steps:")
    print(
        "1. Review the migration action plan: "
        "../ha-external-connector/PYTHON_MIGRATION_ACTION_PLAN.md"
    )
    print("2. Start with Phase 1.2: Implement core models and configuration")
    print("3. Run tests with: poetry run pytest")
    print("4. Check code quality with: poetry run mypy src/")
    print("5. Format code with: poetry run black src/ tests/")


def main() -> None:
    """Initialize the project."""
    project_root = Path(__file__).parent

    logging.info("🚀 Initializing Home Assistant External Connector Python project...")

    try:
        check_prerequisites()
        install_dependencies()
        setup_development_tools()
        create_initial_tests(project_root)
        run_quality_checks()
        print_next_steps()
    except KeyboardInterrupt:
        logging.warning("⚠️  Setup interrupted by user")
        sys.exit(1)
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        logging.error("Setup failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
