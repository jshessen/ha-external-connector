# GitHub Copilot Instructions Index

## 📋 Navigation & Hierarchy

This directory contains specialized instruction files for GitHub Copilot to ensure consistent, high-quality code development across the HA External Connector project.

### 🎯 Conflict Resolution Hierarchy

When instructions conflict between files, follow this precedence order:

1. **`.github/copilot-instructions.md`** - Master guidelines (highest priority)
2. **`instructions/core/`** - Fundamental patterns (medium priority)
3. **`instructions/specialized/`** - Domain-specific guidance (contextual priority)
4. **`instructions/documentation/`** - Content standards (lowest priority)

## 📁 Directory Structure

### Core Instructions (Fundamental Patterns)

**Purpose**: Essential patterns that apply across all development work.

- **`core/environment-setup.md`** - Environment activation, terminal automation, dependency management
- **`core/quality-standards.md`** - Code quality requirements, linting standards, testing protocols
- **`core/agent-refresh.md`** - Agent guidance refresh system and instruction validation

### Specialized Instructions (Domain-Specific Patterns)

**Purpose**: Detailed patterns for specific technology domains and architectural components.

- **`specialized/aws-patterns.md`** - AWS client creation, resource management, security patterns
- **`specialized/lambda-patterns.md`** - Lambda deployment markers, transfer blocks, service specialization
- **`specialized/testing-patterns.md`** - Testing standards, moto library usage, fixture design
- **`specialized/security-patterns.md`** - Security best practices, secret management, input validation

### Documentation Instructions (Content Standards)

**Purpose**: Standards for documentation creation, organization, and maintenance.

- **`documentation/markdown-standards.md`** - Markdown formatting compliance, heading structure
- **`documentation/docs-organization.md`** - Documentation structure patterns, audience-based organization

## 🔄 Transfer Block System

**Primary Source**: `specialized/lambda-patterns.md` contains the authoritative Transfer Block documentation for Lambda functions.

**Cross-References**: Other files may reference transfer blocks but should defer to the primary source for implementation details.

## 🚀 Quick Reference

### Essential Commands

```bash
# Environment setup and validation
python scripts/agent_helper.py setup          # Full environment setup
python scripts/agent_helper.py check          # Quick health check
python scripts/agent_helper.py refresh        # Reload instructions

# Code quality
source .venv/bin/activate && ruff check src/  # Fast linting
source .venv/bin/activate && pylint src/      # Comprehensive analysis
```

### File Pattern Matching

| Pattern | Instruction File | Description |
|---------|-----------------|-------------|
| `**/test_*.py`, `**/tests/**/*.py` | `specialized/testing-patterns.md` | Testing standards & moto usage |
| `**/aws_*.py`, `**/adapters/**/*.py` | `specialized/aws-patterns.md` | AWS client creation & patterns |
| `**/lambda_functions/**/*.py` | `specialized/lambda-patterns.md` | Lambda deployment & transfer blocks |
| `**/security/**/*.py`, `**/*security*.py` | `specialized/security-patterns.md` | Security best practices |
| `**/*.md` | `documentation/markdown-standards.md` | Markdown formatting compliance |
| `**/docs/**/*` | `documentation/docs-organization.md` | Documentation structure patterns |

## 🔧 Agent Usage Guidelines

1. **Start with Master Instructions**: Always review `.github/copilot-instructions.md` first
2. **Apply Core Patterns**: Use `core/` instructions for fundamental development patterns
3. **Reference Specialized Guidance**: Use `specialized/` files for domain-specific requirements
4. **Follow Documentation Standards**: Apply `documentation/` patterns for content creation
5. **Resolve Conflicts**: Use hierarchy precedence when instructions conflict
6. **Refresh When Needed**: Use `python scripts/agent_helper.py refresh` to reload guidance

## 🎯 Quality Targets

- **Ruff**: All checks must pass (no warnings/errors allowed)
- **Pylint**: Perfect 10.00/10 score required
- **MyPy**: Clean type checking with appropriate flags
- **Bandit**: Zero security vulnerabilities permitted

---

**Maintained By**: HA External Connector Development Team  
**Last Updated**: Automated via instruction validation system
