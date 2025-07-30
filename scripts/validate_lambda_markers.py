#!/usr/bin/env python3
"""
🔄 Lambda Deployment Marker System Validation Script

This script validates that all Lambda function files have properly implemented
the standardized marker system for automated deployment file generation.

Key Features:
- Validates presence of required deployment markers
- Checks visual consistency of marker formatting
- Identifies shared configuration imports
- Demonstrates content extraction capabilities
- Provides comprehensive validation reporting

Usage:
    python scripts/validate_lambda_markers.py
"""

import re
from pathlib import Path


def validate_lambda_markers(file_path: Path) -> tuple[bool, list[str]]:
    """
    Validate that a file has proper deployment markers.

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        issues.append(f"Failed to read file: {e}")
        return False, issues

    # Required markers for Lambda function files
    required_markers = [
        "IMPORT_BLOCK_START",
        "IMPORT_BLOCK_END",
        "FUNCTION_BLOCK_START",
        "FUNCTION_BLOCK_END",
    ]

    # Check for required markers
    for marker in required_markers:
        if marker not in content:
            issues.append(f"Missing required marker: {marker}")

    # Check marker count (should have exactly one of each)
    start_markers = content.count("IMPORT_BLOCK_START")
    end_markers = content.count("IMPORT_BLOCK_END")

    if start_markers != 1:
        issues.append(f"Expected 1 IMPORT_BLOCK_START, found {start_markers}")
    if end_markers != 1:
        issues.append(f"Expected 1 IMPORT_BLOCK_END, found {end_markers}")

    # Check function block markers
    func_start = content.count("FUNCTION_BLOCK_START")
    func_end = content.count("FUNCTION_BLOCK_END")

    if func_start != 1:
        issues.append(f"Expected 1 FUNCTION_BLOCK_START, found {func_start}")
    if func_end != 1:
        issues.append(f"Expected 1 FUNCTION_BLOCK_END, found {func_end}")

    # Check visual consistency (markers should use proper bracket style)
    if "IMPORT_BLOCK_START" in content:
        start_line = next(
            (line for line in content.split("\n") if "IMPORT_BLOCK_START" in line), ""
        )
        if not start_line.startswith("# ╭") or not start_line.endswith("╮"):
            issues.append(
                "IMPORT_BLOCK_START marker doesn't use proper visual brackets"
            )

    if "IMPORT_BLOCK_END" in content:
        end_line = next(
            (line for line in content.split("\n") if "IMPORT_BLOCK_END" in line), ""
        )
        if not end_line.startswith("# ╰") or not end_line.endswith("╯"):
            issues.append("IMPORT_BLOCK_END marker doesn't use proper visual brackets")

    # Check shared configuration import identification
    # (except for shared_configuration.py itself)
    if (
        file_path.name != "shared_configuration.py"
        and "from .shared_configuration import" in content
    ):
        # Look for the shared config import marker
        shared_import_pattern = r"# === SHARED CONFIGURATION IMPORTS ==="
        if not re.search(shared_import_pattern, content):
            issues.append("Missing shared configuration import identification comment")

    return len(issues) == 0, issues


def extract_marked_content(file_path: Path) -> dict[str, str]:
    """
    Extract content using deployment markers.

    This demonstrates how the deployment script extracts content.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return {}

    lines = content.split("\n")
    result = {}

    # Extract import block
    in_import_block = False
    import_lines = []

    for line in lines:
        if "IMPORT_BLOCK_START" in line:
            in_import_block = True
            continue
        elif "IMPORT_BLOCK_END" in line:
            in_import_block = False
            continue
        elif in_import_block:
            import_lines.append(line)

    result["imports"] = "\n".join(import_lines)

    # Extract function block
    in_function_block = False
    function_lines = []

    for line in lines:
        if "FUNCTION_BLOCK_START" in line:
            in_function_block = True
            continue
        elif "FUNCTION_BLOCK_END" in line:
            in_function_block = False
            continue
        elif in_function_block:
            function_lines.append(line)

    result["functions"] = "\n".join(function_lines)

    return result


def main() -> bool:
    """
    Main validation function that checks all Lambda function files.

    Returns:
        True if all validations pass, False otherwise
    """
    print("🔍 Validating Lambda Deployment Marker System\n")

    # Define Lambda function files to validate
    lambda_files = [
        "src/ha_connector/integrations/alexa/lambda_functions/oauth_gateway.py",
        "src/ha_connector/integrations/alexa/lambda_functions/smart_home_bridge.py",
        "src/ha_connector/integrations/alexa/lambda_functions/configuration_manager.py",
        "src/ha_connector/integrations/alexa/lambda_functions/shared_configuration.py",
    ]

    all_valid = True
    workspace_root = Path.cwd()

    for file_path_str in lambda_files:
        file_path = workspace_root / file_path_str

        if not file_path.exists():
            print(f"❌ File not found: {file_path_str}")
            all_valid = False
            continue

        print(f"📁 Validating: {file_path.name}")
        is_valid, issues = validate_lambda_markers(file_path)

        if is_valid:
            print("   ✅ All markers present and properly formatted")

            # Demonstrate content extraction
            extracted = extract_marked_content(file_path)
            if extracted.get("imports"):
                import_line_count = len(
                    [l for l in extracted["imports"].split("\n") if l.strip()]
                )
                print(f"   📦 Import block: {import_line_count} lines")

            if extracted.get("functions"):
                func_line_count = len(
                    [l for l in extracted["functions"].split("\n") if l.strip()]
                )
                print(f"   🔧 Function block: {func_line_count} lines")

                # Show first few lines as example
                func_lines = [
                    l for l in extracted["functions"].split("\n") if l.strip()
                ]
                if func_lines:
                    print("   📋 Function preview:")
                    for i, line in enumerate(func_lines[:3]):
                        print(f"     {line[:60]}{'...' if len(line) > 60 else ''}")
                    if len(func_lines) > 3:
                        line_count = len(func_lines)
                        print(f"     ... ({line_count - 3} more lines)")

        else:
            print("   ❌ Validation failed:")
            for issue in issues:
                print(f"      • {issue}")
            all_valid = False

        print()  # Empty line for readability

    if all_valid:
        print(
            "🚀 Deployment system is ready for automated Lambda " "package generation!"
        )
        return True
    else:
        print("❌ Please fix marker issues before proceeding with deployment.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
