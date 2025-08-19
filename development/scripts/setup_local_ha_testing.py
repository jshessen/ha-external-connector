#!/usr/bin/env python3
"""
Local Home Assistant setup script for HACS integration testing.

This script sets up a minimal Home Assistant environment with our integration
and Browser Mod for local development and testing.
"""

import asyncio
import logging
import os
import shutil
import subprocess  # nosec B404: usage is controlled and arguments are not user-supplied
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
HA_DEV_DIR = PROJECT_ROOT / "ha-dev-instance"
HA_CONFIG_DIR = HA_DEV_DIR / "config"
CUSTOM_COMPONENTS_DIR = HA_CONFIG_DIR / "custom_components"


def check_prerequisites():
    """Check that prerequisites are available."""
    _LOGGER.info("🔍 Checking prerequisites...")

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 11):
        _LOGGER.error(
            "❌ Python 3.11+ required, found %d.%d",
            python_version.major,
            python_version.minor,
        )
        return False

    _LOGGER.info(
        "✅ Python %d.%d.%d",
        python_version.major,
        python_version.minor,
        python_version.micro,
    )

    # Check git
    git_path = shutil.which("git")
    if not git_path:
        _LOGGER.error("❌ Git not found. Install git to continue.")
        return False
    try:
        # Safe: git_path is resolved by shutil.which and not user input
        subprocess.run(
            [git_path, "--version"], check=True, capture_output=True
        )  # nosec B603
        _LOGGER.info("✅ Git available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        _LOGGER.error("❌ Git not found or failed to run. Install git to continue.")
        return False

    return True


def setup_ha_dev_environment():
    """Set up Home Assistant development environment."""
    _LOGGER.info("🏗️ Setting up HA development environment...")

    # Create HA dev directory
    HA_DEV_DIR.mkdir(exist_ok=True)
    os.chdir(HA_DEV_DIR)

    # Create virtual environment for HA
    venv_dir = HA_DEV_DIR / "ha-venv"
    if not venv_dir.exists():
        _LOGGER.info("Creating HA virtual environment...")
        try:
            # nosec B603: sys.executable and venv_dir are trusted, not user input
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)], check=True
            )  # nosec B603
        except subprocess.CalledProcessError as exc:
            _LOGGER.error("❌ Failed to create virtual environment: %s", exc)
            sys.exit(1)
    else:
        _LOGGER.info("✅ HA virtual environment exists")

    # Install Home Assistant in the virtual environment
    ha_python = HA_DEV_DIR / "ha-venv" / "bin" / "python"
    if not ha_python.exists():
        ha_python = HA_DEV_DIR / "ha-venv" / "Scripts" / "python.exe"  # Windows

    _LOGGER.info("Installing Home Assistant...")
    try:
        subprocess.run(
            [str(ha_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,  # nosec B603
        )
        subprocess.run(
            [str(ha_python), "-m", "pip", "install", "homeassistant"],
            check=True,  # nosec B603
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        _LOGGER.error("❌ Failed to install Home Assistant: %s", exc)
        sys.exit(1)

    # Initialize HA configuration
    HA_CONFIG_DIR.mkdir(exist_ok=True)

    _LOGGER.info("✅ HA development environment ready")
    return ha_python


def install_browser_mod():
    """Install Browser Mod custom component."""
    _LOGGER.info("📦 Installing Browser Mod...")

    CUSTOM_COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    browser_mod_dir = CUSTOM_COMPONENTS_DIR / "browser_mod"

    if not browser_mod_dir.exists():
        _LOGGER.info("Cloning Browser Mod repository...")
        os.chdir(CUSTOM_COMPONENTS_DIR)
        git_path = shutil.which("git")
        if not git_path:
            _LOGGER.error("❌ Git not found. Install git to continue.")
            raise FileNotFoundError("git executable not found")
        subprocess.run(
            [
                git_path,
                "clone",
                "https://github.com/thomasloven/hass-browser_mod.git",
                "browser_mod",
            ],
            check=True,  # nosec B603: arguments are hardcoded and safe
        )
    else:
        _LOGGER.info("✅ Browser Mod already installed")

    return browser_mod_dir


def install_our_integration():
    """Install our HACS integration in the dev environment."""
    _LOGGER.info("🔧 Installing our integration...")

    our_integration_dir = CUSTOM_COMPONENTS_DIR / "ha_external_connector"
    source_dir = PROJECT_ROOT / "custom_components" / "ha_external_connector"

    # Remove existing and copy fresh
    if our_integration_dir.exists():
        shutil.rmtree(our_integration_dir)

    shutil.copytree(source_dir, our_integration_dir)
    _LOGGER.info("✅ Our integration installed")

    return our_integration_dir


def create_ha_configuration():
    """Create minimal Home Assistant configuration."""
    _LOGGER.info("⚙️ Creating HA configuration...")

    config_yaml = HA_CONFIG_DIR / "configuration.yaml"

    config_content = """
# Basic Home Assistant configuration for testing
homeassistant:
  name: "HA External Connector Test"
  time_zone: "UTC"
  unit_system: "metric"

# Enable default config components
default_config:

# Enable Browser Mod
browser_mod:

# Enable our integration (will be added via UI)
ha_external_connector:

# Enable development mode
logger:
  default: info
  logs:
    homeassistant.components.ha_external_connector: debug
    custom_components.ha_external_connector: debug
    custom_components.browser_mod: debug

# Enable API for testing
api:

# Enable frontend
frontend:

# Enable HTTP for web access
http:
  server_port: 8123
"""

    with open(config_yaml, "w", encoding="utf-8") as f:
        f.write(config_content.strip())

    _LOGGER.info("✅ Configuration created")


def create_test_scripts():
    """Create test scripts for Browser Mod integration testing."""
    _LOGGER.info("📝 Creating test scripts...")

    scripts_dir = HA_CONFIG_DIR / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Browser Mod test script
    test_script = scripts_dir / "test_browser_mod_integration.py"

    test_content = '''#!/usr/bin/env python3
"""Test script for Browser Mod + HA External Connector integration."""

import asyncio
import sys
from pathlib import Path

# Add HA config to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_browser_mod_services():
    """Test Browser Mod services are available."""
    try:
        from homeassistant.core import HomeAssistant
        from homeassistant.setup import async_setup_component

        hass = HomeAssistant()

        # Setup Browser Mod
        await async_setup_component(hass, "browser_mod", {})

        # Test our integration
        # Test our integration  # noqa: E501
        from custom_components.ha_external_connector.browser_mod_lwa_assistant import (
            BrowserModLWAAssistant,
        )

        assistant = BrowserModLWAAssistant(hass)
        availability = await assistant.check_browser_mod_availability()

        print(f"✅ Browser Mod availability: {availability}")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_browser_mod_services())
    sys.exit(0 if success else 1)
'''

    with open(test_script, "w", encoding="utf-8") as f:
        f.write(test_content)

    _LOGGER.info("✅ Test scripts created")


def create_startup_script():
    """Create startup script for the development environment."""
    startup_script = HA_DEV_DIR / "start_ha_dev.sh"

    startup_content = f"""#!/bin/bash
# Home Assistant development startup script

cd "{HA_DEV_DIR}"

echo "🚀 Starting Home Assistant development environment..."
echo "🏠 Config directory: {HA_CONFIG_DIR}"
echo "🔧 Custom components: {CUSTOM_COMPONENTS_DIR}"
echo ""

# Activate virtual environment
source ha-venv/bin/activate

# Start Home Assistant
echo "Starting Home Assistant on http://localhost:8123"
echo "Press Ctrl+C to stop"
echo ""

hass --config config --debug
"""

    with open(startup_script, "w", encoding="utf-8") as f:
        f.write(startup_content)

    startup_script.chmod(0o755)
    _LOGGER.info("✅ Startup script created")


def print_usage_instructions():
    """Print instructions for using the development environment."""
    _LOGGER.info("\n🎉 Local HA development environment ready!")
    _LOGGER.info("\n📋 Usage Instructions:")
    _LOGGER.info("1. Start HA: cd %s && ./start_ha_dev.sh", HA_DEV_DIR)
    _LOGGER.info("2. Open browser: http://localhost:8123")
    _LOGGER.info("3. Go through HA setup wizard")
    _LOGGER.info("4. Add our integration via Configuration > Integrations")
    _LOGGER.info("5. Test Browser Mod services in Developer Tools")

    _LOGGER.info("\n🧪 Testing Workflow:")
    _LOGGER.info("- Developer Tools > Services > browser_mod.popup")
    _LOGGER.info(
        "- Developer Tools > Services > ha_external_connector.setup_lwa_profile"
    )
    _LOGGER.info(
        "- Developer Tools > Services > ha_external_connector.check_browser_mod"
    )

    _LOGGER.info("\n📁 Environment Locations:")
    _LOGGER.info("- HA Config: %s", HA_CONFIG_DIR)
    _LOGGER.info("- Our Integration: %s/ha_external_connector", CUSTOM_COMPONENTS_DIR)
    _LOGGER.info("- Browser Mod: %s/browser_mod", CUSTOM_COMPONENTS_DIR)


async def main():
    """Set up the complete local testing environment."""
    _LOGGER.info("🚀 Setting up HA External Connector local testing environment...")

    try:
        # Check prerequisites
        if not check_prerequisites():
            return False

        # Set up HA environment
        setup_ha_dev_environment()

        # Install Browser Mod
        install_browser_mod()

        # Install our integration
        install_our_integration()

        # Create configuration
        create_ha_configuration()

        # Create test scripts
        create_test_scripts()

        # Create startup script
        create_startup_script()

        # Print usage instructions
        print_usage_instructions()

        return True

    except (OSError, subprocess.CalledProcessError) as exc:
        _LOGGER.error("❌ Setup failed: %s", exc)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
