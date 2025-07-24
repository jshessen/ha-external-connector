# Project Standards & Development Philosophy

## Overview

This document defines the established standards, patterns, and philosophical approaches for the HA External Connector project. These standards have been developed through iterative refinement and should guide all future development decisions.

## Code Quality Philosophy

### Zero-Tolerance Quality Standards

**✅ MANDATORY TARGETS:**

- **Ruff**: All checks must pass (no warnings/errors allowed)
- **Pylint**: Perfect 10.00/10 score required
- **Bandit**: Zero security vulnerabilities permitted
- **MyPy**: Clean type checking with appropriate flags

**🎯 QUALITY PRINCIPLES:**

- **No suppression without justification**: Avoid `# pylint: disable` comments except for architectural constraints which cannot be resolved with proper coding practices.
- **Fix root causes, not symptoms**: Address underlying issues, not warnings
- **Modern Python patterns**: Use current best practices over legacy approaches
- **Security first**: Always prioritize security over convenience

**🚨 ARCHITECTURAL EXEMPTIONS:**

- **AWS Lambda Functions**: May use `# pylint: disable=duplicate-code` due to standalone requirements
- **CLI Commands**: May use `# pylint: disable=too-many-arguments` for legitimate user interfaces
- **Context Objects**: May use `# pylint: disable=too-many-arguments` for initialization parameters

### Type Safety Standards

**✅ TYPE ANNOTATION REQUIREMENTS:**

- All functions must have return type annotations
- All function parameters must be typed
- Use modern Python typing syntax (`dict` vs `Dict`, `|` vs `Union`)
- Generator types must specify full `Generator[YieldType, SendType, ReturnType]`

**🔧 MYPY CONFIGURATION:**

- Run with `--ignore-missing-imports` for internal modules
- Import warnings for `ha_connector.*` modules are expected and normal
- Focus on actual type errors, not missing stub warnings

## Test Architecture Standards

### Fixture Design Pattern

**✅ PREFERRED PATTERN (conftest.py style):**

```python
@pytest.fixture(name="mock_service")
def service_mock() -> ServiceClass:
    """Clear fixture naming using name= parameter"""
    return ServiceClass()
```

**❌ AVOID PATTERN:**

```python
@pytest.fixture
def mock_service() -> ServiceClass:  # pylint: disable=redefined-outer-name
    """Avoid disable comments when possible"""
    return ServiceClass()
```

**🎯 FIXTURE PRINCIPLES:**

- Use `name=` parameter to avoid `redefined-outer-name` issues
- Session-scoped fixtures for expensive operations (AWS clients, secrets)
- Dynamic secret generation with `secrets.token_urlsafe()`
- No hardcoded secrets in test code

### Security in Testing

**✅ SECURITY REQUIREMENTS:**

- Generate test secrets dynamically using `secrets` module
- Session-cached secrets for performance without compromising security
- Secure temporary directories for file operations
- Mock external services to prevent accidental real API calls

## Configuration Management Standards

### Modern Configuration Approach

**✅ CURRENT STANDARD:**

- **Single source of truth**: `pyproject.toml` for all tool configuration
- **No legacy files**: Eliminated redundant `setup.cfg`
- **Centralized settings**: All linting, formatting, and build config in one place

**🔧 CONSOLIDATION PRINCIPLES:**

- Remove duplicate configuration files when consolidating
- Verify tool compatibility with `pyproject.toml` before migration
- Maintain backward compatibility where required

## Security Standards

### Dynamic Secret Management

**✅ SECURITY PATTERNS:**

```python
# Generate secure test secrets
def generate_test_secret(prefix: str = "test", length: int = 32) -> str:
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}-{random_part}"
```

**❌ PROHIBITED PATTERNS:**

```python
# Never hardcode secrets
ALEXA_SECRET = "hardcoded-secret-123"  # ❌ Security violation
```

### Subprocess Security

**✅ SECURE EXECUTION:**

- Use `subprocess.run()` with explicit arguments
- Validate all user inputs before shell execution
- Implement timeout protections for long-running processes
- Use type guards instead of assertions for validation

## Performance Standards

### Test Performance Optimization

**✅ PERFORMANCE PATTERNS:**

- Session-scoped fixtures for expensive setup (60-80% performance improvement)
- Mock external API calls to prevent network delays
- Efficient resource cleanup with context managers
- Batch operations where possible

**🎯 PERFORMANCE PRINCIPLES:**

- Prioritize test speed without compromising coverage
- Cache expensive operations at appropriate scopes
- Use appropriate fixture scopes (`session`, `module`, `function`)

## Development Workflow Standards

### Terminal Automation Philosophy

**✅ AUTOMATION PRINCIPLES:**

- Allowlist trusted development commands for zero-touch automation
- Use `source .venv/bin/activate` pattern for virtual environment consistency
- Prefer direct command execution over complex task configurations
- Enable immediate output capture for better development feedback

### Quality Assurance Workflow

**✅ STANDARD QUALITY CHECKS:**

1. **Ruff**: Fast linting and formatting checks
2. **Pylint**: Comprehensive code quality analysis
3. **Bandit**: Security vulnerability scanning
4. **MyPy**: Type safety validation (with appropriate flags)

**🎯 QUALITY PRINCIPLES:**

- Run quality checks frequently during development
- Address issues immediately rather than accumulating technical debt
- Automate quality checks where possible
- Maintain tool configuration in `pyproject.toml`

## Error Handling Standards

### Graceful Degradation

**✅ ERROR HANDLING PATTERNS:**

- Provide clear, actionable error messages
- Implement proper exception hierarchies
- Use type guards for input validation
- Log errors at appropriate levels

**🔧 RESILIENCE PRINCIPLES:**

- Fail fast with clear error messages
- Provide recovery suggestions where possible
- Validate inputs at system boundaries
- Use timeouts for external operations

## Architectural Standards

### AWS Lambda Function Constraints

**🚨 CRITICAL AWS LAMBDA RULES:**

- **Lambda functions MUST be standalone**: Files in `src/aws/` cannot import from local modules
- **No shared modules in AWS directory**: Lambda functions are deployed as isolated units
- **Duplicate code is acceptable**: Lambda functions require self-contained code
- **Use `# pylint: disable=duplicate-code` liberally**: Lambda architectural constraints override DRY principles
- **Security headers duplication**: Each Lambda must contain its own security constants

**✅ LAMBDA-SPECIFIC PATTERNS:**

```python
# In each Lambda function file - this is REQUIRED duplication
# pylint: disable=duplicate-code
SECURITY_HEADERS = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store, no-cache, must-revalidate",
    # ... other headers
}
```

**❌ PROHIBITED IN AWS LAMBDA DIRECTORY:**

- Local imports between Lambda functions (`from .other_lambda import something`)
- Shared utility modules within `src/aws/`
- Cross-Lambda dependencies
- Refactoring that breaks Lambda isolation

**🔧 LAMBDA DUPLICATION GUIDELINES:**

- Security headers, constants, and utility functions MUST be duplicated
- Each Lambda function is deployed independently and cannot share code
- Use `# pylint: disable=duplicate-code` to suppress warnings for required duplication
- Document why duplication is necessary (deployment architecture)

### Modular Design Patterns

**✅ MODULARITY PRINCIPLES (NON-LAMBDA CODE):**

- Separate concerns into focused modules (except AWS Lambda functions)
- Use dependency injection for testability
- Design for extensibility and maintainability
- Follow single responsibility principle

### API Design Standards

**✅ API CONSISTENCY:**

- Use consistent return types (`AWSResourceResponse`, etc.)
- Implement proper error response patterns
- Provide comprehensive type hints
- Design for both sync and async use cases

## Documentation Standards

### Code Documentation

**✅ DOCUMENTATION REQUIREMENTS:**

- All public functions must have docstrings
- Include parameter and return type documentation
- Provide usage examples for complex functions
- Document security considerations and performance implications

### Project Documentation

**✅ DOCUMENTATION PRINCIPLES:**

- Keep documentation current with code changes
- Provide clear setup and development instructions
- Document architectural decisions and rationale
- Include troubleshooting guides

## Migration Standards

### Legacy Code Modernization

**✅ MIGRATION PRINCIPLES:**

- Modernize configuration files (`setup.cfg` → `pyproject.toml`)
- Update type annotations to current Python standards
- Eliminate deprecated patterns and dependencies
- Maintain backward compatibility during transitions

## Future Development Guidelines

### Adding New Features

**✅ FEATURE DEVELOPMENT CHECKLIST:**

1. ✅ Follow established fixture patterns in tests
2. ✅ Implement proper type annotations
3. ✅ Add security considerations
4. ✅ Include performance optimizations
5. ✅ Update documentation
6. ✅ Verify all quality checks pass

### Refactoring Guidelines

**✅ REFACTORING PRINCIPLES:**

- Identify and eliminate anti-patterns
- Improve type safety incrementally
- Optimize performance bottlenecks
- Enhance security posture
- Maintain test coverage throughout

## Enforcement Mechanisms

### Automated Quality Gates

**✅ CONTINUOUS VALIDATION:**

- All quality tools must pass before code integration
- Automated test execution on changes
- Security scanning in CI/CD pipeline
- Performance regression detection

### Code Review Standards

**✅ REVIEW CRITERIA:**

- Adherence to established patterns
- Security considerations addressed
- Performance implications considered
- Documentation completeness
- Test coverage maintained

---

## Summary

These standards represent the evolved best practices for this project. They should guide all future development decisions and help maintain the high quality standards we've established.

**Key Philosophy**: *Quality, Security, and Performance are non-negotiable. Modern patterns and practices should be adopted consistently to prevent regression to legacy approaches.*

**Last Updated**: July 22, 2025
**Version**: 1.0
