# VS Code GitHub Copilot Terminal Automation Setup

## 🚨 CRITICAL: Post-Reload Environment Activation

**When VS Code reloads, ALWAYS run this first:**

```bash
source .venv/bin/activate
```

**Why this is critical:**

- VS Code UI may show the correct interpreter (.venv)
- But `run_in_terminal` tool creates new terminals without environment activation
- Without activation: `ruff`, `black`, `pytest` commands will fail with "command not found"
- Tools like `poetry` may work but use system Python instead of project environment

## Quick Start: Enable Automated Terminal Commands

### 1. Configure User Settings

Add this to your VS Code user settings (`~/.config/Code/User/settings.json` on Linux):

```json
{
  "github.copilot.chat.agent.terminal.allowList": {
    // === GENERAL COMMANDS ===
    "echo": true,
    "ls": true,
    "pwd": true,
    "cat": true,
    "head": true,
    "tail": true,
    "wc": true,
    "grep": true,
    "find": true,
    "test": true,
    "git": true,
    "mv": true,
    "cp": true,
    "mkdir": true,
    "touch": true,
    "which": true,
    "whoami": true,
    "date": true,
    "source": true,

    // === PYTHON DEVELOPMENT ===
    "python": true,
    "pip": true,
    "poetry": true,
    "ruff": true,
    "pylint": true,
    "mypy": true,
    "flake8": true,
    "bandit": true,
    "black": true,
    "pytest": true,
    "make": true
  }
}
```

### 2. Activate in VS Code UI

1. Open **Settings** → **Extensions** → **GitHub Copilot** → **Agent** → **Terminal: Allow List**
2. Add each command individually using the **"Add Item"** button
3. Both JSON configuration AND UI activation are required

### 3. Test Your Setup

Commands should now run without approval prompts:

```bash
echo "Testing allowlist"           # ✅ Works automatically
python --version                   # ✅ Works automatically (in VS Code terminal)
ruff check src/                    # ✅ Works automatically (in VS Code terminal)
```

## Development Workflow Best Practices

### Virtual Environment Usage

**✅ Recommended Pattern for VS Code Tasks:**

```bash
# Use direct executable paths in tasks and scripts
${workspaceFolder}/.venv/bin/python --version
${workspaceFolder}/.venv/bin/ruff check src/
```

**✅ Recommended Pattern for Terminal:**

```bash
python --version             # Use simple command names in VS Code terminal
ruff check src/              # All tools work automatically
```

### Command Matching Rules

- **Simple names work**: `"python": true` covers both system and venv Python
- **Full paths don't match**: `.venv/bin/python` requires separate allowlist entry
- **VS Code handles activation**: Environment is automatically available in terminal

## File Locations

| Platform | User Settings Location |
|----------|------------------------|
| **Linux** | `~/.config/Code/User/settings.json` |
| **macOS** | `~/Library/Application Support/Code/User/settings.json` |
| **Windows** | `%APPDATA%\Code\User\settings.json` |

## How Terminal Automation Works

### Technical Implementation

The allowlist enables **direct subprocess execution with full output capture**:

```text
Agent → run_in_terminal → Direct Process → Complete Output → Agent
```

**Key mechanisms:**

- **Synchronous execution**: Tool waits for command completion (`isBackground=false`)
- **Complete output capture**: Both stdout and stderr returned immediately
- **No UI interruption**: Allowlisted commands bypass approval prompts
- **Pipeline support**: Complex commands like `ruff check src/ | head -10` work seamlessly

### VS Code Tasks vs Direct Commands

#### VS Code Tasks (Complex Approach)

```json
{
  "command": "/bin/bash",
  "args": ["-c", "python scripts/lint.py 2>&1 | tee output.log"]
}
```

**Issues:**

- Output goes to terminal UI, not agent
- Requires file redirection + polling
- Asynchronous execution complexity

#### Direct Terminal (Recommended)

```bash
# In VS Code terminal (environment is automatically available)
python scripts/lint.py

# Or using explicit path in scripts/tasks
${workspaceFolder}/.venv/bin/python scripts/lint.py
```

**Advantages:**

- Immediate output capture
- Single-step execution
- Full subprocess control

## Key Benefits

- **Zero-touch automation** for development workflows
- **Immediate output capture** without file I/O complexity
- **Seamless virtual environment integration** with `source` command
- **Enhanced productivity** for linting, testing, and code analysis
- **Maintains security** through explicit allowlist configuration

## Setup Requirements

1. **User-level allowlist configuration** (takes precedence over workspace settings)
2. **Manual UI activation** in VS Code settings (required in addition to JSON)
3. **Agent mode enabled**: `"github.copilot.chat.agent.enabled": true`
4. **Command name matching**: Allowlist matches simple names, not full paths

## Security Note

Only add trusted commands to the allowlist. Each command bypasses VS Code's approval prompts, so ensure you understand what each command does before adding it.

---

## Project Standards & Coding Guidelines

### Specialized Instruction Files

**📂 CONTEXT-SPECIFIC GUIDANCE:**

This project includes specialized instruction files in `.github/instructions/` that provide detailed patterns for:

- **`aws-patterns.instructions.md`**: AWS client creation, resource management, security patterns
- **`code-quality-refactoring.instructions.md`**: Function decomposition, logging standards, exception handling
- **`testing-patterns.instructions.md`**: Mandatory moto library usage, fixture design, performance requirements
- **`security-patterns.instructions.md`**: Secret management, input validation, secure error handling
- **`markdown-formatting.instructions.md`**: Markdownlint compliance, heading structure, list formatting

**🤖 AI ASSISTANT USAGE:**

When working on files matching these patterns, reference the relevant instruction file for detailed guidance:

- AWS files (`**/aws_*.py`, `**/adapters/**/*.py`): Use AWS patterns
- All Python files (`**/*.py`): Apply code quality and refactoring standards
- Test files (`**/test_*.py`, `**/tests/**/*.py`): Follow testing patterns
- Security files (`**/security/**/*.py`, `**/*security*.py`): Apply security patterns
- Markdown files (`**/*.md`): Use markdown formatting standards

### Code Quality Requirements

**✅ MANDATORY QUALITY TARGETS:**

- **Ruff**: All checks must pass (no warnings/errors allowed)
- **Pylint**: Perfect 10.00/10 score required
- **Bandit**: Zero security vulnerabilities permitted
- **MyPy**: Clean type checking with appropriate flags

**🎯 QUALITY PRINCIPLES:**

- Fix root causes, not symptoms - address underlying issues, not warnings
- Use modern Python patterns over legacy approaches
- Security first - always prioritize security over convenience
- No suppression without justification - avoid `# pylint: disable` except for architectural constraints
- **Function complexity refactoring**: Decompose large functions into single-responsibility helpers
- **Configuration objects**: Use Pydantic models to group related parameters and reduce argument count

### Type Safety Standards

**✅ TYPE ANNOTATION REQUIREMENTS:**

- All functions must have return type annotations
- All function parameters must be typed
- Use modern Python typing syntax (`dict` vs `Dict`, `|` vs `Union`)
- Generator types must specify full `Generator[YieldType, SendType, ReturnType]`

**🔧 BOTO3 TYPE HANDLING:**

- Use `types-boto3` packages for AWS client type annotations
- Import AWS client types in `TYPE_CHECKING` blocks
- Use `# pyright: ignore[reportArgumentType, reportUnknownMemberType]` for boto3.client() calls (MyPy/Pylance compatibility)

### Testing Standards

**🚨 MANDATORY AWS MOCKING:**

- **ALL AWS testing MUST use `moto` library**
- **NO exceptions for `unittest.mock` with AWS services**
- Use `@mock_aws` decorator or `mock_aws()` context manager
- Performance requirement: Test suites must complete in <20 seconds

**✅ FIXTURE DESIGN:**

- Use `name=` parameter to avoid `redefined-outer-name` issues
- Session-scoped fixtures for expensive operations
- Dynamic secret generation with `secrets.token_urlsafe()`

### Code Quality and Refactoring Standards

**🔧 FUNCTION COMPLEXITY MANAGEMENT:**

- **R0917** (too many arguments): Use Pydantic configuration objects for >5 parameters
- **R0912** (too many branches): Extract decision logic into focused helper functions
- **R0915** (too many statements): Decompose into logical workflow steps (main function <20 lines)
- **CLI exception**: CLI functions inherently need many parameters - use targeted `# pylint: disable=too-many-positional-arguments`

**⚡ PERFORMANCE LOGGING:**

- **MANDATORY**: Use lazy % formatting: `logger.info("User %s logged in", username)`
- **AVOID**: f-string logging: `logger.info(f"User {username} logged in")` (performance impact)
- **BENEFIT**: Logging performance and structured log compatibility

**🚀 REFACTORING PROCESS (Proven Pattern from alexa_setup Success):**

1. **Identify complexity triggers**: Use Pylint R-family rules to find refactoring targets
2. **Create configuration objects**: Use Pydantic models to group related parameters
3. **Extract helper functions**: Single-responsibility functions with clear names (_validate_*, _setup_*, _generate_*)
4. **Preserve functionality**: All refactoring must maintain exact behavior and imports
5. **Validate continuously**: Run `ruff check` and import tests after each step

**💡 EXCEPTION HANDLING EVOLUTION:**

- **Replace broad catching**: `except Exception:` → `except (ValidationError, ClientError):`
- **AWS response safety**: `e.response["Error"]` → `e.response.get("Error", {})`
- **Chain exceptions**: Always use `raise typer.Exit(1) from e` to preserve traceback

**🎯 ARCHITECTURAL CONSTRAINTS:**

- **CLI parameters**: CLI functions naturally need 5+ parameters - use targeted disable with justification
- **Configuration objects**: Prefer Pydantic models over parameter tuples for type safety
- **Helper function organization**: Group related helpers near their main function

### Project Structure

**📁 KEY DIRECTORIES:**

- `/src`: Core application source code
- `/tests`: Comprehensive test suite with AWS mocking
- `/scripts`: Development and automation scripts
- `/infrastructure`: Deployment and infrastructure code
- `/docs`: Project documentation

**🔧 CONFIGURATION:**

- Single source of truth: `pyproject.toml` for all tool configuration
- No legacy files: Eliminated redundant `setup.cfg`
- Virtual environment: `.venv` for isolated dependencies

### Markdown Documentation Standards

**🔧 MARKDOWNLINT COMPLIANCE:**

- Use proper heading levels (`##`, `###`) instead of emphasized text (`**bold**`)
- Surround all lists with blank lines (MD032)
- Specify language for all fenced code blocks (MD040)
- Use descriptive link text instead of "click here"
- Maintain consistent heading hierarchy

**❌ AVOID MD036 VIOLATIONS:**

```markdown
❌ WRONG: **Important Section**
✅ CORRECT: ## Important Section

❌ WRONG: **Key Points:**
✅ CORRECT: ### Key Points
```

**✅ PROPER LIST FORMATTING:**

- Always add blank lines before and after lists
- Use consistent bullet or numbering style
- Maintain proper indentation for nested items

### AI Assistant Guidelines

**🔍 PROBLEM ANALYSIS:**

- Always run code quality checks (`ruff check`, `pylint`) to identify specific issues
- Focus on root causes rather than suppressing symptoms
- Use specific error codes to target fixes (W1203, R0917, R0912, R0915)

**🛠️ REFACTORING APPROACH:**

- For complex functions: Extract helper functions with single responsibilities
- For many parameters: Create Pydantic configuration objects
- For logging: Convert f-strings to lazy % formatting
- For exceptions: Replace broad `Exception` with specific types
- For AWS responses: Use `.get()` for safe dictionary access

**✅ VALIDATION PROCESS:**

- Test imports after refactoring: `python -c "from module import function"`
- Run Ruff after each change: `ruff check file.py`
- Preserve exact functionality during decomposition
- Document architectural constraints with targeted disables

---

**Project Source**: This configuration was developed for Python projects requiring comprehensive linting and development tool automation.
