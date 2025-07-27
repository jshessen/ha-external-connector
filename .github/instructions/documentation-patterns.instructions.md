---
description: "Documentation organization and maintenance patterns for HA External Connector"
applyTo: "**/*.md,**/docs/**/*"
note: "Some MD031 warnings in numbered lists with code blocks are acceptable for instructional clarity"
---

# Documentation Organization Patterns

## Professional Documentation Structure

### Audience-Based Directory Organization

```text
docs/
├── README.md                      # Navigation hub and directory guide
├── integrations/                  # END USER documentation
│   ├── alexa/                    # Alexa integration user guides
│   │   ├── USER_GUIDE.md         # Complete user setup guide
│   │   └── TEAM_SETUP.md         # Team collaboration setup
│   └── {future_integrations}/    # iOS, Android, etc.
├── development/                   # DEVELOPER documentation
│   ├── AUTOMATION_SETUP.md       # Development environment setup
│   ├── CODE_QUALITY_SUITE.md     # Code standards and tooling
│   ├── ROADMAP.md                # Strategic planning and phases
│   └── ARCHITECTURE.md           # Technical architecture decisions
├── deployment/                    # OPERATIONS documentation
│   ├── DEPLOYMENT_GUIDE.md       # Step-by-step deployment
│   ├── TROUBLESHOOTING.md        # Issue resolution procedures
│   └── SECURITY.md               # Security considerations
└── history/                      # HISTORICAL documentation
    ├── AUTOMATION_GAPS_ANALYSIS.md  # Legacy analysis
    ├── ARCHITECTURE_EVOLUTION.md    # Design decision history
    └── PHASE_*_COMPLETE.md          # Milestone records
```

### Root Directory File Management

**✅ KEEP IN ROOT:**

- `README.md` - Project overview and navigation
- `CHANGELOG.md` - Version history
- `LICENSE` - Project licensing
- Configuration files (`pyproject.toml`, `Makefile`, etc.)

**❌ MOVE TO docs/:**

- Planning documents (`ROADMAP.md` → `docs/development/ROADMAP.md`)
- User guides (`ALEXA_SETUP.md` → `docs/integrations/alexa/USER_GUIDE.md`)
- Analysis documents (`gaps_analysis.md` → `docs/history/AUTOMATION_GAPS_ANALYSIS.md`)
- Development guides (`AUTOMATION_SETUP.md` → `docs/development/AUTOMATION_SETUP.md`)

## Documentation Lifecycle Management

### File Reorganization Process

1. **Assessment Phase**

   ```bash
   # Inventory current documentation
   find . -name "*.md" -not -path "./.git/*" | sort

   # Identify audience for each document
   # Users: Setup guides, troubleshooting, usage examples
   # Developers: Architecture, coding standards, contribution guides
   # Operations: Deployment, monitoring, security procedures
   # Historical: Completed analyses, migration records, evolution notes
   ```

2. **Categorization Strategy**
   - **User-focused**: Clear setup instructions, troubleshooting, feature usage
   - **Developer-focused**: Architecture decisions, coding patterns,
     contribution workflows
   - **Operations-focused**: Deployment procedures, monitoring, security
   - **Historical**: Completed analyses, design evolution, legacy content

3. **File Movement Protocol**

   ```bash
   # Use descriptive names that indicate purpose and audience
   mv old_analysis.md docs/history/AUTOMATION_GAPS_ANALYSIS.md
   mv future_plans.md docs/development/ROADMAP.md
   mv user_setup.md docs/integrations/alexa/USER_GUIDE.md
   ```

4. **Reference Update Process**

   ```bash
   # Find all references to moved files
   grep -r "old_filename.md" . --include="*.md"

   # Update internal links using relative paths
   # From: [link](../old_filename.md)
   # To:   [link](docs/development/ROADMAP.md)
   ```

5. **Validation Steps**

   ```bash
   # Ensure no code imports break after documentation moves
   python scripts/agent_helper.py imports

   # Verify markdown formatting compliance
   markdownlint docs/
   ```

### Cross-Reference Standards

**✅ PROPER LINKING:**

```markdown
# Root README.md links
- [Development Setup](docs/development/AUTOMATION_SETUP.md)
- [User Guide](docs/integrations/alexa/USER_GUIDE.md)
- [Deployment](docs/deployment/DEPLOYMENT_GUIDE.md)

# Internal docs/ links (use relative paths)
- [Related Guide](../deployment/TROUBLESHOOTING.md)
- [Architecture](./ARCHITECTURE.md)
```

**❌ AVOID:**

```markdown
# Absolute paths (breaks portability)
- [Guide](/home/user/project/docs/guide.md)

# Non-descriptive links
- [Click here](docs/guide.md)

# Broken references after moves
- [Old Location](old_filename.md)
```

## HACS Publication Readiness

### Documentation Requirements for HACS

1. **User-Centric Organization**
   - Integration guides easily discoverable by end users
   - Clear setup instructions without technical jargon
   - Troubleshooting guides for common issues

2. **Professional Presentation**
   - Consistent formatting and navigation
   - Proper heading hierarchy
   - Complete cross-referencing

3. **Community Contribution Support**
   - Developer guides separated from user content
   - Clear contribution workflows
   - Code quality standards documented

### HACS-Ready File Structure

```text
Root Repository (HACS-visible):
├── README.md                      # Project overview (HACS displays this)
├── docs/integrations/alexa/       # Primary user documentation
│   └── USER_GUIDE.md             # Main setup guide
├── docs/deployment/               # Installation and deployment
│   └── DEPLOYMENT_GUIDE.md       # Step-by-step deployment
└── docs/development/              # Developer resources (secondary)
    └── CONTRIBUTING.md            # How to contribute
```

## Naming Conventions

### File Naming Standards

**✅ PREFERRED PATTERNS:**

- `USER_GUIDE.md` - Complete user setup and usage
- `DEPLOYMENT_GUIDE.md` - Installation and deployment procedures
- `TROUBLESHOOTING.md` - Issue resolution procedures
- `AUTOMATION_SETUP.md` - Development environment setup
- `CODE_QUALITY_SUITE.md` - Quality standards and tooling
- `ARCHITECTURE_EVOLUTION.md` - Design decision history
- `ROADMAP.md` - Strategic planning and future phases

**✅ DESCRIPTIVE NAMING:**

- Purpose clear from filename
- Audience indicated by content type (`GUIDE`, `SETUP`, `ANALYSIS`)
- Consistent `UPPERCASE_WITH_UNDERSCORES.md` for major documents

**❌ AVOID:**

- Generic names (`notes.md`, `stuff.md`, `temp.md`)
- Unclear purpose (`file1.md`, `new_doc.md`)
- Mixed case without pattern (`CamelCase.md`, `mixedStyle.md`)

### Directory Naming Standards

- `integrations/` - User-focused integration guides
- `development/` - Developer-focused content
- `deployment/` - Operations and deployment procedures
- `history/` - Historical context and completed analyses

## Content Organization Principles

### Document Structure Standards

1. **Clear Audience Declaration**

   ```markdown
   # Document Title

   > **Audience**: End users setting up Alexa integration
   > **Prerequisites**: Home Assistant installation, AWS account
   ```

2. **Comprehensive Table of Contents**

   ```markdown
   ## Table of Contents

   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Configuration](#configuration)
   - [Troubleshooting](#troubleshooting)
   ```

3. **Progressive Disclosure**
   - Basic setup first, advanced options later
   - Quick start guide, then detailed explanations
   - Common paths emphasized, edge cases documented separately

### Cross-Document Consistency

1. **Shared Terminology**
   - Use consistent terms across all documentation
   - Define technical terms in a central glossary
   - Link to authoritative definitions

2. **Format Standardization**
   - Consistent heading styles
   - Standardized code block formatting
   - Uniform list and table formatting

3. **Navigation Patterns**
   - Consistent "Previous/Next" navigation
   - Breadcrumb navigation for deep hierarchies
   - Clear "return to index" links

## Automation-Friendly Patterns

### Version Control Integration

```bash
# Meaningful commit messages for documentation changes
git commit -m "docs: reorganize documentation with audience-based structure

- Move ROADMAP.md to docs/development/ for developer focus
- Move automation gaps analysis to docs/history/
- Update all internal links to reflect new structure
- Maintain HACS publication readiness"
```

### Tool Integration

```bash
# Use tools for systematic updates
grep_search --query "old_filename" --includePattern "**/*.md"
replace_string_in_file --filePath docs/README.md \
  --oldString "[old](path)" --newString "[new](path)"
```

### Quality Assurance

```bash
# Automated validation after documentation changes
markdownlint-cli2 docs/                      # Format compliance
python scripts/agent_helper.py imports       # Code integrity
find docs/ -name "*.md" -exec linkchecker {} \;  # Link validation
```

**🔧 MARKDOWN LINTING STANDARDS:**

- **Line Length**: Maximum 80 characters per line (MD013)
- **Code Block Languages**: Always specify language for fenced code blocks
- **List Formatting**: Surround all lists with blank lines
- **Heading Hierarchy**: Use proper heading levels instead of emphasized text
- **Link Quality**: Use descriptive link text, avoid "click here"

**✅ RECOMMENDED TOOLS:**

- `markdownlint-cli2` for comprehensive markdown linting
- `linkchecker` for validating external links
- VS Code markdownlint extension for real-time feedback

## Migration and Evolution Patterns

### Documentation Debt Management

1. **Regular Audits**
   - Monthly review of documentation structure
   - Identify outdated or misplaced content
   - Plan consolidation opportunities

2. **Incremental Improvement**
   - Improve documentation during related feature work
   - Consolidate related documents when editing
   - Update cross-references during maintenance

3. **Community Feedback Integration**
   - User feedback on documentation clarity
   - Developer feedback on technical accuracy
   - Iterative improvement based on usage patterns

### Legacy Content Handling

1. **Historical Preservation**
   - Move completed analyses to `docs/history/`
   - Preserve decision context for future reference
   - Maintain links from current documentation to historical context

2. **Gradual Migration**
   - Phase out legacy documentation gradually
   - Provide migration guides for breaking changes
   - Maintain backwards compatibility during transitions

3. **Consolidation Strategies**
   - Merge related documents when appropriate
   - Eliminate duplicate content
   - Create comprehensive guides from fragmented information

---

This pattern guide ensures professional documentation organization that supports
both current development needs and future HACS publication requirements, while
maintaining clear audience focus and comprehensive cross-referencing.
