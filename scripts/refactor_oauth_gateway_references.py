#!/usr/bin/env python3
"""
🔄 CLOUDFLARE SECURITY GATEWAY TO CLOUDFLARE SECURITY GATEWAY REFACTORING SCRIPT

Comprehensive script to update all references from 'cloudflare_security_gateway' to
'cloudflare_security_gateway' across the entire codebase.

This script systematically updates:
- File references in Python imports and strings
- Documentation references in Markdown files
- Configuration references in JSON/TOML files
- Infrastructure deployment references
- Directory and file names that need updating

Usage:
    # Preview changes
    python scripts/refactor_cloudflare_security_gateway_references.py --dry-run
    # Apply changes
    python scripts/refactor_cloudflare_security_gateway_references.py --execute
"""

import argparse
from pathlib import Path


class CloudFlareSecurityGatewayRefactorer:
    """Comprehensive refactoring utility for CloudFlare Security Gateway references."""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.changes_made: list[tuple[str, str, str]] = []  # (file, old, new)
        self.files_renamed: list[tuple[str, str]] = []  # (old_path, new_path)

        # Define replacement mappings (OLD → NEW)
        self.string_replacements = {
            # Python variable and function references
            "cloudflare_security_gateway": "cloudflare_security_gateway",
            "CloudFlareSecurityGateway": "CloudFlareSecurityGateway",
            "CLOUDFLARE_SECURITY_GATEWAY": "CLOUDFLARE_SECURITY_GATEWAY",
            # AWS function names and descriptions
            "CloudFlare-Security-Gateway": "CloudFlare-Security-Gateway",
            "CloudFlare Security Gateway": "CloudFlare Security Gateway",
            "cloudflare security gateway": "cloudflare security gateway",
            # File and directory references
            "cloudflare_security_gateway.py": "cloudflare_security_gateway.py",
            "cloudflare-security-gateway": "cloudflare-security-gateway",
            "cloudflare_security_gateway_config": "cloudflare_security_gateway_config",
            # Documentation references
            "cloudflare_cloudflare_security_gateway.py": "cloudflare_security_gateway.py",
            "CLOUDFLARE SECURITY GATEWAY": "CLOUDFLARE SECURITY GATEWAY",
            # SSM and cache key references
            "cloudflare-security-gateway-arn": "cloudflare-security-gateway-arn",
            "SSM_CLOUDFLARE_SECURITY_GATEWAY_ARN": "SSM_CLOUDFLARE_SECURITY_GATEWAY_ARN",
        }

        # Directories that might need renaming (OLD → NEW)
        self.directory_renames = {
            "infrastructure/deployment/cloudflare_security_gateway": "infrastructure/deployment/cloudflare_security_gateway"
        }

    def scan_files_to_update(self) -> list[Path]:
        """Scan workspace for files that need updates."""
        files_to_check = []

        # File patterns to check
        patterns = [
            "**/*.py",
            "**/*.md",
            "**/*.json",
            "**/*.toml",
            "**/*.yml",
            "**/*.yaml",
            "**/*.txt",
            "**/*.sh",
        ]

        for pattern in patterns:
            files_to_check.extend(self.workspace_root.glob(pattern))

        # Filter out files that likely don't need changes
        exclude_patterns = [
            ".git/",
            "__pycache__/",
            ".venv/",
            "node_modules/",
            ".vscode/",
            "htmlcov/",
        ]

        filtered_files = []
        for file_path in files_to_check:
            if any(exclude in str(file_path) for exclude in exclude_patterns):
                continue
            if file_path.is_file():
                filtered_files.append(file_path)

        return filtered_files

    def scan_file_for_references(self, file_path: Path) -> list[tuple[str, str]]:
        """Scan a single file for cloudflare_security_gateway references."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or files we can't read
            return []

        replacements = []
        for old_text, new_text in self.string_replacements.items():
            if old_text in content:
                replacements.append((old_text, new_text))

        return replacements

    def update_file_content(self, file_path: Path, dry_run: bool = True) -> bool:
        """Update cloudflare_security_gateway references in a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
        except (UnicodeDecodeError, PermissionError):
            return False

        # Apply all string replacements
        for old_text, new_text in self.string_replacements.items():
            if old_text in content:
                content = content.replace(old_text, new_text)
                self.changes_made.append((str(file_path), old_text, new_text))

        # Write back if content changed and not dry run
        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
            return True

        return False

    def rename_directories(self, dry_run: bool = True) -> None:
        """Rename directories that contain cloudflare_security_gateway references."""
        for old_dir_rel, new_dir_rel in self.directory_renames.items():
            old_dir = self.workspace_root / old_dir_rel
            new_dir = self.workspace_root / new_dir_rel

            if old_dir.exists() and old_dir.is_dir():
                if not dry_run:
                    if new_dir.exists():
                        print(f"⚠️  Target directory exists: {new_dir}")
                        continue
                    old_dir.rename(new_dir)

                self.files_renamed.append((str(old_dir), str(new_dir)))
                print(
                    f"📁 {'Would rename' if dry_run else 'Renamed'}: {old_dir_rel} → {new_dir_rel}"
                )

    def generate_report(
        self, files_scanned: list[Path], files_with_changes: list[Path]
    ) -> str:
        """Generate a comprehensive report of changes."""
        report = []
        report.append("🔄 CLOUDFLARE SECURITY GATEWAY REFACTORING REPORT")
        report.append("=" * 50)
        report.append(f"📊 Files scanned: {len(files_scanned)}")
        report.append(f"📝 Files with changes: {len(files_with_changes)}")
        report.append(f"🔄 String replacements made: {len(self.changes_made)}")
        report.append(f"📁 Directories renamed: {len(self.files_renamed)}")
        report.append("")

        # Group changes by file
        if self.changes_made:
            report.append("📝 DETAILED CHANGES BY FILE:")
            report.append("-" * 30)

            changes_by_file = {}
            for file_path, old_text, new_text in self.changes_made:
                if file_path not in changes_by_file:
                    changes_by_file[file_path] = []
                changes_by_file[file_path].append((old_text, new_text))

            for file_path, changes in changes_by_file.items():
                report.append(f"\n📄 {file_path}")
                for old_text, new_text in changes:
                    report.append(f"   '{old_text}' → '{new_text}'")

        # Directory renames
        if self.files_renamed:
            report.append("\n📁 DIRECTORY RENAMES:")
            report.append("-" * 20)
            for old_path, new_path in self.files_renamed:
                report.append(f"   {old_path} → {new_path}")

        return "\n".join(report)

    def refactor_all_references(self, dry_run: bool = True) -> str:
        """Main refactoring function."""
        print(f"🔍 Scanning workspace: {self.workspace_root}")

        # 1. Scan all files
        files_to_check = self.scan_files_to_update()
        print(f"📋 Found {len(files_to_check)} files to check")

        # 2. Rename directories first
        print("\n📁 Checking directories...")
        self.rename_directories(dry_run)

        # 3. Update file contents
        print(f"\n📝 {'Analyzing' if dry_run else 'Updating'} file contents...")
        files_with_changes = []

        for file_path in files_to_check:
            # Check if file has cloudflare_security_gateway references
            references = self.scan_file_for_references(file_path)
            if references:
                files_with_changes.append(file_path)

                if dry_run:
                    print(f"   📄 {file_path.relative_to(self.workspace_root)}")
                    for old_text, new_text in references:
                        print(f"      '{old_text}' → '{new_text}'")
                else:
                    updated = self.update_file_content(file_path, dry_run=False)
                    if updated:
                        print(
                            f"   ✅ Updated: {file_path.relative_to(self.workspace_root)}"
                        )

        # 4. Generate report
        report = self.generate_report(files_to_check, files_with_changes)

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Refactor CloudFlare Security Gateway references"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )
    parser.add_argument(
        "--execute", action="store_true", help="Apply all changes (no preview)"
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory)",
    )

    args = parser.parse_args()

    if not (args.dry_run or args.execute):
        print("❌ Must specify either --dry-run or --execute")
        parser.print_help()
        return 1

    workspace_root = Path(args.workspace).resolve()
    if not workspace_root.exists():
        print(f"❌ Workspace not found: {workspace_root}")
        return 1

    refactorer = CloudFlareSecurityGatewayRefactorer(str(workspace_root))

    try:
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be applied")
            print("=" * 50)
        else:
            print("⚡ EXECUTE MODE - Changes will be applied")
            print("=" * 50)

        report = refactorer.refactor_all_references(dry_run=args.dry_run)

        print("\n" + report)

        if args.dry_run:
            print("\n💡 To apply these changes, run with --execute")
        else:
            print("\n✅ Refactoring complete!")

        return 0

    except Exception as e:
        print(f"❌ Error during refactoring: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
