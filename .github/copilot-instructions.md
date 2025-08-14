# VS Code GitHub Copilot Terminal Automation Setup

## 🚨 CRITICAL: Quick Environment Setup

**Single Command Setup:**

```bash
# NEW: One command for complete setup and validation
python scripts/agent_helper.py setup
```

**Essential Commands for Agents:**

```bash
python scripts/agent_helper.py check          # Quick health check
python scripts/agent_helper.py refresh        # Reload instructions
python scripts/agent_helper.py quick-reference # Display key patterns
```

## 🔄 Instruction Hierarchy System

This project uses a hierarchical instruction system to eliminate conflicts:

### Conflict Resolution Precedence

1. **`.github/copilot-instructions.md`** - Master guidelines (highest priority)
2. **`instructions/core/`** - Fundamental patterns (medium priority)
3. **`instructions/specialized/`** - Domain-specific guidance (contextual priority)
4. **`instructions/documentation/`** - Content standards (lowest priority)

### Quick Pattern Reference

- **AWS files** (`**/aws_*.py`, `**/adapters/**/*.py`) → `instructions/specialized/aws-patterns.md`
- **Lambda functions** (`**/lambda_functions/**/*.py`) → `instructions/specialized/lambda-patterns.md`
- **Test files** (`**/test_*.py`, `**/tests/**/*.py`) → `instructions/specialized/testing-patterns.md`
- **Security files** (`**/security/**/*.py`) → `instructions/specialized/security-patterns.md`
- **Markdown files** (`**/*.md`) → `instructions/documentation/markdown-standards.md`

## ⚡ Streamlined Terminal Automation

### Essential Allowlist Commands

```json
{
  "github.copilot.chat.agent.terminal.allowList": {
    "python": true,
    "source": true,
    "ruff": true,
    "pylint": true,
    "mypy": true,
    "pytest": true,
    "git": true
  }
}
```

### Environment Activation

**Always activate first:**

```bash
source .venv/bin/activate
```

**Why environment activation is critical:**

- Commands like `ruff`, `pylint`, `pytest` will fail without activation
- System Python may be used instead of project environment
- Import paths may not be configured correctly

## Quick Start: Enable Automated Tool Approvals (VS Code 2024+)

### 1. Configure New Tool Approval System

Add this to your VS Code user settings (`~/.config/Code/User/settings.json` on Linux):

```json
{
  "github.copilot.chat.tools.autoApprove": {
    "run_in_terminal": [
      // === GENERAL COMMANDS ===
      "echo",
      "ls",
      "pwd",
      "cat",
      "head",
      "tail",
      "wc",
      "grep",
      "find",
      "test",
      "git",
      "mv",
      "cp",
      "mkdir",
      "touch",
      "which",
      "whoami",
      "date",
      "source",

      // === PYTHON DEVELOPMENT ===
      "python",
      "pip",
      "poetry",
      "ruff",
      "pylint",
      "mypy",
      "flake8",
      "bandit",
      "black",
      "pytest",
      "make",

      // === AWS CLI (with pager disabled) ===
      "aws --no-cli-pager"
    ]
  }
}
```

### 2. Activate in VS Code UI

1. Open **Settings** → **Extensions** → **GitHub Copilot** → **Chat** → **Tools: Auto Approve**
2. **CRITICAL**: Check the checkbox to enable the experimental feature
3. Add tools using the UI or directly edit `settings.json`
4. **Both JSON configuration AND UI activation are required for experimental features**

### 3. Migration from Legacy System

#### ⚠️ DEPRECATED: Legacy Terminal Allowlist (Pre-2024)

```json
// OLD SYSTEM - No longer supported
{
  "github.copilot.chat.agent.terminal.allowList": {
    "python": true,
    "source": true
  }
}
```

#### ✅ NEW SYSTEM: Unified Tool Approval

```json
// NEW SYSTEM - Current standard
{
  "github.copilot.chat.tools.autoApprove": {
    "run_in_terminal": ["python", "source"]
  }
}
```

## ⚠️ LEGACY SECTION (DEPRECATED) - For Reference Only

> **Note**: The following configuration uses the deprecated terminal allowlist system.
> Use the new [Tool Approval System](#quick-start-enable-automated-tool-approvals-vs-code-2024) instead.

```json
{
  "github.copilot.chat.agent.terminal.allowList": {
    // Core development commands
    "python": true,
    "source": true,
    "ruff": true,
    "pylint": true,
    "mypy": true,
    "pytest": true,
    "git": true,
    "echo": true,
    "ls": true,
    "cat": true
  }
}
```

### Legacy VS Code UI Activation (Deprecated)

1. Open **Settings** → **Extensions** → **GitHub Copilot** → **Agent** → **Terminal: Allow List**
2. Add commands using the **"Add Item"** button
3. Both JSON and UI activation are required

### Test Your Setup

```bash
# Quick validation - these commands should work with session approval
echo "Testing tool approval system"     # Use "Always approve for session"
python scripts/agent_helper.py env     # Use "Always approve for session"
ruff check src/ --no-fix               # Use "Always approve for session"
```

**Note**: The auto-approve configuration is experimental and may require manual approval initially. Use the "Continue" dropdown to select "Always approve for this session" or "Always approve for this workspace" for seamless operation within the current session.

## AWS CLI Configuration

**🚨 MANDATORY: Always use `--no-cli-pager` with AWS commands**

```bash
# ✅ CORRECT: Disable pager for automation compatibility
aws lambda list-functions --no-cli-pager
aws logs describe-log-streams --log-group-name /aws/lambda/HomeAssistant --no-cli-pager
aws s3 ls --no-cli-pager

# ❌ WRONG: Default pager will block terminal automation
aws lambda list-functions         # Will hang waiting for user input
aws logs describe-log-streams      # Pager blocks automation
```

**Why this is critical:**

- AWS CLI pager blocks terminal automation tools
- Pager requires user interaction to navigate/exit
- `--no-cli-pager` ensures clean, automatable output
- Required for all AWS CLI commands in automation context

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

## Agent Automation Solution: Python Script Alternative

### Problem: `python -c` Commands Trigger Prompts

VS Code's allowlist has limitations with complex `python -c` patterns, even with wildcards like `"python -c*": true`. Commands like `python -c 'import sys; print(sys.executable)'` consistently trigger approval prompts regardless of allowlist configuration.

### Solution: Use `scripts/agent_helper.py`

**Instead of `python -c` commands, use the dedicated agent helper script:**

```bash
# ❌ BLOCKED: python -c 'import sys; print(sys.executable)'
# ✅ WORKS: python scripts/agent_helper.py python

# ❌ BLOCKED: python -c 'import module; print("success")'
# ✅ WORKS: python scripts/agent_helper.py imports

# ❌ BLOCKED: python -c 'import os; print(os.getcwd())'
# ✅ WORKS: python scripts/agent_helper.py env
```

### Available Agent Helper Actions

- **`python scripts/agent_helper.py env`** - Environment validation (Python version, venv status, working directory, key files)
- **`python scripts/agent_helper.py imports`** - Module import testing (validates core project imports)
- **`python scripts/agent_helper.py tools`** - Development tools check (ruff, pytest, mypy, black versions)
- **`python scripts/agent_helper.py python`** - Python environment info (executable path, version, platform)
- **`python scripts/agent_helper.py all`** - Complete automation suite (all checks combined)

### Benefits Over `python -c`

- **✅ No VS Code prompts** - Works seamlessly with allowlist
- **✅ Comprehensive output** - More detailed information than one-liners
- **✅ Type-safe and maintainable** - Proper Python code with error handling
- **✅ Extensible** - Easy to add new automation tasks
- **✅ Debuggable** - Full stack traces and clear error messages

### Usage Pattern for Agents

When you need to validate environment or test imports in agent automation:

```bash
# Environment validation
python scripts/agent_helper.py env

# Import testing
python scripts/agent_helper.py imports

# Quick comprehensive check
python scripts/agent_helper.py all
```

This approach eliminates the `python -c` allowlist limitations while providing superior functionality for agent automation tasks.

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
- **`documentation-patterns.instructions.md`**: Documentation organization, HACS readiness, audience-based structure
- **`lambda-functions-patterns.instructions.md`**: Lambda deployment markers, transfer blocks, service specialization

**🤖 AI ASSISTANT USAGE:**

When working on files matching these patterns, reference the relevant instruction file for detailed guidance:

- AWS files (`**/aws_*.py`, `**/adapters/**/*.py`): Use AWS patterns
- All Python files (`**/*.py`): Apply code quality and refactoring standards
- Test files (`**/test_*.py`, `**/tests/**/*.py`): Follow testing patterns
- Security files (`**/security/**/*.py`, `**/*security*.py`): Apply security patterns
- Markdown files (`**/*.md`): Use markdown formatting standards
- Documentation work (`**/docs/**/*`, documentation reorganization): Apply documentation patterns
- Lambda functions (`**/lambda_functions/**/*.py`): Follow Lambda functions patterns

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

## Quality Standards

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

### Documentation Organization Standards

**📁 AUDIENCE-BASED STRUCTURE:**

Follow the established `docs/` directory structure for professional documentation organization:

```text
docs/
├── README.md                      # Navigation hub with clear audience routing
├── integrations/                  # User-focused guides (end-user perspective)
│   ├── alexa/                    # Integration-specific user documentation
│   └── ios_companion/            # Future integration guides
├── development/                   # Developer-focused content (contributor perspective)
│   ├── AUTOMATION_SETUP.md       # Development environment setup
│   ├── CODE_QUALITY_SUITE.md     # Code standards and tooling
│   └── ROADMAP.md                # Strategic planning and phases
├── deployment/                    # Operations-focused guides (deployment perspective)
│   ├── DEPLOYMENT_GUIDE.md       # Step-by-step deployment instructions
│   └── TROUBLESHOOTING.md        # Operational issue resolution
└── history/                      # Historical context (evolution perspective)
    ├── AUTOMATION_GAPS_ANALYSIS.md  # Historical problem analysis
    ├── ARCHITECTURE_EVOLUTION.md    # Design decision history
    └── PHASE_6_COMPLETE.md          # Milestone completion records
```

**🎯 DOCUMENTATION PLACEMENT PRINCIPLES:**

- **Root Directory**: Only essential project files (`README.md`, `CHANGELOG.md`, configuration)
- **User Guides**: Place in `docs/integrations/{service}/` for service-specific user instructions
- **Development Planning**: Place in `docs/development/` for roadmaps, architecture decisions, setup guides
- **Operations**: Place in `docs/deployment/` for deployment, monitoring, troubleshooting content
- **Historical Records**: Place in `docs/history/` for completed analyses, evolution records, legacy content

**🔗 CROSS-REFERENCE STANDARDS:**

- **Root README.md**: Should link to relevant `docs/` content with clear audience indicators
- **docs/README.md**: Must provide comprehensive navigation with audience-based sections
- **Relative Paths**: Use relative paths for internal documentation links for portability
- **Clear Audience**: Each document should clearly indicate its target audience (users/developers/operators)

**📋 DOCUMENTATION LIFECYCLE MANAGEMENT:**

When reorganizing documentation:

1. **Audit Phase**: Identify all documentation files and their current audiences
2. **Categorize**: Assign each document to user/developer/operations/historical category
3. **Move & Rename**: Use descriptive names that indicate purpose and audience
4. **Update References**: Search and update all internal links using `grep_search` tool
5. **Validate**: Ensure no broken links and proper navigation flow
6. **HACS Preparation**: Organize with future HACS publication requirements in mind

**🚀 HACS-READY DOCUMENTATION:**

Maintain documentation structure that supports future HACS (Home Assistant Community Store) publication:

- **Professional presentation**: Clear, consistent formatting and navigation
- **User-focused organization**: Integration guides easily discoverable by end users
- **Comprehensive coverage**: Setup, configuration, troubleshooting all documented
- **Community-friendly**: Contributing guides and developer documentation separated from user guides

**🔧 AUTOMATION-FRIENDLY PATTERNS:**

- **Consistent naming**: Use `UPPERCASE_WITH_UNDERSCORES.md` for major documents
- **Clear file purposes**: Filename should indicate content type (`GUIDE`, `SETUP`, `TROUBLESHOOTING`)
- **Tool-friendly**: Structure documents for easy parsing by automation tools
- **Version control**: Use meaningful commit messages when reorganizing documentation structure

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

### Transfer Block System for Duplicate Code Management

**🔄 STRATEGIC DUPLICATE CODE SYNCHRONIZATION:**

This project intentionally maintains synchronized duplicate code between Lambda functions using a **Transfer Block System** for optimal performance and deployment independence.

**📋 TRANSFER BLOCK LOCATIONS:**

- **Primary Source**: `src/ha_connector/integrations/alexa/lambda_functions/cloudflare_security_gateway.py` (line ~3149)
- **Synchronized Target**: `src/ha_connector/integrations/alexa/lambda_functions/smart_home_bridge.py` (line ~255)
- **Infrastructure**: `infrastructure/deployment/smart_home_bridge.py` (separate deployment script)

**🎯 TRANSFER BLOCK MARKERS:**

```python
# ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
# ║                           🚀 TRANSFER-READY CODE 🚀                       ║
# ║ 📋 BLOCK PURPOSE: Strategic 3-tier caching for <500ms voice commands     ║
# ║ 🔄 TRANSFER STATUS: Ready for duplication across Lambda functions        ║
# ║ ⚡ PERFORMANCE: Container 0-1ms | Shared 20-50ms | SSM 100-200ms         ║
# ║                                                                           ║
# ║ 🎯 USAGE PATTERN:                                                         ║
# ║   1. Copy entire block between "BLOCK_START" and "BLOCK_END" markers     ║
# ║   2. Update function prefixes as needed (e.g., _oauth_ → _bridge_)        ║
# ║   3. Adjust cache keys and table names for target service                ║
# ║   4. Maintain identical core functionality across Lambda functions       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

def load_standardized_configuration(...):
    # Core speed-optimized configuration loading
    # ... transfer block content ...

# ╭─────────────────── TRANSFER BLOCK END ───────────────────╮
```

**⚠️ CRITICAL AI ASSISTANT GUIDELINES:**

1. **NEVER "Clean Up" Duplicate Code**: The duplicate code between CloudFlare Security Gateway and Smart Home Bridge is INTENTIONAL
2. **Preserve Transfer Blocks**: When editing one transfer block, copy changes to the synchronized location
3. **Maintain Service-Specific Customizations**: Each Lambda function has its own cache prefixes and service identifiers
4. **Infrastructure Files Are Separate**: Don't confuse `infrastructure/deployment/` files with main Lambda functions

**🔧 TRANSFER WORKFLOW:**

When updating shared functionality:

1. **Edit Primary Source** (cloudflare_security_gateway.py transfer block)
2. **Copy Transfer Block Content** (between START/END markers)
3. **Update Target Location** (smart_home_bridge.py transfer block)
4. **Apply Service Customizations**:
   - Cache prefixes: `oauth_config_` → `bridge_config_`
   - Lambda function names: `"cloudflare_security_gateway"` → `"smart_home_bridge"`
   - Service-specific constants and identifiers
5. **Test Both Functions** independently after synchronization

**🎯 ARCHITECTURAL RATIONALE:**

- **Lambda Independence**: Each function can be deployed separately without shared dependencies
- **Performance Optimization**: Eliminates import overhead and cold start penalties
- **Service Specialization**: CloudFlare Security Gateway handles authentication, Smart Home Bridge handles voice commands
- **Maintenance Efficiency**: Transfer blocks enable quick synchronization of shared optimizations

**📊 PERFORMANCE BENEFITS:**

- **Container Cache**: 0-1ms access for warm Lambda containers
- **Shared Cache**: 20-50ms cross-Lambda function sharing via DynamoDB
- **SSM Fallback**: 100-200ms authoritative configuration source
- **Voice Command Target**: Sub-500ms total response time

**🚨 VALIDATION CHECKLIST:**

After transfer block updates:

- [ ] Both Lambda functions import successfully
- [ ] Ruff/Pylint checks pass for both files
- [ ] Service-specific prefixes updated correctly
- [ ] Transfer block markers remain intact
- [ ] Core functionality preserved across both functions

**📚 DOCUMENTATION WORKFLOW:**

When working with documentation:

1. **Assessment**: Use `list_dir` and `grep_search` to understand current documentation landscape
2. **Organization**: Apply audience-based categorization (users/developers/operations/history)
3. **Movement**: Use `run_in_terminal` with `mv` commands for file reorganization
4. **Reference Updates**: Use `grep_search` to find and update internal links after moves
5. **Validation**: Use `python scripts/agent_helper.py imports` to ensure no code breaks after documentation changes
6. **Professional Standards**: Apply markdownlint compliance and HACS-ready formatting throughout

**🎯 DOCUMENTATION BEST PRACTICES:**

- **Root directory cleanup**: Keep only essential project files in root, move documentation to `docs/`
- **Audience clarity**: Each document should clearly serve users, developers, operators, or historical context
- **Link maintenance**: Always update internal references when moving documentation files
- **HACS readiness**: Organize documentation to support future Home Assistant Community Store publication
- **Consistency**: Use established naming conventions and directory structure patterns

---

**Project Source**: This configuration was developed for Python projects requiring comprehensive linting and development tool automation.
