#!/usr/bin/env python3
"""
Home Assistant Development Environment Setup Script

This script automates the setup of a development environment that provides
full Home Assistant module access and type support for VS Code + Pylance.

Usage:
    python scripts/setup_ha_dev.py [--check-only]

Features:
- Creates symlink to Home Assistant core modules
- Verifies all dependencies are installed
- Tests import functionality
- Provides status information for troubleshooting
"""

import os
import subprocess  # nosec B404 # Only used with static, validated command lists
import sys
from pathlib import Path


def run_command(cmd: list[str], capture_output: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr.

    Security: Only use this with trusted, static command lists.
    """
    # Validate that cmd is a list of strings and not constructed from untrusted input
    if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
        raise ValueError("Command must be a list of strings")
    try:
        # SECURITY: cmd is always a static, trusted list (never user input)
        # This is enforced by the function's docstring and input validation above.
        result: subprocess.CompletedProcess[str] = (
            subprocess.run(  # nosec B603 # cmd validated as trusted list
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
            )
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.SubprocessError as e:
        return 1, "", str(e)
    except OSError as e:
        # Handle unexpected OS-related errors
        return 1, "", str(e)


def check_poetry_env() -> bool:
    """Check if we're in a Poetry virtual environment."""
    return "POETRY_ACTIVE" in os.environ or "VIRTUAL_ENV" in os.environ


def get_venv_path() -> Path:
    """Get the path to the virtual environment."""
    if "VIRTUAL_ENV" in os.environ:
        return Path(os.environ["VIRTUAL_ENV"])

    # Try to get from Poetry
    code: int
    stdout: str
    code, stdout, _ = run_command(["poetry", "env", "info", "--path"])
    if code == 0:
        return Path(stdout.strip())

    # Fallback to .venv
    return Path(".venv")


def get_ha_core_path() -> Path | None:
    """Get the path to Home Assistant core repository."""
    # Check common locations
    candidates: list[Path] = [
        Path("/mnt/development/GitHub/ha-core"),
        Path("../ha-core"),
        Path("../../ha-core"),
        Path("~/Development/GitHub/ha-core").expanduser(),
    ]

    for path in candidates:
        ha_path: Path = path / "homeassistant"
        if ha_path.exists() and ha_path.is_dir():
            return ha_path

    return None


def create_ha_symlink(venv_path: Path, ha_core_path: Path) -> bool:
    """Create symlink to Home Assistant core modules."""
    # Find the site-packages directory
    site_packages: Path | None = None
    for python_dir in venv_path.glob("lib/python*/site-packages"):
        site_packages = python_dir
        break

    if not site_packages:
        print("❌ Could not find site-packages directory")
        return False

    symlink_path: Path = site_packages / "homeassistant"

    # Remove existing symlink/directory if it exists
    if symlink_path.exists() or symlink_path.is_symlink():
        if symlink_path.is_symlink():
            symlink_path.unlink()
        else:
            print(f"⚠️  Found existing homeassistant directory at {symlink_path}")
            print("   Please remove it manually if you want to create a symlink")
            return False

    try:
        # Create relative symlink
        relative_path: str = os.path.relpath(ha_core_path, symlink_path.parent)
        symlink_path.symlink_to(relative_path)
        print(f"✅ Created symlink: {symlink_path} -> {relative_path}")
        return True
    except (OSError, ValueError) as e:
        print(f"❌ Failed to create symlink: {e}")
        return False


def test_imports() -> bool:
    """Test that Home Assistant modules can be imported."""
    modules_to_test: list[str] = [
        "homeassistant",
        "homeassistant.core",
        "homeassistant.exceptions",
        "homeassistant.data_entry_flow",
    ]

    success_count: int = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")

    return success_count == len(modules_to_test)


def main():
    """Main setup function."""
    check_only = "--check-only" in sys.argv

    print("🏠 Home Assistant Development Environment Setup")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)

    # Check Poetry environment
    venv_path = get_venv_path()
    print(f"📁 Virtual environment: {venv_path}")

    if not venv_path.exists():
        print(
            "❌ Virtual environment not found. Please create and activate your virtual "
            "environment before running this script."
        )
        sys.exit(1)
    ha_core_path = get_ha_core_path()
    if ha_core_path is None:
        print("❌ Home Assistant core repository not found.")
        print("   Expected locations:")
        print("   - /mnt/development/GitHub/ha-core/homeassistant/")
        print("   - ../ha-core/homeassistant/")
        print("   - ~/Development/GitHub/ha-core/homeassistant/")
        sys.exit(1)

    print(f"🏠 Home Assistant core: {ha_core_path}")

    print(f"🏠 Home Assistant core: {ha_core_path}")

    # Check symlink
    site_packages = None
    for python_dir in venv_path.glob("lib/python*/site-packages"):
        site_packages = python_dir
        break

    if site_packages:
        symlink_path = site_packages / "homeassistant"
        if symlink_path.is_symlink():
            target = symlink_path.readlink()
            print(f"🔗 Symlink exists: homeassistant -> {target}")
        elif symlink_path.exists():
            print("⚠️  homeassistant directory exists but is not a symlink")
        else:
            if not check_only:
                print("📎 Creating symlink...")
                if not create_ha_symlink(venv_path, ha_core_path):
                    sys.exit(1)
            else:
                print("❌ No symlink found")

    # Test imports
    print("\n🧪 Testing imports...")
    if test_imports():
        print("\n🎉 SUCCESS! Home Assistant development environment is ready!")
        print("💻 VS Code + Pylance should now have full type support")
    else:
        print(
            "\n❌ Some imports failed. You may need to install additional dependencies:"
        )
        print("   poetry install --with dev")
        sys.exit(1)


if __name__ == "__main__":
    main()
