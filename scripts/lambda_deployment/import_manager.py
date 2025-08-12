#!/usr/bin/env python3
"""
🔧 IMPORT MANAGER

Handles Python import parsing, consolidation, and formatting for Lambda deployments.
Extracted from deployment_manager.py to reduce complexity and improve maintainability.

Key Features:
- Parse and classify imports (standard library vs third-party)
- Merge and deduplicate imports from multiple sources
- Consolidate imports from same modules (e.g., multiple "from typing import")
- Filter shared configuration imports
- Format imports with proper grouping and sorting
"""

import re
from typing import Any


class ImportManager:
    """Manages Python import parsing, merging, and formatting operations."""

    def __init__(self) -> None:
        """Initialize the import manager."""
        self._standard_library_modules = self._get_standard_library_modules()

    def merge_imports(self, lambda_imports: str, shared_imports: str) -> str:
        """
        Merge and deduplicate imports from Lambda and shared code.

        This method removes shared configuration imports from lambda imports,
        merges with shared configuration imports, and consolidates imports
        from the same modules (e.g., multiple "from typing import" lines).

        Args:
            lambda_imports: Import statements from Lambda function
            shared_imports: Import statements from shared configuration

        Returns:
            Merged and deduplicated import statements with proper formatting
        """
        import_groups = self._parse_imports_into_groups(lambda_imports, shared_imports)
        return self._format_consolidated_imports(import_groups)

    def _parse_imports_into_groups(
        self, lambda_imports: str, shared_imports: str
    ) -> dict[str, Any]:
        """Parse imports into consolidated groups by module."""
        # Initialize import group containers
        import_groups = self._initialize_import_groups()

        # Collect all import lines
        all_import_lines = self._collect_import_lines(lambda_imports, shared_imports)

        # Process each import line
        for line in all_import_lines:
            self._process_import_line(line, import_groups)

        return import_groups

    def _initialize_import_groups(self) -> dict[str, Any]:
        """Initialize containers for different import types."""
        return {
            "standard": set(),
            "third_party": set(),
            "standard_from": {},
            "third_party_from": {},
        }

    def _get_standard_library_modules(self) -> set[str]:
        """Get the set of Python standard library modules."""
        return {
            "os",
            "sys",
            "time",
            "json",
            "logging",
            "configparser",
            "urllib",
            "re",
            "collections",
            "typing",
            "dataclasses",
            "pathlib",
            "functools",
            "itertools",
            "datetime",
            "calendar",
            "math",
            "random",
            "hashlib",
            "base64",
            "uuid",
            "secrets",
            "ssl",
            "socket",
            "urllib.parse",
            "urllib.request",
            "urllib.error",
            "http",
            "http.client",
            "http.server",
            "email",
            "mimetypes",
            "tempfile",
            "shutil",
            "glob",
            "fnmatch",
            "abc",
            "contextlib",
            "warnings",
            "inspect",
            "copy",
            "pickle",
            "enum",
            "decimal",
            "fractions",
            "statistics",
            "threading",
            "multiprocessing",
            "subprocess",
            "signal",
            "traceback",
            "io",
            "codecs",
            "locale",
            "gettext",
            "argparse",
            "optparse",
            "textwrap",
            "string",
            "difflib",
            "pprint",
            "reprlib",
            "weakref",
            "gc",
            "types",
            "operator",
            "keyword",
            "heapq",
            "bisect",
            "array",
            "struct",
            "zlib",
            "gzip",
            "bz2",
            "lzma",
            "zipfile",
            "tarfile",
            "csv",
            "xml",
            "html",
            "sqlite3",
            "dbm",
            "platform",
            "ctypes",
            "unittest",
            "doctest",
            "test",
            "pdb",
            "profile",
            "cProfile",
            "timeit",
            "trace",
            "distutils",
            "venv",
            "ensurepip",
            "importlib",
            "pkgutil",
            "modulefinder",
            "runpy",
            "ast",
            "symtable",
            "token",
            "tokenize",
            "tabnanny",
            "py_compile",
            "compileall",
            "dis",
            "pickletools",
        }

    def _collect_import_lines(
        self, lambda_imports: str, shared_imports: str
    ) -> list[str]:
        """Collect and filter import lines from lambda and shared imports."""
        all_import_lines: list[str] = []

        # Add lambda imports (excluding shared config imports)
        all_import_lines.extend(
            self._filter_import_lines(lambda_imports, exclude_shared_config=True)
        )

        # Add shared imports
        all_import_lines.extend(
            self._filter_import_lines(shared_imports, exclude_shared_config=False)
        )

        return all_import_lines

    def _filter_import_lines(
        self, imports_text: str, exclude_shared_config: bool = False
    ) -> list[str]:
        """
        Filter import lines, removing comments and optionally shared config imports.
        """
        filtered_lines: list[str] = []

        for line in imports_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if exclude_shared_config and self._is_shared_configuration_import(line):
                continue

            filtered_lines.append(line)

        return filtered_lines

    def _process_import_line(self, line: str, import_groups: dict[str, Any]) -> None:
        """Process a single import line and add it to appropriate groups."""
        if line.startswith("import "):
            self._process_standard_import(line, import_groups)
        elif line.startswith("from "):
            self._process_from_import(line, import_groups)

    def _process_standard_import(
        self, line: str, import_groups: dict[str, Any]
    ) -> None:
        """Process standard import statements (import module)."""
        module = line[7:].strip()  # Remove "import "

        if self._is_standard_library_module(module):
            import_groups["standard"].add(module)
        else:
            import_groups["third_party"].add(module)

    def _process_from_import(self, line: str, import_groups: dict[str, Any]) -> None:
        """Process from import statements (from module import items)."""
        try:
            module, imported_items = self._parse_from_import(line)
            is_stdlib = self._is_standard_library_module(module)

            # Add to appropriate group
            target_group = "standard_from" if is_stdlib else "third_party_from"
            self._add_to_from_imports(
                import_groups[target_group], module, imported_items
            )

        except (IndexError, ValueError):
            # Malformed import, treat as third-party
            import_groups["third_party"].add(line)

    def _parse_from_import(self, line: str) -> tuple[str, list[str]]:
        """Parse a from import line into module and imported items."""
        parts = line.split(" import ")
        if len(parts) != 2:
            raise ValueError("Invalid from import format")

        module = parts[0][5:].strip()  # Remove "from "
        imports_str = parts[1].strip()

        # Parse imported items (handle commas)
        imported_items = [
            item.strip() for item in imports_str.split(",") if item.strip()
        ]

        return module, imported_items

    def _add_to_from_imports(
        self,
        from_imports_dict: dict[str, set[str]],
        module: str,
        imported_items: list[str],
    ) -> None:
        """Add imported items to the from imports dictionary."""
        if module not in from_imports_dict:
            from_imports_dict[module] = set()
        from_imports_dict[module].update(imported_items)

    def _is_standard_library_module(self, module: str) -> bool:
        """Check if a module is part of the Python standard library."""
        # Check exact match
        if module in self._standard_library_modules:
            return True

        # Check if it's a submodule of a standard library module
        module_parts = module.split(".")
        for i in range(len(module_parts)):
            parent_module = ".".join(module_parts[: i + 1])
            if parent_module in self._standard_library_modules:
                return True

        return False

    def _format_consolidated_imports(self, import_groups: dict[str, Any]) -> str:
        """Format consolidated imports with proper grouping and sorting."""
        lines: list[str] = []

        # Group 1: Standard library imports (import statements)
        if import_groups["standard"]:
            lines.extend(sorted(f"import {imp}" for imp in import_groups["standard"]))

        # Group 2: Standard library from imports
        if import_groups["standard_from"]:
            if lines:
                lines.append("")  # Empty line between groups
            for module, items in sorted(import_groups["standard_from"].items()):
                lines.append(f"from {module} import {', '.join(sorted(items))}")

        # Group 3: Third party imports (import statements)
        if import_groups["third_party"]:
            if lines:
                lines.append("")  # Empty line between groups
            third_party_import_lines = [
                f"import {imp}" for imp in import_groups["third_party"]
            ]
            lines.extend(sorted(third_party_import_lines))

        # Group 4: Third party from imports
        if import_groups["third_party_from"]:
            if lines:
                lines.append("")  # Empty line between groups
            for module, items in sorted(import_groups["third_party_from"].items()):
                lines.append(f"from {module} import {', '.join(sorted(items))}")

        return "\n".join(lines)

    def _is_shared_configuration_import(self, line: str) -> bool:
        """Check if an import line is from shared configuration."""
        shared_patterns = [
            r"from \.shared_configuration import",
            r"import shared_configuration",
            r"from shared_configuration import",
            r"# === SHARED CONFIGURATION IMPORTS ===",
            r"# SHARED_CONFIG_IMPORT:",
        ]

        return any(re.search(pattern, line) for pattern in shared_patterns)
