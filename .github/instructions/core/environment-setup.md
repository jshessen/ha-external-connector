# Environment Setup & Terminal Automation

## 🚨 CRITICAL: Environment Activation

**ALWAYS activate the virtual environment first:**

```bash
source .venv/bin/activate
```

**Why this is critical:**

- Commands like `ruff`, `pylint`, `pytest` will fail with "command not found" without activation
- System Python may be used instead of project environment
- Import paths may not be set correctly for project modules

## Streamlined Environment Commands

### New Unified Commands

```bash
# Single command environment setup and validation
python scripts/agent_helper.py setup

# Quick health check
python scripts/agent_helper.py check

# Full environment validation
python scripts/agent_helper.py env

# Refresh agent instructions (new feature)
python scripts/agent_helper.py refresh
```

## Terminal Automation Configuration

### Essential VS Code Allowlist Commands

```json
{
  "github.copilot.chat.agent.terminal.allowList": {
    // Core commands
    "python": true,
    "source": true,
    "echo": true,
    "ls": true,
    "pwd": true,
    "cat": true,
    "git": true,
    "mv": true,
    "cp": true,
    "mkdir": true,
    
    // Development tools
    "ruff": true,
    "pylint": true,
    "mypy": true,
    "pytest": true,
    "make": true
  }
}
```

### AWS CLI Configuration

**🚨 MANDATORY: Always use `--no-cli-pager` with AWS commands**

```bash
# ✅ CORRECT: Disable pager for automation compatibility
aws lambda list-functions --no-cli-pager
aws logs describe-log-streams --log-group-name /aws/lambda/HomeAssistant --no-cli-pager

# ❌ WRONG: Default pager will block terminal automation
aws lambda list-functions  # Will hang waiting for user input
```

## Development Environment Validation

### Required Environment Checks

```bash
# 1. Python version (3.11+)
python --version

# 2. Virtual environment active
python scripts/agent_helper.py env

# 3. Dependencies installed
python scripts/agent_helper.py imports

# 4. Development tools available
python scripts/agent_helper.py tools
```

### Project Structure Validation

```bash
# Verify essential project structure
ls -la src/ha_connector/     # Core package
ls -la tests/               # Test suite
ls -la scripts/             # Development scripts
ls -la .venv/               # Virtual environment
```

## Quality Assurance Commands

### Fast Development Workflow

```bash
# Quick quality check
source .venv/bin/activate && ruff check src/

# Comprehensive analysis
source .venv/bin/activate && pylint src/

# Type checking
source .venv/bin/activate && mypy src/

# Run tests
source .venv/bin/activate && pytest
```

### Auto-fix Capabilities

```bash
# Auto-fix code style issues
source .venv/bin/activate && ruff check --fix src/

# Format code
source .venv/bin/activate && ruff format src/

# Organize imports
source .venv/bin/activate && ruff check --select I --fix src/
```

## Environment Troubleshooting

### Common Issues and Solutions

**Issue**: `ruff: command not found`
**Solution**: 
```bash
source .venv/bin/activate
# Verify with: which ruff
```

**Issue**: Import errors in scripts
**Solution**:
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
# Or use agent helper
python scripts/agent_helper.py imports
```

**Issue**: VS Code shows wrong Python interpreter
**Solution**:
```bash
# Command Palette: Python: Select Interpreter
# Choose: ./.venv/bin/python
```

## Agent Helper Enhancement

### Extended Functionality

The `scripts/agent_helper.py` script provides these enhanced commands:

- **`setup`** - Complete environment setup with validation
- **`check`** - Quick health check of environment and tools
- **`refresh`** - Reload agent instructions and validate consistency
- **`activate-and-validate`** - Single command for full environment activation

### Usage Examples

```bash
# Start of development session
python scripts/agent_helper.py setup

# During development - quick checks
python scripts/agent_helper.py check

# When instructions seem stale or inconsistent
python scripts/agent_helper.py refresh

# Validate all systems
python scripts/agent_helper.py all
```

## Performance Optimization

### Container-Level Optimization

```bash
# Use consistent Python executable
export PYTHON_EXECUTABLE=$(pwd)/.venv/bin/python

# Cache validation results
export HA_CONNECTOR_ENV_VALIDATED=1
```

### Batch Operations

```bash
# Combined quality check
source .venv/bin/activate && \
ruff check src/ && \
pylint src/ && \
mypy src/ && \
pytest tests/ -v
```

## Integration with IDE

### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "python.testing.pytestEnabled": true,
  "github.copilot.chat.agent.terminal.allowList": {
    "python": true,
    "source": true,
    "ruff": true,
    "pylint": true,
    "mypy": true,
    "pytest": true
  }
}
```

### Terminal Integration

```bash
# Add to shell profile (.bashrc, .zshrc)
alias ha-setup="cd /path/to/ha-external-connector && source .venv/bin/activate"
alias ha-check="python scripts/agent_helper.py check"
alias ha-lint="source .venv/bin/activate && ruff check src/"
```

---

**Key Principle**: Single command setup with comprehensive validation reduces friction and ensures consistent development environment across all sessions.