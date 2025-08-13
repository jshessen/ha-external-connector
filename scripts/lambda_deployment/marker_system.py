#!/usr/bin/env python3
"""
🏗️ LAMBDA DEPLOYMENT MARKER SYSTEM

Core marker processing system for Lambda deployment automation.
Provides standardized marker validation, content extraction, and processing.

Key Features:
- Standardized marker definitions and validation
- Content extraction between markers
- Visual marker formatting consistency
- Comprehensive error reporting

Marker Format:
    # ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
    # ... content ...
    # ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯
"""

import logging
import re
from pathlib import Path
from typing import NamedTuple


class MarkerValidationResult(NamedTuple):
    """Result of marker validation."""

    is_valid: bool
    issues: list[str]
    marker_positions: dict[str, int]


class ExtractedContent(NamedTuple):
    """Content extracted using markers."""

    header: str
    imports: str
    configuration_classes: str
    functions: str
    shared_imports: list[str]


class _ContentExtractor:
    """Helper class to extract content from file lines using markers."""

    # pylint: disable=too-many-instance-attributes  # Data holder class needs multiple attributes

    def __init__(self):
        """Initialize content extractor with empty sections."""
        self.header_lines: list[str] = []
        self.import_lines: list[str] = []
        self.configuration_lines: list[str] = []
        self.function_lines: list[str] = []
        self.shared_imports: list[str] = []

        self.current_section = "header"
        self.in_import_block = False
        self.in_configuration_block = False
        self.in_function_block = False
        self.in_shared_imports_section = False

    def process_line(self, line: str) -> None:
        """Process a single line and categorize it into appropriate section."""
        stripped = line.strip()

        # Check for marker transitions
        if self._handle_marker_transitions(stripped):
            return

        # Check for shared import handling
        if self._handle_shared_imports(line, stripped):
            return

        # Categorize content into appropriate section
        self._categorize_content_line(line)

    def _handle_marker_transitions(self, stripped: str) -> bool:
        """Handle marker transitions and return True if line was a marker."""
        # pylint: disable=too-many-return-statements  # Early returns improve readability
        if "IMPORT_BLOCK_START" in stripped:
            self.in_import_block = True
            self.current_section = "imports"
            return True
        if "IMPORT_BLOCK_END" in stripped:
            self.in_import_block = False
            self.in_shared_imports_section = False
            return True
        if "CONFIGURATION_CLASSES_START" in stripped:
            self.in_configuration_block = True
            self.current_section = "configuration_classes"
            return True
        if "CONFIGURATION_CLASSES_END" in stripped:
            self.in_configuration_block = False
            return True
        if "FUNCTION_BLOCK_START" in stripped:
            self.in_function_block = True
            self.current_section = "functions"
            return True
        if "FUNCTION_BLOCK_END" in stripped:
            self.in_function_block = False
            return True
        return False

    def _handle_shared_imports(self, line: str, stripped: str) -> bool:
        """Handle shared import detection and return True if line was processed."""
        # Check for shared configuration imports marker
        if "=== SHARED CONFIGURATION IMPORTS ===" in stripped:
            self.in_shared_imports_section = True
            return True

        # Check for shared configuration imports (individual lines)
        if self._is_shared_import_line(stripped):
            self.shared_imports.append(line)
            return True

        # If we're in the shared imports section, treat everything as shared imports
        if self.in_shared_imports_section and self.in_import_block:
            self.shared_imports.append(line)
            return True

        return False

    def _categorize_content_line(self, line: str) -> None:
        """Categorize a content line into the appropriate section."""
        if self.in_import_block:
            self.import_lines.append(line)
        elif self.in_configuration_block:
            self.configuration_lines.append(line)
        elif self.in_function_block:
            self.function_lines.append(line)
        elif self.current_section == "header":
            self.header_lines.append(line)

    def _is_shared_import_line(self, line: str) -> bool:
        """Check if a line is a shared configuration import."""
        patterns = [
            r"from \.shared_configuration import",
            r"import shared_configuration",
            r"from shared_configuration import",
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def build_extracted_content(self) -> ExtractedContent:
        """Build and return the final ExtractedContent object."""
        return ExtractedContent(
            header="\n".join(self.header_lines),
            imports="\n".join(self.import_lines),
            configuration_classes="\n".join(self.configuration_lines),
            functions="\n".join(self.function_lines),
            shared_imports=self.shared_imports,
        )


class DeploymentMarkerSystem:
    """Core marker processing system for Lambda deployment."""

    # Standard deployment markers
    MARKERS = {
        "IMPORT_BLOCK_START": (
            "# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮"
        ),
        "IMPORT_BLOCK_END": (
            "# ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯"
        ),
        "CONFIGURATION_CLASSES_START": (
            "# ╭─────────────────── CONFIGURATION_CLASSES_START ───────────────────╮"
        ),
        "CONFIGURATION_CLASSES_END": (
            "# ╰─────────────────── CONFIGURATION_CLASSES_END ─────────────────────╯"
        ),
        "FUNCTION_BLOCK_START": (
            "# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮"
        ),
        "FUNCTION_BLOCK_END": (
            "# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯"
        ),
    }

    # Shared configuration patterns
    SHARED_IMPORT_PATTERNS = [
        r"from \.shared_configuration import",
        r"import shared_configuration",
        r"from shared_configuration import",
    ]

    SHARED_IMPORT_MARKER = "# === SHARED CONFIGURATION IMPORTS ==="

    def __init__(self, logger: logging.Logger | None = None):
        self._logger = logger or logging.getLogger(__name__)

    def validate_markers(self, file_path: Path) -> MarkerValidationResult:
        """
        Validate that a file has proper deployment markers.

        Args:
            file_path: Path to the file to validate

        Returns:
            MarkerValidationResult with validation status and details
        """
        issues: list[str] = []
        marker_positions: dict[str, int] = {}

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            issues.append(f"Failed to read file: {e}")
            return MarkerValidationResult(False, issues, marker_positions)

        lines = content.split("\n")

        # Check for required markers (excluding shared_configuration.py)
        required_markers = [
            "IMPORT_BLOCK_START",
            "IMPORT_BLOCK_END",
            "FUNCTION_BLOCK_START",
            "FUNCTION_BLOCK_END",
        ]

        if file_path.name == "shared_configuration.py":
            # Shared config needs configuration class and function markers
            required_markers = [
                "CONFIGURATION_CLASSES_START",
                "CONFIGURATION_CLASSES_END",
                "FUNCTION_BLOCK_START",
                "FUNCTION_BLOCK_END",
            ]

        # Validate marker presence and count
        for marker in required_markers:
            count = content.count(marker)
            if count == 0:
                issues.append(f"Missing required marker: {marker}")
            elif count > 1:
                issues.append(f"Expected 1 {marker}, found {count}")
            else:
                # Find marker position
                for i, line in enumerate(lines):
                    if marker in line:
                        marker_positions[marker] = i
                        break

        # Validate visual formatting
        self._validate_marker_formatting(lines, issues)

        # Validate shared configuration imports (if applicable)
        if file_path.name != "shared_configuration.py":
            self._validate_shared_imports(content, issues)

        # Validate marker order
        self._validate_marker_order(marker_positions, issues)

        is_valid = len(issues) == 0
        return MarkerValidationResult(is_valid, issues, marker_positions)

    def extract_content(self, file_path: Path) -> ExtractedContent:
        """
        Extract content using deployment markers.

        Args:
            file_path: Path to the file to process

        Returns:
            ExtractedContent with extracted sections
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            self._logger.error("Failed to read file %s: %s", file_path, e)
            return ExtractedContent("", "", "", "", [])

        lines = content.split("\n")
        return self._process_content_lines(lines)

    def _process_content_lines(self, lines: list[str]) -> ExtractedContent:
        """Process file lines and extract content by sections."""
        extractor = _ContentExtractor()

        for line in lines:
            extractor.process_line(line)

        return extractor.build_extracted_content()

    def _validate_marker_formatting(self, lines: list[str], issues: list[str]) -> None:
        """Validate visual consistency of marker formatting."""
        for line in lines:
            stripped = line.strip()

            if "IMPORT_BLOCK_START" in stripped or "FUNCTION_BLOCK_START" in stripped:
                if not stripped.startswith("# ╭") or not stripped.endswith("╮"):
                    issues.append(
                        f"START marker doesn't use proper visual brackets: {stripped}"
                    )

            elif (
                "IMPORT_BLOCK_END" in stripped or "FUNCTION_BLOCK_END" in stripped
            ) and (not stripped.startswith("# ╰") or not stripped.endswith("╯")):
                issues.append(
                    f"END marker doesn't use proper visual brackets: {stripped}"
                )

    def _validate_shared_imports(self, content: str, issues: list[str]) -> None:
        """Validate shared configuration import identification."""
        has_shared_imports = any(
            re.search(pattern, content) for pattern in self.SHARED_IMPORT_PATTERNS
        )

        if has_shared_imports and self.SHARED_IMPORT_MARKER not in content:
            issues.append("Missing shared configuration import identification comment")

    def _validate_marker_order(
        self, positions: dict[str, int], issues: list[str]
    ) -> None:
        """Validate that markers appear in the correct order."""
        if (
            "IMPORT_BLOCK_START" in positions
            and "IMPORT_BLOCK_END" in positions
            and positions["IMPORT_BLOCK_START"] >= positions["IMPORT_BLOCK_END"]
        ):
            issues.append("IMPORT_BLOCK_START must come before IMPORT_BLOCK_END")

        if (
            "FUNCTION_BLOCK_START" in positions
            and "FUNCTION_BLOCK_END" in positions
            and positions["FUNCTION_BLOCK_START"] >= positions["FUNCTION_BLOCK_END"]
        ):
            issues.append("FUNCTION_BLOCK_START must come before FUNCTION_BLOCK_END")

        # Import blocks should come before function blocks
        if (
            "IMPORT_BLOCK_END" in positions
            and "FUNCTION_BLOCK_START" in positions
            and positions["IMPORT_BLOCK_END"] >= positions["FUNCTION_BLOCK_START"]
        ):
            issues.append("Import blocks must come before function blocks")

    def _is_shared_import_line(self, line: str) -> bool:
        """Check if a line is a shared configuration import."""
        return any(re.search(pattern, line) for pattern in self.SHARED_IMPORT_PATTERNS)

    def get_marker_template(self, marker_type: str) -> str:
        """
        Get the standard template for a marker.

        Args:
            marker_type: Type of marker (IMPORT_BLOCK_START, etc.)

        Returns:
            Standard marker template string
        """
        return self.MARKERS.get(marker_type, "")

    def create_marked_section(self, marker_type: str, content: str) -> str:
        """
        Create a properly marked section with content.

        Args:
            marker_type: Type of marker (IMPORT_BLOCK_START, etc.)
            content: Content to wrap with markers

        Returns:
            Content wrapped with proper start/end markers
        """
        if marker_type.endswith("_START"):
            start_marker = self.MARKERS.get(marker_type, "")
            end_marker_type = marker_type.replace("_START", "_END")
            end_marker = self.MARKERS.get(end_marker_type, "")

            return f"{start_marker}\n{content}\n{end_marker}"

        return content
