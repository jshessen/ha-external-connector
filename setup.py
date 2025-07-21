#!/usr/bin/env python3
"""Simple setup script to initialize the project."""

import subprocess  # nosec B404
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command."""
    print(f"Running: {cmd}")
    # nosec B602 - shell=True needed for setup commands like "poetry install"
    result = subprocess.run(  # nosec B602
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )

    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)

    return result


def main() -> None:
    """Initialize the project."""
    project_root = Path(__file__).parent

    print("🚀 Initializing Home Assistant External Connector Python project...")

    # Check if poetry is installed
    poetry_check = run_command("poetry --version", check=False)
    if poetry_check.returncode != 0:
        print("❌ Poetry not found. Please install Poetry first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        sys.exit(1)

    print("✅ Poetry found")

    # Install dependencies
    print("📦 Installing dependencies...")
    run_command("poetry install")

    # Setup pre-commit hooks
    print("🔧 Setting up pre-commit hooks...")
    run_command("poetry run pre-commit install")

    # Create initial empty test file
    test_dir = project_root / "tests" / "unit"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_initial.py"
    if not test_file.exists():
        test_file.write_text(
            '"""Initial test file.\n\n'
            "import pytest\n\n"
            "def test_project_structure():\n"
            '    """Test that the project structure is correct."""\n'
            "    import ha_connector\n"
            '    assert ha_connector.__version__ == "0.1.0"\n\n\n'
            "def test_imports():\n"
            '    """Test that basic imports work."""\n'
            "    from ha_connector.models import InstallationScenario\n"
            "    from ha_connector.config import Settings\n"
            "    # Test enum values\n"
            '    assert InstallationScenario.DIRECT_ALEXA == "direct_alexa"\n'
            '    assert InstallationScenario.CLOUDFLARE_ALEXA == "cloudflare_alexa"\n'
            '    assert InstallationScenario.CLOUDFLARE_IOS == "cloudflare_ios"\n'
            "    # Test settings instantiation\n"
            "    settings = Settings()\n"
            '    assert settings.aws_region == "us-east-1"\n'
            '    assert settings.log_level == "INFO"\n'
        )

    # Run initial tests
    print("🧪 Running initial tests...")
    run_command("poetry run python -m pytest tests/unit/test_initial.py -v")
    # Check code quality
    print("🔍 Running code quality checks...")
    run_command(
        "poetry run mypy --install-types --non-interactive src/ha_connector/",
        check=False,
    )
    print("✅ Project initialization complete!")
    print("\n📖 Next steps:")
    print(
        "1. Review the migration action plan: "
        "../ha-external-connector/PYTHON_MIGRATION_ACTION_PLAN.md"
    )
    print("2. Start with Phase 1.2: Implement core models and configuration")
    print("3. Run tests with: poetry run pytest")
    print("4. Check code quality with: poetry run mypy src/")
    print("5. Format code with: poetry run black src/ tests/")


if __name__ == "__main__":
    main()
