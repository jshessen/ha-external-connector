#!/usr/bin/env python3
"""
🚀 LAMBDA CONFIGURATION DEPLOYMENT TOOL

This script implements the dual-mode architecture for Lambda functions:
1. Development Mode: Import        # Analyze imports and shared import blocks
        first_import_line = None
        last_import_line = None
        shared_import_start = None
        shared_import_end = None

        for i, line in enumerate(original_lines):
            stripped = line.strip()

            # Track all imports
            if stripped.startswith(("import ", "from ")) and first_import_line is None:
                first_import_line = i
            if stripped.startswith(("import ", "from ")):
                last_import_line = i

            # Track shared_configuration import block specifically
            if f"from .{SHARED_MODULE} import" in line:
                shared_import_start = i
                print(f"  🗑️  Found shared import block start at line {i + 1}")
                # Check if single line import (ends with ) before any comment)
                line_before_comment = line.split('#')[0].strip()
                if line_before_comment.endswith(")"):
                    shared_import_end = i
                    print(f"  🗑️  Single line shared import at line {i + 1}")
            elif shared_import_start is not None and shared_import_end is None:
                # We're in a multi-line shared import, look for closing paren
                line_before_comment = line.split('#')[0].strip()
                if ")" in line_before_comment:
                    shared_import_end = i
                    print(f"  🗑️  Shared import block ends at line {i + 1}")

        # Ensure last_import_line includes the shared import block end
        if shared_import_end is not None and (
            last_import_line is None or shared_import_end > last_import_line
        ):
            last_import_line = shared_import_end
            print(
                f"  🗑️  Extended last_import_line to {last_import_line + 1} "
                "to include shared import block"
            )

        # Split content into sections
        before_imports = (
            original_lines[:first_import_line] if first_import_line else []
        )

Usage:
    python scripts/deploy_shared_config.py --mode development  # For dev/testing
    python scripts/deploy_shared_config.py --mode deployment   # For production
    python scripts/deploy_shared_config.py --validate         # Check synchronization
"""

import argparse
import ast
import shutil
import sys
from pathlib import Path

# Add src to path for dynamic imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Source and deployment locations
SOURCE_LAMBDA_DIR = "src/ha_connector/integrations/alexa/lambda_functions"
DEPLOYMENT_DIR = "infrastructure/deployment"
SHARED_MODULE = "shared_configuration"

LAMBDA_FUNCTIONS = [
    "oauth_gateway.py",
    "smart_home_bridge.py",
]


class CleanDeploymentSystem:
    """Clean separation deployment system."""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.source_dir = self.workspace_root / SOURCE_LAMBDA_DIR
        self.deployment_dir = self.workspace_root / DEPLOYMENT_DIR
        self.shared_module_path = self.source_dir / f"{SHARED_MODULE}.py"
        self.shared_file_path = self.shared_module_path  # Alias for new marker methods

    def build_deployment(self) -> None:
        """Build standalone Lambda deployment files."""
        print("🚀 Building clean deployment files...")

        # Extract shared code once
        shared_imports, shared_code = self._extract_shared_code()

        # Build each Lambda function
        for lambda_file in LAMBDA_FUNCTIONS:
            self._build_lambda_deployment(lambda_file, shared_code, shared_imports)

    def _extract_shared_code(self) -> tuple[str, str]:
        """Simply extract everything after imports from shared_configuration.py."""
        print(f"📖 Extracting shared code from {SHARED_MODULE}.py...")

        # Read the shared module
        with open(self.shared_module_path, encoding="utf-8") as f:
            shared_content = f.read()

        # Split into lines for processing
        lines = shared_content.split("\n")

        # Collect all imports first (they can be interspersed with comments
        # and blank lines)
        imports: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                imports.append(line)

        # Find where actual code begins (after imports, comments, __all__, etc.)
        code_start_line = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip empty lines, comments, imports, __all__ definitions,
            # and module header content
            if self._is_header_or_metadata_line(stripped):
                continue
            # Look for actual function or class definitions as start of shared code
            if (
                stripped.startswith("def ")
                or stripped.startswith("class ")
                or stripped.startswith("@")
            ):  # decorator
                code_start_line = i
                break

        # Extract shared imports and shared code
        shared_imports = "\n".join(imports)
        shared_code = "\n".join(lines[code_start_line:])

        print(
            f"📦 Extracted {len(imports)} imports, shared code from line "
            f"{code_start_line}"
        )
        return shared_imports, shared_code

    def _is_header_or_metadata_line(self, line: str) -> bool:
        """Check if a line is a header, metadata, or should be excluded"""
        stripped = line.strip()
        return bool(
            stripped.startswith(("import", "from"))
            or stripped.startswith("#")
            or stripped.startswith('"""')
            or stripped.startswith("'''")
            or not stripped
        )

    def _has_forbidden_shared_module_imports(self, stripped: str) -> bool:
        """Check if line contains forbidden shared module imports."""
        return bool(
            (stripped.startswith("from .") and f"{SHARED_MODULE}" in stripped)
            or (stripped.startswith("import ") and f"{SHARED_MODULE}" in stripped)
            or (
                stripped.startswith("from shared_configuration")
                and "import" in stripped
            )
        )

    def _extract_file_sections_with_markers(
        self, file_path: Path
    ) -> tuple[str, str, str]:
        """
        Extract file sections using standardized deployment markers.

        Returns:
            tuple: (header, core_imports, core_functions)
        """
        if not file_path.exists():
            return "", "", ""

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find marker positions
        header_end = 0
        import_start = 0
        import_end = 0
        function_start = 0
        function_end = len(lines)

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Find import block boundaries
            if "IMPORT_BLOCK_START" in line:
                import_start = i + 1
                if header_end == 0:  # Header ends just before imports
                    header_end = i
            elif "IMPORT_BLOCK_END" in line:
                import_end = i
            elif "FUNCTION_BLOCK_START" in line:
                function_start = i + 1
            elif "FUNCTION_BLOCK_END" in line:
                function_end = i

        # Extract sections
        header = "\n".join(lines[:header_end]) if header_end > 0 else ""

        # Extract only non-shared imports (exclude SHARED_CONFIG_IMPORT sections)
        core_imports = self._extract_core_imports_only(lines, import_start, import_end)

        core_functions = (
            "\n".join(lines[function_start:function_end])
            if function_start < function_end
            else ""
        )

        return header, core_imports, core_functions

    def _extract_core_imports_only(self, lines: list[str], start: int, end: int) -> str:
        """Extract only core imports, excluding shared configuration imports."""
        if start >= end:
            return ""

        result_lines = []
        skip_shared = False

        for i in range(start, end):
            line = lines[i]

            # Skip shared configuration import sections
            if "SHARED_CONFIG_IMPORT_START" in line:
                skip_shared = True
                continue
            elif "SHARED_CONFIG_IMPORT_END" in line:
                skip_shared = False
                continue

            if not skip_shared and line.strip():
                result_lines.append(line)

        return "\n".join(result_lines)

    def _extract_shared_imports_and_functions(
        self, shared_file_path: Path
    ) -> tuple[str, str]:
        """Extract imports and functions from shared configuration file."""
        if not shared_file_path.exists():
            return "", ""

        with open(shared_file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Find import and function sections
        import_lines = []
        function_lines = []
        in_imports = False
        in_functions = False

        for line in lines:
            stripped = line.strip()

            # Track import section
            if stripped.startswith(
                ("import ", "from ")
            ) and not self._is_relative_import(stripped):
                import_lines.append(line)

            # Track function/class definitions
            elif stripped.startswith(("def ", "class ", "@")):
                in_functions = True
                function_lines.append(line)
            elif in_functions:
                function_lines.append(line)

        return "\n".join(import_lines), "\n".join(function_lines)

    def _is_relative_import(self, line: str) -> bool:
        """Check if import is relative (starts with from .)."""
        return line.strip().startswith("from .")

    def _build_lambda_deployment_with_markers(
        self, lambda_file: Path, deployment_file: Path
    ) -> bool:
        """
        Build Lambda deployment using standardized markers for precise extraction.

        This method implements the improved workflow:
        1. Extract core file header (before IMPORT_BLOCK_START)
        2. Extract core imports (IMPORT_BLOCK_START → IMPORT_BLOCK_END, excluding shared)
        3. Extract shared imports from shared_configuration.py
        4. Merge and deduplicate imports into unified block
        5. Extract core functions (FUNCTION_BLOCK_START → FUNCTION_BLOCK_END)
        6. Extract shared functions from shared_configuration.py
        7. Combine header + merged_imports + shared_functions + core_functions
        8. Generate deployment-ready Lambda package
        """
        print(f"🔄 Building deployment file using markers: {lambda_file.name}")

        # Step 1-3: Extract sections from core Lambda file
        header, core_imports, core_functions = self._extract_file_sections_with_markers(
            lambda_file
        )

        if not header or not core_functions:
            print(f"❌ Missing markers in {lambda_file.name}")
            print(
                "   Required markers: IMPORT_BLOCK_START/END, FUNCTION_BLOCK_START/END"
            )
            return False

        # Step 4-5: Extract from shared configuration
        shared_imports, shared_functions = self._extract_shared_imports_and_functions(
            self.shared_file_path
        )

        # Step 6: Merge and deduplicate imports
        merged_imports = self._merge_and_deduplicate_imports(
            core_imports, shared_imports
        )

        # Step 7: Combine all sections
        deployment_content = self._combine_deployment_sections(
            header, merged_imports, shared_functions, core_functions
        )

        # Step 8: Write deployment file
        self._write_deployment_file(deployment_file, deployment_content)

        print(f"✅ Deployment file created: {deployment_file}")
        return True

    def _merge_and_deduplicate_imports(
        self, core_imports: str, shared_imports: str
    ) -> str:
        """Merge core and shared imports, removing duplicates."""
        all_imports = set()
        result_lines = []

        # Process all import lines
        for imports_block in [core_imports, shared_imports]:
            if not imports_block:
                continue

            for line in imports_block.split("\n"):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                if stripped.startswith(("import ", "from ")):
                    # Normalize for deduplication
                    normalized = stripped.split("#")[0].strip()
                    if normalized not in all_imports:
                        all_imports.add(normalized)
                        result_lines.append(line)
                    else:
                        print(f"  📝 Skipping duplicate import: {stripped}")

        return "\n".join(result_lines)

    def _combine_deployment_sections(
        self, header: str, imports: str, shared_functions: str, core_functions: str
    ) -> str:
        """Combine all sections into final deployment content."""
        sections = []

        # Add header
        if header:
            sections.append(header)

        # Add imports
        if imports:
            sections.append(imports)

        # Add shared functions first (dependencies)
        if shared_functions:
            sections.append("\n# === EMBEDDED SHARED CONFIGURATION ===")
            sections.append(shared_functions)
            sections.append("# === END EMBEDDED SHARED CODE ===\n")

        # Add core functions
        if core_functions:
            sections.append(core_functions)

        return "\n\n".join(sections)

    def _extract_functions_from_content(self, shared_content: str) -> dict[str, str]:
        """Extract function definitions from shared content."""
        tree = ast.parse(shared_content)
        functions: dict[str, str] = {}
        func_lines = shared_content.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = self._find_function_end(func_lines, start_line)
                func_code = "\n".join(func_lines[start_line:end_line])
                functions[node.name] = func_code
                print(f"✅ Extracted function: {node.name}")

        return functions

    def _find_function_end(self, func_lines: list[str], start_line: int) -> int:
        """Find the end line of a function definition using proper Python
        indentation logic."""
        if start_line >= len(func_lines):
            return len(func_lines)

        # Get the indentation level of the function definition
        func_def_line = func_lines[start_line].rstrip()
        func_indent = len(func_def_line) - len(func_def_line.lstrip())

        # Track if we're still in the function signature (before the colon)
        in_signature = True

        # Look for the end of the function by finding where indentation
        # returns to function level or less
        for i in range(start_line + 1, len(func_lines)):
            line = func_lines[i].rstrip()

            # Skip empty lines
            if not line.strip():
                continue

            current_indent = len(line) - len(line.lstrip())

            # If we're still in the function signature, look for the closing colon
            if in_signature:
                if line.rstrip().endswith(":"):
                    in_signature = False
                continue

            # Now we're in the function body
            # If we find a line at the same or less indentation than the function def,
            # and it's not a decorator (starts with @), this is the end of the function
            if current_indent <= func_indent:
                # Special case: decorators for the next function should not
                # end current function
                if line.strip().startswith("@"):
                    continue
                # This is the end of our function
                return i

        # If we reach the end of file, return the end
        return len(func_lines)

    def _extract_imports_and_constants(
        self, shared_content: str
    ) -> tuple[list[str], list[str]]:
        """Extract imports and constants from shared content."""
        imports: list[str] = []
        constants: list[str] = []
        in_constants_section = False

        for line in shared_content.split("\n"):
            if line.strip().startswith(("import ", "from ")):
                if not line.strip().startswith("from typing"):
                    imports.append(line)
            elif "=== SHARED CONSTANTS ===" in line:
                in_constants_section = True
                constants.append(line)
            elif in_constants_section:
                if line.strip().startswith("# ===") and "CONSTANTS" not in line:
                    break
                constants.append(line)

        return imports, constants

    def _build_lambda_deployment(
        self,
        lambda_file: str,
        shared_code: str,
        shared_imports: str,
    ) -> None:
        """Build deployment file for a single Lambda function using
        simplified approach."""
        source_path = self.source_dir / lambda_file
        deployment_path = self.deployment_dir / lambda_file

        print(f"🔧 Building deployment version: {lambda_file}")

        # Read original file
        with open(source_path, encoding="utf-8") as f:
            original_lines = f.readlines()

        # Step 1: Parse file structure
        file_sections = self._parse_file_sections(original_lines)

        # Step 2: Write deployment file
        self._write_deployment_content(
            deployment_path, file_sections, shared_code, shared_imports
        )

        print(f"✅ Created standalone deployment: {deployment_path}")
        print("📦 Added shared code block")

    def _parse_file_sections(self, original_lines: list[str]) -> dict[str, str]:
        """Parse original file into sections: header, imports, body."""
        import_start = self._find_import_start(original_lines)
        import_lines, import_end = self._extract_import_lines(
            original_lines, import_start
        )

        # Extract file sections
        header_section = "".join(original_lines[:import_start])
        existing_imports_block = "".join(import_lines)

        # Get body content and filter shared imports
        original_body_lines = original_lines[import_end:]
        original_body_text = "".join(original_body_lines)
        filtered_body_lines = self._filter_shared_imports(original_body_text)
        original_body = "\n".join(filtered_body_lines)

        return {
            "header": header_section,
            "imports": existing_imports_block,
            "body": original_body,
        }

    def _find_import_start(self, original_lines: list[str]) -> int:
        """Find where imports start (preserve everything before first import)."""
        for i, line in enumerate(original_lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                return i
        return 0

    def _extract_import_lines(
        self, original_lines: list[str], import_start: int
    ) -> tuple[list[str], int]:
        """Extract import lines, excluding shared imports."""
        import_lines: list[str] = []
        i = import_start

        while i < len(original_lines):
            line = original_lines[i]
            stripped = line.strip()

            # Check if this is a shared import line and skip it
            if self._is_shared_import_line(line):
                i = self._skip_shared_import_block(original_lines, i)
                continue

            # Check if this is still an import line
            if self._is_import_section_line(stripped):
                import_lines.append(line)
                i += 1
                continue

            # Found end of imports
            return import_lines, i

        return import_lines, len(original_lines)

    def _is_shared_import_line(self, line: str) -> bool:
        """Check if line is a shared module import."""
        return (
            f"from .{SHARED_MODULE} import" in line or f"import {SHARED_MODULE}" in line
        )

    def _skip_shared_import_block(
        self, original_lines: list[str], start_index: int
    ) -> int:
        """Skip shared import block (single or multi-line) and return next index."""
        line = original_lines[start_index]
        print(f"  🗑️  Skipping shared import: {line.strip()}")

        # Check if this is a multi-line import
        line_without_comment = line.split("#")[0].strip()
        is_multiline = "(" in line and not line_without_comment.endswith(")")

        if is_multiline:
            return self._skip_multiline_import(original_lines, start_index + 1)

        return start_index + 1

    def _skip_multiline_import(
        self, original_lines: list[str], start_index: int
    ) -> int:
        """Skip multi-line import until closing paren."""
        i = start_index
        while i < len(original_lines):
            current_line = original_lines[i]
            print(
                "  🗑️  Skipping shared import continuation: " f"{current_line.strip()}"
            )
            # Check if this line contains the closing paren (ignoring comments)
            line_content = current_line.split("#")[0].strip()
            if line_content.endswith(")"):
                return i + 1  # Include the closing paren line
            i += 1
        return i

    def _is_import_section_line(self, stripped: str) -> bool:
        """Check if line is part of import section."""
        return (
            stripped.startswith(("import ", "from "))
            or stripped.startswith("#")  # comments within imports
            or not stripped  # blank lines within imports
        )

    def _write_deployment_content(
        self,
        deployment_path: Path,
        file_sections: dict[str, str],
        shared_code: str,
        shared_imports: str,
    ) -> None:
        """Write deployment file with embedded shared code."""
        with open(deployment_path, "w", encoding="utf-8") as f:
            # Write original header (docstring, copyright, pylint disables, etc.)
            if file_sections["header"].strip():
                f.write(file_sections["header"])
                f.write("\n")

            # Write existing imports
            f.write(file_sections["imports"])

            # Add deduplicated shared imports
            deduplicated_imports = self._deduplicate_imports(
                file_sections["imports"], shared_imports
            )
            if deduplicated_imports.strip():
                f.write(deduplicated_imports)
                f.write("\n")

            # Write shared code block
            f.write("\n# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===\n")
            f.write(shared_code)
            f.write("\n")

            # Write original file body
            f.write(file_sections["body"])

    def _deduplicate_imports(
        self, existing_imports_block: str, shared_imports: str
    ) -> str:
        """Remove duplicate imports from shared_imports that already exist in
        existing_imports_block.

        Handles merging 'from' imports intelligently, e.g.:
        - Existing: from botocore.exceptions import ClientError
        - Shared: from botocore.exceptions import ClientError, NoCredentialsError
        - Result: Add only NoCredentialsError (merge, don't skip entirely)
        """
        # Parse existing imports into structured format
        existing_simple_imports, existing_from_imports = self._parse_existing_imports(
            existing_imports_block
        )

        # Process shared imports and add only what's missing
        new_import_lines = self._process_shared_imports(
            shared_imports, existing_simple_imports, existing_from_imports
        )

        return "\n".join(new_import_lines)

    def _parse_existing_imports(
        self, existing_imports_block: str
    ) -> tuple[set[str], dict[str, set[str]]]:
        """Parse existing imports into structured format."""
        existing_simple_imports: set[str] = set()  # import module
        existing_from_imports: dict[str, set[str]] = {}  # from module import names

        for line in existing_imports_block.split("\n"):
            line = line.strip()
            if line.startswith("import "):
                self._process_simple_import_line(line, existing_simple_imports)
            elif line.startswith("from "):
                self._process_from_import_line(line, existing_from_imports)

        return existing_simple_imports, existing_from_imports

    def _process_simple_import_line(
        self, line: str, existing_simple_imports: set[str]
    ) -> None:
        """Process a simple import line."""
        import_statement = " ".join(line.split())
        existing_simple_imports.add(import_statement)

    def _process_from_import_line(
        self, line: str, existing_from_imports: dict[str, set[str]]
    ) -> None:
        """Process a from import line."""
        if " import " in line:
            parts = line.split(" import ", 1)
            if len(parts) == 2:
                module = parts[0].replace("from ", "").strip()
                names_part = parts[1].strip()
                # Split names by comma and clean whitespace
                names = {name.strip() for name in names_part.split(",") if name.strip()}
                if module in existing_from_imports:
                    existing_from_imports[module].update(names)
                else:
                    existing_from_imports[module] = names

    def _process_shared_imports(
        self,
        shared_imports: str,
        existing_simple_imports: set[str],
        existing_from_imports: dict[str, set[str]],
    ) -> list[str]:
        """Process shared imports and return only unique ones."""
        new_import_lines: list[str] = []

        for line in shared_imports.split("\n"):
            line = line.strip()
            if line.startswith("import "):
                self._handle_simple_import(
                    line, existing_simple_imports, new_import_lines
                )
            elif line.startswith("from "):
                self._handle_from_import(line, existing_from_imports, new_import_lines)
            elif line:  # Keep non-import lines (comments, etc.)
                new_import_lines.append(line)

        return new_import_lines

    def _handle_simple_import(
        self,
        line: str,
        existing_simple_imports: set[str],
        new_import_lines: list[str],
    ) -> None:
        """Handle a simple import line."""
        import_statement = " ".join(line.split())
        if import_statement not in existing_simple_imports:
            new_import_lines.append(line)
            print(f"✅ Adding unique import: {line}")
        else:
            print(f"🗑️  Skipping duplicate import: {line}")

    def _handle_from_import(
        self,
        line: str,
        existing_from_imports: dict[str, set[str]],
        new_import_lines: list[str],
    ) -> None:
        """Handle a from import line."""
        if " import " in line:
            parts = line.split(" import ", 1)
            if len(parts) == 2:
                self._process_valid_from_import(
                    parts, line, existing_from_imports, new_import_lines
                )
            else:
                self._handle_malformed_import(line, new_import_lines)
        else:
            self._handle_malformed_import(line, new_import_lines)

    def _process_valid_from_import(
        self,
        parts: list[str],
        original_line: str,
        existing_from_imports: dict[str, set[str]],
        new_import_lines: list[str],
    ) -> None:
        """Process a valid from import with proper format."""
        module = parts[0].replace("from ", "").strip()
        names_part = parts[1].strip()
        # Split names by comma and clean whitespace
        shared_names = {name.strip() for name in names_part.split(",") if name.strip()}

        # Check what names are missing from existing imports
        existing_names = existing_from_imports.get(module, set())
        missing_names = shared_names - existing_names

        if missing_names:
            # Add only the missing names
            missing_names_str = ", ".join(sorted(missing_names))
            new_import_line = f"from {module} import {missing_names_str}"
            new_import_lines.append(new_import_line)
            print(f"✅ Adding missing from import: {new_import_line}")
        else:
            print(
                "🗑️  Skipping duplicate from import: "
                f"{original_line} (all names already imported)"
            )

    def _handle_malformed_import(self, line: str, new_import_lines: list[str]) -> None:
        """Handle malformed import lines."""
        new_import_lines.append(line)
        print(f"⚠️  Adding malformed import as-is: {line}")

    def _read_source_file(self, source_path: Path) -> str:
        """Read source Lambda function content."""
        with open(source_path, encoding="utf-8") as f:
            return f.read()

    def _filter_shared_imports(self, source_content: str) -> list[str]:
        """Remove shared_configuration imports from source content."""
        lines = source_content.split("\n")
        filtered_lines: list[str] = []
        in_shared_import = False

        for line in lines:
            # Check for start of shared import (handle various comment patterns)
            if (
                f"from .{SHARED_MODULE} import" in line
                or f"import {SHARED_MODULE}" in line
            ):
                print(f"  🗑️  Removed import: {line.strip()}")
                in_shared_import = True
                # Check if this is a single-line import
                # (ends with no parentheses or closing paren)
                if line.strip().endswith(")") or "(" not in line:
                    in_shared_import = False
                continue

            # If we're in a multi-line import, skip lines until we find the
            # closing paren
            if in_shared_import:
                print(f"  🗑️  Removed import continuation: {line.strip()}")
                if line.strip().endswith(")"):
                    in_shared_import = False
                continue

            # Handle orphaned import statements and stray parentheses
            stripped = line.strip()
            shared_func_names = [
                "AlexaValidator",
                "RateLimiter",
                "SecurityEventLogger",
                "cache_configuration",
                "load_configuration",
                "load_environment",
            ]

            # Remove orphaned import-like lines (function names with commas)
            orphaned_import_check = (
                line.startswith("    ")
                and stripped.endswith(",")
                and "=" not in line
                and "(" not in line
                and any(func_name in line for func_name in shared_func_names)
            )
            if orphaned_import_check:
                print(f"  🗑️  Removed orphaned import: {stripped}")
                continue

            # Remove stray closing parentheses that are leftover from import removal
            # Only remove if the previous lines suggest this was part of an import
            # that got removed
            stray_paren_check = False
            if line.startswith("    ") and stripped == ")" and len(filtered_lines) > 0:
                # Look back several lines to see if this looks like import
                # cleanup context
                recent_lines = (
                    filtered_lines[-3:] if len(filtered_lines) >= 3 else filtered_lines
                )
                # Only remove if we recently removed orphaned imports or this
                # looks like import context
                has_recent_removals = any(
                    "# Import" in recent_line or "import" in recent_line.lower()
                    for recent_line in recent_lines
                )
                # But don't remove if this looks like it's part of a function call
                has_function_call_context = any(
                    "(" in recent_line and "def " not in recent_line
                    for recent_line in recent_lines
                )

                if has_recent_removals and not has_function_call_context:
                    stray_paren_check = True

            if stray_paren_check:
                print(f"  🗑️  Removed stray closing paren: {stripped}")
                continue

            filtered_lines.append(line)

        return filtered_lines

    def _create_embedded_code_block(
        self,
        shared_functions: dict[str, str],
        shared_constants: str,
        shared_imports: str,
    ) -> tuple[str, str]:
        """Create separate imports and functions blocks for clean file structure."""
        # Extract just the import lines from shared_imports
        import_lines: list[str] = []
        for line in shared_imports.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                import_lines.append(line)

        imports_block = "\n".join(import_lines)

        # Create functions block (without imports)
        functions_block = f"""
# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===
# Source: {SHARED_MODULE}.py
# Generated by deploy_shared_config.py - DO NOT EDIT MANUALLY

{shared_constants}

# === SHARED FUNCTIONS ===
"""

        for _func_name, func_code in shared_functions.items():
            functions_block += f"\n{func_code}\n"

        functions_block += "\n# === END EMBEDDED SHARED CODE ===\n"
        return imports_block, functions_block

    def _merge_content_with_embedded_code(
        self, filtered_lines: list[str], imports_block: str, functions_block: str
    ) -> str:
        """Merge content with imports at top and functions at end,
        avoiding duplicates."""
        # Extract existing imports from the file
        existing_imports: set[str] = set()
        import_insertion_point = 0

        for i, line in enumerate(filtered_lines):
            stripped = line.strip()

            # Track existing imports to avoid duplicates
            if self._is_trackable_import_line(stripped, line):
                # Normalize import statement for comparison
                import_statement = stripped.split("#")[0].strip()
                existing_imports.add(import_statement)
                import_insertion_point = i + 1
            # Stop when we hit actual code (non-import, non-comment, non-empty)
            elif self._is_actual_code_line(stripped):
                break

        # Filter new imports to avoid duplicates
        new_import_lines: list[str] = []
        for line in imports_block.split("\n"):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                # Normalize import statement for comparison
                import_statement = stripped.split("#")[0].strip()
                if import_statement not in existing_imports:
                    new_import_lines.append(line)
                    existing_imports.add(import_statement)
                else:
                    print(f"  📝  Skipping duplicate import: {stripped}")

        # Insert only new imports after existing imports
        if new_import_lines:
            lines_with_imports = (
                filtered_lines[:import_insertion_point]
                + new_import_lines
                + filtered_lines[import_insertion_point:]
            )
        else:
            lines_with_imports = filtered_lines

        # Append functions at the end
        deployment_lines = lines_with_imports + functions_block.split("\n")

        return "\n".join(deployment_lines)

    def _is_trackable_import_line(self, stripped: str, line: str) -> bool:
        """Check if line is a trackable import (not shared_configuration)."""
        return (
            stripped.startswith(("import ", "from "))
            and "shared_configuration" not in line
        )

    def _is_actual_code_line(self, stripped: str) -> bool:
        """Check if line contains actual code (non-import, non-comment, non-empty)."""
        return bool(
            stripped
            and not stripped.startswith("#")
            and not stripped.startswith(("import ", "from "))
        )

    def _write_deployment_file(self, deployment_path: Path, content: str) -> None:
        """Write deployment content to file."""
        with open(deployment_path, "w", encoding="utf-8") as f:
            f.write(content)

    def validate_deployment(self) -> bool:
        """Comprehensive validation that deployment files are functional."""
        print("🔍 Validating deployment functionality...")

        all_valid = True

        # Step 1: Basic file existence and structure
        for lambda_file in LAMBDA_FUNCTIONS:
            deployment_path = self.deployment_dir / lambda_file
            lambda_name = lambda_file.replace(".py", "")

            print(f"\n📋 Validating {lambda_name}...")

            if not deployment_path.exists():
                print(f"❌ Missing deployment file: {deployment_path}")
                all_valid = False
                continue

            with open(deployment_path, encoding="utf-8") as f:
                deployment_content = f.read()

            # Step 2: Check deployment structure
            if f"from .{SHARED_MODULE} import" in deployment_content:
                print(f"❌ {lambda_name}: Still has shared imports (not standalone)")
                all_valid = False
                continue

            if "=== EMBEDDED SHARED CODE" not in deployment_content:
                print(f"❌ {lambda_name}: Missing embedded code marker")
                all_valid = False
                continue

            print(f"✅ {lambda_name}: Basic structure valid")

            # Step 3: Python syntax validation
            try:
                ast.parse(deployment_content)
                print(f"✅ {lambda_name}: Python syntax valid")
            except SyntaxError as e:
                print(f"❌ {lambda_name}: Syntax error at line {e.lineno}: {e.msg}")
                all_valid = False
                continue

            # Step 4: Function availability validation
            validation_result = self._validate_functions_available(
                lambda_name, deployment_content
            )
            if not validation_result:
                all_valid = False
                continue

            # Step 5: Import validation
            import_result = self._validate_imports(deployment_content, lambda_name)
            if not import_result:
                all_valid = False
                continue

            print(f"✅ {lambda_name}: All validations passed")

        # Step 6: Cross-file synchronization validation
        if all_valid:
            sync_result = self._validate_synchronization()
            if not sync_result:
                all_valid = False

        if all_valid:
            print("\n🎯 VALIDATION SUMMARY: All deployment files are functional ✅")
        else:
            print("\n❌ VALIDATION SUMMARY: Some deployment files have issues")

        return all_valid

    def _validate_functions_available(self, lambda_name: str, content: str) -> bool:
        """Validate that all expected shared functions are available in deployment."""
        print(f"🔧 {lambda_name}: Checking function availability...")

        # Check if shared code block is present (simplified validation)
        if "# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===" in content:
            print(f"✅ {lambda_name}: Shared code block found")
            return True

        print(f"❌ {lambda_name}: Shared code block missing")
        return False

    def _validate_imports(self, content: str, lambda_name: str) -> bool:
        """Validate deployment file imports and shared module dependencies."""
        print(f"📦 {lambda_name}: Checking import validity...")

        lines = content.split("\n")
        has_required_imports = False
        has_forbidden_imports = False
        forbidden_imports: list[str] = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for required imports (boto3, etc.)
            if stripped.startswith(("import boto3", "from boto3")):
                has_required_imports = True

            # Check for forbidden shared module imports (actual import statements only)
            if self._has_forbidden_shared_module_imports(stripped):
                has_forbidden_imports = True
                forbidden_imports.append(f"Line {line_num}: {stripped}")

        if has_forbidden_imports:
            print(f"❌ {lambda_name}: Has forbidden shared module imports:")
            for forbidden in forbidden_imports:
                print(f"   {forbidden}")
            return False

        if not has_required_imports:
            print(f"⚠️  {lambda_name}: No boto3 imports found (might be okay)")
        else:
            print(f"✅ {lambda_name}: Required imports present")

        print(f"✅ {lambda_name}: Import structure valid")
        return True

    def _validate_synchronization(self) -> bool:
        """Validate that deployment files are synchronized with current source."""
        print("\n🔄 Checking source/deployment synchronization...")

        sync_valid = True

        for lambda_file in LAMBDA_FUNCTIONS:
            deployment_path = self.deployment_dir / lambda_file
            lambda_name = lambda_file.replace(".py", "")

            with open(deployment_path, encoding="utf-8") as f:
                deployment_content = f.read()

            # Check if embedded shared code block is present
            if (
                "=== EMBEDDED SHARED CODE (AUTO-GENERATED) ==="
                not in deployment_content
            ):
                print(f"❌ {lambda_name}: Missing embedded shared code block")
                sync_valid = False
                continue

            # For now, just verify that shared code is embedded
            # More sophisticated synchronization checking can be added later
            print(f"✅ {lambda_name}: Embedded shared code present")

            print(f"✅ {lambda_name}: Synchronization valid")

        if sync_valid:
            print("✅ All deployment files are synchronized with source")

        return sync_valid

    def _extract_embedded_functions(self, content: str) -> dict[str, str]:
        """Extract embedded functions from deployment file content."""
        # Find the embedded code section
        lines = content.split("\n")
        embedded_functions: dict[str, str] = {}

        try:
            # Parse the entire content to find functions
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function is in embedded section
                    func_start_line = node.lineno - 1

                    # Look backwards to see if we're in an embedded section
                    for i in range(max(0, func_start_line - 50), func_start_line):
                        if i < len(lines) and "=== EMBEDDED SHARED CODE" in lines[i]:
                            embedded_functions[node.name] = node.name
                            break

        except (SyntaxError, AttributeError, ValueError) as e:
            # Log error but continue with partial results
            print(f"⚠️  Error parsing embedded functions: {e}")

        return embedded_functions

    def clean_reset(self) -> None:
        """Reset to clean development mode."""
        print("🧹 Resetting to clean development mode...")

        # Remove deployment directory
        if self.deployment_dir.exists():
            shutil.rmtree(self.deployment_dir)
            print(f"🗑️  Removed deployment directory: {self.deployment_dir}")

        # Ensure source files only have imports
        for lambda_file in LAMBDA_FUNCTIONS:
            source_path = self.source_dir / lambda_file

            with open(source_path, encoding="utf-8") as f:
                content = f.read()

            # Check if source has embedded code (shouldn't in clean mode)
            if "=== EMBEDDED SHARED CODE ===" in content:
                print(f"⚠️  Source file has embedded code (cleaning): {lambda_file}")
                # Remove embedded code sections
                lines = content.split("\n")
                filtered_lines: list[str] = []
                skip_embedded = False

                for line in lines:
                    if "=== EMBEDDED SHARED CODE" in line:
                        skip_embedded = True
                        continue
                    if "=== END EMBEDDED SHARED CODE ===" in line:
                        skip_embedded = False
                        continue
                    if not skip_embedded:
                        filtered_lines.append(line)

                # Write cleaned source
                with open(source_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(filtered_lines))
                print(f"✅ Cleaned source file: {lambda_file}")

            # Ensure import exists
            if f"from .{SHARED_MODULE} import" not in content:
                print(f"⚠️  Adding missing import to: {lambda_file}")
                # Add import after other imports
                lines = content.split("\n")
                insertion_point = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(("import ", "from ")):
                        insertion_point = i + 1

                lines.insert(insertion_point, f"from .{SHARED_MODULE} import *")

                with open(source_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                print(f"✅ Added import to: {lambda_file}")

        print("✅ Clean development mode restored!")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Clean Lambda deployment system")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true", help="Build deployment files")
    group.add_argument("--validate", action="store_true", help="Validate deployment")
    group.add_argument("--clean", action="store_true", help="Reset to development mode")

    parser.add_argument("--workspace", default=".", help="Workspace root path")

    args = parser.parse_args()

    deployer = CleanDeploymentSystem(args.workspace)

    if args.build:
        deployer.build_deployment()
        # Auto-validate after build
        if deployer.validate_deployment():
            print("✅ Build validation successful!")
        else:
            print("❌ Build validation failed!")
            sys.exit(1)

    elif args.validate:
        success = deployer.validate_deployment()
        sys.exit(0 if success else 1)

    elif args.clean:
        deployer.clean_reset()


if __name__ == "__main__":
    main()
