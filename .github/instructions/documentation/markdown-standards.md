---
description: "Markdown formatting standards and markdownlint compliance for HA External Connector"
applyTo: "**/*.md"
---

# Markdown Formatting Standards

## Heading Structure (MD036 Compliance)

### Use Proper Heading Levels

```markdown
# Main Title (H1)

## Section Title (H2)

### Subsection Title (H3)

#### Detail Section (H4)
```

### Avoid Emphasis as Headings (MD036 Violation)

```markdown
❌ WRONG: **Important Section**
✅ CORRECT: ## Important Section

❌ WRONG: **Key Points:**
✅ CORRECT: ### Key Points

❌ WRONG: *Configuration Notes*
✅ CORRECT: #### Configuration Notes
```

## List Formatting (MD032 Compliance)

### Proper List Spacing

```markdown
Text before list.

- First item
- Second item
- Third item

Text after list.

**Another list example:**

1. Numbered item one
2. Numbered item two
3. Numbered item three

Additional content follows.
```

## Code Block Standards

### Fenced Code Blocks with Language

```markdown
✅ CORRECT:
```

```python
def example_function() -> str:
    return "example"
```

```markdown
❌ WRONG:
```

```text
def example_function():
    return "example"
```

```markdown
```

### Inline Code for Technical Terms

```markdown
Use `pytest` for testing, not **pytest**.
Configure the `pyproject.toml` file properly.
The `@mock_aws` decorator is required.
```

## Link and Reference Standards

### Descriptive Link Text

```markdown
✅ CORRECT: [GitHub Copilot documentation](https://docs.github.com/copilot)
❌ WRONG: Click [here](https://docs.github.com/copilot) for documentation
```

### File References

```markdown
See the `src/ha_connector/cli/main.py` file for implementation details.
Review the configuration in `pyproject.toml`.
```

## Table Formatting

### Properly Aligned Tables

```markdown
| Tool | Purpose | Required |
|------|---------|----------|
| Ruff | Linting | Yes |
| Pylint | Code quality | Yes |
| MyPy | Type checking | Yes |
```

## Emphasis and Strong Text

### Appropriate Use Cases

```markdown
**Important**: Use strong text for critical information.
*Note*: Use emphasis for secondary information.
`code`: Use backticks for technical terms and code.
```

## Common MD036 Violations to Avoid

```markdown
❌ **AWS Configuration:** - Use heading instead
✅ ## AWS Configuration

❌ **Key Features** - Use heading instead
✅ ### Key Features

❌ *Prerequisites* - Use heading instead
✅ #### Prerequisites

❌ **⚠️ WARNING:** - Use heading or proper callout
✅ ### ⚠️ WARNING

❌ **✅ SUCCESS:** - Use heading or proper callout
✅ ### ✅ SUCCESS
```

## Emoji and Symbol Usage

### Appropriate Contexts

```markdown
## ✅ Requirements Met
## 🚨 Critical Issues
## 🔧 Configuration Steps
## 📁 Directory Structure
```

### Avoid in Body Text

```markdown
❌ **✅ This is working** - Creates MD036 violation
✅ The system is working properly.

❌ **🔧 Configuration** - Use as heading instead
✅ ## 🔧 Configuration
```

## Document Structure Standards

### Standard Document Template

```markdown
# Document Title

Brief description of the document purpose.

## Overview

High-level information about the topic.

## Prerequisites

Required setup or knowledge.

### System Requirements

Specific technical requirements.

### Installation Steps

1. Step one
2. Step two
3. Step three

## Configuration

Detailed configuration instructions.

### Basic Setup

Basic configuration steps.

### Advanced Options

Advanced configuration details.

## Troubleshooting

Common issues and solutions.

### Known Issues

List of known problems.

### Solutions

Recommended fixes.

## References

- [External Link](https://example.com)
- Related documentation files
```

## Markdownlint Integration

Always run markdownlint checks and fix violations:

- Use proper heading levels instead of emphasized text
- Ensure blank lines around lists
- Specify language for code blocks
- Use descriptive link text
- Maintain consistent formatting throughout documents

When generating markdown content, automatically apply these standards to ensure compliance with markdownlint rules and maintain consistent documentation quality.
