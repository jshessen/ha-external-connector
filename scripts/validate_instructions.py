#!/usr/bin/env python3
"""
Instruction validation script for GitHub Copilot instructions.

This script validates the consistency and integrity of all instruction files
to prevent conflicts and ensure proper hierarchy.
"""

import argparse
import re
import sys
from pathlib import Path


def find_transfer_block_references(content: str) -> list[str]:
    """Find all transfer block references in content."""
    patterns = [
        r"transfer block",
        r"TRANSFER BLOCK",
        r"Transfer Block",
        r"╭─.*TRANSFER.*─╮",
        r"╰─.*TRANSFER.*─╯",
    ]

    references: list[str] = []
    for pattern in patterns:
        matches: list[str] = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        references.extend(matches)

    return references


def validate_transfer_block_consolidation() -> tuple[bool, list[str]]:
    """Validate that transfer blocks are properly consolidated."""
    project_root = Path(__file__).parent.parent
    instructions_path = project_root / ".github" / "instructions"

    lambda_patterns_path = instructions_path / "specialized" / "lambda-patterns.md"
    aws_patterns_path = instructions_path / "specialized" / "aws-patterns.md"

    issues: list[str] = []

    if not lambda_patterns_path.exists():
        issues.append("❌ specialized/lambda-patterns.md not found")
        return False, issues

    if not aws_patterns_path.exists():
        issues.append("❌ specialized/aws-patterns.md not found")
        return False, issues

    lambda_content = lambda_patterns_path.read_text()
    aws_content = aws_patterns_path.read_text()

    # Check lambda-patterns.md has comprehensive transfer block content
    has_transfer_markers = "TRANSFER BLOCK START" in lambda_content
    has_sync_workflow = "Transfer Block Synchronization Workflow" in lambda_content

    if not has_transfer_markers:
        issues.append("❌ lambda-patterns.md missing transfer block markers")

    if not has_sync_workflow:
        issues.append("❌ lambda-patterns.md missing synchronization workflow")

    # Check aws-patterns.md only has references, not full content
    aws_transfer_refs = find_transfer_block_references(aws_content)
    has_reference_to_lambda = "lambda-patterns.md" in aws_content
    has_detailed_transfer_content = (
        len([ref for ref in aws_transfer_refs if "START" in ref or "END" in ref]) > 0
    )

    if not has_reference_to_lambda:
        issues.append("❌ aws-patterns.md missing reference to lambda-patterns.md")

    if has_detailed_transfer_content:
        issues.append(
            "⚠️  aws-patterns.md contains detailed transfer block content "
            "(should only reference)"
        )

    # Summary
    if not issues:
        issues.append("✅ Transfer block consolidation properly implemented")

    return len([i for i in issues if i.startswith("❌")]) == 0, issues


def validate_instruction_hierarchy() -> tuple[bool, list[str]]:
    """Validate instruction hierarchy is properly structured."""
    issues: list[str] = []
    project_root = Path(__file__).parent.parent
    instructions_path = project_root / ".github" / "instructions"

    expected_structure = {
        "core": ["environment-setup.md", "quality-standards.md", "agent-refresh.md"],
        "specialized": [
            "aws-patterns.md",
            "lambda-patterns.md",
            "testing-patterns.md",
            "security-patterns.md",
        ],
        "documentation": ["markdown-standards.md", "docs-organization.md"],
    }

    if not instructions_path.exists():
        issues.append("❌ Instructions directory not found")
        return False, issues

    # Check README.md exists
    readme_path = instructions_path / "README.md"
    if not readme_path.exists():
        issues.append("❌ Instructions README.md not found")
    else:
        readme_content = readme_path.read_text()
        if "Conflict Resolution Hierarchy" not in readme_content:
            issues.append("❌ README.md missing conflict resolution hierarchy")
        else:
            issues.append("✅ Instructions README.md properly structured")

    # Check directory structure
    for category, files in expected_structure.items():
        category_path = instructions_path / category
        if not category_path.exists():
            issues.append(f"❌ Missing directory: {category}")
            continue

        for file in files:
            file_path = category_path / file
            if file_path.exists():
                issues.append(f"✅ {category}/{file}")
            else:
                issues.append(f"❌ Missing: {category}/{file}")

    error_count = len([i for i in issues if i.startswith("❌")])
    return error_count == 0, issues


def validate_cross_references() -> tuple[bool, list[str]]:
    """Validate cross-references between instruction files."""
    project_root = Path(__file__).parent.parent
    instructions_path = project_root / ".github" / "instructions"

    issues: list[str] = []

    # Find all markdown files
    md_files = list(instructions_path.rglob("*.md"))

    # Extract all internal links
    internal_links: dict[Path, list[str]] = {}
    for md_file in md_files:
        content = md_file.read_text()
        # Find markdown links [text](path)
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        internal_links[md_file] = [
            link[1] for link in links if not link[1].startswith("http")
        ]

    # Validate each link
    for file_path, links in internal_links.items():
        for link in links:
            if link.startswith("./") or link.startswith("../"):
                # Resolve relative path
                target_path = (file_path.parent / link).resolve()
                if not target_path.exists():
                    issues.append(f"❌ Broken link in {file_path.name}: {link}")
                else:
                    issues.append(f"✅ Valid link in {file_path.name}: {link}")

    if not issues:
        issues.append("✅ No cross-references to validate")

    error_count = len([i for i in issues if i.startswith("❌")])
    return error_count == 0, issues


def validate_pattern_matching() -> tuple[bool, list[str]]:
    """Validate file pattern matching consistency."""
    project_root = Path(__file__).parent.parent
    instructions_path = project_root / ".github" / "instructions"

    issues: list[str] = []

    # Expected pattern mappings
    expected_patterns = {
        "specialized/testing-patterns.md": ["**/test_*.py", "**/tests/**/*.py"],
        "specialized/aws-patterns.md": ["**/aws_*.py", "**/adapters/**/*.py"],
        "specialized/lambda-patterns.md": ["**/lambda_functions/**/*.py"],
        "specialized/security-patterns.md": ["**/security/**/*.py", "**/*security*.py"],
        "documentation/markdown-standards.md": ["**/*.md"],
        "documentation/docs-organization.md": ["**/docs/**/*"],
    }

    # Check README.md contains pattern mappings
    readme_path = instructions_path / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()

        for _file_pattern, patterns in expected_patterns.items():
            for pattern in patterns:
                if pattern in readme_content:
                    issues.append(f"✅ Pattern {pattern} documented in README")
                else:
                    issues.append(f"❌ Pattern {pattern} missing from README")
    else:
        issues.append("❌ README.md not found for pattern validation")

    error_count = len([i for i in issues if i.startswith("❌")])
    return error_count == 0, issues


def validate_master_instructions() -> tuple[bool, list[str]]:
    """Validate master copilot-instructions.md file."""
    project_root = Path(__file__).parent.parent
    master_instructions_path = project_root / ".github" / "copilot-instructions.md"

    issues: list[str] = []

    if not master_instructions_path.exists():
        issues.append("❌ Master copilot-instructions.md not found")
        return False, issues

    content = master_instructions_path.read_text()

    # Check for key sections
    required_sections = [
        "Environment Activation",
        "Terminal Automation",
        "Quality Standards",
        "Agent Helper",
    ]

    for section in required_sections:
        if section in content:
            issues.append(f"✅ Master instructions contain {section}")
        else:
            issues.append(f"❌ Master instructions missing {section}")

    # Check if it references the instruction hierarchy
    if "instructions/" in content:
        issues.append("✅ Master instructions reference instruction hierarchy")
    else:
        issues.append("❌ Master instructions should reference instruction hierarchy")

    error_count = len([i for i in issues if i.startswith("❌")])
    return error_count == 0, issues


def main() -> int:
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate GitHub Copilot instruction consistency"
    )
    parser.add_argument(
        "--section",
        choices=[
            "transfer-blocks",
            "hierarchy",
            "cross-refs",
            "patterns",
            "master",
            "all",
        ],
        default="all",
        help="Section to validate",
    )

    args = parser.parse_args()

    print("🔍 GitHub Copilot Instruction Validation")
    print("=" * 50)

    validators = {
        "transfer-blocks": validate_transfer_block_consolidation,
        "hierarchy": validate_instruction_hierarchy,
        "cross-refs": validate_cross_references,
        "patterns": validate_pattern_matching,
        "master": validate_master_instructions,
    }

    if args.section == "all":
        sections_to_validate = validators.keys()
    else:
        sections_to_validate = [args.section]

    all_passed = True
    total_issues: list[str] = []

    for section in sections_to_validate:
        print(f"\n🔍 Validating {section.replace('-', ' ').title()}:")
        print("-" * 30)

        validator = validators[section]
        passed, issues = validator()

        for issue in issues:
            print(f"  {issue}")

        if not passed:
            all_passed = False

        total_issues.extend(issues)

    # Summary
    print("\n" + "=" * 50)
    error_count = len([i for i in total_issues if i.startswith("❌")])
    warning_count = len([i for i in total_issues if i.startswith("⚠️")])
    success_count = len([i for i in total_issues if i.startswith("✅")])

    print("📊 Validation Summary:")
    print(f"  ✅ Passed: {success_count}")
    print(f"  ⚠️  Warnings: {warning_count}")
    print(f"  ❌ Errors: {error_count}")

    if all_passed:
        print("\n🎉 All instruction validations passed!")
        return 0

    print(f"\n⚠️  Validation failed with {error_count} errors")
    return 1


if __name__ == "__main__":
    sys.exit(main())
