"""
Deployment Marker System

This module provides comprehensive marker processing for Lambda deployment automation.
Handles marker detection, validation, content extraction, and synchronization across
Lambda functions with proper error handling and performance optimization.

Features:
- Advanced marker pattern recognition and validation
- Content extraction between marker boundaries
- Marker format validation and standardization  
- Performance-optimized processing with O(1) lookups
- Comprehensive error handling and logging
"""

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Configure logging with lazy formatting
logger = logging.getLogger(__name__)


class MarkerType(str, Enum):
    """Types of deployment markers"""
    IMPORT_BLOCK_START = "IMPORT_BLOCK_START"
    IMPORT_BLOCK_END = "IMPORT_BLOCK_END"
    FUNCTION_BLOCK_START = "FUNCTION_BLOCK_START"
    FUNCTION_BLOCK_END = "FUNCTION_BLOCK_END"
    DEPLOYMENT_BLOCK_START = "DEPLOYMENT_BLOCK_START"
    DEPLOYMENT_BLOCK_END = "DEPLOYMENT_BLOCK_END"
    TRANSFER_BLOCK_START = "TRANSFER_BLOCK_START"
    TRANSFER_BLOCK_END = "TRANSFER_BLOCK_END"


class MarkerValidationIssue(BaseModel):
    """Represents a marker validation issue"""
    line_number: int
    issue_type: str
    marker_type: str
    description: str
    severity: str = Field(default="error")

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level"""
        valid_severities = {"error", "warning", "info"}
        if v not in valid_severities:
            raise ValueError(f"Severity must be one of: {valid_severities}")
        return v


class MarkerBlock(BaseModel):
    """Represents a marker block with content"""
    start_marker: MarkerType
    end_marker: MarkerType
    start_line: int
    end_line: int
    content: list[str] = Field(default_factory=list)
    is_valid: bool = True
    issues: list[MarkerValidationIssue] = Field(default_factory=list)


class DeploymentMarkerSystem:
    """
    Advanced marker processing system for Lambda deployment automation
    
    Provides comprehensive marker detection, validation, and content extraction
    with performance optimization and detailed error reporting.
    """

    def __init__(self):
        """Initialize marker system with optimized lookups"""
        self.marker_patterns = self._build_marker_patterns()
        self.required_marker_pairs = self._build_required_pairs()
        self.marker_format_validators = self._build_format_validators()

    def _build_marker_patterns(self) -> dict[str, re.Pattern]:
        """Build optimized regex patterns for marker detection"""
        patterns = {}

        # Start marker patterns with box drawing
        start_pattern = re.compile(
            r'^\s*#\s*╭─+\s*(\w+)_START\s*─+╮\s*$',
            re.IGNORECASE
        )
        patterns['start'] = start_pattern

        # End marker patterns with box drawing
        end_pattern = re.compile(
            r'^\s*#\s*╰─+\s*(\w+)_END\s*─+╯\s*$',
            re.IGNORECASE
        )
        patterns['end'] = end_pattern

        # Transfer block patterns (special case)
        transfer_start = re.compile(
            r'^\s*#\s*╭─+\s*TRANSFER\s+BLOCK\s+START\s*─+╮\s*$',
            re.IGNORECASE
        )
        patterns['transfer_start'] = transfer_start

        transfer_end = re.compile(
            r'^\s*#\s*╰─+\s*TRANSFER\s+BLOCK\s+END\s*─+╯\s*$',
            re.IGNORECASE
        )
        patterns['transfer_end'] = transfer_end

        return patterns

    def _build_required_pairs(self) -> dict[MarkerType, MarkerType]:
        """Build required marker pairs for validation"""
        return {
            MarkerType.IMPORT_BLOCK_START: MarkerType.IMPORT_BLOCK_END,
            MarkerType.FUNCTION_BLOCK_START: MarkerType.FUNCTION_BLOCK_END,
            MarkerType.DEPLOYMENT_BLOCK_START: MarkerType.DEPLOYMENT_BLOCK_END,
            MarkerType.TRANSFER_BLOCK_START: MarkerType.TRANSFER_BLOCK_END,
        }

    def _build_format_validators(self) -> dict[str, callable]:
        """Build format validation functions"""
        def validate_start_format(line: str) -> bool:
            return line.strip().startswith("# ╭") and line.strip().endswith("╮")

        def validate_end_format(line: str) -> bool:
            return line.strip().startswith("# ╰") and line.strip().endswith("╯")

        return {
            'start': validate_start_format,
            'end': validate_end_format
        }

    def detect_markers(self, file_path: Path) -> dict[str, list[tuple[int, str, str]]]:
        """
        Detect all markers in file with line numbers and types
        
        Returns:
            Dict with marker types as keys and list of (line_num, marker_type, line_content)
        """
        try:
            content = self._read_file_safely(file_path)
            lines = content.split('\n')

            detected_markers = {
                'start_markers': [],
                'end_markers': [],
                'all_markers': []
            }

            for line_num, line in enumerate(lines, 1):
                marker_info = self._analyze_line_for_markers(line_num, line)
                if marker_info:
                    marker_type, marker_category = marker_info
                    detected_markers[marker_category].append(
                        (line_num, marker_type, line.strip())
                    )
                    detected_markers['all_markers'].append(
                        (line_num, marker_type, line.strip())
                    )

            return detected_markers

        except Exception as e:
            logger.error("Failed to detect markers in %s: %s", file_path, str(e))
            raise ValueError(f"Marker detection failed for {file_path}") from e

    def _read_file_safely(self, file_path: Path) -> str:
        """Safely read file with proper error handling"""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            logger.error("Unicode decode error in %s: %s", file_path, str(e))
            raise ValueError(f"Cannot decode file {file_path}") from e
        except OSError as e:
            logger.error("Cannot read file %s: %s", file_path, str(e))
            raise ValueError(f"Cannot read file {file_path}") from e

    def _analyze_line_for_markers(self, line_num: int, line: str) -> tuple[str, str] | None:
        """Analyze single line for marker patterns"""
        # Check for transfer block markers first (special handling)
        if self.marker_patterns['transfer_start'].match(line):
            return ("TRANSFER_BLOCK_START", "start_markers")
        if self.marker_patterns['transfer_end'].match(line):
            return ("TRANSFER_BLOCK_END", "end_markers")

        # Check for standard start markers
        start_match = self.marker_patterns['start'].match(line)
        if start_match:
            marker_prefix = start_match.group(1).upper()
            marker_type = f"{marker_prefix}_START"
            return (marker_type, "start_markers")

        # Check for standard end markers
        end_match = self.marker_patterns['end'].match(line)
        if end_match:
            marker_prefix = end_match.group(1).upper()
            marker_type = f"{marker_prefix}_END"
            return (marker_type, "end_markers")

        return None

    def extract_marker_blocks(self, file_path: Path) -> list[MarkerBlock]:
        """
        Extract all marker blocks with content and validation
        
        Returns:
            List of MarkerBlock objects with content and validation status
        """
        try:
            content = self._read_file_safely(file_path)
            lines = content.split('\n')

            markers = self.detect_markers(file_path)
            blocks = []

            # Group markers into blocks
            start_markers = markers['start_markers']
            end_markers = markers['end_markers']

            for start_line, start_type, start_content in start_markers:
                # Find matching end marker
                end_marker_type = self._get_matching_end_marker(start_type)
                end_match = self._find_matching_end_marker(
                    end_markers, end_marker_type, start_line
                )

                if end_match:
                    end_line, end_type, end_content = end_match
                    block_content = lines[start_line:end_line-1]  # Exclude marker lines

                    # Create and validate block
                    marker_block = MarkerBlock(
                        start_marker=MarkerType(start_type),
                        end_marker=MarkerType(end_type),
                        start_line=start_line,
                        end_line=end_line,
                        content=block_content
                    )

                    # Validate block format and content
                    self._validate_marker_block(marker_block, start_content, end_content)
                    blocks.append(marker_block)
                else:
                    # Create incomplete block for missing end marker
                    marker_block = MarkerBlock(
                        start_marker=MarkerType(start_type),
                        end_marker=MarkerType(end_marker_type),
                        start_line=start_line,
                        end_line=-1,
                        content=[],
                        is_valid=False
                    )
                    marker_block.issues.append(
                        MarkerValidationIssue(
                            line_number=start_line,
                            issue_type="missing_end_marker",
                            marker_type=start_type,
                            description=f"Missing end marker {end_marker_type}",
                            severity="error"
                        )
                    )
                    blocks.append(marker_block)

            return blocks

        except Exception as e:
            logger.error("Failed to extract marker blocks from %s: %s", file_path, str(e))
            raise ValueError(f"Marker block extraction failed for {file_path}") from e

    def _get_matching_end_marker(self, start_marker: str) -> str:
        """Get the expected end marker for a start marker"""
        try:
            start_enum = MarkerType(start_marker)
            return self.required_marker_pairs[start_enum].value
        except (ValueError, KeyError):
            # Handle unknown markers by pattern matching
            if start_marker.endswith('_START'):
                return start_marker.replace('_START', '_END')
            return f"{start_marker}_END"

    def _find_matching_end_marker(
        self,
        end_markers: list[tuple[int, str, str]],
        target_type: str,
        after_line: int
    ) -> tuple[int, str, str] | None:
        """Find the first matching end marker after the start line"""
        for line_num, marker_type, content in end_markers:
            if marker_type == target_type and line_num > after_line:
                return (line_num, marker_type, content)
        return None

    def _validate_marker_block(
        self,
        block: MarkerBlock,
        start_content: str,
        end_content: str
    ) -> None:
        """Validate marker block format and content"""
        issues = []

        # Validate start marker format
        if not self.marker_format_validators['start'](start_content):
            issues.append(
                MarkerValidationIssue(
                    line_number=block.start_line,
                    issue_type="invalid_format",
                    marker_type=block.start_marker.value,
                    description="Invalid start marker format",
                    severity="error"
                )
            )

        # Validate end marker format
        if not self.marker_format_validators['end'](end_content):
            issues.append(
                MarkerValidationIssue(
                    line_number=block.end_line,
                    issue_type="invalid_format",
                    marker_type=block.end_marker.value,
                    description="Invalid end marker format",
                    severity="error"
                )
            )

        # Check for empty blocks (might be warning vs error)
        if not block.content or all(not line.strip() for line in block.content):
            issues.append(
                MarkerValidationIssue(
                    line_number=block.start_line,
                    issue_type="empty_block",
                    marker_type=block.start_marker.value,
                    description="Marker block contains no content",
                    severity="warning"
                )
            )

        # Update block validation status
        block.issues.extend(issues)
        block.is_valid = not any(issue.severity == "error" for issue in issues)

    def validate_all_markers(self, file_path: Path) -> dict[str, Any]:
        """
        Comprehensive marker validation for a file
        
        Returns:
            Validation results with detailed analysis
        """
        try:
            blocks = self.extract_marker_blocks(file_path)

            total_blocks = len(blocks)
            valid_blocks = sum(1 for block in blocks if block.is_valid)
            error_count = sum(
                len([issue for issue in block.issues if issue.severity == "error"])
                for block in blocks
            )
            warning_count = sum(
                len([issue for issue in block.issues if issue.severity == "warning"])
                for block in blocks
            )

            # Check for orphaned code (content outside marker blocks)
            orphaned_lines = self._detect_orphaned_code(file_path, blocks)

            return {
                'is_valid': error_count == 0,
                'total_blocks': total_blocks,
                'valid_blocks': valid_blocks,
                'error_count': error_count,
                'warning_count': warning_count,
                'blocks': blocks,
                'orphaned_lines': orphaned_lines,
                'summary': f"{valid_blocks}/{total_blocks} blocks valid, "
                          f"{error_count} errors, {warning_count} warnings"
            }

        except Exception as e:
            logger.error("Failed to validate markers in %s: %s", file_path, str(e))
            return {
                'is_valid': False,
                'error_count': 1,
                'error_message': str(e),
                'blocks': [],
                'orphaned_lines': []
            }

    def _detect_orphaned_code(self, file_path: Path, blocks: list[MarkerBlock]) -> list[dict]:
        """Detect code that exists outside of marker blocks"""
        try:
            content = self._read_file_safely(file_path)
            lines = content.split('\n')

            # Build set of lines that are within marker blocks
            covered_lines = set()
            for block in blocks:
                if block.end_line > 0:  # Valid block with end marker
                    for line_num in range(block.start_line, block.end_line + 1):
                        covered_lines.add(line_num)

            # Find orphaned code lines
            orphaned_lines = []
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Skip empty lines, comments, and covered lines
                if (line_num in covered_lines or
                    not stripped or
                    stripped.startswith('#') or
                    self._is_valid_outside_marker(stripped)):
                    continue

                orphaned_lines.append({
                    'line_number': line_num,
                    'content': line.rstrip(),
                    'severity': 'warning'
                })

            return orphaned_lines

        except Exception as e:
            logger.error("Failed to detect orphaned code in %s: %s", file_path, str(e))
            return []

    def _is_valid_outside_marker(self, line: str) -> bool:
        """Check if line is valid outside marker blocks"""
        # Allow module docstrings, imports, and certain patterns
        return (
            line.startswith(('"""', "'''", 'import ', 'from ')) or
            line.startswith('__') and line.endswith('__') or  # Module attributes
            line in ('', 'pass') or
            line.startswith('# ') or  # Comments
            '=' in line and line.count('=') == 1  # Simple assignments
        )
