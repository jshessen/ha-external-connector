# 🏗️ HA Connector Architecture Standards

## 🎯 Core Utility Usage Guidelines

### Standard Import Patterns

**✅ CORRECT - Use absolute imports for core utilities:**

```python
from ha_connector.utils import HAConnectorLogger, ValidationError, AWSError
```

**❌ AVOID - Relative imports or re-export wrappers:**

```python
from ..utils import HAConnectorLogger          # Inconsistent
from .utils import ValidationError             # Pointless wrapper
```

### Logging Standards

**✅ CORRECT - Use enhanced HAConnectorLogger:**

```python
from ha_connector.utils import HAConnectorLogger

logger = HAConnectorLogger("module.submodule")
logger.info("Processing request: %s", request_id)  # Lazy formatting
```

**❌ AVOID - Standard Python logging:**

```python
import logging
logger = logging.getLogger(__name__)           # Missing enhanced features
logger.info(f"Processing {request_id}")        # Performance impact
```

### Directory-Specific Patterns

#### Web Module (`src/ha_connector/web/`)

- **Purpose**: Flask-based web interfaces and APIs
- **Standard imports**: `from ha_connector.utils import HAConnectorLogger, ValidationError`
- **Logging pattern**: `HAConnectorLogger("web.module_name")`

#### CLI Module (`src/ha_connector/cli/`)

- **Purpose**: Command-line interfaces and automation scripts
- **Standard imports**: `from ha_connector.utils import HAConnectorLogger, ValidationError, error_exit`
- **Logging pattern**: `HAConnectorLogger("cli.command_name")`

#### Integration Module (`src/ha_connector/integrations/`)

- **Purpose**: Service-specific integration implementations
- **Standard imports**: `from ha_connector.utils import HAConnectorLogger, ValidationError`
- **Logging pattern**: `HAConnectorLogger("integrations.service_name")`

## 🚫 Anti-Patterns to Avoid

### 1. Utils Duplication

**❌ DO NOT create service-specific utils wrappers:**

```python
# Bad: integrations/utils.py
from ..utils import HAConnectorLogger, ValidationError
# Re-export for convenience  ← This adds no value
```

### 2. Mixed Import Styles

**❌ DO NOT mix import patterns within same module:**

```python
from ha_connector.utils import HAConnectorLogger    # Absolute
from ..utils import ValidationError                 # Relative - inconsistent
```

### 3. Custom Logging Implementations

**❌ DO NOT implement module-specific loggers:**

```python
# Bad: Custom logger per module
def setup_module_logger():
    logger = logging.getLogger("custom")
    # Custom setup code...
```

## ✅ Quality Standards

### Code Organization

- **Single source of truth**: Core utilities in `ha_connector.utils`
- **Consistent imports**: Always use absolute imports for project modules
- **Enhanced logging**: Use HAConnectorLogger throughout for consistent features

### Line Length Management

- **Automatic formatting**: Use `ruff format` for most issues
- **Complex strings**: Break long descriptions/URLs at logical boundaries
- **F-strings**: Extract to variables when too long for single line

### Refactoring Guidelines

- **Function complexity**: Extract helpers when Pylint reports R0912/R0915
- **Parameter count**: Use Pydantic configuration objects for >5 parameters
- **Import validation**: Always test imports after refactoring: `python -c "from module import class"`

## 🔄 Quality Maintenance Workflow

### Before Adding New Features

1. Check existing `ha_connector.utils` for reusable functionality
2. Use standard import patterns from this guide
3. Implement enhanced logging with HAConnectorLogger

### After Code Changes

1. Run `ruff format src/` for automatic formatting
2. Run `ruff check src/ --no-fix` to identify remaining issues
3. Test imports: `python -c "from new_module import new_class"`

### Code Review Checklist

- [ ] Uses `from ha_connector.utils import` for core utilities
- [ ] Uses `HAConnectorLogger("module.name")` for logging
- [ ] No new utils wrapper files created
- [ ] Line length under 88 characters
- [ ] All imports tested and functional

## 📚 Background: Why These Standards Matter

**Historical Context**: This project grew organically with inconsistent patterns:

- Mixed import styles across 50+ Python files
- Pointless re-export wrappers that added confusion
- Quality regression with 62 line length violations during refactoring
- Standard logging mixed with enhanced HAConnectorLogger

**Solution**: Systematic cleanup eliminated architectural debt while preserving functionality:

- ✅ Removed redundant `integrations/utils.py`
- ✅ Standardized all imports to absolute paths
- ✅ Unified logging approach
- ✅ Reduced quality violations by 50%

**Result**: Clean, maintainable architecture that supports growth in web, cli, and integration directories without duplicating utility functionality.
