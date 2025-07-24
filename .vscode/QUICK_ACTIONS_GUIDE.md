# Quick Actions for Code Formatting

This document describes the quick actions set up for fixing common formatting and linting issues with **Ruff** (primary), **Flake8** (complementary), **Black** (formatting), and **Pylint** (design patterns).

## Linting Strategy

**🚀 Optimized Multi-Tool Approach**: This project uses complementary linters for comprehensive coverage:

- **Ruff handles**: E/W (pycodestyle), F (Pyflakes), I (imports), UP (pyupgrade), B (bugbear), SIM (simplify) - with auto-fix
- **Flake8 handles**: Plugin-specific rules, complex analysis not yet in Ruff, advanced checks
- **Black handles**: Code formatting (line length, quotes, indentation)
- **Pylint handles**: Design patterns and complex analysis (with overlapping rules disabled)

### Overlap Management

- **Flake8 ignores**: E501, F401, F841, W291-W293, W391, E302-E305 (auto-fixed by Ruff)
- **Ruff focuses**: Fast auto-fixable rules for immediate remediation
- **Flake8 focuses**: Plugin rules and complex analysis requiring human judgment

## Available Quick Actions

### Via Tasks (Ctrl+Shift+P → "Tasks: Run Task")

| Task Name | Description | Use Case |
|-----------|-------------|----------|
| **Quick Fix: Black + Ruff Fix Current File** | Format current file with Black + fix with Ruff | Best all-in-one fix for open file |
| **Quick Fix: Black + Ruff Fix All** | Format all project files with Black + fix with Ruff | Full project cleanup |
| **Quick Fix: Black Format Current File** | Format current file with Black only | Just formatting, no lint fixes |
| **Quick Fix: Black Format All** | Format all project files with Black only | Project-wide formatting |
| **Quick Fix: Ruff Fix Current File** | Fix current file with Ruff only | Just lint fixes, no formatting |
| **Quick Fix: Ruff Fix All** | Fix all project files with Ruff only | Project-wide lint fixes |
| **Quick Fix: Ruff Format Current File** | Format current file with Ruff formatter | Alternative to Black |
| **Quick Fix: Ruff Format All** | Format all project files with Ruff formatter | Alternative to Black |
| **Quick Fix: Import Organization** | Fix import order and organization | Clean up import statements |
| **Quick Fix: Line Length Issues (W2xx)** | Fix line length violations | Specifically target line length problems |

### Via Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| **Ctrl+Alt+F** | Black + Ruff Fix Current File | Python files only |
| **Ctrl+Alt+Shift+F** | Black + Ruff Fix All Files | Global |
| **Ctrl+Alt+B** | Black Format Current File | Python files only |
| **Ctrl+Alt+R** | Ruff Fix Current File | Python files only |
| **Ctrl+Alt+Shift+R** | Ruff Format Current File | Python files only |
| **Ctrl+Alt+I** | Import Organization | Global |
| **Ctrl+Alt+L** | Line Length Issues Fix | Global |

### Existing Shortcuts (unchanged)

| Shortcut | Action | Context |
|----------|--------|---------|
| **Ctrl+Shift+F** | Standard VS Code Format Document | All files |
| **Ctrl+K Ctrl+F** | Format Selection | All files |
| **Ctrl+Shift+Alt+F** | Black Formatter Extension | Python files only |

## Common Workflow Examples

### 1. Fix All Issues in Current File

**Shortcut:** `Ctrl+Alt+F`
**Command:** Quick Fix: Black + Ruff Fix Current File

This is the most comprehensive single-file fix:

- Formats code with Black (line length, quotes, etc.)
- Fixes Ruff linting issues (imports, unused variables, etc.)
- Shows progress in terminal

### 2. Project-Wide Cleanup

**Shortcut:** `Ctrl+Alt+Shift+F`
**Command:** Quick Fix: Black + Ruff Fix All

Use this for complete project formatting:

- Formats entire codebase with Black
- Fixes all Ruff issues across the project
- Good for preparing commits

### 3. Just Fix Imports

**Shortcut:** `Ctrl+Alt+I`
**Command:** Quick Fix: Import Organization

Quickly organize imports without other changes:

- Sorts imports alphabetically
- Groups imports properly
- Removes unused imports

### 4. Target Line Length Issues

**Shortcut:** `Ctrl+Alt+L`
**Command:** Quick Fix: Line Length Issues (W2xx)

Specifically target line length problems:

- Black formatting for line breaks
- Ruff fixes for specific line length rules
- Focuses on E501, W292, W391 errors

## Common Error Codes These Fix

### Ruff Fixes (Primary - E/W/F/I/UP/B/SIM)

- **Import organization** (I001, I002)
- **Unused imports** (F401)
- **Unused variables** (F841)
- **Line too long** (E501)
- **Trailing whitespace** (W291, W292, **W293**)
- **Missing final newline** (W292)
- **Blank line at end of file** (W391)
- **Pycodestyle errors/warnings** (All E/W family)
- **Modern Python syntax** (UP001-UP999)
- **Bug prevention** (B001-B999)
- **Code simplification** (SIM001-SIM999)

### Black Fixes (Formatting)

- **Line length violations** (E501 - with Ruff)
- **Quote style inconsistencies**
- **Indentation issues**
- **Code formatting standardization**

### Pylint Fixes (Design Patterns Only)

- **Complex code analysis** (overlapping E/W/F rules disabled)
- **Design pattern violations**
- **Code complexity metrics** (when enabled)

## Pro Tips

1. **Use `Ctrl+Alt+F` as your go-to shortcut** - it handles most formatting needs
2. **Run project-wide fixes before commits** with `Ctrl+Alt+Shift+F`
3. **Use import organization** (`Ctrl+Alt+I`) when adding new dependencies
4. **Line length fixes** (`Ctrl+Alt+L`) are great for legacy code cleanup

## Integration with Existing Setup

These quick actions work alongside your existing configuration:

- **VS Code settings**: Automatic formatting on save still works
- **Ruff extension**: Native language server integration unchanged
- **Black extension**: Direct formatter integration unchanged
- **Problem matchers**: VS Code will show issues in Problems panel

## Customization

To modify these actions:

1. Edit `.vscode/tasks.json` for task definitions
2. Edit `.vscode/keybindings.json` for keyboard shortcuts
3. Edit `.vscode/settings.json` for behavior modifications

The tasks use your virtual environment automatically (`source .venv/bin/activate`) and provide clear terminal output with emojis for easy identification.
