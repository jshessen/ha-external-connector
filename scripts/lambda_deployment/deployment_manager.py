"""
Refactored Lambda Deployment Manager

This module provides the refactored version of the deployment manager,
addressing all code quality issues identified in the original implementation.

Improvements:
- Decomposed complex functions into single-responsibility helpers
- Created Pydantic configuration objects for parameter management
- Implemented secure error handling and input validation
- Optimized import parsing efficiency with set-based lookups
- Reduced nested blocks through better control flow
- Enhanced performance with efficient data structures
"""

import ast
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, validator

# Configure logging with lazy formatting
logger = logging.getLogger(__name__)


class ImportType(str, Enum):
    """Types of imports for categorization"""
    STANDARD_LIBRARY = "standard_library"
    THIRD_PARTY = "third_party"
    LOCAL_IMPORT = "local_import"
    SHARED_CONFIG = "shared_config"
    RELATIVE_IMPORT = "relative_import"


class ImportGroup(BaseModel):
    """Import group classification with validation"""
    import_type: ImportType
    module_name: str
    import_names: list[str] = Field(default_factory=list)
    original_line: str
    line_number: int

    @validator('module_name')
    def validate_module_name(cls, v):
        """Validate module name is not empty"""
        if not v or not v.strip():
            raise ValueError("Module name cannot be empty")
        return v.strip()


class MarkerValidationResult(BaseModel):
    """Result of marker validation with comprehensive details"""
    is_valid: bool
    file_path: str
    missing_markers: list[str] = Field(default_factory=list)
    orphaned_code: list[str] = Field(default_factory=list)
    marker_issues: list[str] = Field(default_factory=list)
    performance_metrics: dict[str, float] = Field(default_factory=dict)


class DeploymentConfig(BaseModel):
    """Configuration object for deployment parameters (R0917 fix)"""
    source_dir: Path
    deployment_dir: Path
    shared_module: str = "shared_configuration"
    lambda_functions: list[str] = Field(default_factory=lambda: [
        "oauth_gateway.py",
        "smart_home_bridge.py",
        "configuration_manager.py"
    ])
    verbose: bool = False
    force_rebuild: bool = False
    validate_syntax: bool = True
    backup_existing: bool = True

    @validator('source_dir', 'deployment_dir')
    def validate_paths(cls, v):
        """Validate paths exist or can be created"""
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValueError(f"Cannot create directory {path}: {e}") from e
        return path


class ImportClassifier:
    """Efficient import classification using set-based lookups (performance fix)"""

    def __init__(self):
        # Use sets for O(1) lookup instead of linear search
        self.standard_library_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'logging', 'typing',
            'pathlib', 'ast', 'shutil', 'configparser', 'enum', 'collections',
            'functools', 'itertools', 'operator', 're', 'string', 'textwrap',
            'unicodedata', 'io', 'tempfile', 'glob', 'pickle', 'shelve',
            'dbm', 'sqlite3', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
            'csv', 'html', 'xml', 'urllib', 'http', 'email', 'hashlib',
            'hmac', 'secrets', 'ssl', 'socket', 'threading', 'multiprocessing',
            'subprocess', 'signal', 'sched', 'queue', 'contextlib', 'warnings',
            'unittest', 'doctest', 'pdb', 'profile', 'timeit', 'traceback'
        }

        self.third_party_modules = {
            'boto3', 'botocore', 'pydantic', 'typer', 'click', 'rich',
            'structlog', 'httpx', 'requests', 'asyncio_throttle', 'pytest',
            'mypy', 'ruff', 'pylint', 'black', 'isort', 'moto', 'fastapi'
        }

    def classify_module(self, module_name: str) -> ImportType:
        """Classify module type efficiently using set lookups"""
        # Extract base module name for classification
        base_module = module_name.split('.')[0]

        if base_module in self.standard_library_modules:
            return ImportType.STANDARD_LIBRARY
        elif base_module in self.third_party_modules:
            return ImportType.THIRD_PARTY
        elif module_name.startswith('.'):
            return ImportType.RELATIVE_IMPORT
        else:
            return ImportType.LOCAL_IMPORT


class ImportParser:
    """Optimized import parser with reduced complexity (R0912/R1702 fix)"""

    def __init__(self, shared_module: str):
        self.shared_module = shared_module
        self.classifier = ImportClassifier()

    def parse_file_imports(self, file_path: Path) -> dict[str, list[ImportGroup]]:
        """Parse imports from file with optimized control flow"""
        import_groups = {
            "standard_library": [],
            "third_party": [],
            "local_imports": [],
            "shared_config": [],
            "relative_imports": [],
            "unclassified": []
        }

        try:
            content = self._read_file_safely(file_path)
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Early exit for non-import lines
                if not self._is_import_line(stripped):
                    if stripped and not stripped.startswith('#'):
                        break  # Stop at first non-import code
                    continue

                # Parse import line
                import_group = self._parse_single_import_line(stripped, line, line_num)
                if import_group:
                    category = self._get_import_category(import_group.import_type)
                    import_groups[category].append(import_group)

            return import_groups

        except Exception as e:
            logger.error("Failed to parse imports from %s: %s", file_path, str(e))
            raise ValueError(f"Import parsing failed for {file_path}") from e

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

    def _is_import_line(self, line: str) -> bool:
        """Check if line is an import statement"""
        return line.startswith(('import ', 'from ')) or not line or line.startswith('#')

    def _parse_single_import_line(
        self, stripped: str, original_line: str, line_num: int
    ) -> ImportGroup | None:
        """Parse a single import line (reduced complexity)"""
        if stripped.startswith('import '):
            return self._parse_simple_import(stripped, original_line, line_num)
        elif stripped.startswith('from '):
            return self._parse_from_import(stripped, original_line, line_num)
        return None

    def _parse_simple_import(
        self, line: str, original_line: str, line_num: int
    ) -> ImportGroup:
        """Parse simple import statement"""
        import_part = line.replace('import ', '').strip()

        # Handle aliases
        if ' as ' in import_part:
            module_name, alias = import_part.split(' as ', 1)
            import_names = [f"{module_name.strip()} as {alias.strip()}"]
            module_name = module_name.strip()
        else:
            module_name = import_part
            import_names = []

        import_type = self.classifier.classify_module(module_name)

        return ImportGroup(
            import_type=import_type,
            module_name=module_name,
            import_names=import_names,
            original_line=original_line,
            line_number=line_num
        )

    def _parse_from_import(
        self, line: str, original_line: str, line_num: int
    ) -> ImportGroup | None:
        """Parse from import statement"""
        if ' import ' not in line:
            return None

        parts = line.split(' import ', 1)
        if len(parts) != 2:
            return None

        module_part = parts[0].replace('from ', '').strip()
        import_part = parts[1].strip()

        # Check for shared configuration import
        if self.shared_module in module_part:
            import_type = ImportType.SHARED_CONFIG
        else:
            import_type = self.classifier.classify_module(module_part)

        import_names = self._parse_import_names(import_part)

        return ImportGroup(
            import_type=import_type,
            module_name=module_part,
            import_names=import_names,
            original_line=original_line,
            line_number=line_num
        )

    def _parse_import_names(self, import_string: str) -> list[str]:
        """Parse import names from import string"""
        # Remove parentheses and split by comma
        cleaned = import_string.strip().replace('(', '').replace(')', '')

        if ',' in cleaned:
            return [name.strip() for name in cleaned.split(',') if name.strip()]
        else:
            return [cleaned] if cleaned else []

    def _get_import_category(self, import_type: ImportType) -> str:
        """Map import type to category key"""
        mapping = {
            ImportType.STANDARD_LIBRARY: "standard_library",
            ImportType.THIRD_PARTY: "third_party",
            ImportType.LOCAL_IMPORT: "local_imports",
            ImportType.SHARED_CONFIG: "shared_config",
            ImportType.RELATIVE_IMPORT: "relative_imports"
        }
        return mapping.get(import_type, "unclassified")


class LambdaMarkerValidator:
    """Enhanced Lambda marker validator with comprehensive validation"""

    def __init__(self, lambda_functions_dir: str):
        self.lambda_functions_dir = Path(lambda_functions_dir)
        self.required_markers = [
            "IMPORT_BLOCK_START",
            "IMPORT_BLOCK_END",
            "FUNCTION_BLOCK_START",
            "FUNCTION_BLOCK_END"
        ]

    def validate_all_lambda_markers(self) -> dict[str, MarkerValidationResult]:
        """Validate markers for all Lambda functions"""
        results = {}

        lambda_files = [
            "oauth_gateway.py",
            "smart_home_bridge.py",
            "configuration_manager.py",
            "shared_configuration.py"
        ]

        for file_name in lambda_files:
            file_path = self.lambda_functions_dir / file_name
            if file_path.exists():
                results[file_name] = self.validate_lambda_markers(file_path)
            else:
                results[file_name] = MarkerValidationResult(
                    is_valid=False,
                    file_path=str(file_path),
                    marker_issues=[f"File not found: {file_path}"]
                )

        return results

    def validate_lambda_markers(self, file_path: Path) -> MarkerValidationResult:
        """Validate Lambda function deployment markers"""
        import time
        start_time = time.time()

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return MarkerValidationResult(
                is_valid=False,
                file_path=str(file_path),
                marker_issues=[f"Failed to read file: {str(e)}"]
            )

        # Check for missing markers
        missing_markers = self._find_missing_markers(content)

        # Check for orphaned code
        orphaned_code = self._find_orphaned_code(content)

        # Check marker format issues
        marker_issues = self._validate_marker_format(content)

        elapsed_time = time.time() - start_time

        is_valid = (
            len(missing_markers) == 0 and
            len(orphaned_code) == 0 and
            len(marker_issues) == 0
        )

        return MarkerValidationResult(
            is_valid=is_valid,
            file_path=str(file_path),
            missing_markers=missing_markers,
            orphaned_code=orphaned_code,
            marker_issues=marker_issues,
            performance_metrics={"validation_time": elapsed_time}
        )

    def _find_missing_markers(self, content: str) -> list[str]:
        """Find missing required markers"""
        missing = []
        for marker in self.required_markers:
            if marker not in content:
                missing.append(marker)
        return missing

    def _find_orphaned_code(self, content: str) -> list[str]:
        """Find code outside marker blocks"""
        orphaned = []
        lines = content.split('\n')
        in_marked_section = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track marker boundaries
            if any(marker in line for marker in self.required_markers):
                in_marked_section = "_START" in line
                continue

            # Check for orphaned code
            if (stripped and
                not stripped.startswith('#') and
                not in_marked_section and
                not self._is_valid_outside_marker(stripped)):
                orphaned.append(f"Line {line_num}: {stripped}")

        return orphaned

    def _validate_marker_format(self, content: str) -> list[str]:
        """Validate marker formatting"""
        issues = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            for marker in self.required_markers:
                if marker in line:
                    if "_START" in marker and not (line.startswith("# ╭") and line.endswith("╮")):
                        issues.append(f"Line {line_num}: Invalid START marker format")
                    elif "_END" in marker and not (line.startswith("# ╰") and line.endswith("╯")):
                        issues.append(f"Line {line_num}: Invalid END marker format")

        return issues

    def _is_valid_outside_marker(self, line: str) -> bool:
        """Check if line is valid outside marker blocks"""
        return (
            line.startswith('"""') or
            line.startswith("'''") or
            line.startswith('import ') or
            line.startswith('from ') or
            line.startswith('__') or
            line.startswith('# ')
        )


class DeploymentFileProcessor:
    """Handles deployment file creation and processing"""

    def __init__(self, config: DeploymentConfig):
        self.config = config

    def create_deployment_file(
        self,
        source_path: Path,
        deployment_path: Path,
        import_analysis: dict[str, list[ImportGroup]]
    ) -> bool:
        """Create deployment file with embedded shared code"""
        try:
            # Backup existing file if requested
            if self.config.backup_existing and deployment_path.exists():
                self._backup_existing_file(deployment_path)

            # Read source content
            source_content = source_path.read_text(encoding='utf-8')

            # Read shared configuration
            shared_content = self._read_shared_configuration()

            # Combine content
            deployment_content = self._combine_source_and_shared(
                source_content, shared_content, import_analysis
            )

            # Validate syntax if requested
            if self.config.validate_syntax:
                self._validate_python_syntax(deployment_content)

            # Write deployment file
            deployment_path.write_text(deployment_content, encoding='utf-8')

            logger.info("Created deployment file: %s", deployment_path)
            return True

        except Exception as e:
            logger.error(
                "Failed to create deployment file %s: %s", deployment_path, str(e)
            )
            return False

    def _backup_existing_file(self, file_path: Path) -> None:
        """Create backup of existing file"""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        shutil.copy2(file_path, backup_path)
        logger.info("Backed up existing file to: %s", backup_path)

    def _read_shared_configuration(self) -> str:
        """Read shared configuration content"""
        shared_path = self.config.source_dir / f"{self.config.shared_module}.py"
        if shared_path.exists():
            return shared_path.read_text(encoding='utf-8')
        return ""

    def _combine_source_and_shared(
        self,
        source_content: str,
        shared_content: str,
        import_analysis: dict[str, list[ImportGroup]]
    ) -> str:
        """Combine source and shared content intelligently"""
        lines = source_content.split('\n')

        # Filter out shared configuration imports
        filtered_lines = [
            line for line in lines
            if not self._is_shared_import_line(line)
        ]

        # Add embedded shared code if available
        if shared_content:
            filtered_lines.extend([
                "",
                "# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===",
                shared_content,
                "# === END EMBEDDED SHARED CODE ===",
                ""
            ])

        return '\n'.join(filtered_lines)

    def _is_shared_import_line(self, line: str) -> bool:
        """Check if line contains shared module import"""
        return (
            f"from .{self.config.shared_module} import" in line or
            f"import {self.config.shared_module}" in line
        )

    def _validate_python_syntax(self, content: str) -> None:
        """Validate Python syntax of generated content"""
        try:
            ast.parse(content)
        except SyntaxError as e:
            logger.error("Syntax error in generated content: %s", str(e))
            raise ValueError(f"Generated content has syntax error: {e}") from e


class DeploymentManager:
    """
    Refactored deployment manager with improved code quality

    Improvements:
    - Reduced function complexity through decomposition
    - Better error handling with exception chaining
    - Performance optimizations with efficient data structures
    - Security improvements with input validation
    - Comprehensive logging with lazy formatting
    """

    def __init__(self, source_dir: str, deployment_dir: str, verbose: bool = False):
        self.config = DeploymentConfig(
            source_dir=Path(source_dir),
            deployment_dir=Path(deployment_dir),
            verbose=verbose
        )
        self.import_parser = ImportParser(self.config.shared_module)
        self.file_processor = DeploymentFileProcessor(self.config)

        # Configure logging
        if verbose:
            logging.basicConfig(level=logging.INFO)

    def process_deployment(self, force_rebuild: bool = False) -> dict[str, Any]:
        """Main deployment processing with comprehensive error handling"""
        self.config.force_rebuild = force_rebuild

        results = {
            "success": False,
            "processed_files": [],
            "errors": [],
            "import_analysis": {},
            "performance_metrics": {}
        }

        import time
        start_time = time.time()

        try:
            self._prepare_deployment_directory()

            for lambda_file in self.config.lambda_functions:
                success = self._process_single_lambda_file(lambda_file, results)
                if not success:
                    logger.warning("Failed to process %s, continuing with others", lambda_file)

            elapsed_time = time.time() - start_time
            results["performance_metrics"]["total_time"] = elapsed_time
            results["success"] = len(results["errors"]) == 0

            logger.info(
                "Deployment completed in %.2f seconds. Success: %s",
                elapsed_time, results["success"]
            )

            return results

        except Exception as e:
            logger.error("Deployment process failed: %s", str(e))
            results["errors"].append(f"Deployment failed: {str(e)}")
            return results

    def _prepare_deployment_directory(self) -> None:
        """Prepare deployment directory"""
        if self.config.force_rebuild and self.config.deployment_dir.exists():
            shutil.rmtree(self.config.deployment_dir)

        self.config.deployment_dir.mkdir(parents=True, exist_ok=True)

    def _process_single_lambda_file(
        self, lambda_file: str, results: dict[str, Any]
    ) -> bool:
        """Process a single Lambda function file"""
        source_path = self.config.source_dir / lambda_file
        deployment_path = self.config.deployment_dir / lambda_file

        if not source_path.exists():
            error_msg = f"Source file not found: {lambda_file}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return False

        try:
            # Parse imports
            import_analysis = self.import_parser.parse_file_imports(source_path)
            results["import_analysis"][lambda_file] = import_analysis

            # Create deployment file
            success = self.file_processor.create_deployment_file(
                source_path, deployment_path, import_analysis
            )

            if success:
                results["processed_files"].append(lambda_file)
                logger.info("Successfully processed: %s", lambda_file)
                return True
            else:
                error_msg = f"Failed to create deployment file: {lambda_file}"
                results["errors"].append(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error processing {lambda_file}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg, exc_info=True)
            return False

    # Maintain compatibility with original API
    def _parse_imports_into_groups(
        self, file_path: Path
    ) -> dict[str, list[ImportGroup]]:
        """Compatibility method that delegates to optimized parser"""
        return self.import_parser.parse_file_imports(file_path)

    def _is_standard_library(self, module_name: str) -> bool:
        """Compatibility method using optimized classifier"""
        return (
            self.import_parser.classifier.classify_module(module_name)
            == ImportType.STANDARD_LIBRARY
        )

    def _is_third_party_library(self, module_name: str) -> bool:
        """Compatibility method using optimized classifier"""
        return (
            self.import_parser.classifier.classify_module(module_name)
            == ImportType.THIRD_PARTY
        )

    def validate_lambda_markers(self, file_path: Path) -> MarkerValidationResult:
        """Validate Lambda markers using enhanced validator"""
        validator = LambdaMarkerValidator(str(self.config.source_dir))
        return validator.validate_lambda_markers(file_path)
