# Code Quality Analysis Suite

This document describes the comprehensive code quality automation system that replaces the original `lint.py` script.

## 🚀 Overview

The new `code_quality.py` script provides a unified interface for running various code quality tools organized by logical categories with support for different usage profiles and automatic fixing.

## 📁 Tool Categories

### 🎨 Formatters

- **black** - Code formatting (PEP 8 style) ✅ Auto-fix
- **isort** - Import sorting and organization ✅ Auto-fix

### 🔍 Linters

- **ruff** - Fast Python linter (replaces flake8, isort, etc.) ✅ Auto-fix
- **flake8** - Style guide enforcement ❌ No auto-fix
- **pylint** - Comprehensive code analysis ❌ No auto-fix

### 🔎 Type Checkers

- **mypy** - Static type checking ❌ No auto-fix
- **pyright** - Microsoft's Python type checker (Pylance engine) ❌ No auto-fix

### 🛡️ Security Tools

- **bandit** - Security vulnerability scanner ❌ No auto-fix
- **safety** - Known security vulnerabilities in dependencies ❌ No auto-fix
- **pip-audit** - OWASP dependency vulnerability check ❌ No auto-fix

### 🧹 Code Analysis

- **vulture** - Dead code detection ❌ No auto-fix

## 🏷️ Configuration Profiles

### Development Profile

#### Quick checks for development workflow

- Tools: black, isort, ruff
- Use case: Fast feedback during development

### CI Profile

#### Comprehensive checks for CI/CD pipeline

- Categories: formatters, linters, type-checkers, security
- Use case: Complete validation in continuous integration

### Pre-commit Profile

#### Fast pre-commit hooks

- Tools: black, isort, ruff
- Use case: Git pre-commit hook automation

### Security Profile

#### Security-focused analysis

- Tools: bandit, safety, pip-audit
- Use case: Security vulnerability assessment

### Typing Profile

#### Type checking focus

- Tools: mypy, pyright
- Use case: Static type analysis and validation

## 🔧 Usage Examples

### Basic Usage

```bash
# Run all tools on default targets (src/, tests/, scripts/, setup.py)
python scripts/code_quality.py

# Run specific profile
python scripts/code_quality.py --profile development

# Run specific categories
python scripts/code_quality.py --categories formatters linters

# Run specific tools
python scripts/code_quality.py --tools black mypy

# Apply automatic fixes
python scripts/code_quality.py --fix

# Target specific files
python scripts/code_quality.py src/specific_file.py --tools black isort

# Verbose output for detailed analysis
python scripts/code_quality.py --verbose

# Save detailed report to file
python scripts/code_quality.py --verbose --output-file quality-report.txt
```

### Advanced Usage

```bash
# Development workflow with fixes
python scripts/code_quality.py --profile development --fix

# Security audit
python scripts/code_quality.py --profile security

# Type checking only
python scripts/code_quality.py --profile typing

# Show all available options
python scripts/code_quality.py --show-tools
```

### VS Code Integration

The following tasks are available in VS Code:

- **Code Quality: All Tools** - Run comprehensive analysis
- **Code Quality: Development Profile** - Quick development checks
- **Code Quality: Fix Issues** - Apply automatic fixes
- **Code Quality: Type Checking** - Run type checkers only
- **Code Quality: Security Check** - Security-focused analysis
- **Code Quality: Show Available Tools** - List all options

## 🎯 Key Features

### Enhanced Reporting

- Categorized results (Passed, Issues, Fixed, Errors)
- Detailed tool-specific output processing
- Fix vs check mode distinction
- Clear summary with actionable suggestions

### Flexible Tool Selection

- **By Profile**: Predefined tool combinations for common workflows
- **By Category**: Group related tools (formatters, linters, etc.)
- **By Individual Tools**: Select specific tools
- **All Tools**: Comprehensive analysis

### Automatic Fixing

- Supports tools with auto-fix capabilities
- Clear indication of what was fixed vs what needs manual attention
- Safe operation with detailed reporting

### Smart Tool Execution

- Proper virtual environment detection and usage
- Node.js tool support (pyright)
- Timeout protection
- Error handling and reporting

### Verbose Output for Automated Remediation

- **--verbose**: Captures complete tool output for detailed analysis
- **--output-file**: Writes verbose report to file for AI-assisted remediation
- Full command output preservation for debugging and issue resolution
- Structured output format suitable for automated processing

#### Verbose Output Examples

```bash
# Show detailed output for all issues
python scripts/code_quality.py --verbose

# Write detailed report to file for analysis
python scripts/code_quality.py --verbose --output-file code-quality-report.txt

# Combine with specific tools for focused analysis
python scripts/code_quality.py --tools pylint mypy --verbose --output-file type-check-report.txt
```

The verbose output includes:

- Complete stdout/stderr from each tool
- Return codes and execution details
- Structured format for easy parsing
- Integration with automated remediation workflows

## 🔄 Migration from lint.py

The original `lint.py` script has been preserved as `lint.py.backup`. The new system provides all the same functionality with these enhancements:

### What's New

- ✅ Tool categorization and profiles
- ✅ Enhanced isort integration
- ✅ Pyright support (Pylance engine)
- ✅ Automatic fixing capabilities
- ✅ Better error handling and reporting
- ✅ Flexible tool selection options

### Compatibility

- All original tools are supported
- Same virtual environment detection
- Same target file/directory logic
- Same command-line interface patterns

### VS Code Tasks

Tasks have been updated to use the new script with enhanced profiles and functionality.

## 🚀 Best Practices

### Development Workflow

```bash
# Quick development checks
python scripts/code_quality.py --profile development

# Apply fixes during development
python scripts/code_quality.py --profile development --fix

# Before committing
python scripts/code_quality.py --profile pre-commit --fix
```

### CI/CD Pipeline

```bash
# Comprehensive CI checks
python scripts/code_quality.py --profile ci

# Security audit in CI
python scripts/code_quality.py --profile security
```

### Specific Use Cases

```bash
# Fix formatting issues
python scripts/code_quality.py --categories formatters --fix

# Type checking validation
python scripts/code_quality.py --profile typing

# Security vulnerability scan
python scripts/code_quality.py --profile security
```

## 📊 Output Format

The enhanced reporting provides:

- **Summary Statistics**: Passed, Issues, Fixed, Errors counts
- **Detailed Results**: Tool-by-tool breakdown with status
- **Actionable Suggestions**: Next steps and manual tool commands
- **Fix/Check Distinction**: Clear indication of what was automatically fixed

This comprehensive system provides a powerful, flexible, and user-friendly approach to code quality automation that scales from quick development checks to comprehensive CI/CD validation.
