#!/usr/bin/env python3
"""
Agent automation helper for HA External Connector.

This script provides common automation tasks that would typically use
`python -c` commands, but are implemented as proper scripts to work
with VS Code's terminal allowlist restrictions.
"""

import argparse
import importlib.util
import os
import subprocess  # nosec B404  # Safe for known development tools
import sys
from pathlib import Path


def diagnose_import_issue() -> list[str]:
    """Diagnose the specific import issue we're encountering."""
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    diagnostics: list[str] = []

    # Check if ha_connector package exists
    ha_connector_path = src_path / "ha_connector"
    diagnostics.append(f"📁 ha_connector path: {ha_connector_path}")
    diagnostics.append(f"📁 ha_connector exists: {ha_connector_path.exists()}")

    # Check platforms directory
    platforms_path = ha_connector_path / "platforms"
    diagnostics.append(f"📁 platforms path: {platforms_path}")
    diagnostics.append(f"📁 platforms exists: {platforms_path.exists()}")

    # Check utils
    utils_path = ha_connector_path / "utils"
    diagnostics.append(f"📁 utils path: {utils_path}")
    diagnostics.append(f"📁 utils exists: {utils_path.exists()}")

    # Check if there's any utils inside platforms (shouldn't exist)
    platforms_utils_path = platforms_path / "utils"
    diagnostics.append(f"❓ platforms/utils path: {platforms_utils_path}")
    diagnostics.append(f"❓ platforms/utils exists: {platforms_utils_path.exists()}")

    try:
        # Test basic sys.path
        spec = importlib.util.find_spec("ha_connector.utils")
        if spec:
            diagnostics.append(f"✅ ha_connector.utils spec found: {spec.origin}")
        else:
            diagnostics.append("❌ ha_connector.utils spec not found")
    except (ImportError, ModuleNotFoundError) as e:
        diagnostics.append(f"❌ spec check failed: {e}")

    try:
        # Try the main package last (most likely to have circular dependencies)
        spec = importlib.util.find_spec("ha_connector")
        if spec:
            diagnostics.append("✅ ha_connector package spec found")
        else:
            diagnostics.append("❌ ha_connector package spec not found")
    except (ImportError, ModuleNotFoundError) as e:
        diagnostics.append(f"❌ ha_connector package spec check failed: {e}")

    return diagnostics


def check_imports() -> list[str]:
    """Test if key project modules can be imported successfully."""
    # Add src to path for project imports
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    import_tests = [
        ("ha_connector", "Main connector module"),
        ("ha_connector.cli.commands", "CLI commands"),
        ("ha_connector.platforms.aws.resource_manager", "AWS manager"),
        ("ha_connector.config.manager", "Config manager"),
    ]

    results: list[str] = []
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            results.append(f"✅ {description}: {module_name}")
        except ImportError as e:
            results.append(f"❌ {description}: {module_name} - {e}")

    return results


def check_environment() -> list[str]:
    """Validate development environment setup."""
    checks: list[str] = []

    # Python version
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    checks.append(f"🐍 Python version: {python_version}")

    # Virtual environment
    venv_path = sys.executable
    if ".venv" in venv_path:
        checks.append(f"✅ Virtual environment: Active ({venv_path})")
    else:
        checks.append(f"⚠️  Virtual environment: Not detected ({venv_path})")

    # Working directory
    cwd = os.getcwd()
    checks.append(f"📁 Working directory: {cwd}")

    # Project files
    key_files = ["pyproject.toml", "src/ha_connector", ".venv"]
    for file_path in key_files:
        if Path(file_path).exists():
            checks.append(f"✅ {file_path}: Found")
        else:
            checks.append(f"❌ {file_path}: Missing")

    return checks


def check_tools() -> list[str]:
    """Check availability of development tools."""
    tools = ["ruff", "pytest", "mypy", "black"]
    tool_status: list[str] = []

    for tool in tools:
        try:
            # nosec B603: subprocess call - Safe because 'tool' is from a hardcoded
            # trusted list, not user input.
            result = subprocess.run(  # nosec B603
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,  # We handle return codes explicitly
            )
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                tool_status.append(f"✅ {tool}: {version}")
            else:
                tool_status.append(f"❌ {tool}: Failed to get version")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            tool_status.append(f"❌ {tool}: Not found")

    return tool_status


def show_python_info() -> None:
    """Display comprehensive Python environment information."""
    print("🐍 Python Environment Information")
    print("=" * 50)
    print(f"Executable: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Path entries: {len(sys.path)}")
    print(f"Working directory: {os.getcwd()}")


def _handle_imports_action() -> None:
    """Handle the imports action."""
    print("🔍 Testing module imports...")
    for result in check_imports():
        print(result)


def _handle_env_action() -> None:
    """Handle the environment action."""
    print("🔧 Environment validation...")
    for check in check_environment():
        print(check)


def _handle_tools_action() -> None:
    """Handle the tools action."""
    print("🛠️  Development tools...")
    for status in check_tools():
        print(status)


def _handle_diagnose_action() -> None:
    """Handle the diagnose action."""
    print("🔍 Diagnosing import issues...")
    for result in diagnose_import_issue():
        print(result)


def _handle_setup_action() -> None:
    """Handle the setup action - full environment setup with validation."""
    print("🚀 Setting up development environment...")
    
    # Check if virtual environment exists
    venv_path = Path(__file__).parent.parent / ".venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run: python -m venv .venv")
        return
    
    # Activate virtual environment reminder
    print("✅ Virtual environment found")
    print("🔧 Ensure environment is activated:")
    print("   source .venv/bin/activate")
    
    # Run all validation checks
    print("\n🔧 Environment Validation")
    print("=" * 40)
    for check in check_environment():
        print(check)
    
    print("\n🛠️  Development Tools")
    print("=" * 40)
    for status in check_tools():
        print(status)
    
    print("\n🔍 Module Imports")
    print("=" * 40)
    for result in check_imports():
        print(result)
    
    print("\n✅ Setup complete! Environment ready for development.")


def _handle_check_action() -> None:
    """Handle the check action - quick health check."""
    print("🩺 Quick health check...")
    
    # Check basic environment
    print("🐍 Python:", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check virtual environment
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print("🔧 Virtual env:", "✅ Active" if venv_active else "❌ Not active")
    
    # Check key directories
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src" / "ha_connector"
    print("📁 Project structure:", "✅ Valid" if src_path.exists() else "❌ Invalid")
    
    # Quick import test
    try:
        __import__("ha_connector")
        print("📦 Package import:", "✅ Working")
    except ImportError:
        print("📦 Package import:", "❌ Failed")
    
    print("\n🎯 Status: Environment ready" if venv_active and src_path.exists() else "⚠️  Status: Setup needed")


def _handle_refresh_action() -> None:
    """Handle the refresh action - reload agent instructions."""
    print("🔄 Refreshing agent instructions...")
    
    instructions_path = Path(__file__).parent.parent / ".github" / "instructions"
    if not instructions_path.exists():
        print("❌ Instructions directory not found")
        return
    
    # Validate instruction files exist
    core_files = ["environment-setup.md", "quality-standards.md", "agent-refresh.md"]
    specialized_files = ["aws-patterns.md", "lambda-patterns.md", "testing-patterns.md", "security-patterns.md"]
    documentation_files = ["markdown-standards.md", "docs-organization.md"]
    
    print("📋 Validating instruction files...")
    
    # Check core instructions
    core_path = instructions_path / "core"
    for file in core_files:
        file_path = core_path / file
        status = "✅" if file_path.exists() else "❌"
        print(f"  {status} core/{file}")
    
    # Check specialized instructions
    specialized_path = instructions_path / "specialized"
    for file in specialized_files:
        file_path = specialized_path / file
        status = "✅" if file_path.exists() else "❌"
        print(f"  {status} specialized/{file}")
    
    # Check documentation instructions
    doc_path = instructions_path / "documentation"
    for file in documentation_files:
        file_path = doc_path / file
        status = "✅" if file_path.exists() else "❌"
        print(f"  {status} documentation/{file}")
    
    # Check for transfer block consistency
    lambda_patterns = specialized_path / "lambda-patterns.md"
    aws_patterns = specialized_path / "aws-patterns.md"
    
    print("\n🔄 Transfer Block Validation:")
    if lambda_patterns.exists() and aws_patterns.exists():
        lambda_content = lambda_patterns.read_text()
        aws_content = aws_patterns.read_text()
        
        # Check if lambda-patterns has comprehensive transfer block content
        has_transfer_blocks = "TRANSFER BLOCK START" in lambda_content
        aws_has_reference = "lambda-patterns.md" in aws_content
        
        print(f"  ✅ Lambda patterns has transfer blocks: {has_transfer_blocks}")
        print(f"  ✅ AWS patterns references lambda patterns: {aws_has_reference}")
        
        if has_transfer_blocks and aws_has_reference:
            print("  ✅ Transfer block consolidation: VALIDATED")
        else:
            print("  ⚠️  Transfer block consolidation: NEEDS REVIEW")
    
    print("\n✅ Instruction refresh complete!")


def _handle_validate_instructions_action() -> None:
    """Handle instruction validation."""
    print("🔍 Validating instruction consistency...")
    
    instructions_path = Path(__file__).parent.parent / ".github" / "instructions"
    
    # Check hierarchy structure
    expected_structure = {
        "core": ["environment-setup.md", "quality-standards.md", "agent-refresh.md"],
        "specialized": ["aws-patterns.md", "lambda-patterns.md", "testing-patterns.md", "security-patterns.md"],
        "documentation": ["markdown-standards.md", "docs-organization.md"]
    }
    
    validation_results = []
    
    for category, files in expected_structure.items():
        category_path = instructions_path / category
        if not category_path.exists():
            validation_results.append(f"❌ Missing directory: {category}")
            continue
        
        for file in files:
            file_path = category_path / file
            if file_path.exists():
                validation_results.append(f"✅ {category}/{file}")
            else:
                validation_results.append(f"❌ Missing: {category}/{file}")
    
    # Print results
    for result in validation_results:
        print(result)
    
    # Summary
    failed_checks = [r for r in validation_results if r.startswith("❌")]
    if failed_checks:
        print(f"\n⚠️  Validation failed: {len(failed_checks)} issues found")
    else:
        print("\n✅ All instruction files validated successfully!")


def _handle_quick_reference_action() -> None:
    """Handle quick reference display."""
    print("🚀 Quick Reference Guide")
    print("=" * 50)
    
    print("\n🔧 Essential Commands:")
    print("  python scripts/agent_helper.py setup     # Full environment setup")
    print("  python scripts/agent_helper.py check     # Quick health check")
    print("  python scripts/agent_helper.py refresh   # Reload instructions")
    print("  source .venv/bin/activate                # Activate environment")
    
    print("\n🎯 Code Quality:")
    print("  source .venv/bin/activate && ruff check src/   # Fast linting")
    print("  source .venv/bin/activate && pylint src/       # Comprehensive analysis")
    print("  source .venv/bin/activate && mypy src/         # Type checking")
    print("  source .venv/bin/activate && pytest            # Run tests")
    
    print("\n📁 File Pattern Mappings:")
    print("  **/test_*.py                 → specialized/testing-patterns.md")
    print("  **/aws_*.py                  → specialized/aws-patterns.md")
    print("  **/lambda_functions/**/*.py  → specialized/lambda-patterns.md")
    print("  **/*.md                      → documentation/markdown-standards.md")
    
    print("\n🎯 Quality Targets:")
    print("  • Ruff: All checks must pass")
    print("  • Pylint: Perfect 10.00/10 score")
    print("  • MyPy: Clean type checking")
    print("  • Transfer Blocks: Sync from specialized/lambda-patterns.md")
    
    print("\n🔄 Instruction Hierarchy:")
    print("  1. .github/copilot-instructions.md (highest priority)")
    print("  2. instructions/core/ (fundamental patterns)")
    print("  3. instructions/specialized/ (domain-specific)")
    print("  4. instructions/documentation/ (content standards)")


def _handle_all_action() -> None:
    """Handle the all action."""
    show_python_info()
    print("\n🔧 Environment Validation")
    print("=" * 40)
    for check in check_environment():
        print(check)

    print("\n🛠️  Development Tools")
    print("=" * 40)
    for status in check_tools():
        print(status)

    print("\n🔍 Module Imports")
    print("=" * 40)
    for result in check_imports():
        print(result)


def main() -> None:
    """Main automation helper function."""
    parser = argparse.ArgumentParser(description="Agent automation helper")
    parser.add_argument(
        "action",
        choices=[
            "imports", "env", "tools", "python", "all", "diagnose",
            "setup", "check", "refresh", "validate-instructions", "quick-reference"
        ],
        help="Action to perform",
    )

    args = parser.parse_args()

    # Dispatch to appropriate handler functions
    action_handlers = {
        "imports": _handle_imports_action,
        "env": _handle_env_action,
        "tools": _handle_tools_action,
        "python": show_python_info,
        "diagnose": _handle_diagnose_action,
        "all": _handle_all_action,
        "setup": _handle_setup_action,
        "check": _handle_check_action,
        "refresh": _handle_refresh_action,
        "validate-instructions": _handle_validate_instructions_action,
        "quick-reference": _handle_quick_reference_action,
    }

    handler = action_handlers.get(args.action)
    if handler:
        handler()
    else:
        print(f"Unknown action: {args.action}")


if __name__ == "__main__":
    main()
