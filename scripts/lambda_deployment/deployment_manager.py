"""
Enhanced Lambda Deployment Manager

This module provides the comprehensive deployment manager for Lambda function automation,
integrating marker processing, validation, and deployment generation with enhanced
performance and modular architecture.

Features:
- Modular architecture with integrated marker and validation systems
- Advanced import processing with PEP 8 compliance
- Performance-optimized classification with O(1) lookups
- Comprehensive error handling and recovery mechanisms
- Real-time progress feedback and logging
- Deployment file generation with standardized structure
- Integration with validation and marker systems
"""

import ast
import logging
import shutil
import time
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

try:
    from .marker_system import DeploymentMarkerSystem
    from .validation_system import DeploymentValidationSystem, ValidationType
except ImportError:
    # Handle case where modules are run standalone
    DeploymentMarkerSystem = None
    DeploymentValidationSystem = None
    ValidationType = None

# Configure logging with lazy formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

    @field_validator('module_name')
    @classmethod
    def validate_module_name(cls, v: str) -> str:
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

    @field_validator('source_dir', 'deployment_dir')
    @classmethod
    def validate_paths(cls, v: Any) -> Path:
        """Validate paths exist and are directories"""
        if not isinstance(v, Path):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v


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


class EnhancedDeploymentManager:
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
    Enhanced deployment manager with comprehensive modular architecture
    
    Integrates marker processing, validation, and deployment generation with
    performance optimization and detailed error reporting. Provides complete
    Lambda deployment automation with real-time progress feedback.
    
    Features:
    - Modular architecture with integrated systems
    - Advanced import processing with PEP 8 compliance
    - Performance-optimized O(1) classification
    - Comprehensive error handling and recovery
    - Real-time progress feedback and logging
    - Deployment file generation with standardized structure
    - Infrastructure organization support
    """

    def __init__(self, source_dir: str, deployment_dir: str, verbose: bool = False):
        """Initialize enhanced deployment manager"""
        self.config = DeploymentConfig(
            source_dir=Path(source_dir),
            deployment_dir=Path(deployment_dir),
            verbose=verbose
        )

        # Initialize integrated systems
        self.import_parser = ImportParser(self.config.shared_module)
        self.file_processor = DeploymentFileProcessor(self.config)
        self.marker_system = DeploymentMarkerSystem()
        self.validation_system = DeploymentValidationSystem()

        # Performance tracking
        self.performance_metrics = {
            'total_files_processed': 0,
            'total_processing_time': 0.0,
            'validation_time': 0.0,
            'import_processing_time': 0.0,
            'file_generation_time': 0.0
        }

        # Configure enhanced logging
        self._configure_logging(verbose)

    def _configure_logging(self, verbose: bool) -> None:
        """Configure comprehensive logging with performance tracking"""
        if verbose:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            logger.info("Enhanced deployment manager initialized")
            logger.info("Source directory: %s", self.config.source_dir)
            logger.info("Deployment directory: %s", self.config.deployment_dir)

    def build_deployment(self, force_rebuild: bool = False) -> dict[str, Any]:
        """
        Build complete deployment with comprehensive validation and processing
        
        This is the main entry point for the enhanced deployment system,
        providing complete automation with integrated marker processing,
        validation, and deployment file generation.
        
        Args:
            force_rebuild: Force rebuild of all deployment files
            
        Returns:
            Comprehensive deployment results with detailed metrics
        """
        start_time = time.time()
        self.config.force_rebuild = force_rebuild

        logger.info("Starting enhanced deployment build process")

        # Initialize results tracking
        results = {
            'success': False,
            'processed_files': [],
            'errors': [],
            'warnings': [],
            'performance_metrics': {},
            'validation_results': {},
            'marker_validation': {},
            'infrastructure_status': {}
        }

        try:
            # Phase 1: Discovery and validation
            discovery_results = self._discover_and_validate_files()
            results['validation_results'] = discovery_results

            if discovery_results['critical_errors'] > 0:
                logger.error("Critical validation errors found, aborting deployment")
                results['errors'].extend(discovery_results['error_messages'])
                return results

            # Phase 2: Infrastructure preparation
            infra_results = self._prepare_infrastructure()
            results['infrastructure_status'] = infra_results

            # Phase 3: Process Lambda functions
            processing_results = self._process_lambda_functions()
            results.update(processing_results)

            # Phase 4: Validate deployment integrity
            integrity_results = self._validate_deployment_integrity()
            results['deployment_integrity'] = integrity_results

            # Calculate final metrics
            total_time = time.time() - start_time
            self.performance_metrics['total_processing_time'] = total_time
            results['performance_metrics'] = self.performance_metrics

            # Determine overall success
            results['success'] = (
                len(results['errors']) == 0 and
                processing_results.get('processed_count', 0) > 0 and
                integrity_results.get('is_valid', False)
            )

            # Log completion status
            if results['success']:
                logger.info(
                    "Deployment build completed successfully in %.3fs: %d files processed",
                    total_time,
                    processing_results.get('processed_count', 0)
                )
            else:
                logger.error(
                    "Deployment build failed after %.3fs: %d errors",
                    total_time,
                    len(results['errors'])
                )

            return results

        except Exception as e:
            error_msg = f"Deployment build failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg, exc_info=True)
            return results

    def _discover_and_validate_files(self) -> dict[str, Any]:
        """Discover and validate Lambda function files"""
        validation_start = time.time()

        logger.info("Discovering and validating Lambda function files")

        # Find Python files in source directory
        python_files = list(self.config.source_dir.rglob("*.py"))
        lambda_files = [f for f in python_files if self._is_lambda_function_file(f)]

        logger.info("Found %d Python files, %d appear to be Lambda functions",
                   len(python_files), len(lambda_files))

        # Validate each Lambda function file
        validation_results = {
            'total_files': len(lambda_files),
            'valid_files': 0,
            'files_with_warnings': 0,
            'files_with_errors': 0,
            'critical_errors': 0,
            'error_messages': [],
            'warning_messages': [],
            'file_details': {}
        }

        for lambda_file in lambda_files:
            file_result = self._validate_single_file(lambda_file)
            validation_results['file_details'][str(lambda_file)] = file_result

            if file_result['critical_count'] > 0:
                validation_results['critical_errors'] += 1
                validation_results['error_messages'].extend(file_result['error_messages'])
            elif file_result['error_count'] > 0:
                validation_results['files_with_errors'] += 1
                validation_results['error_messages'].extend(file_result['error_messages'])
            elif file_result['warning_count'] > 0:
                validation_results['files_with_warnings'] += 1
                validation_results['warning_messages'].extend(file_result['warning_messages'])
            else:
                validation_results['valid_files'] += 1

        validation_time = time.time() - validation_start
        self.performance_metrics['validation_time'] = validation_time

        logger.info(
            "Validation completed in %.3fs: %d valid, %d with warnings, %d with errors",
            validation_time,
            validation_results['valid_files'],
            validation_results['files_with_warnings'],
            validation_results['files_with_errors']
        )

        return validation_results

    def _validate_single_file(self, file_path: Path) -> dict[str, Any]:
        """Validate a single Lambda function file comprehensively"""
        try:
            # Run comprehensive validation
            validation_result = self.validation_system.validate_file(
                file_path,
                [ValidationType.SYNTAX, ValidationType.IMPORTS,
                 ValidationType.MARKERS, ValidationType.DEPLOYMENT]
            )

            # Run marker validation
            marker_result = self.marker_system.validate_all_markers(file_path)

            return {
                'is_valid': validation_result.is_valid and marker_result['is_valid'],
                'critical_count': validation_result.critical_count,
                'error_count': validation_result.error_count,
                'warning_count': validation_result.warning_count,
                'validation_time': validation_result.validation_time,
                'marker_blocks': marker_result.get('total_blocks', 0),
                'orphaned_lines': len(marker_result.get('orphaned_lines', [])),
                'error_messages': [issue.message for issue in validation_result.issues
                                 if issue.level.value in ['critical', 'error']],
                'warning_messages': [issue.message for issue in validation_result.issues
                                   if issue.level.value == 'warning']
            }

        except Exception as e:
            logger.error("Failed to validate %s: %s", file_path, str(e))
            return {
                'is_valid': False,
                'critical_count': 1,
                'error_count': 0,
                'warning_count': 0,
                'validation_time': 0.0,
                'error_messages': [f"Validation failed: {str(e)}"]
            }

    def _prepare_infrastructure(self) -> dict[str, Any]:
        """Prepare deployment infrastructure directories"""
        logger.info("Preparing deployment infrastructure")

        try:
            # Create deployment structure based on configuration
            if self.config.deployment_structure == "nested":
                return self._create_nested_structure()
            else:
                return self._create_flat_structure()

        except Exception as e:
            logger.error("Failed to prepare infrastructure: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _create_nested_structure(self) -> dict[str, Any]:
        """Create nested deployment structure (function/lambda_function.py)"""
        created_dirs = []

        for lambda_file in self.config.lambda_functions:
            function_name = Path(lambda_file).stem
            function_dir = self.config.deployment_dir / function_name

            try:
                function_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(function_dir))
                logger.info("Created function directory: %s", function_dir)

            except OSError as e:
                logger.error("Failed to create directory %s: %s", function_dir, str(e))
                return {'success': False, 'error': f"Directory creation failed: {str(e)}"}

        return {
            'success': True,
            'structure': 'nested',
            'created_directories': created_dirs
        }

    def _create_flat_structure(self) -> dict[str, Any]:
        """Create flat deployment structure (function.py)"""
        try:
            self.config.deployment_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Prepared flat deployment directory: %s", self.config.deployment_dir)

            return {
                'success': True,
                'structure': 'flat',
                'deployment_directory': str(self.config.deployment_dir)
            }

        except OSError as e:
            logger.error("Failed to prepare deployment directory: %s", str(e))
            return {'success': False, 'error': str(e)}

    def _process_lambda_functions(self) -> dict[str, Any]:
        """Process all Lambda functions with enhanced error handling"""
        process_start = time.time()

        logger.info("Processing Lambda functions for deployment")

        results = {
            'processed_count': 0,
            'failed_count': 0,
            'processed_files': [],
            'failed_files': [],
            'errors': []
        }

        lambda_files = [
            f for f in self.config.source_dir.rglob("*.py")
            if self._is_lambda_function_file(f)
        ]

        for lambda_file in lambda_files:
            try:
                success = self._process_single_lambda_file(lambda_file)

                if success:
                    results['processed_count'] += 1
                    results['processed_files'].append(str(lambda_file))
                    logger.info("Successfully processed: %s", lambda_file.name)
                else:
                    results['failed_count'] += 1
                    results['failed_files'].append(str(lambda_file))
                    logger.warning("Failed to process: %s", lambda_file.name)

            except Exception as e:
                error_msg = f"Error processing {lambda_file}: {str(e)}"
                results['errors'].append(error_msg)
                results['failed_count'] += 1
                results['failed_files'].append(str(lambda_file))
                logger.error(error_msg, exc_info=True)

        process_time = time.time() - process_start
        self.performance_metrics['file_generation_time'] = process_time
        self.performance_metrics['total_files_processed'] = results['processed_count']

        logger.info(
            "Lambda function processing completed in %.3fs: %d processed, %d failed",
            process_time,
            results['processed_count'],
            results['failed_count']
        )

        return results

    def _process_single_lambda_file(self, lambda_file: Path) -> bool:
        """Process a single Lambda function file with comprehensive handling"""
        try:
            # Parse imports
            import_start = time.time()
            import_analysis = self.import_parser.parse_file_imports(lambda_file)
            import_time = time.time() - import_start
            self.performance_metrics['import_processing_time'] += import_time

            # Generate deployment file
            deployment_path = self._get_deployment_path(lambda_file)

            success = self.file_processor.create_deployment_file(
                lambda_file, deployment_path, import_analysis
            )

            if success:
                logger.info("Generated deployment file: %s", deployment_path)
                return True
            else:
                logger.error("Failed to generate deployment file for: %s", lambda_file)
                return False

        except Exception as e:
            logger.error("Error processing %s: %s", lambda_file, str(e))
            return False

    def _get_deployment_path(self, source_file: Path) -> Path:
        """Get deployment path based on configuration structure"""
        function_name = source_file.stem

        if self.config.deployment_structure == "nested":
            return self.config.deployment_dir / function_name / "lambda_function.py"
        else:
            return self.config.deployment_dir / f"{function_name}.py"

    def _validate_deployment_integrity(self) -> dict[str, Any]:
        """Validate deployment integrity and completeness"""
        logger.info("Validating deployment integrity")

        try:
            deployment_files = list(self.config.deployment_dir.rglob("*.py"))

            integrity_results = {
                'is_valid': True,
                'deployment_files_count': len(deployment_files),
                'validation_issues': [],
                'syntax_valid': True,
                'all_markers_valid': True
            }

            # Validate each deployment file
            for deployment_file in deployment_files:
                try:
                    # Check syntax
                    content = deployment_file.read_text(encoding='utf-8')
                    ast.parse(content, filename=str(deployment_file))

                    # Validate markers if enabled
                    if self.config.enable_marker_validation:
                        marker_result = self.marker_system.validate_all_markers(deployment_file)
                        if not marker_result['is_valid']:
                            integrity_results['all_markers_valid'] = False
                            integrity_results['validation_issues'].append(
                                f"Marker validation failed for {deployment_file.name}"
                            )

                except SyntaxError as e:
                    integrity_results['syntax_valid'] = False
                    integrity_results['validation_issues'].append(
                        f"Syntax error in {deployment_file.name}: {e.msg}"
                    )
                except Exception as e:
                    integrity_results['validation_issues'].append(
                        f"Validation error in {deployment_file.name}: {str(e)}"
                    )

            # Overall validity
            integrity_results['is_valid'] = (
                integrity_results['syntax_valid'] and
                integrity_results['all_markers_valid'] and
                len(integrity_results['validation_issues']) == 0
            )

            logger.info(
                "Deployment integrity validation: %s (%d files, %d issues)",
                "PASSED" if integrity_results['is_valid'] else "FAILED",
                integrity_results['deployment_files_count'],
                len(integrity_results['validation_issues'])
            )

            return integrity_results

        except Exception as e:
            logger.error("Deployment integrity validation failed: %s", str(e))
            return {
                'is_valid': False,
                'error': str(e)
            }

    def _is_lambda_function_file(self, file_path: Path) -> bool:
        """Check if file is a Lambda function with enhanced detection"""
        # Skip test files and __init__.py files
        if (file_path.name.startswith('test_') or
            file_path.name == '__init__.py' or
            'test' in str(file_path).lower()):
            return False

        try:
            content = file_path.read_text(encoding='utf-8')

            # Enhanced Lambda function detection
            lambda_indicators = [
                'lambda_handler',
                'def handler(',
                'aws_lambda',
                'boto3',
                'IMPORT_BLOCK_START',
                'FUNCTION_BLOCK_START',
                'event',
                'context'
            ]

            content_lower = content.lower()
            indicators_found = sum(1 for indicator in lambda_indicators
                                 if indicator.lower() in content_lower)

            return indicators_found >= 2

        except Exception:
            return False

    # Maintain compatibility with original API
    def process_deployment(self, force_rebuild: bool = False) -> dict[str, Any]:
        """Compatibility method that delegates to enhanced build_deployment"""
        return self.build_deployment(force_rebuild)
    # Maintain compatibility with original API methods
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

    def validate_lambda_markers(self, file_path: Path) -> dict[str, Any]:
        """Validate Lambda markers using enhanced marker system"""
        return self.marker_system.validate_all_markers(file_path)
