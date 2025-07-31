#!/usr/bin/env python3
"""
Comprehensive Python Code Quality Analysis Suite

This script provides a unified interface for running various code quality tools
organized by categories: formatters, linters, type checkers, security tools,
and analyzers.

NOTE: This file is synchronized with scripts/code_quality.sh
When modifying tool configurations or order, update both files.
"""

import argparse
import os
import subprocess  # nosec B404 # Required for running code quality tools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SummaryStats:
    """Container for code quality analysis summary statistics."""

    passed: list[tuple[str, str, int, str, str]]
    issues: list[tuple[str, str, int, str, str]]
    fixed: list[tuple[str, str, int, str, str]]
    errors: list[tuple[str, str, int, str, str]]
    total_issues: int


@dataclass
class ToolResult:
    """Container for tool execution result data."""

    name: str
    returncode: int
    stdout: str
    stderr: str
    apply_fixes: bool
    verbose: bool


@dataclass
class SummaryConfig:
    """Container for summary building configuration."""

    stats: SummaryStats
    apply_fixes: bool
    results: list[tuple[str, str, int, str, str]]
    verbose: bool


# =============================================================================
# TOOL CATEGORIES AND CONFIGURATIONS
# =============================================================================

FORMATTERS = {
    "black": {
        "description": "Code formatting (PEP 8 style)",
        "cmd_check": ["black", "--check", "--diff"],
        "cmd_fix": ["black"],
        "python_tool": True,
        "supports_fix": True,
    },
    "isort": {
        "description": "Import sorting and organization",
        "cmd_check": ["isort", "--check-only", "--diff"],
        "cmd_fix": ["isort"],
        "python_tool": True,
        "supports_fix": True,
    },
}

LINTERS = {
    "ruff": {
        "description": "Fast Python linter (replaces flake8, isort, etc.)",
        "cmd_check": ["ruff", "check"],
        "cmd_fix": ["ruff", "check", "--fix"],
        "python_tool": True,
        "supports_fix": True,
    },
    "flake8": {
        "description": "Style guide enforcement",
        "cmd_check": ["flake8"],
        "cmd_fix": ["flake8"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
    "pylint": {
        "description": "Comprehensive code analysis",
        "cmd_check": ["pylint"],
        "cmd_fix": ["pylint"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
}

TYPE_CHECKERS = {
    "mypy": {
        "description": "Static type checking",
        "cmd_check": ["mypy"],
        "cmd_fix": ["mypy"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
    "pyright": {
        "description": "Microsoft's Python type checker (Pylance engine)",
        "cmd_check": ["pyright"],
        "cmd_fix": ["pyright"],  # No auto-fix
        "python_tool": False,  # Node.js tool
        "supports_fix": False,
    },
}

SECURITY_TOOLS = {
    "bandit": {
        "description": "Security vulnerability scanner",
        "cmd_check": ["bandit", "-c", "pyproject.toml", "-r"],
        "cmd_fix": ["bandit", "-c", "pyproject.toml", "-r"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
    "safety": {
        "description": "Known security vulnerabilities in dependencies",
        "cmd_check": ["safety", "check"],
        "cmd_fix": ["safety", "check"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
    "pip-audit": {
        "description": "OWASP dependency vulnerability check",
        "cmd_check": ["pip_audit"],
        "cmd_fix": ["pip_audit"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
}

CODE_ANALYSIS = {
    "vulture": {
        "description": "Dead code detection",
        "cmd_check": ["vulture"],
        "cmd_fix": ["vulture"],  # No auto-fix
        "python_tool": True,
        "supports_fix": False,
    },
}

# All tool categories combined
ALL_CATEGORIES = {
    "formatters": FORMATTERS,
    "linters": LINTERS,
    "type-checkers": TYPE_CHECKERS,
    "security": SECURITY_TOOLS,
    "analysis": CODE_ANALYSIS,
}

# Configuration profiles for different use cases
PROFILES = {
    "development": {
        "description": "Quick checks for development workflow",
        "categories": ["formatters", "linters"],
        "tools": ["black", "isort", "ruff"],
    },
    "ci": {
        "description": "Comprehensive checks for CI/CD pipeline",
        "categories": ["formatters", "linters", "type-checkers", "security"],
        "tools": ["black", "isort", "ruff", "flake8", "pylint", "mypy", "bandit", "safety", "pip-audit"],  # Exclude pyright (Node.js tool)
    },
    "pre-commit": {
        "description": "Fast pre-commit hooks",
        "categories": ["formatters"],
        "tools": ["black", "isort", "ruff"],
    },
    "security": {
        "description": "Security-focused analysis",
        "categories": ["security"],
        "tools": ["bandit", "safety", "pip-audit"],
    },
    "typing": {
        "description": "Type checking focus",
        "categories": ["type-checkers"],
        "tools": ["mypy", "pyright"],
    },
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_venv_python() -> str:
    """Get the Python executable from the virtual environment."""
    # Check if we're already in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if in_venv:
        return sys.executable

    # Look for .venv directory
    venv_path = Path(".venv")
    if venv_path.exists():
        python_exe = venv_path / "bin" / "python"
        if python_exe.exists():
            return str(python_exe)

    # Fallback to system python
    return sys.executable


def get_all_tools() -> dict[str, dict[str, Any]]:
    """Get all tools from all categories."""
    all_tools: dict[str, dict[str, Any]] = {}
    for category_tools in ALL_CATEGORIES.values():
        all_tools.update(category_tools)
    return all_tools


def get_tools_by_categories(categories: list[str]) -> dict[str, dict[str, Any]]:
    """Get tools filtered by categories."""
    tools: dict[str, dict[str, Any]] = {}
    for category in categories:
        if category in ALL_CATEGORIES:
            tools.update(ALL_CATEGORIES[category])
    return tools


def get_quality_targets(file_args: list[str] | None = None) -> list[str]:
    """Get list of directories and files to analyze."""
    # If specific files were provided, validate and use those
    if file_args:
        validated_targets: list[str] = []
        for target in file_args:
            # Security: Validate file paths to prevent directory traversal
            if ".." in target or target.startswith("/"):
                print(f"❌ Security: Invalid file path rejected: {target}")
                continue

            # Security: Check path length to prevent buffer overflow
            if len(target) > 1024:
                print(f"❌ Security: File path too long: {target}")
                continue

            # Validate that target exists
            target_path = Path(target)
            if target_path.exists():
                validated_targets.append(target)
            else:
                print(f"❌ Target not found: {target}")

        if not validated_targets:
            print("❌ No valid targets provided")
            sys.exit(1)

        return validated_targets

    targets: list[str] = []

    # Always include src
    targets.append("src/")

    # Include tests if it exists
    if Path("tests").exists():
        targets.append("tests/")

    # Include scripts if it exists
    if Path("scripts").exists():
        targets.append("scripts/")

    # Include root-level Python files
    root_py_files = ["setup.py", "conftest.py"]
    for py_file in root_py_files:
        if Path(py_file).exists():
            targets.append(py_file)

    return targets


def run_command(
    cmd: list[str], description: str, tool_config: dict[str, Any]
) -> tuple[int, str, str]:
    """Run a command and return the result."""
    print(f"🔍 {description}...")

    # Security: Validate command arguments
    if not cmd:
        return -1, "", "Invalid command arguments"

    # Security: Check command length to prevent buffer overflow
    full_cmd_str = " ".join(cmd)
    if len(full_cmd_str) > 4096:
        return -1, "", "Command too long"

    # Prepend Python executable for Python tools
    if tool_config.get("python_tool", True):
        venv_python = get_venv_python()
        cmd = [venv_python, "-m"] + cmd

    # Security: Create clean environment
    clean_env = os.environ.copy()
    # Remove potentially dangerous environment variables
    for var in ["LD_PRELOAD", "LD_LIBRARY_PATH"]:
        clean_env.pop(var, None)

    try:
        # Enhanced output capture for better terminal integration
        result = subprocess.run(  # nosec B603 # Commands from known tools
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5 minute timeout
            env=clean_env,  # Use clean environment
            cwd=Path.cwd(),  # Explicit working directory
        )

        # Security: Limit output size to prevent memory exhaustion
        max_output_size = 1024 * 1024  # 1MB limit
        if len(result.stdout) > max_output_size:
            result.stdout = result.stdout[:max_output_size] + "\n... (output truncated)"
        if len(result.stderr) > max_output_size:
            result.stderr = result.stderr[:max_output_size] + "\n... (output truncated)"

        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after 300 seconds: {' '.join(cmd)}"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except OSError as e:
        return -1, "", f"System error executing command: {e}"


def process_tool_result(tool_data: ToolResult) -> tuple[str, str, int, str, str]:
    """Process the result of running a code quality tool."""
    name = tool_data.name
    returncode = tool_data.returncode
    stdout = tool_data.stdout
    stderr = tool_data.stderr
    apply_fixes = tool_data.apply_fixes
    verbose = tool_data.verbose

    # Store detailed output for verbose reporting
    detailed_output = ""

    if verbose:
        detailed_output = f"\n{'=' * 60}\n"
        detailed_output += f"TOOL: {name}\n"
        detailed_output += f"RETURN CODE: {returncode}\n"
        detailed_output += f"{'=' * 60}\n"

        if stdout.strip():
            detailed_output += f"\nSTDOUT:\n{'-' * 40}\n{stdout}\n"

        if stderr.strip():
            detailed_output += f"\nSTDERR:\n{'-' * 40}\n{stderr}\n"

        detailed_output += f"\n{'=' * 60}\n"

    if returncode == -1:
        print(f"❌ {name}: {stderr}")
        return (name, "ERROR", 0, stderr, detailed_output)

    if returncode == 0:
        status_msg = "Applied fixes" if apply_fixes else "No issues found"
        print(f"✅ {name}: {status_msg}")
        return (name, "PASS", 0, status_msg, detailed_output)

    # Handle specific tool output formats
    if "Black" in name:
        return _process_black_result(tool_data)
    if "isort" in name:
        return _process_isort_result(tool_data)
    if "Bandit" in name:
        return _process_bandit_result(tool_data)

    return _process_generic_result(
        name=name,
        _returncode=returncode,
        stdout=stdout,
        _stderr=stderr,
        detailed_output=detailed_output,
    )


def _process_black_result(tool_data: ToolResult) -> tuple[str, str, int, str, str]:
    """Process Black-specific output."""
    name = tool_data.name
    returncode = tool_data.returncode
    stdout = tool_data.stdout
    stderr = tool_data.stderr
    apply_fixes = tool_data.apply_fixes
    detailed_output = ""

    if tool_data.verbose:
        detailed_output = f"\n{'=' * 60}\n"
        detailed_output += f"TOOL: {name}\n"
        detailed_output += f"RETURN CODE: {returncode}\n"
        detailed_output += f"{'=' * 60}\n"

        if stdout.strip():
            detailed_output += f"\nSTDOUT:\n{'-' * 40}\n{stdout}\n"

        if stderr.strip():
            detailed_output += f"\nSTDERR:\n{'-' * 40}\n{stderr}\n"

        detailed_output += f"\n{'=' * 60}\n"

    if "would reformat" in stderr:
        # Extract the summary line like "1 file would be reformatted"
        lines = stderr.strip().split("\n")
        for line in lines:
            if "would reformat" in line:
                # Extract number of files from the message
                words = line.split()
                if words and words[0].isdigit():
                    file_count = int(words[0])
                    action = "formatted" if apply_fixes else "need formatting"
                    print(f"⚠️ {name}: {file_count} file(s) {action}")
                    return (
                        name,
                        "ISSUES" if not apply_fixes else "FIXED",
                        file_count,
                        f"{file_count} file(s) {action}",
                        detailed_output,
                    )
        # Fallback if we can't parse the number
        action = "formatted" if apply_fixes else "need formatting"
        print(f"⚠️ {name}: Files {action}")
        return (
            name,
            "ISSUES" if not apply_fixes else "FIXED",
            1,
            f"Files {action}",
            detailed_output,
        )
    if returncode == 1:
        print(f"⚠️ {name}: Formatting issues found")
        return (name, "ISSUES", 1, "Formatting issues found", detailed_output)

    return _process_generic_result(
        name=name,
        _returncode=returncode,
        stdout=stdout,
        _stderr=stderr,
        detailed_output=detailed_output,
    )


def _process_isort_result(tool_data: ToolResult) -> tuple[str, str, int, str, str]:
    """Process isort-specific output."""
    name = tool_data.name
    returncode = tool_data.returncode
    stdout = tool_data.stdout
    stderr = tool_data.stderr
    apply_fixes = tool_data.apply_fixes
    detailed_output = ""

    if tool_data.verbose:
        detailed_output = f"\n{'=' * 60}\n"
        detailed_output += f"TOOL: {name}\n"
        detailed_output += f"RETURN CODE: {returncode}\n"
        detailed_output += f"{'=' * 60}\n"

        if stdout.strip():
            detailed_output += f"\nSTDOUT:\n{'-' * 40}\n{stdout}\n"

        if stderr.strip():
            detailed_output += f"\nSTDERR:\n{'-' * 40}\n{stderr}\n"

        detailed_output += f"\n{'=' * 60}\n"
    if "Fixing" in stdout or "would fix" in stdout:
        # Count import fixes
        lines = stdout.strip().split("\n")
        fix_lines = [line for line in lines if "Fixing" in line or "would fix" in line]
        fix_count = len(fix_lines)
        action = "fixed" if apply_fixes else "need fixing"
        print(f"⚠️ {name}: {fix_count} import(s) {action}")
        return (
            name,
            "ISSUES" if not apply_fixes else "FIXED",
            fix_count,
            f"{fix_count} import(s) {action}",
            detailed_output,
        )

    return _process_generic_result(
        name=name,
        _returncode=returncode,
        stdout=stdout,
        _stderr=stderr,
        detailed_output=detailed_output,
    )


def _process_bandit_result(tool_data: ToolResult) -> tuple[str, str, int, str, str]:
    """Process Bandit-specific output to correctly count security issues."""
    name = tool_data.name
    returncode = tool_data.returncode
    stdout = tool_data.stdout
    stderr = tool_data.stderr
    detailed_output = ""

    if tool_data.verbose:
        detailed_output = f"\n{'=' * 60}\n"
        detailed_output += f"TOOL: {name}\n"
        detailed_output += f"RETURN CODE: {returncode}\n"
        detailed_output += f"{'=' * 60}\n"

        if stdout.strip():
            detailed_output += f"\nSTDOUT:\n{'-' * 40}\n{stdout}\n"

        if stderr.strip():
            detailed_output += f"\nSTDERR:\n{'-' * 40}\n{stderr}\n"

        detailed_output += f"\n{'=' * 60}\n"

    # Count actual issues by looking for ">> Issue:" markers
    issue_count = stdout.count(">> Issue:") if stdout else 0

    if issue_count > 0:
        print(f"⚠️ {name}: {issue_count} issues found")
        return (name, "ISSUES", issue_count, f"{issue_count} issues", detailed_output)

    # No issues found
    print(f"✅ {name}: No issues found")
    return (name, "PASS", 0, "No issues found", detailed_output)


def _process_generic_result(
    name: str, _returncode: int, stdout: str, _stderr: str, detailed_output: str
) -> tuple[str, str, int, str, str]:
    """Process generic tool output."""
    issue_count = len(stdout.strip().split("\n")) if stdout.strip() else 0
    print(f"⚠️ {name}: {issue_count} issues found")
    return (name, "ISSUES", issue_count, f"{issue_count} issues", detailed_output)


def _categorize_results(
    results: list[tuple[str, str, int, str, str]],
) -> tuple[
    list[tuple[str, str, int, str, str]],
    list[tuple[str, str, int, str, str]],
    list[tuple[str, str, int, str, str]],
    list[tuple[str, str, int, str, str]],
]:
    """Categorize results by status."""
    passed = [r for r in results if r[1] == "PASS"]
    issues = [r for r in results if r[1] == "ISSUES"]
    fixed = [r for r in results if r[1] == "FIXED"]
    errors = [r for r in results if r[1] == "ERROR"]
    return passed, issues, fixed, errors


def _build_summary_header(stats: SummaryStats, apply_fixes: bool) -> list[str]:
    """Build the summary header section."""
    summary_text: list[str] = []
    summary_text.append("\n📊 Code Quality Analysis Summary")
    summary_text.append("=" * 50)

    summary_text.append(f"✅ Passed: {len(stats.passed)}")
    summary_text.append(
        f"⚠️ Issues found: {len(stats.issues)} (Total: {stats.total_issues})"
    )
    if apply_fixes:
        summary_text.append(f"🔧 Fixed: {len(stats.fixed)}")
    summary_text.append(f"❌ Errors: {len(stats.errors)}")
    return summary_text


def _build_detailed_results(
    results: list[tuple[str, str, int, str, str]], verbose: bool
) -> tuple[list[str], list[str]]:
    """Build detailed results and collect verbose output."""
    summary_text: list[str] = ["\n📋 Detailed Results:"]
    verbose_text: list[str] = []

    for name, status, _count, description, detailed_output in results:
        icon = {"PASS": "✅", "ERROR": "❌", "FIXED": "🔧"}.get(status, "⚠️")
        summary_text.append(f"  {icon} {name}: {description}")

        # Collect verbose output
        if verbose and detailed_output:
            verbose_text.append(detailed_output)

    return summary_text, verbose_text


def _build_summary_text(config: SummaryConfig) -> tuple[list[str], list[str]]:
    """Build summary and verbose text."""
    # Build header
    summary_text = _build_summary_header(config.stats, config.apply_fixes)

    # Build detailed results and collect verbose output
    detailed_results, verbose_text = _build_detailed_results(
        config.results, config.verbose
    )
    summary_text.extend(detailed_results)

    # Add suggestions
    _add_suggestions_to_summary(
        summary_text,
        config.stats.total_issues,
        len(config.stats.errors),
        config.apply_fixes,
        len(config.stats.fixed),
    )
    return summary_text, verbose_text


def _add_suggestions_to_summary(
    summary_text: list[str],
    total_issues: int,
    error_count: int,
    apply_fixes: bool,
    fixed_count: int,
) -> None:
    """Add suggestions section to summary."""
    if total_issues == 0 and error_count == 0:
        summary_text.append("\n🎉 All code quality checks passed!")
    elif apply_fixes and fixed_count > 0:
        summary_text.append("\n🔧 Applied fixes. Re-run without --fix to verify.")
    else:
        summary_text.append("\n💡 Suggestions:")
        summary_text.append("  • Run with --fix to apply automatic fixes")
        summary_text.append("  • Use --tools to focus on specific tools")
        summary_text.append("  • Use --categories to run tool groups")
        summary_text.append("\n🔧 Manual tool execution examples:")
        summary_text.append("    .venv/bin/python -m mypy src/")
        summary_text.append("    .venv/bin/python -m ruff check src/ tests/")
        summary_text.append("    .venv/bin/python -m pylint src/")
        summary_text.append("    .venv/bin/python -m bandit -r src/")


def _handle_verbose_output(
    verbose_text: list[str], output_file: str | None, summary_text: list[str]
) -> None:
    """Handle verbose output to file or console."""
    verbose_content = (
        [
            "\n" + "=" * 80,
            "VERBOSE OUTPUT - DETAILED TOOL RESULTS",
            "=" * 80,
            "This section contains the complete output from tools with issues.",
            "Use this information for detailed remediation and analysis.",
            "=" * 80,
        ]
        + verbose_text
        + [
            "\n" + "=" * 80,
            "END VERBOSE OUTPUT",
            "=" * 80,
        ]
    )

    if output_file:
        # Write verbose output to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(summary_text + verbose_content))
            print(f"\n📄 Detailed report written to: {output_file}")
        except OSError as e:
            print(f"\n❌ Error writing to file {output_file}: {e}")
            print("\n📋 Verbose output:")
            for line in verbose_content:
                print(line)
    else:
        # Print verbose output to console
        for line in verbose_content:
            print(line)


def print_enhanced_summary(
    results: list[tuple[str, str, int, str, str]],
    total_issues: int,
    apply_fixes: bool,
    verbose: bool = False,
    output_file: str | None = None,
) -> None:
    """Print an enhanced summary of code quality results."""
    passed, issues, fixed, errors = _categorize_results(results)

    stats = SummaryStats(
        passed=passed,
        issues=issues,
        fixed=fixed,
        errors=errors,
        total_issues=total_issues,
    )

    config = SummaryConfig(
        stats=stats,
        apply_fixes=apply_fixes,
        results=results,
        verbose=verbose,
    )
    summary_text, verbose_text = _build_summary_text(config)

    # Print summary to console
    for line in summary_text:
        print(line)

    # Handle verbose output
    if verbose and verbose_text:
        _handle_verbose_output(verbose_text, output_file, summary_text)


def show_available_options() -> None:
    """Show all available tools, categories, and profiles."""
    print("🛠️ Available Tools by Category:")
    print("=" * 50)

    for category_name, category_tools in ALL_CATEGORIES.items():
        print(f"\n📁 {category_name.upper()}:")
        for tool_name, tool_info in category_tools.items():
            fix_support = "✅" if tool_info["supports_fix"] else "❌"
            print(
                f"  • {tool_name:12} - {tool_info['description']} (Fix: {fix_support})"
            )

    print("\n🏷️ Available Profiles:")
    print("=" * 30)
    for profile_name, profile_info in PROFILES.items():
        print(f"  • {profile_name:12} - {profile_info['description']}")

    print("\n�� Available Categories:")
    print("=" * 30)
    for category_name in ALL_CATEGORIES:
        print(f"  • {category_name}")


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Python Code Quality Analysis Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run all tools on default targets
  %(prog)s --profile development              # Use development profile
  %(prog)s --categories formatters linters    # Run specific categories
  %(prog)s --tools black mypy                 # Run specific tools
  %(prog)s --fix                              # Apply automatic fixes
  %(prog)s src/specific_file.py               # Target specific files
  %(prog)s --show-tools                       # List all available options

Profiles:
  development   - Quick checks (formatters + ruff)
  ci            - Comprehensive CI/CD checks
  pre-commit    - Fast pre-commit hooks
  security      - Security-focused analysis
  typing        - Type checking focus
        """,
    )

    # Positional arguments
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files or directories to analyze "
        "(default: src/, tests/, scripts/, setup.py)",
    )

    # Tool selection options
    parser.add_argument(
        "--tools",
        nargs="+",
        choices=list(get_all_tools().keys()),
        help="Specific tools to run (default: all tools)",
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        choices=list(ALL_CATEGORIES.keys()),
        help="Tool categories to run (default: all categories)",
    )

    parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()),
        help="Predefined configuration profile",
    )

    # Execution options
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply automatic fixes where possible",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output from each tool for remediation",
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="Write detailed report to file (requires --verbose)",
    )

    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Show all available tools, categories, and profiles",
    )

    return parser


def _determine_tools_to_run(args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    """Determine which tools to run based on command line arguments."""
    if args.profile:
        # Use profile configuration
        profile = PROFILES[args.profile]
        if profile["tools"]:
            # Profile specifies specific tools
            all_tools = get_all_tools()
            return {tool: all_tools[tool] for tool in profile["tools"]}
        # Profile specifies categories
        return get_tools_by_categories(list(profile["categories"]))
    if args.categories:
        # Use specified categories
        return get_tools_by_categories(args.categories)
    if args.tools:
        # Use specified tools
        all_tools = get_all_tools()
        return {tool: all_tools[tool] for tool in args.tools}
    # Use all tools
    return get_all_tools()


def _validate_targets_and_environment(
    targets: list[str], args: argparse.Namespace
) -> None:
    """Validate analysis targets and environment setup."""
    # Validate that target files/directories exist
    for target in targets:
        if not Path(target).exists():
            print(f"❌ Target not found: {target}")
            sys.exit(1)

    # Check for source directories if using defaults
    if not args.files:
        src_path = Path("src")
        if not src_path.exists():
            print("❌ Source directory 'src' not found")
            sys.exit(1)


def _print_execution_summary(targets: list[str], args: argparse.Namespace) -> None:
    """Print summary of what will be executed."""
    mode = "fix mode" if args.fix else "check mode"
    print(f"🚀 Running code quality analysis in {mode}...")
    print(f"🔍 Analysis targets: {', '.join(targets)}")
    if args.profile:
        print(f"📋 Using profile: {args.profile}")
    if args.categories:
        print(f"📁 Using categories: {', '.join(args.categories)}")
    if args.tools:
        print(f"🔧 Using tools: {', '.join(args.tools)}")
    print("=" * 60)


def _prepare_tool_command(
    tool_name: str, tool_config: dict[str, Any], targets: list[str], fix_mode: bool
) -> tuple[list[str], str]:
    """Prepare the command and description for a tool."""
    if fix_mode and tool_config["supports_fix"]:
        cmd = tool_config["cmd_fix"] + targets
        description = f"{tool_name.title()} (applying fixes)"
    else:
        cmd = tool_config["cmd_check"] + targets
        description = f"{tool_name.title()} (checking)"

    # Skip targets for tools that don't need them
    if tool_name in ["pip-audit", "safety"]:
        cmd = tool_config["cmd_check"] if not fix_mode else tool_config["cmd_fix"]

    return cmd, description


def _run_quality_tools(
    tools_to_run: dict[str, dict[str, Any]],
    targets: list[str],
    args: argparse.Namespace,
) -> tuple[int, list[tuple[str, str, int, str, str]]]:
    """Run all configured quality tools and collect results."""
    total_issues = 0
    results: list[tuple[str, str, int, str, str]] = []

    for tool_name, tool_config in tools_to_run.items():
        cmd, description = _prepare_tool_command(
            tool_name, tool_config, targets, args.fix
        )

        returncode, stdout, stderr = run_command(cmd, description, tool_config)
        tool_data = ToolResult(
            name=tool_name.title(),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            apply_fixes=args.fix,
            verbose=args.verbose,
        )
        result = process_tool_result(tool_data)
        results.append(result)

        if result[1] in ["ISSUES", "FIXED"]:
            total_issues += result[2]

        print("-" * 40)

    return total_issues, results


def main() -> None:
    """Run comprehensive code quality analysis."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    # Show available options and exit
    if args.show_tools:
        show_available_options()
        return

    # Determine which tools to run
    tools_to_run = _determine_tools_to_run(args)

    # Get analysis targets
    targets = get_quality_targets(args.files if args.files else None)

    # Validate environment and targets
    _validate_targets_and_environment(targets, args)

    # Print execution summary
    _print_execution_summary(targets, args)

    # Run tools and collect results
    total_issues, results = _run_quality_tools(tools_to_run, targets, args)

    # Validate output file argument
    if args.output_file and not args.verbose:
        print("❌ --output-file requires --verbose flag")
        sys.exit(1)

    # Print enhanced summary
    print_enhanced_summary(
        results, total_issues, args.fix, args.verbose, args.output_file
    )


if __name__ == "__main__":
    main()
