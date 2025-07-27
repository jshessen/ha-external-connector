# GitHub Copilot Instructions

This directory contains specialized instruction files for GitHub Copilot to provide context-specific guidance.

## Instruction Files

### Core Instructions

- **`../.github/copilot-instructions.md`** - Main project instructions including terminal automation, code quality standards, and development workflows

### Specialized Pattern Files

- **`aws-patterns.instructions.md`** - AWS-specific coding patterns, client creation, resource management, and security best practices
- **`code-quality-refactoring.instructions.md`** - Code quality and refactoring patterns including function complexity management, logging standards, and exception handling
- **`testing-patterns.instructions.md`** - Testing standards with mandatory moto library usage, fixture design, and performance requirements
- **`security-patterns.instructions.md`** - Security patterns including secret management, input validation, and secure error handling
- **`markdown-formatting.instructions.md`** - Markdown formatting standards and markdownlint compliance guidelines

## File Application Scope

Each instruction file uses `applyTo` frontmatter to specify when it should be automatically applied:

- **AWS patterns**: Applied to `**/aws_*.py`, `**/adapters/**/*.py`, `**/infrastructure/**/*.py`
- **Code quality & refactoring**: Applied to `**/*.py` (all Python files)
- **Testing patterns**: Applied to `**/test_*.py`, `**/tests/**/*.py`, `**/*_test.py`
- **Security patterns**: Applied to `**/security/**/*.py`, `**/secrets/**/*.py`, `**/*security*.py`
- **Markdown formatting**: Applied to `**/*.md`

## VS Code Configuration

The instruction files are automatically loaded when the following settings are configured in `.vscode/settings.json`:

```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "chat.instructionsFilesLocations": [
    ".github/instructions"
  ]
}
```

## Usage

These instruction files provide specialized guidance for:

1. **Code Generation** - Automatic application of project-specific patterns
2. **Code Quality** - Function complexity refactoring, logging standards, and exception handling patterns
3. **Code Review** - Context-aware suggestions based on file type
4. **Documentation** - Consistent markdown formatting and compliance
5. **Security** - Enforcement of security best practices
6. **Testing** - Standardized testing patterns and AWS mocking

The instructions are automatically included in relevant chat requests based on the file patterns specified in each instruction file's frontmatter.
