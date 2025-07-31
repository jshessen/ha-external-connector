"""
Deployment Validation System

This module provides comprehensive validation framework for Lambda deployment automation.
Handles file validation, syntax checking, import validation, and deployment verification
with detailed reporting and performance optimization.

Features:
- Multi-level validation framework (syntax, imports, markers, deployment)
- Performance-optimized validation with parallel processing support
- Comprehensive error reporting with severity levels
- Extensible validation rule system
- Integration with marker system for complete validation
"""

import ast
import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .marker_system import DeploymentMarkerSystem

# Configure logging with lazy formatting
logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation level severity"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(str, Enum):
    """Types of validation checks"""
    SYNTAX = "syntax"
    IMPORTS = "imports"
    MARKERS = "markers"
    DEPLOYMENT = "deployment"
    PERFORMANCE = "performance"
    SECURITY = "security"


class ValidationIssue(BaseModel):
    """Represents a validation issue"""
    validation_type: ValidationType
    level: ValidationLevel
    line_number: int = Field(default=0)
    column_number: int = Field(default=0)
    message: str
    code: str = Field(default="")
    file_path: str = Field(default="")
    suggestion: str = Field(default="")

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate severity level"""
        if v not in ValidationLevel.__members__.values():
            raise ValueError(f"Level must be one of: {list(ValidationLevel)}")
        return v


class ValidationResult(BaseModel):
    """Comprehensive validation result"""
    is_valid: bool
    file_path: str
    validation_time: float = Field(default=0.0)
    total_issues: int = Field(default=0)
    critical_count: int = Field(default=0)
    error_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    info_count: int = Field(default=0)
    issues: list[ValidationIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add validation issue and update counts"""
        self.issues.append(issue)
        self.total_issues += 1

        if issue.level == ValidationLevel.CRITICAL:
            self.critical_count += 1
        elif issue.level == ValidationLevel.ERROR:
            self.error_count += 1
        elif issue.level == ValidationLevel.WARNING:
            self.warning_count += 1
        elif issue.level == ValidationLevel.INFO:
            self.info_count += 1

        # Update overall validity
        self.is_valid = self.critical_count == 0 and self.error_count == 0

    def get_summary(self) -> str:
        """Get human-readable validation summary"""
        if self.is_valid:
            status = "✅ VALID"
        else:
            status = "❌ INVALID"

        return (
            f"{status} - {self.total_issues} issues "
            f"(Critical: {self.critical_count}, Errors: {self.error_count}, "
            f"Warnings: {self.warning_count}, Info: {self.info_count})"
        )


class DeploymentValidationSystem:
    """
    Comprehensive validation system for Lambda deployment automation
    
    Provides multi-level validation including syntax, imports, markers,
    and deployment readiness with detailed reporting and performance metrics.
    """

    def __init__(self):
        """Initialize validation system with optimized components"""
        self.marker_system = DeploymentMarkerSystem()
        self.standard_library_modules = self._build_standard_library_set()
        self.validation_rules = self._build_validation_rules()

    def _build_standard_library_set(self) -> set[str]:
        """Build comprehensive set of Python standard library modules"""
        return {
            # Core modules
            'os', 'sys', 'time', 'datetime', 'json', 'logging', 'configparser',
            'argparse', 'optparse', 'getopt', 'tempfile', 'shutil', 'glob',
            'fnmatch', 'linecache', 'fileinput', 'stat', 'filecmp', # Data structures and algorithms
            'collections', 'heapq', 'bisect', 'array', 'weakref', 'copy',
            'pprint', 'reprlib', 'enum', 'types', 'functools', 'itertools',
            'operator', 'contextlib', 'abc', 'atexit', 'traceback', 'inspect',

            # Text processing
            're', 'string', 'difflib', 'textwrap', 'unicodedata', 'codecs',
            'encodings', 'locale', 'calendar',

            # Binary data and parsing
            'struct', 'pickle', 'copyreg', 'shelve', 'marshal', 'dbm',
            'sqlite3', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',

            # File formats
            'csv', 'netrc', 'xdrlib', 'plistlib',

            # Cryptographic services
            'hashlib', 'hmac', 'secrets', 'ssl',

            # Generic OS services
            'io', 'errno', 'platform', 'ctypes', 'threading', 'multiprocessing',
            'concurrent', 'subprocess', 'sched', 'queue', 'dummy_threading',
            '_thread', '_dummy_thread', 'signal',

            # Internet protocols and formats
            'socket', 'email', 'mailcap', 'mailbox', 'mimetypes',
            'base64', 'binhex', 'binascii', 'quopri', 'uu',

            # Structured markup
            'html', 'xml', 'urllib', 'http', 'ftplib', 'poplib',
            'imaplib', 'nntplib', 'smtplib', 'smtpd', 'telnetlib',
            'uuid', 'socketserver', 'xmlrpc',

            # Multimedia
            'audioop', 'aifc', 'sunau', 'wave', 'chunk', 'colorsys',
            'imghdr', 'sndhdr', 'ossaudiodev',

            # Internationalization
            'gettext', # Program frameworks
            'turtle', 'cmd', 'shlex',

            # Graphical user interfaces
            'tkinter', # Development tools
            'typing', 'pydoc', 'doctest', 'unittest', 'test', '2to3',
            'lib2to3', 'py_compile', 'compileall', 'dis', 'pickletools',

            # Debugging and profiling
            'pdb', 'profile', 'pstats', 'timeit', 'trace', 'tracemalloc',
            'faulthandler',

            # Software packaging
            'distutils', 'ensurepip', 'venv', 'zipapp',

            # Runtime services
            'sysconfig', 'builtins', '__main__', 'warnings',
            'dataclasses', 'gc', 'site', 'fpectl',

            # Custom Python interpreters
            'code', 'codeop',

            # Importing modules
            'zipimport', 'pkgutil', 'modulefinder', 'runpy', 'importlib',

            # Python language services
            'parser', 'ast', 'symtable', 'symbol', 'token', 'keyword',
            'tokenize', 'tabnanny', 'pyclbr', # Miscellaneous services
            'formatter', 'msilib', 'msvcrt', 'winreg', 'winsound'
        }

    def _build_validation_rules(self) -> dict[str, callable]:
        """Build validation rule functions"""
        return {
            'syntax': self._validate_syntax,
            'imports': self._validate_imports,
            'markers': self._validate_markers,
            'deployment': self._validate_deployment_readiness,
            'performance': self._validate_performance,
            'security': self._validate_security
        }

    def validate_file(
        self,
        file_path: Path,
        validation_types: list[ValidationType] | None = None
    ) -> ValidationResult:
        """
        Comprehensive file validation with specified validation types
        
        Args:
            file_path: Path to file to validate
            validation_types: List of validation types to run (all if None)
            
        Returns:
            ValidationResult with comprehensive analysis
        """
        start_time = time.time()

        result = ValidationResult(
            file_path=str(file_path),
            is_valid=True
        )

        # Default to all validation types if none specified
        if validation_types is None:
            validation_types = list(ValidationType)

        try:
            # Run each requested validation type
            for validation_type in validation_types:
                if validation_type.value in self.validation_rules:
                    validator_func = self.validation_rules[validation_type.value]
                    validator_func(file_path, result)
                else:
                    result.add_issue(
                        ValidationIssue(
                            validation_type=ValidationType.DEPLOYMENT,
                            level=ValidationLevel.WARNING,
                            message=f"Unknown validation type: {validation_type}",
                            code="UNKNOWN_VALIDATION_TYPE"
                        )
                    )

            # Calculate validation time
            result.validation_time = time.time() - start_time

            # Add performance metadata
            result.metadata.update({
                'validation_types': [vt.value for vt in validation_types],
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
                'line_count': self._count_lines(file_path) if file_path.exists() else 0
            })

            logger.info(
                "Validated %s in %.3fs: %s",
                file_path.name,
                result.validation_time,
                result.get_summary()
            )

            return result

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.DEPLOYMENT,
                    level=ValidationLevel.CRITICAL,
                    message=f"Validation failed: {str(e)}",
                    code="VALIDATION_EXCEPTION"
                )
            )
            result.validation_time = time.time() - start_time
            logger.error("Validation failed for %s: %s", file_path, str(e))
            return result

    def _validate_syntax(self, file_path: Path, result: ValidationResult) -> None:
        """Validate Python syntax"""
        try:
            if not file_path.exists():
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.SYNTAX,
                        level=ValidationLevel.CRITICAL,
                        message="File does not exist",
                        code="FILE_NOT_FOUND",
                        file_path=str(file_path)
                    )
                )
                return

            content = file_path.read_text(encoding='utf-8')

            # Parse AST to check syntax
            ast.parse(content, filename=str(file_path))

            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.SYNTAX,
                    level=ValidationLevel.INFO,
                    message="Syntax validation passed",
                    code="SYNTAX_OK"
                )
            )

        except SyntaxError as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.SYNTAX,
                    level=ValidationLevel.CRITICAL,
                    line_number=e.lineno or 0,
                    column_number=e.offset or 0,
                    message=f"Syntax error: {e.msg}",
                    code="SYNTAX_ERROR",
                    suggestion="Check Python syntax and fix errors"
                )
            )
        except UnicodeDecodeError as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.SYNTAX,
                    level=ValidationLevel.CRITICAL,
                    message=f"Unicode decode error: {str(e)}",
                    code="ENCODING_ERROR",
                    suggestion="Ensure file is saved with UTF-8 encoding"
                )
            )

    def _validate_imports(self, file_path: Path, result: ValidationResult) -> None:
        """Validate import statements and dependencies"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))

            imports_found = []
            unknown_modules = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_found.append(alias.name)
                        if not self._is_known_module(alias.name):
                            unknown_modules.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_found.append(node.module)
                        if not self._is_known_module(node.module):
                            unknown_modules.append(node.module)

            # Report unknown modules as warnings
            for module in unknown_modules:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.IMPORTS,
                        level=ValidationLevel.WARNING,
                        message=f"Unknown module: {module}",
                        code="UNKNOWN_MODULE",
                        suggestion="Verify module is installed or available"
                    )
                )

            # Add import summary
            result.metadata['imports_found'] = imports_found
            result.metadata['unknown_modules'] = unknown_modules

            if not unknown_modules:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.IMPORTS,
                        level=ValidationLevel.INFO,
                        message=f"All {len(imports_found)} imports are recognized",
                        code="IMPORTS_OK"
                    )
                )

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.IMPORTS,
                    level=ValidationLevel.ERROR,
                    message=f"Import validation failed: {str(e)}",
                    code="IMPORT_VALIDATION_ERROR"
                )
            )

    def _validate_markers(self, file_path: Path, result: ValidationResult) -> None:
        """Validate deployment markers"""
        try:
            marker_validation = self.marker_system.validate_all_markers(file_path)

            if marker_validation['is_valid']:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.MARKERS,
                        level=ValidationLevel.INFO,
                        message=marker_validation['summary'],
                        code="MARKERS_OK"
                    )
                )
            else:
                # Add issues from marker validation
                for block in marker_validation.get('blocks', []):
                    for issue in block.issues:
                        result.add_issue(
                            ValidationIssue(
                                validation_type=ValidationType.MARKERS,
                                level=ValidationLevel.ERROR if issue.severity == "error"
                                      else ValidationLevel.WARNING,
                                line_number=issue.line_number,
                                message=f"Marker issue: {issue.description}",
                                code=f"MARKER_{issue.issue_type.upper()}"
                            )
                        )

                # Add orphaned code warnings
                for orphan in marker_validation.get('orphaned_lines', []):
                    result.add_issue(
                        ValidationIssue(
                            validation_type=ValidationType.MARKERS,
                            level=ValidationLevel.WARNING,
                            line_number=orphan['line_number'],
                            message=f"Orphaned code outside markers: {orphan['content'][:50]}...",
                            code="ORPHANED_CODE"
                        )
                    )

            # Add marker metadata
            result.metadata['marker_validation'] = marker_validation

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.MARKERS,
                    level=ValidationLevel.ERROR,
                    message=f"Marker validation failed: {str(e)}",
                    code="MARKER_VALIDATION_ERROR"
                )
            )

    def _validate_deployment_readiness(self, file_path: Path, result: ValidationResult) -> None:
        """Validate deployment readiness"""
        try:
            # Check if it's a Lambda function file
            if not self._is_lambda_function_file(file_path):
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.DEPLOYMENT,
                        level=ValidationLevel.WARNING,
                        message="File does not appear to be a Lambda function",
                        code="NOT_LAMBDA_FUNCTION"
                    )
                )
                return

            # Check for required Lambda patterns
            content = file_path.read_text(encoding='utf-8')

            # Check for handler function
            if 'def lambda_handler(' not in content and 'def handler(' not in content:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.DEPLOYMENT,
                        level=ValidationLevel.ERROR,
                        message="No Lambda handler function found",
                        code="MISSING_HANDLER",
                        suggestion="Add a lambda_handler(event, context) function"
                    )
                )

            # Check for deployment markers
            marker_validation = self.marker_system.validate_all_markers(file_path)
            if marker_validation['total_blocks'] == 0:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.DEPLOYMENT,
                        level=ValidationLevel.WARNING,
                        message="No deployment markers found",
                        code="NO_DEPLOYMENT_MARKERS",
                        suggestion="Add deployment markers for automated processing"
                    )
                )

            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.DEPLOYMENT,
                    level=ValidationLevel.INFO,
                    message="Deployment readiness check completed",
                    code="DEPLOYMENT_CHECK_OK"
                )
            )

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.DEPLOYMENT,
                    level=ValidationLevel.ERROR,
                    message=f"Deployment validation failed: {str(e)}",
                    code="DEPLOYMENT_VALIDATION_ERROR"
                )
            )

    def _validate_performance(self, file_path: Path, result: ValidationResult) -> None:
        """Validate performance characteristics"""
        try:
            file_size = file_path.stat().st_size
            line_count = self._count_lines(file_path)

            # Check file size
            if file_size > 1024 * 1024:  # 1MB
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.PERFORMANCE,
                        level=ValidationLevel.WARNING,
                        message=f"Large file size: {file_size / 1024:.1f}KB",
                        code="LARGE_FILE_SIZE",
                        suggestion="Consider splitting into smaller modules"
                    )
                )

            # Check line count
            if line_count > 1000:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.PERFORMANCE,
                        level=ValidationLevel.WARNING,
                        message=f"High line count: {line_count} lines",
                        code="HIGH_LINE_COUNT",
                        suggestion="Consider refactoring into smaller functions"
                    )
                )

            result.metadata.update({
                'file_size_bytes': file_size,
                'line_count': line_count
            })

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.PERFORMANCE,
                    level=ValidationLevel.WARNING,
                    message=f"Performance validation failed: {str(e)}",
                    code="PERFORMANCE_VALIDATION_ERROR"
                )
            )

    def _validate_security(self, file_path: Path, result: ValidationResult) -> None:
        """Validate security aspects"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Check for hardcoded secrets (basic patterns)
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]

            import re
            for pattern in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    result.add_issue(
                        ValidationIssue(
                            validation_type=ValidationType.SECURITY,
                            level=ValidationLevel.ERROR,
                            line_number=line_num,
                            message="Potential hardcoded secret detected",
                            code="HARDCODED_SECRET",
                            suggestion="Use environment variables or AWS Secrets Manager"
                        )
                    )

            # Check for eval() usage
            if 'eval(' in content:
                result.add_issue(
                    ValidationIssue(
                        validation_type=ValidationType.SECURITY,
                        level=ValidationLevel.ERROR,
                        message="Use of eval() function detected",
                        code="UNSAFE_EVAL",
                        suggestion="Avoid eval() for security reasons"
                    )
                )

        except Exception as e:
            result.add_issue(
                ValidationIssue(
                    validation_type=ValidationType.SECURITY,
                    level=ValidationLevel.WARNING,
                    message=f"Security validation failed: {str(e)}",
                    code="SECURITY_VALIDATION_ERROR"
                )
            )

    def _is_known_module(self, module_name: str) -> bool:
        """Check if module is a known standard library or common third-party module"""
        base_module = module_name.split('.')[0]

        # Check standard library
        if base_module in self.standard_library_modules:
            return True

        # Check common third-party modules
        common_third_party = {
            'boto3', 'botocore', 'pydantic', 'typer', 'click', 'rich',
            'structlog', 'httpx', 'requests', 'asyncio_throttle', 'pytest',
            'mypy', 'ruff', 'pylint', 'black', 'isort', 'moto', 'fastapi',
            'flask', 'django', 'numpy', 'pandas', 'matplotlib', 'scipy'
        }

        return base_module in common_third_party

    def _is_lambda_function_file(self, file_path: Path) -> bool:
        """Check if file appears to be a Lambda function"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for Lambda patterns
            lambda_indicators = [
                'lambda_handler',
                'def handler(',
                'event',
                'context',
                'boto3',
                'aws'
            ]

            content_lower = content.lower()
            indicators_found = sum(1 for indicator in lambda_indicators
                                 if indicator in content_lower)

            return indicators_found >= 2

        except Exception:
            return False

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file efficiently"""
        try:
            with file_path.open('rb') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
