---
description: "Code quality and refactoring patterns for HA External Connector"
applyTo: "**/*.py"
---

# Code Quality and Refactoring Patterns

## Function Complexity Refactoring (Lessons from alexa_setup)

### When to Refactor (Pylint R-family triggers)

**Triggers for immediate refactoring:**

- **R0917**: Too many positional arguments (>5) - Consider parameter objects
- **R0912**: Too many branches (>12) - Extract decision logic into helper functions
- **R0915**: Too many statements (>50) - Decompose into logical steps
- **R0914**: Too many local variables (>15) - Group related variables into classes

### Decomposition Strategy

#### Correct Pattern: Step-by-step Function Decomposition

```python
# BEFORE: Monolithic function with 86 statements, 23 branches
def complex_alexa_setup(param1, param2, param3, param4, param5, param6, param7, param8, param9):
    """Massive function doing everything."""
    # 86 lines of mixed logic...

# AFTER: Clean main function with helper functions
class AlexaSetupConfig(BaseModel):
    """Configuration object to reduce parameter count."""
    function_name: str
    skill_id: Optional[str] = None
    region: str
    verbose: bool
    # ... other parameters

def alexa_setup(params...):  # pylint: disable=too-many-positional-arguments
    """Main function now reads like a workflow."""
    config = AlexaSetupConfig(...)
    alexa_manager = AlexaSkillManager(region=config.region)

    # Clear step-by-step execution
    _validate_alexa_region(alexa_manager, config)
    _setup_alexa_trigger(alexa_manager, config)
    _generate_test_data(alexa_manager, config)
    _generate_configuration_guide(alexa_manager, config)
    _validate_home_assistant_config(alexa_manager, config)
    _display_alexa_setup_summary(config)

def _validate_alexa_region(alexa_manager: AlexaSkillManager, config: AlexaSetupConfig) -> None:
    """Single responsibility: region validation only."""
    # Focused logic for one specific task

def _setup_alexa_trigger(alexa_manager: AlexaSkillManager, config: AlexaSetupConfig) -> None:
    """Single responsibility: trigger setup only."""
    # Focused logic for one specific task
```

**Key principles:**

1. **Configuration Objects**: Use Pydantic models to group related parameters
2. **Single Responsibility**: Each helper function has one clear purpose
3. **Workflow Clarity**: Main function reads like a high-level workflow
4. **Type Safety**: Maintain strong typing throughout decomposition

### CLI Function Exception Handling

#### Required Pattern: CLI Functions Need Targeted Suppression

```python
def cli_command(  # pylint: disable=too-many-positional-arguments
    param1: str,
    param2: str,
    # ... 9+ parameters for comprehensive CLI
):
    """CLI commands inherently need many parameters - this is architectural."""
    # Implementation
```

**Justification**: CLI interfaces require many parameters for user flexibility. This is an architectural constraint, not a design flaw.

## Exception Handling Patterns

### Replace Broad Exception Catching

#### Avoid Pattern: Broad Exception Catching

```python
try:
    aws_operation()
except Exception as e:
    logger.error(f"Something failed: {e}")
```

#### Correct Pattern: Specific Exception Handling

```python
try:
    aws_operation()
except (ValidationError, ClientError) as e:
    logger.error("AWS operation failed: %s", str(e))
except (OSError, KeyError) as e:
    logger.error("System or data error: %s", str(e))
```

### Exception Chain Strategy

**Always use `raise ... from e` for proper exception chaining:**

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error("Operation failed: %s", str(e))
    raise typer.Exit(1) from e  # Preserves original traceback
```

## Import Pattern Standards

### Absolute vs Relative Imports

#### Avoid Pattern: Relative Imports (E0402)

```python
from ..utils import ValidationError  # Can cause import resolution issues
from .aws_manager import AWSManager  # Relative import
```

#### Correct Pattern: Absolute Imports

```python
from ha_connector.utils import ValidationError  # Clear absolute path
from ha_connector.aws.aws_manager import AWSManager  # Explicit absolute import
```

**Benefits:**

- **Import clarity**: Makes module relationships explicit
- **IDE support**: Better autocomplete and navigation
- **Refactoring safety**: Moving files doesn't break imports
- **Testing compatibility**: Absolute imports work consistently in test environments

## Logging Format Compliance (W1203)

### Lazy % Formatting (MANDATORY)

#### Avoid Pattern: f-string Formatting in Logging

```python
logger.info(f"Processing {count} items for {user}")
logger.error(f"Failed to connect to {host}:{port}")
```

#### Correct Pattern: Lazy % Formatting

```python
logger.info("Processing %d items for %s", count, user)
logger.error("Failed to connect to %s:%d", host, port)
```

**Benefits:**

- Performance: String formatting only happens if log level is enabled
- Structured logging: Log aggregators can parse parameters properly
- Security: Prevents injection attacks through user data

### Complex Logging Scenarios

```python
# ✅ Multiple parameters
logger.warning("User %s exceeded limit %d by %d requests",
               username, rate_limit, excess_count)

# ✅ Exception logging with context
try:
    operation()
except ClientError as e:
    logger.error("AWS operation failed for region %s: %s",
                 region, str(e), exc_info=True)
```

## TypedDict Safety Patterns

### AWS Boto3 Response Handling

#### Avoid Pattern: Direct Dictionary Access

```python
try:
    lambda_client.invoke(FunctionName="test")
except ClientError as e:
    error_code = e.response["Error"]["Code"]  # KeyError risk
```

#### Correct Pattern: Safe Dictionary Access

```python
try:
    lambda_client.invoke(FunctionName="test")
except ClientError as e:
    error_info = e.response.get("Error", {})
    error_code = error_info.get("Code", "UnknownError")
    error_message = error_info.get("Message", "No error message")
```

### Pattern for AWS Response Processing

```python
def process_aws_response(response: Dict[str, Any]) -> ProcessedResult:
    """Safely process AWS API responses."""
    # Extract with defaults for optional fields
    function_arn = response.get("FunctionArn", "unknown")
    state = response.get("State", "Unknown")

    # Handle nested dictionaries safely
    config_info = response.get("Configuration", {})
    runtime = config_info.get("Runtime", "unknown")

    return ProcessedResult(
        arn=function_arn,
        state=state,
        runtime=runtime
    )
```

### Boto3 Client Type Annotation Pattern

#### Correct Pattern: Import in TYPE_CHECKING Block

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_boto3_lambda.client import LambdaClient

class MyManager:
    def __init__(self, lambda_client: "LambdaClient | None" = None) -> None:
        self._lambda_client = lambda_client

    @property
    def lambda_client(self) -> "LambdaClient":
        """Get Lambda client with lazy initialization."""
        if self._lambda_client is None:
            self._lambda_client = boto3.client(  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
                "lambda", region_name=self.region
            )
        return self._lambda_client
```

**Key points:**

- Import boto3 client types only in `TYPE_CHECKING` blocks
- Use quoted type annotations for forward references
- Use `# pyright: ignore[reportArgumentType, reportUnknownMemberType]` for boto3.client() calls
- This resolves MyPy/Pylance compatibility issues with boto3 dynamic client creation

## Refactoring Process Guidelines

### Step-by-step Refactoring Approach

1. **Identify Complexity Issues**: Use Pylint R-family rules to find targets
2. **Preserve Functionality**: All refactoring must maintain exact behavior
3. **Extract Helper Functions**: Group related logic into focused functions
4. **Create Configuration Objects**: Use Pydantic models for parameter management
5. **Validate Continuously**: Run tests and linting after each refactoring step
6. **Document Architectural Constraints**: Use targeted `# pylint: disable` with justification

### Quality Gates During Refactoring

```bash
# After each refactoring step, validate:
ruff check src/ha_connector/cli/commands.py  # Must pass
python -c "from src.module import function; print('✅ Import works')"  # Must import
pytest tests/test_module.py -v  # Tests must still pass
```

### Refactoring Success Metrics

- **Function line count**: Reduced from 86+ to <20 lines in main function
- **Branching complexity**: Each helper function has <5 branches
- **Parameter count**: Main function uses configuration objects for >5 parameters
- **Single responsibility**: Each function has one clear, testable purpose

## Code Review Checklist

### Before Submitting Code

- [ ] All Ruff checks pass (`ruff check src/`)
- [ ] Logging uses lazy % formatting (no f-strings in logging calls)
- [ ] Exception handling is specific, not broad `Exception` catches
- [ ] AWS responses use `.get()` for safe dictionary access
- [ ] Functions with >50 statements are decomposed into helpers
- [ ] CLI functions with >5 parameters use configuration objects
- [ ] All imports work correctly after refactoring
- [ ] Tests still pass after refactoring

### Architectural Decisions

- **CLI Parameter Count**: CLI functions naturally need many parameters - use targeted disable
- **Helper Function Organization**: Group related helper functions near their main function
- **Configuration Objects**: Use Pydantic models for type safety and validation
- **Exception Chaining**: Always preserve original traceback with `raise ... from e`

## Performance Considerations

### Logging Performance

```python
# ✅ Efficient: Only formats if debug enabled
logger.debug("Processing item %d of %d: %s", current, total, item_name)

# ❌ Inefficient: Always formats string
logger.debug(f"Processing item {current} of {total}: {item_name}")
```

### Memory Management in Large Functions

- **Before refactoring**: Large functions hold all variables in memory
- **After refactoring**: Helper functions release memory after completion
- **Benefit**: Better memory utilization for long-running processes

## Validation Commands for Quality Assurance

### After Code Changes - Run These Commands

```bash
# 1. Import validation - ensure refactoring didn't break imports
python -c "from module.path import ClassName; print('✅ Import works')"

# 2. Ruff comprehensive check
source .venv/bin/activate && ruff check src/ tests/ scripts/

# 3. MyPy type checking
source .venv/bin/activate && mypy src/ tests/ scripts/

# 4. Specific file validation
source .venv/bin/activate && ruff check path/to/file.py --no-fix
```

### Quality Gate Validation

```bash
# Complete validation pipeline
source .venv/bin/activate
ruff check src/ tests/ scripts/ && \
mypy src/ tests/ scripts/ && \
python -c "from ha_connector.aws.alexa_skill_manager import AlexaSkillManager; print('✅ All imports working')" && \
echo "✅ All quality checks passed!"
```

### Common Fix Commands

```bash
# Auto-fix most issues
source .venv/bin/activate && ruff check --fix src/ tests/ scripts/

# Format code
source .venv/bin/activate && ruff format src/ tests/ scripts/

# Fix import organization
source .venv/bin/activate && ruff check --select I --fix src/ tests/ scripts/
```

---

**Key Takeaway**: Address root causes (complexity, unclear responsibilities) rather than symptoms (individual warnings). Well-structured code naturally avoids most quality issues.
