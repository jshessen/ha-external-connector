# Lambda Deployment System

🚀 **Modular Lambda deployment automation for HA External Connector**

This directory contains the new modular Lambda deployment system that replaces the previous monolithic deployment scripts.

## Core Components

### 📁 System Files

- **`deployment_manager.py`** - Main orchestrator for deployment operations
- **`marker_system.py`** - Core marker processing and content extraction
- **`validation_system.py`** - Comprehensive validation framework
- **`marker_validator.py`** - Standalone validation tool

### 🔧 Utility Scripts

- **`migrate_deployment_system.py`** - Migration tool from old to new system
- **`test_new_system.py`** - Comprehensive testing suite

## Quick Start

### 1. Validate Lambda Markers

```bash
# Validate all Lambda function files
python scripts/lambda_deployment/marker_validator.py --all

# Validate specific file
python scripts/lambda_deployment/marker_validator.py --file oauth_gateway.py

# Complete project validation
python scripts/lambda_deployment/marker_validator.py --complete
```

### 2. Build Deployment Files

```bash
# Build deployment files with embedded shared code
python scripts/lambda_deployment/deployment_manager.py --build

# Validate existing deployment
python scripts/lambda_deployment/deployment_manager.py --validate

# Clean deployment files (reset to development mode)
python scripts/lambda_deployment/deployment_manager.py --clean
```

### 3. Run System Tests

```bash
# Run complete test suite
python scripts/lambda_deployment/test_new_system.py --all

# Run specific test categories
python scripts/lambda_deployment/test_new_system.py --unit
python scripts/lambda_deployment/test_new_system.py --integration
```

## Architecture Overview

### Marker System

The system uses visual box-drawing characters to mark code sections:

```python
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import json
import logging
from typing import Any
# ╰─────────────────── IMPORT_BLOCK_END ─────────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮
def lambda_handler(event, context):
    return {"statusCode": 200}
# ╰─────────────────── FUNCTION_BLOCK_END ─────────────────────╯
```

### Deployment Workflow

1. **Validation** - Verify marker integrity and code structure
2. **Extraction** - Extract marked sections from source files
3. **Merging** - Combine Lambda code with shared configuration
4. **Generation** - Create standalone deployment files
5. **Verification** - Validate generated deployment files

### File Structure

```text
scripts/lambda_deployment/
├── deployment_manager.py      # Main deployment orchestrator
├── marker_system.py          # Core marker processing
├── validation_system.py      # Validation framework
├── marker_validator.py       # Standalone validation tool
├── migrate_deployment_system.py  # Migration utility
├── test_new_system.py        # Testing suite
└── README.md                 # This file
```

## Key Features

### ✅ Modular Architecture

- **Single Responsibility** - Each component has a clear, focused purpose
- **Pluggable Design** - Components can be used independently
- **Clean Interfaces** - Well-defined APIs between components

### ✅ Comprehensive Validation

- **Marker Integrity** - Validates proper marker syntax and pairing
- **Content Structure** - Ensures code follows expected patterns
- **Import Management** - Handles shared configuration imports
- **Error Reporting** - Detailed feedback on validation issues

### ✅ Robust Error Handling

- **Graceful Degradation** - System continues working with partial failures
- **Detailed Logging** - Comprehensive error reporting and debugging
- **Recovery Mechanisms** - Rollback and cleanup capabilities

### ✅ Developer Experience

- **CLI Tools** - Easy-to-use command-line interfaces
- **Verbose Modes** - Detailed output for debugging
- **Help Documentation** - Built-in help for all commands

## Migration from Old System

If migrating from the legacy deployment system:

```bash
# Create backup and migrate to new system
python scripts/lambda_deployment/migrate_deployment_system.py --migrate

# Validate migration
python scripts/lambda_deployment/migrate_deployment_system.py --validate

# Rollback if needed
python scripts/lambda_deployment/migrate_deployment_system.py --rollback
```

## Development Guidelines

### Adding New Lambda Functions

1. **Add markers** to your Lambda function source code
2. **Update configuration** in `deployment_manager.py`
3. **Test validation** using marker_validator.py
4. **Build deployment** using deployment_manager.py

### Marker Requirements

- Use exact marker text (copy from existing files)
- Ensure proper pairing (START/END markers)
- Place imports between IMPORT_BLOCK markers
- Place functions between FUNCTION_BLOCK markers

### Code Quality

- All scripts pass Ruff and Pylint checks
- Comprehensive type annotations
- Error handling for all operations
- Logging for debugging and monitoring

## Troubleshooting

### Common Issues

#### Missing Required Marker

- Solution: Add missing START/END marker pairs to your source file

#### Marker Formatting Invalid

- Solution: Copy exact marker text from working files

#### Import Validation Failed

- Solution: Ensure shared imports are properly marked

#### Content Extraction Failed

- Solution: Check for balanced marker pairs and proper syntax

### Debug Mode

Run any tool with `--verbose` for detailed debugging output:

```bash
python scripts/lambda_deployment/deployment_manager.py --build --verbose
```

## Future Enhancements

- **Automated Testing** - CI/CD integration for validation
- **Template Generation** - Auto-generate marker templates
- **Performance Optimization** - Parallel processing for large projects
- **IDE Integration** - VS Code extensions for marker management

---

**📚 For more information:**

- See individual script help: `python script_name.py --help`
- Review source code comments for implementation details
- Check test files for usage examples
