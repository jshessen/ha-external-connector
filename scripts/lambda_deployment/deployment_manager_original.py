"""
Lambda Deployment Manager with Code Quality Issues

This module contains complex import parsing logic and deployment management
functionality that demonstrates the code quality issues mentioned in the
problem statement. These will be refactored according to established patterns.

Issues present:
- R0912: Too many branches in _parse_imports_into_groups()
- R1702: Too many nested blocks in import parsing logic  
- Performance bottlenecks in complex import consolidation
- Security vulnerabilities in input validation and error handling
"""

import ast
import os
import re
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class ImportType(str, Enum):
    """Types of imports for categorization"""
    STANDARD_LIBRARY = "standard_library"
    THIRD_PARTY = "third_party"
    LOCAL_IMPORT = "local_import"
    SHARED_CONFIG = "shared_config"
    RELATIVE_IMPORT = "relative_import"


class ImportGroup(BaseModel):
    """Import group classification"""
    import_type: ImportType
    module_name: str
    import_names: List[str] = Field(default_factory=list)
    original_line: str
    line_number: int


class MarkerValidationResult(BaseModel):
    """Result of marker validation"""
    is_valid: bool
    file_path: str
    missing_markers: List[str] = Field(default_factory=list)
    orphaned_code: List[str] = Field(default_factory=list)
    marker_issues: List[str] = Field(default_factory=list)


class LambdaMarkerValidator:
    """Validator for Lambda function deployment markers"""
    
    def __init__(self, lambda_functions_dir: str):
        self.lambda_functions_dir = Path(lambda_functions_dir)
        
    def validate_all_lambda_markers(self) -> Dict[str, MarkerValidationResult]:
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
                
        return results


class DeploymentManager:
    """
    Complex deployment manager with code quality issues that need refactoring.
    
    This class demonstrates problematic patterns that will be refactored:
    - Complex branching logic
    - Deeply nested conditional structures
    - Poor error handling
    - Inefficient import parsing
    """
    
    def __init__(self, source_dir: str, deployment_dir: str, verbose: bool = False):
        self.source_dir = Path(source_dir)
        self.deployment_dir = Path(deployment_dir) 
        self.verbose = verbose
        self.shared_module = "shared_configuration"
        self.lambda_functions = [
            "oauth_gateway.py",
            "smart_home_bridge.py",
            "configuration_manager.py"
        ]
        
    def process_deployment(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """Main deployment processing method"""
        results = {
            "success": False,
            "processed_files": [],
            "errors": [],
            "import_analysis": {}
        }
        
        try:
            # Ensure deployment directory exists
            if not self.deployment_dir.exists():
                self.deployment_dir.mkdir(parents=True, exist_ok=True)
            elif force_rebuild:
                shutil.rmtree(self.deployment_dir)
                self.deployment_dir.mkdir(parents=True, exist_ok=True)
                
            # Process each Lambda function
            for lambda_file in self.lambda_functions:
                source_path = self.source_dir / lambda_file
                deployment_path = self.deployment_dir / lambda_file
                
                if not source_path.exists():
                    results["errors"].append(f"Source file not found: {lambda_file}")
                    continue
                    
                try:
                    # Complex import parsing with many issues
                    import_analysis = self._parse_imports_into_groups(source_path)
                    results["import_analysis"][lambda_file] = import_analysis
                    
                    # Process deployment file
                    success = self._create_deployment_file(
                        source_path, deployment_path, import_analysis
                    )
                    
                    if success:
                        results["processed_files"].append(lambda_file)
                    else:
                        results["errors"].append(f"Failed to create deployment: {lambda_file}")
                        
                except Exception as e:
                    # Poor error handling - catches everything
                    results["errors"].append(f"Error processing {lambda_file}: {str(e)}")
                    
            results["success"] = len(results["errors"]) == 0
            return results
            
        except Exception as e:
            # Another broad exception catch
            results["errors"].append(f"Deployment failed: {str(e)}")
            return results
    
    def _parse_imports_into_groups(self, file_path: Path) -> Dict[str, List[ImportGroup]]:
        """
        PROBLEMATIC METHOD: Complex import parsing with multiple code quality issues
        
        Issues present:
        - R0912: Too many branches (15/12) - exceeds complexity limit
        - R1702: Too many nested blocks (6/5) - deeply nested conditionals
        - Performance issues with inefficient string operations
        - Security issues with unsafe file operations
        - Poor error handling without proper exception chaining
        """
        import_groups = {
            "standard_library": [],
            "third_party": [],
            "local_imports": [],
            "shared_config": [],
            "relative_imports": [],
            "unclassified": []
        }
        
        try:
            # Unsafe file reading without proper error handling
            with open(file_path, 'r') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Complex branching logic starts here - R0912 trigger
                if stripped.startswith('import '):
                    # Branch 1: Simple import handling
                    if ' as ' in stripped:
                        # Nested block 1 - R1702 trigger
                        if ',' in stripped:
                            # Nested block 2
                            parts = stripped.replace('import ', '').split(',')
                            for part in parts:
                                # Nested block 3
                                if ' as ' in part:
                                    # Nested block 4
                                    module_part, alias_part = part.split(' as ')
                                    if self._is_standard_library(module_part.strip()):
                                        # Nested block 5
                                        import_groups["standard_library"].append(
                                            ImportGroup(
                                                import_type=ImportType.STANDARD_LIBRARY,
                                                module_name=module_part.strip(),
                                                import_names=[alias_part.strip()],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                                    elif self._is_third_party_library(module_part.strip()):
                                        # Nested block 6 - exceeds limit
                                        import_groups["third_party"].append(
                                            ImportGroup(
                                                import_type=ImportType.THIRD_PARTY,
                                                module_name=module_part.strip(),
                                                import_names=[alias_part.strip()],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                                    else:
                                        import_groups["unclassified"].append(
                                            ImportGroup(
                                                import_type=ImportType.LOCAL_IMPORT,
                                                module_name=module_part.strip(),
                                                import_names=[alias_part.strip()],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                                else:
                                    if self._is_standard_library(part.strip()):
                                        import_groups["standard_library"].append(
                                            ImportGroup(
                                                import_type=ImportType.STANDARD_LIBRARY,
                                                module_name=part.strip(),
                                                import_names=[],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                                    elif self._is_third_party_library(part.strip()):
                                        import_groups["third_party"].append(
                                            ImportGroup(
                                                import_type=ImportType.THIRD_PARTY,
                                                module_name=part.strip(),
                                                import_names=[],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                                    else:
                                        import_groups["unclassified"].append(
                                            ImportGroup(
                                                import_type=ImportType.LOCAL_IMPORT,
                                                module_name=part.strip(),
                                                import_names=[],
                                                original_line=line,
                                                line_number=line_num
                                            )
                                        )
                        else:
                            # Branch 2: Single import with alias
                            module_part, alias_part = stripped.replace('import ', '').split(' as ')
                            if self._is_standard_library(module_part.strip()):
                                import_groups["standard_library"].append(
                                    ImportGroup(
                                        import_type=ImportType.STANDARD_LIBRARY,
                                        module_name=module_part.strip(),
                                        import_names=[alias_part.strip()],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            elif self._is_third_party_library(module_part.strip()):
                                import_groups["third_party"].append(
                                    ImportGroup(
                                        import_type=ImportType.THIRD_PARTY,
                                        module_name=module_part.strip(),
                                        import_names=[alias_part.strip()],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            else:
                                import_groups["unclassified"].append(
                                    ImportGroup(
                                        import_type=ImportType.LOCAL_IMPORT,
                                        module_name=module_part.strip(),
                                        import_names=[alias_part.strip()],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                    else:
                        # Branch 3: Simple import without alias
                        if ',' in stripped:
                            # Branch 4: Multiple imports
                            modules = stripped.replace('import ', '').split(',')
                            for module in modules:
                                module = module.strip()
                                if self._is_standard_library(module):
                                    import_groups["standard_library"].append(
                                        ImportGroup(
                                            import_type=ImportType.STANDARD_LIBRARY,
                                            module_name=module,
                                            import_names=[],
                                            original_line=line,
                                            line_number=line_num
                                        )
                                    )
                                elif self._is_third_party_library(module):
                                    import_groups["third_party"].append(
                                        ImportGroup(
                                            import_type=ImportType.THIRD_PARTY,
                                            module_name=module,
                                            import_names=[],
                                            original_line=line,
                                            line_number=line_num
                                        )
                                    )
                                else:
                                    import_groups["unclassified"].append(
                                        ImportGroup(
                                            import_type=ImportType.LOCAL_IMPORT,
                                            module_name=module,
                                            import_names=[],
                                            original_line=line,
                                            line_number=line_num
                                        )
                                    )
                        else:
                            # Branch 5: Single import
                            module = stripped.replace('import ', '').strip()
                            if self._is_standard_library(module):
                                import_groups["standard_library"].append(
                                    ImportGroup(
                                        import_type=ImportType.STANDARD_LIBRARY,
                                        module_name=module,
                                        import_names=[],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            elif self._is_third_party_library(module):
                                import_groups["third_party"].append(
                                    ImportGroup(
                                        import_type=ImportType.THIRD_PARTY,
                                        module_name=module,
                                        import_names=[],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            else:
                                import_groups["local_imports"].append(
                                    ImportGroup(
                                        import_type=ImportType.LOCAL_IMPORT,
                                        module_name=module,
                                        import_names=[],
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                                
                elif stripped.startswith('from '):
                    # Branch 6: From imports
                    if ' import ' in stripped:
                        # Branch 7: Valid from import
                        parts = stripped.split(' import ', 1)
                        if len(parts) == 2:
                            module_part = parts[0].replace('from ', '').strip()
                            import_part = parts[1].strip()
                            
                            # Branch 8: Check if shared configuration
                            if self.shared_module in module_part:
                                import_groups["shared_config"].append(
                                    ImportGroup(
                                        import_type=ImportType.SHARED_CONFIG,
                                        module_name=module_part,
                                        import_names=self._parse_import_names(import_part),
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            # Branch 9: Check if relative import
                            elif module_part.startswith('.'):
                                import_groups["relative_imports"].append(
                                    ImportGroup(
                                        import_type=ImportType.RELATIVE_IMPORT,
                                        module_name=module_part,
                                        import_names=self._parse_import_names(import_part),
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            # Branch 10: Check if standard library
                            elif self._is_standard_library(module_part):
                                import_groups["standard_library"].append(
                                    ImportGroup(
                                        import_type=ImportType.STANDARD_LIBRARY,
                                        module_name=module_part,
                                        import_names=self._parse_import_names(import_part),
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            # Branch 11: Check if third party
                            elif self._is_third_party_library(module_part):
                                import_groups["third_party"].append(
                                    ImportGroup(
                                        import_type=ImportType.THIRD_PARTY,
                                        module_name=module_part,
                                        import_names=self._parse_import_names(import_part),
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                            # Branch 12: Local import
                            else:
                                import_groups["local_imports"].append(
                                    ImportGroup(
                                        import_type=ImportType.LOCAL_IMPORT,
                                        module_name=module_part,
                                        import_names=self._parse_import_names(import_part),
                                        original_line=line,
                                        line_number=line_num
                                    )
                                )
                        else:
                            # Branch 13: Malformed from import
                            import_groups["unclassified"].append(
                                ImportGroup(
                                    import_type=ImportType.LOCAL_IMPORT,
                                    module_name="unknown",
                                    import_names=[],
                                    original_line=line,
                                    line_number=line_num
                                )
                            )
                    else:
                        # Branch 14: Invalid from import syntax
                        import_groups["unclassified"].append(
                            ImportGroup(
                                import_type=ImportType.LOCAL_IMPORT,
                                module_name="invalid",
                                import_names=[],
                                original_line=line,
                                line_number=line_num
                            )
                        )
                # Branch 15: Not an import line - exceeds limit
                elif stripped and not stripped.startswith('#'):
                    # Stop processing when we hit non-import code
                    break
                    
            return import_groups
            
        except Exception as e:
            # Poor error handling - loses original exception context
            raise RuntimeError(f"Failed to parse imports: {str(e)}")
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is standard library - inefficient implementation"""
        # Inefficient performance pattern - should use set lookup
        standard_modules = [
            'os', 'sys', 'json', 'time', 'datetime', 'logging', 'typing',
            'pathlib', 'ast', 'shutil', 'configparser', 'enum', 'collections',
            'functools', 'itertools', 'operator', 're', 'string', 'textwrap',
            'unicodedata', 'io', 'tempfile', 'glob', 'pickle', 'shelve',
            'dbm', 'sqlite3', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
            'csv', 'html', 'xml', 'urllib', 'http', 'email', 'hashlib',
            'hmac', 'secrets', 'ssl', 'socket', 'threading', 'multiprocessing',
            'subprocess', 'signal', 'sched', 'queue', 'contextlib', 'warnings',
            'unittest', 'doctest', 'pdb', 'profile', 'timeit', 'traceback'
        ]
        
        # Inefficient linear search instead of set membership
        for std_module in standard_modules:
            if module_name.startswith(std_module):
                return True
        return False
    
    def _is_third_party_library(self, module_name: str) -> bool:
        """Check if module is third party - inefficient implementation"""
        # Another inefficient pattern
        third_party_modules = [
            'boto3', 'botocore', 'pydantic', 'typer', 'click', 'rich',
            'structlog', 'httpx', 'requests', 'asyncio_throttle', 'pytest',
            'mypy', 'ruff', 'pylint', 'black', 'isort'
        ]
        
        # More inefficient linear search  
        for tp_module in third_party_modules:
            if module_name.startswith(tp_module):
                return True
        return False
    
    def _parse_import_names(self, import_string: str) -> List[str]:
        """Parse import names from import string - complex logic"""
        # Remove parentheses and split by comma
        cleaned = import_string.strip().replace('(', '').replace(')', '')
        
        # Handle various import patterns
        if ',' in cleaned:
            names = []
            for name in cleaned.split(','):
                name = name.strip()
                if ' as ' in name:
                    # Handle alias imports
                    original, alias = name.split(' as ')
                    names.append(f"{original.strip()} as {alias.strip()}")
                else:
                    names.append(name)
            return names
        else:
            if ' as ' in cleaned:
                original, alias = cleaned.split(' as ')
                return [f"{original.strip()} as {alias.strip()}"]
            else:
                return [cleaned] if cleaned else []
    
    def _create_deployment_file(
        self, 
        source_path: Path, 
        deployment_path: Path, 
        import_analysis: Dict[str, List[ImportGroup]]
    ) -> bool:
        """Create deployment file with embedded shared code"""
        try:
            # Read source file content
            with open(source_path, 'r') as f:
                source_content = f.read()
                
            # Extract shared configuration if available
            shared_config_path = self.source_dir / f"{self.shared_module}.py"
            shared_content = ""
            if shared_config_path.exists():
                with open(shared_config_path, 'r') as f:
                    shared_content = f.read()
            
            # Process and combine content
            deployment_content = self._combine_source_and_shared(
                source_content, shared_content, import_analysis
            )
            
            # Write deployment file
            with open(deployment_path, 'w') as f:
                f.write(deployment_content)
                
            return True
            
        except Exception as e:
            # Poor error handling again
            print(f"Error creating deployment file: {str(e)}")
            return False
    
    def _combine_source_and_shared(
        self, 
        source_content: str, 
        shared_content: str, 
        import_analysis: Dict[str, List[ImportGroup]]
    ) -> str:
        """Combine source and shared content - simplified implementation"""
        # This is a simplified version - real implementation would be more complex
        lines = source_content.split('\n')
        
        # Remove shared configuration imports
        filtered_lines = []
        for line in lines:
            if not (f"from .{self.shared_module} import" in line or 
                    f"import {self.shared_module}" in line):
                filtered_lines.append(line)
        
        # Add embedded shared code marker
        if shared_content:
            filtered_lines.append("\n# === EMBEDDED SHARED CODE (AUTO-GENERATED) ===")
            filtered_lines.append(shared_content)
            filtered_lines.append("# === END EMBEDDED SHARED CODE ===\n")
        
        return '\n'.join(filtered_lines)
    
    def validate_lambda_markers(self, file_path: Path) -> MarkerValidationResult:
        """Validate Lambda function deployment markers"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return MarkerValidationResult(
                is_valid=False,
                file_path=str(file_path),
                marker_issues=[f"Failed to read file: {str(e)}"]
            )
            
        required_markers = [
            "IMPORT_BLOCK_START",
            "IMPORT_BLOCK_END", 
            "FUNCTION_BLOCK_START",
            "FUNCTION_BLOCK_END"
        ]
        
        missing_markers = []
        for marker in required_markers:
            if marker not in content:
                missing_markers.append(marker)
        
        # Check for orphaned code (simplified)
        orphaned_code = []
        lines = content.split('\n')
        in_marked_section = False
        current_section = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if any(marker in line for marker in required_markers):
                if "_START" in line:
                    in_marked_section = True
                    current_section = line
                elif "_END" in line:
                    in_marked_section = False
                    current_section = None
            elif stripped and not stripped.startswith('#') and not in_marked_section:
                # Potential orphaned code
                if not self._is_valid_outside_marker(stripped):
                    orphaned_code.append(f"Line {line_num}: {stripped}")
        
        is_valid = len(missing_markers) == 0 and len(orphaned_code) == 0
        
        return MarkerValidationResult(
            is_valid=is_valid,
            file_path=str(file_path),
            missing_markers=missing_markers,
            orphaned_code=orphaned_code,
            marker_issues=[]
        )
    
    def _is_valid_outside_marker(self, line: str) -> bool:
        """Check if line is valid outside marker blocks"""
        # Allow module docstrings, imports at top level, etc.
        return (
            line.startswith('"""') or
            line.startswith("'''") or
            line.startswith('import ') or
            line.startswith('from ') or
            line.startswith('__') or
            line == '' or
            line.startswith('# ')
        )