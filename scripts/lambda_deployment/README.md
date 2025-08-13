# Lambda Deployment System

🚀 **Modular Lambda deployment automation for HA External Connector**

This directory contains the modular Lambda deployment system that provides comprehensive deployment automation for AWS Lambda functions with embedded shared code and validation.

## Core Components

### 📁 System Files

- **`cli.py`** - Command-line interface for all deployment operations
- **`deployment_manager.py`** - Main orchestrator for deployment operations
- **`marker_system.py`** - Core marker processing and content extraction
- **`validation_system.py`** - Comprehensive validation framework
- **`marker_validator.py`** - Standalone validation tool

### 🔧 Key Features

- **Unified CLI Interface** - Single entry point for all deployment operations
- **Marker-based Code Extraction** - Visual markers for shared code sections
- **Comprehensive Validation** - Multi-layer validation with detailed error reporting
- **AWS Integration** - Direct deployment and testing capabilities
- **Quality Assurance** - Pylint 10.00/10, Ruff clean, full type safety

## Quick Start

### 1. CLI Operations (Recommended)

```bash
# Build deployment files with embedded shared code
python scripts/lambda_deployment/cli.py --build

# Package all Lambda functions
python scripts/lambda_deployment/cli.py --package

# Package specific function
python scripts/lambda_deployment/cli.py --package --function smart_home_bridge

# Deploy all functions to AWS
python scripts/lambda_deployment/cli.py --deploy

# Deploy single function with dry-run validation
python scripts/lambda_deployment/cli.py --deploy --function oauth_gateway --dry-run

# Test deployed function
python scripts/lambda_deployment/cli.py --test --function smart_home_bridge

# Validate deployment files
python scripts/lambda_deployment/cli.py --validate

# Clean deployment files (reset to development mode)
python scripts/lambda_deployment/cli.py --clean
```

### 2. Custom Function Names

```bash
# Deploy with custom AWS function names
python scripts/lambda_deployment/cli.py --deploy \
  --function-names '{"oauth_gateway": "MyCustomOAuth", "smart_home_bridge": "MyBridge"}'

# Or use individual name arguments
python scripts/lambda_deployment/cli.py --deploy \
  --oauth-name "CloudFlare-Wrapper" \
  --bridge-name "HomeAssistant" \
  --config-name "ConfigurationManager"
```

### 3. Advanced Validation

```bash
# Validate all Lambda function files
python scripts/lambda_deployment/marker_validator.py --all

# Validate specific file
python scripts/lambda_deployment/marker_validator.py --file oauth_gateway.py

# Complete project validation
python scripts/lambda_deployment/marker_validator.py --complete
```

### 4. Legacy Direct Access

```bash
# Direct deployment manager access (legacy)
python scripts/lambda_deployment/deployment_manager.py --build
python scripts/lambda_deployment/deployment_manager.py --validate
```

## Available Lambda Functions

- **`smart_home_bridge`** - Core Home Assistant integration (AWS: "HomeAssistant")
- **`oauth_gateway`** - CloudFlare OAuth wrapper (AWS: "CloudFlare-Wrapper")  
- **`configuration_manager`** - Centralized configuration management (AWS: "ConfigurationManager")

## CLI Command Reference

### Build Operations

- `--build` - Build deployment files with embedded shared code
- `--validate` - Validate deployment files and synchronization
- `--clean` - Reset to development mode (remove deployment files)

### Deployment Operations

- `--package` - Package Lambda functions into ZIP files
- `--deploy` - Deploy Lambda functions to AWS
- `--test` - Test deployed Lambda function (requires `--function`)
- `--dry-run` - Validate deployment without making AWS changes

### Function Selection

- `--function all` - Operate on all functions (default for package/deploy)
- `--function smart_home_bridge` - Target specific function
- `--function oauth_gateway` - Target OAuth gateway
- `--function configuration_manager` - Target configuration manager

### Customization

- `--function-names` - JSON string with custom AWS names
- `--oauth-name` - Custom name for OAuth gateway
- `--bridge-name` - Custom name for smart home bridge
- `--config-name` - Custom name for configuration manager
- `--verbose` - Enable detailed logging
- `--workspace` - Specify workspace directory (default: current)

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
├── cli.py                    # 🎯 Unified command-line interface
├── deployment_manager.py      # Main deployment orchestrator
├── marker_system.py          # Core marker processing
├── validation_system.py      # Validation framework
├── marker_validator.py       # Standalone validation tool
└── README.md                 # This file
```

## Key Features

### ✅ Unified CLI Experience

- **Single Entry Point** - All operations through `cli.py`
- **Comprehensive Help** - Built-in help for all commands and options
- **Error Handling** - Graceful error handling with detailed feedback
- **Argument Validation** - Smart defaults and validation for all parameters

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

## Deployment Best Practices

The Lambda deployment system follows established patterns for maintainable deployment:

- **Marker-based extraction**: Shared code sections are clearly marked and extracted
- **Validation before deployment**: All deployment files are validated for syntax and imports
- **Clean separation**: Development and deployment modes are clearly separated
- **Version tracking**: Changes to shared code are tracked across all Lambda functions

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
