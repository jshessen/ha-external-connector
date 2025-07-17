#!/usr/bin/env python3
"""Simple setup script to initialize the project."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    return result


def main():
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
        test_file.write_text('''"""Initial test file."""

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
''')
    
    # Run initial tests
    print("🧪 Running initial tests...")
    run_command("poetry run python -m pytest tests/unit/test_initial.py -v")
    
    # Check code quality
    print("🔍 Running code quality checks...")
    run_command("poetry run mypy --install-types --non-interactive src/ha_connector/", check=False)
    
    print("✅ Project initialization complete!")
    print("\n📖 Next steps:")
    print("1. Review the migration action plan: ../ha-external-connector/PYTHON_MIGRATION_ACTION_PLAN.md")
    print("2. Start with Phase 1.2: Implement core models and configuration")
    print("3. Run tests with: poetry run pytest")
    print("4. Check code quality with: poetry run mypy src/")
    print("5. Format code with: poetry run black src/ tests/")


if __name__ == "__main__":
    main()
