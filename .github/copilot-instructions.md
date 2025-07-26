# VS Code GitHub Copilot Terminal Automation Setup

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

**Project Source**: This configuration was developed for Python projects requiring comprehensive linting and development tool automation.
