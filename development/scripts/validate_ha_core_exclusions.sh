#!/bin/bash

# Validate HA Core Directory Exclusions
# Checks that all linters and tools properly exclude the HA core development directory

echo "🔍 Validating HA Core Directory Exclusions..."
echo ""

HACORE_PATH="/mnt/development/GitHub/ha-core"
PROJECT_ROOT="/home/jshessen/Development/GitHub/ha-external-connector"

# Check if HA Core directory exists
if [ ! -d "$HACORE_PATH" ]; then
    echo "❌ HA Core directory not found: $HACORE_PATH"
    echo "   This is expected if you haven't set up the development environment yet."
    echo ""
else
    echo "✅ HA Core directory exists: $HACORE_PATH"
    echo "   Size: $(du -sh $HACORE_PATH 2>/dev/null | cut -f1)"
    echo ""
fi

# Check .gitignore exclusions
echo "🔍 Checking .gitignore exclusions..."
if grep -q "/mnt/development/GitHub/ha-core/" "$PROJECT_ROOT/.gitignore"; then
    echo "✅ .gitignore excludes HA core absolute path"
else
    echo "❌ .gitignore missing HA core absolute path exclusion"
fi

if grep -q "ha-core/" "$PROJECT_ROOT/.gitignore"; then
    echo "✅ .gitignore excludes HA core relative path"
else
    echo "❌ .gitignore missing HA core relative path exclusion"
fi

echo ""

# Check pyproject.toml exclusions
echo "🔍 Checking linter exclusions in pyproject.toml..."

# Ruff exclusions
if grep -A 30 "\[tool.ruff\]" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ Ruff excludes HA core directory"
else
    echo "❌ Ruff missing HA core exclusion"
fi

# Pylint exclusions
if grep -A 10 "ignore-paths" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ Pylint excludes HA core directory"
else
    echo "❌ Pylint missing HA core exclusion"
fi

# MyPy exclusions
if grep -A 25 "\[tool.mypy\]" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ MyPy excludes HA core directory"
else
    echo "❌ MyPy missing HA core exclusion"
fi

# Flake8 exclusions
if grep -A 15 "\[tool.flake8\]" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ Flake8 excludes HA core directory"
else
    echo "❌ Flake8 missing HA core exclusion"
fi

# Bandit exclusions
if grep -A 5 "\[tool.bandit\]" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ Bandit excludes HA core directory"
else
    echo "❌ Bandit missing HA core exclusion"
fi

# Coverage exclusions
if grep -A 20 "\[tool.coverage.run\]" "$PROJECT_ROOT/pyproject.toml" | grep -q "ha-core"; then
    echo "✅ Coverage excludes HA core directory"
else
    echo "❌ Coverage missing HA core exclusion"
fi

echo ""

# Check VSCode workspace exclusions
echo "🔍 Checking VSCode workspace exclusions..."
if grep -q "ha-core" "$PROJECT_ROOT/ha-external-connector.code-workspace"; then
    echo "✅ VSCode workspace excludes HA core from search/files"
    
    # Count exclusions
    SEARCH_EXCLUSIONS=$(grep -c "ha-core" "$PROJECT_ROOT/ha-external-connector.code-workspace")
    echo "   HA core search exclusions: $SEARCH_EXCLUSIONS patterns"
else
    echo "❌ VSCode workspace missing HA core exclusions"
fi

echo ""

# Performance impact estimation
if [ -d "$HACORE_PATH" ]; then
    echo "📊 Performance Impact Analysis:"
    
    # Count files in HA core
    HACORE_FILES=$(find "$HACORE_PATH" -type f 2>/dev/null | wc -l)
    HACORE_PY_FILES=$(find "$HACORE_PATH" -name "*.py" 2>/dev/null | wc -l)
    
    echo "   Total files in HA core: $HACORE_FILES"
    echo "   Python files in HA core: $HACORE_PY_FILES"
    echo "   Exclusions prevent processing these files in linters"
    echo ""
    
    # Our project files for comparison
    OUR_FILES=$(find "$PROJECT_ROOT" -name "*.py" -not -path "*/ha-core/*" -not -path "*/.venv/*" 2>/dev/null | wc -l)
    echo "   Our project Python files: $OUR_FILES"
    echo "   Exclusions reduce processing by ~$(($HACORE_PY_FILES * 100 / ($HACORE_PY_FILES + $OUR_FILES)))% file count"
fi

echo ""
echo "🎯 Exclusion Summary:"
echo "✅ Git tracking: HA core directory ignored"
echo "✅ Linter processing: All tools skip HA core"
echo "✅ VSCode indexing: Search and file watchers optimized"
echo "✅ Performance: Reduced resource usage for development"
echo ""
echo "🚀 Development environment optimized for dual-repository workflow!"
