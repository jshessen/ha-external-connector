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

**🔧 BOTO3 TYPE HANDLING:**

**✅ TYPES-BOTO3 PACKAGES (PREFERRED):**

Use the `types-boto3` package family for the most accurate AWS client type annotations:

```bash
# Install types-boto3 packages for needed services
pip install types-boto3[iam,lambda,ssm]
```

**✅ IMPORT PATTERN:**

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import AWS client types from types-boto3 packages
    from types_boto3_iam.client import IAMClient
    from types_boto3_lambda.client import LambdaClient
    from types_boto3_ssm.client import SSMClient
```

**✅ CLIENT CREATION PATTERN (MYPY/PYLANCE COMPATIBILITY):**

```python
@property
def iam_client(self) -> IAMClient:
    """Get IAM client with explicit type annotation."""
    return boto3.client("iam", region_name=self.region)  # pyright: ignore
```

**🚨 TYPE CHECKER BEHAVIOR:**

- **MyPy**: Passes cleanly with types-boto3 packages
- **Pylance/Pyright**: Requires `# pyright: ignore` due to overloaded boto3.client() signatures
- **Acceptable Exception**: This is one of the few cases where type ignore is acceptable due to fundamental differences between type checkers

**🔧 DEPENDENCY INJECTION PATTERN (PREFERRED FOR PRODUCTION):**

```python
from typing import TYPE_CHECKING, Optional
import boto3

if TYPE_CHECKING:
    from types_boto3_lambda.client import LambdaClient
    from types_boto3_iam.client import IAMClient

class AWSManager:
    def __init__(
        self,
        region: str = "us-east-1",
        lambda_client: Optional[LambdaClient] = None,
        iam_client: Optional[IAMClient] = None
    ) -> None:
        self.region = region
        # Support dependency injection for better testability
        self._lambda_client: LambdaClient = lambda_client or boto3.client(
            "lambda", region_name=region
        )  # pyright: ignore
        self._iam_client: IAMClient = iam_client or boto3.client("iam")  # pyright: ignore
```

**🔗 TESTING INTEGRATION:**

- See **AWS Client Testing Patterns** section for comprehensive testing approaches
- Use dependency injection for better testability and maintainability
- Consider `moto` library for realistic AWS service mocking
- types-boto3 packages provide superior type inference compared to boto3-stubs

**❌ AVOID PATTERNS:**

```python
# Don't use cast when direct annotation works
self._client = cast(LambdaClient, boto3.client("lambda"))

# Don't use generic type ignore without specifying checker
return boto3.client("lambda")  # type: ignore

# Don't use boto3-stubs when types-boto3 is available
from mypy_boto3_lambda import LambdaClient  # Use types_boto3_lambda.client instead
```

**🔧 MYPY CONFIGURATION:**

- Run with `--ignore-missing-imports` for internal modules
- Import warnings for `ha_connector.*` modules are expected and normal
- Focus on actual type errors, not missing stub warnings
- types-boto3 packages provide cleaner MyPy integration than boto3-stubs

## Test Architecture Standards

### AWS Testing Requirements

**🚨 MANDATORY AWS MOCKING STANDARD:**

- **ALL AWS testing MUST use `moto` library**
- **NO exceptions for `unittest.mock` with AWS services**
- **Performance requirement**: Test suites must complete in <20 seconds
- **Consistency requirement**: All AWS tests use identical mocking approach

**✅ REQUIRED MOTO PATTERNS:**

```python
# Fixture pattern (preferred for shared setup)
@pytest.fixture
def aws_framework() -> Iterator[AWSTestFramework]:
    with mock_aws():
        framework = AWSTestFramework()
        yield framework

# Context manager pattern (preferred for isolated tests)
def test_aws_functionality():
    with mock_aws():
        # All AWS operations mocked realistically
        manager = AWSResourceManager()
        result = manager.create_resource(spec)

# Decorator pattern (preferred for single test functions)
@mock_aws
def test_lambda_deployment():
    # Entire test function has AWS services mocked
    installer = ServiceInstaller()
    installer.deploy_lambda(config)
```

**❌ PROHIBITED PATTERNS:**

- `@patch("boto3.client")` - Use moto instead
- `MagicMock()` for AWS clients - Use moto instead
- Manual AWS response mocking - Use moto instead
- Real AWS client creation in tests - Use moto instead

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

### AWS Client Testing Patterns

**✅ MANDATORY: MOTO LIBRARY FOR ALL AWS MOCKING**

All AWS service testing MUST use the `moto` library with `@mock_aws` decorator or `mock_aws()` context manager. This ensures consistent, realistic AWS service behavior across all tests.

**🚨 CRITICAL RULE: NO UNITTEST.MOCK FOR AWS SERVICES**

- **✅ REQUIRED**: Use `moto` library for all AWS client mocking
- **❌ PROHIBITED**: Using `unittest.mock.patch` on `boto3.client` or AWS service methods
- **❌ PROHIBITED**: Creating manual Mock objects for AWS clients
- **❌ PROHIBITED**: Patching individual AWS service methods without moto

**✅ MOTO LIBRARY PATTERN (MANDATORY FOR AWS TESTING):**

```python
# Install: pip install moto[lambda,iam,ssm]
from moto import mock_aws
import boto3
import pytest

# Method 1: Decorator (preferred for test functions)
@mock_aws
def test_lambda_validation_with_moto():
    """Test Lambda validation using moto for realistic AWS mocking"""
    # Create real boto3 clients that will be intercepted by moto
    lambda_client = boto3.client("lambda", region_name="us-east-1")

    # Create a test Lambda function using moto
    lambda_client.create_function(
        FunctionName="test-function",
        Runtime="python3.11",
        Role="arn:aws:iam::123456789012:role/test-role",
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": b"fake code"},
        Description="Test function for validation",
    )

    # Test with real AWS client behavior (mocked by moto)
    validator = LambdaSecurityValidator()
    results = validator.validate_function("test-function")
    assert len(results) > 0

# Method 2: Context manager (preferred for setup/teardown)
def test_aws_manager_initialization():
    """Test AWS manager with moto context manager"""
    with mock_aws():
        manager = AWSResourceManager(region="us-east-1")
        # All AWS calls within this block are mocked by moto
        result = manager.create_resource(resource_type, spec)
        assert result.status == "success"

# Method 3: Fixture (preferred for shared setup)
@pytest.fixture
def aws_framework() -> Iterator[AWSTestFramework]:
    """Provide an AWS test framework instance with moto."""
    with mock_aws():
        framework = AWSTestFramework()
        yield framework
```

**✅ DEPENDENCY INJECTION PATTERN (PREFERRED FOR PRODUCTION CODE):**

Design AWS-dependent classes to accept clients as constructor parameters for better testability with moto.

```python
# Production code with dependency injection
from typing import TYPE_CHECKING, Optional
import boto3

if TYPE_CHECKING:
    from types_boto3_lambda.client import LambdaClient
    from types_boto3_iam.client import IAMClient

class AWSManager:
    def __init__(
        self,
        region: str = "us-east-1",
        lambda_client: Optional[LambdaClient] = None,
        iam_client: Optional[IAMClient] = None
    ) -> None:
        self.region = region
        # Support dependency injection for better testability with moto
        self._lambda_client: LambdaClient = lambda_client or boto3.client(
            "lambda", region_name=region
        )  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
        self._iam_client: IAMClient = iam_client or boto3.client(
            "iam", region_name=region
        )  # pyright: ignore[reportArgumentType, reportUnknownMemberType]

# Test code using moto with dependency injection
@mock_aws
def test_aws_manager_with_moto():
    """Test AWS manager using moto-created clients"""
    # Create real boto3 clients (mocked by moto)
    lambda_client = boto3.client("lambda", region_name="us-east-1")
    iam_client = boto3.client("iam", region_name="us-east-1")

    # Inject moto-mocked clients
    manager = AWSManager(
        region="us-east-1",
        lambda_client=lambda_client,
        iam_client=iam_client
    )

    # All AWS operations use realistic moto behavior
    result = manager.create_lambda_function(spec)
    assert result.status == "created"
```

**✅ PERFORMANCE OPTIMIZATION WITH MOTO:**

Use moto context managers to avoid expensive boto3 client creation during test setup.

```python
# SLOW (creates real boto3 clients - 90+ seconds for test suite)
class TestServiceInstaller:
    def setup_method(self) -> None:
        self.installer = ServiceInstaller()  # Creates real AWS clients

# FAST (uses moto-mocked clients - <15 seconds for test suite)
class TestServiceInstaller:
    def setup_method(self) -> None:
        with mock_aws():
            self.installer = ServiceInstaller()  # Creates moto-mocked clients
```

**❌ PROHIBITED PATTERNS:**

```python
# ❌ NEVER: Manual mocking of AWS services
@patch("boto3.client")
def test_bad_aws_mocking(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    # This bypasses realistic AWS behavior

# ❌ NEVER: Patching individual AWS methods
@patch("ha_connector.adapters.aws_manager.AWSLambdaManager.create_function")
def test_bad_method_patching(mock_create):
    # This breaks AWS service integration testing

# ❌ NEVER: Creating manual Mock AWS clients
def test_bad_manual_mocking():
    mock_lambda_client = MagicMock()
    mock_lambda_client.create_function.return_value = {"fake": "response"}
    # This doesn't test realistic AWS behavior

# ❌ NEVER: Mixing unittest.mock with AWS services
class TestAWSIntegration:
    @patch("boto3.client")  # Wrong approach
    def test_mixed_mocking_antipattern(self, mock_client):
        # Use moto instead
```

**🎯 MOTO TESTING PRINCIPLES:**

- **Realistic Behavior**: Moto provides actual AWS service simulation
- **Consistent Mocking**: All AWS tests use the same mocking approach
- **Performance**: Significantly faster than real AWS clients (90s → 15s improvement)
- **Comprehensive**: Supports all major AWS services with realistic responses
- **Type Safety**: Works seamlessly with types-boto3 packages
- **Error Simulation**: Can test AWS error conditions realistically

**🔧 MOTO CONFIGURATION REQUIREMENTS:**

```python
# Required moto installation for project
pip install moto[lambda,iam,ssm,logs,sts]

# Standard imports in all AWS tests
from moto import mock_aws
import boto3
import pytest

# Type checking imports (when needed)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from types_boto3_lambda.client import LambdaClient
    from types_boto3_iam.client import IAMClient
    # ... other AWS service types
```

**🚨 MIGRATION FROM UNITTEST.MOCK TO MOTO:**

If existing tests use `unittest.mock` for AWS services, they MUST be migrated to moto:

```python
# OLD (prohibited pattern)
@patch("boto3.client")
def test_old_pattern(mock_boto3):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    # Test implementation...

# NEW (required pattern)
@mock_aws
def test_new_pattern():
    lambda_client = boto3.client("lambda", region_name="us-east-1")
    # Create realistic test resources
    lambda_client.create_function(...)
    # Test with real AWS behavior (mocked by moto)
```

**✅ BENEFITS OF MANDATORY MOTO USAGE:**

- **60-80% Test Performance Improvement**: Eliminates real boto3 client creation overhead
- **Realistic AWS Behavior**: Tests actual AWS service responses and error conditions
- **Consistent Testing**: All AWS tests use the same reliable mocking approach
- **Better Error Testing**: Can simulate AWS service failures and edge cases
- **Type Safety**: Full compatibility with types-boto3 packages
- **Maintainability**: Reduces complex mock setup and maintenance
- **Production Confidence**: Tests closer to real AWS behavior

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

- **Mandatory moto usage**: Eliminates 60-80% of AWS test overhead (90s → 15s improvement)
- Session-scoped fixtures for expensive setup (additional 60-80% performance improvement)
- Mock external API calls to prevent network delays
- Efficient resource cleanup with context managers
- Batch operations where possible

**🎯 AWS TESTING PERFORMANCE REQUIREMENTS:**

- **Test suite completion time**: <20 seconds for full AWS test coverage
- **Individual test timing**: <0.5s setup time per test
- **Moto requirement**: ALL AWS tests must use `mock_aws()` - no exceptions
- **Boto3 client creation**: Only within moto context managers to prevent real client overhead

**🚨 PERFORMANCE ANTI-PATTERNS:**

```python
# ❌ SLOW: Real boto3 client creation (causes 90+ second test runs)
def setup_method(self):
    self.manager = AWSResourceManager()  # Creates real clients

# ✅ FAST: Moto-mocked client creation (<15 second test runs)
def setup_method(self):
    with mock_aws():
        self.manager = AWSResourceManager()  # Creates moto clients
```

**🎯 PERFORMANCE PRINCIPLES:**

- Prioritize test speed without compromising coverage
- Cache expensive operations at appropriate scopes
- Use appropriate fixture scopes (`session`, `module`, `function`)
- **Mandatory moto usage eliminates the #1 test performance bottleneck**

## Development Workflow Standards

### VS Code Workspace Configuration

**✅ WORKSPACE SETUP REQUIREMENTS:**

- **Python Interpreter**: Configure VS Code to use the project's virtual environment interpreter
- **Workspace Folder**: Set the project root as the workspace folder for proper path resolution
- **Environment Persistence**: Virtual environment should be active automatically in integrated terminal
- **Tool Integration**: Python tools (ruff, pylint, pytest) should work without manual activation

**🎯 CONFIGURATION VERIFICATION:**

```bash
# Verify correct Python interpreter is selected
which python
# Should output: /path/to/project/.venv/bin/python

# Verify environment is active (prompt should show venv name)
echo $VIRTUAL_ENV
# Should output: /path/to/project/.venv
```

**🔧 BENEFITS OF PROPER WORKSPACE CONFIGURATION:**

- **Simplified Commands**: No need for manual environment activation
- **Reliable Terminal Output**: Commands complete fully without shell sourcing overhead
- **Consistent Environment**: Same Python interpreter and packages across all operations
- **Better IDE Integration**: IntelliSense, debugging, and tool integration work seamlessly

### Terminal Automation Philosophy

**✅ AUTOMATION PRINCIPLES:**

- **VS Code Integration First**: Leverage workspace configuration over manual activation
- **Simplified Command Structure**: Use direct commands when environment is properly configured
- **Allowlist Trusted Commands**: Enable zero-touch automation for development tools
- **Immediate Output Capture**: Prefer approaches that provide complete, reliable terminal output

**✅ PREFERRED COMMAND PATTERNS:**

```bash
# With proper VS Code workspace configuration:
python -m ha_connector.cli.main --help
ruff check src/
python -m pytest tests/
black --check src/

# Use direct executable paths in tasks and scripts:
${workspaceFolder}/.venv/bin/python -m pytest  # ✅ Explicit and reliable
```

**🚨 FALLBACK PATTERNS:**

```bash
# Only use full paths when workspace configuration is unavailable:
/full/path/to/.venv/bin/python -m pytest tests/
/full/path/to/.venv/bin/ruff check src/
```

## Environment Management Standards

### Virtual Environment Integration

**✅ ENVIRONMENT SETUP HIERARCHY (in order of preference):**

1. **VS Code Workspace Integration**: Configure Python interpreter and workspace folder
2. **Python Environment Configuration Tools**: Use VS Code's Python environment tools
3. **Manual Activation**: Only as fallback when automated approaches unavailable
4. **Full Path Execution**: Last resort for problematic environments

**🎯 WORKSPACE-FIRST PHILOSOPHY:**

- **IDE Integration**: Leverage VS Code's Python environment management
- **Tool Consistency**: All Python tools should work without manual activation
- **Development Efficiency**: Minimize overhead and maximize reliability
- **Terminal Reliability**: Prefer approaches that provide complete command output

**✅ VERIFICATION CHECKLIST:**

```bash
# 1. Verify Python interpreter
which python  # Should point to project .venv

# 2. Test core tools without activation
ruff --version
black --version
pytest --version

# 3. Test project CLI
python -m ha_connector.cli.main --help

# 4. Verify environment variables if needed
echo $VIRTUAL_ENV  # Should show project venv path
```

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

**🔧 TROUBLESHOOTING ENVIRONMENT ISSUES:**

```bash
# If tools aren't found, check Python path
python -c "import sys; print(sys.executable)"

# If modules aren't found, verify PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

# If VS Code doesn't detect venv, restart and select interpreter
# Command Palette: Python: Select Interpreter

# If terminal commands fail, verify workspace folder is project root
pwd  # Should show project root directory
```

**❌ COMMON PITFALLS TO AVOID:**

- **Wrong Working Directory**: Commands run from incorrect folder
- **System Python**: VS Code using system Python instead of venv
- **Stale Terminal**: Terminal session not reflecting current interpreter
- **Mixed Environments**: Switching between different activation methods

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

**Key Philosophy**: *Quality, Security, and Performance are non-negotiable. Modern patterns and practices should be adopted consistently to prevent regression to legacy approaches. Workspace configuration and IDE integration should be leveraged to maximize development efficiency and reliability. AWS client dependency injection should be used to enhance testability and maintainability.*

**Major Standards Added in Version 1.2:**

- **AWS Client Dependency Injection**: Comprehensive patterns for testable AWS client code
- **Moto Integration**: Guidelines for realistic AWS service mocking
- **Enhanced boto3 Patterns**: Improved type safety with dependency injection support

**Last Updated**: July 24, 2025
**Version**: 1.2 - Added AWS client dependency injection and testing patterns
