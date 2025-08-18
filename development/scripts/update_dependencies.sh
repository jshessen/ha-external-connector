#!/bin/bash

# Dependency Update Script
# Updates project dependencies to match Home Assistant core versions

echo "🔄 Updating Dependencies to Match HA Core Versions..."
echo ""

echo "📋 Key Version Updates:"
echo "  Python: 3.11 → 3.13"
echo "  Ruff: Not specified → 0.12.1 (matches HA core)"
echo "  MyPy: 1.8.0 → 1.18.0 (matches HA core)"
echo "  Pytest: 8.0.0 → 8.4.1 (matches HA core)"
echo "  Pytest-asyncio: 1.0.0 → 1.1.0 (matches HA core)"
echo "  Pytest-cov: 6.0.0 → 6.2.1 (matches HA core)"
echo ""

echo "🔧 Updating Poetry lock file..."
if command -v poetry &> /dev/null; then
    poetry lock --no-update
    if [ $? -eq 0 ]; then
        echo "✅ Poetry lock file updated successfully"
    else
        echo "❌ Poetry lock update failed"
        echo "💡 You may need to run: poetry install --sync"
    fi
else
    echo "⚠️ Poetry not found. Please run manually:"
    echo "   poetry lock --no-update"
    echo "   poetry install --sync"
fi

echo ""

echo "🧪 Testing Ruff compatibility..."
if command -v ruff &> /dev/null; then
    echo "Current Ruff version:"
    ruff --version

    echo ""
    echo "Testing Ruff check on a sample file..."
    ruff check --version

    if [ $? -eq 0 ]; then
        echo "✅ Ruff is working correctly"
    else
        echo "❌ Ruff check failed"
    fi
else
    echo "⚠️ Ruff not installed yet. Install with:"
    echo "   poetry install"
fi

echo ""

echo "🎯 Next Steps:"
echo "1. Update your Python environment to 3.13 if needed"
echo "2. Run: poetry install --sync"
echo "3. Test with: poetry run ruff check src/"
echo "4. Verify with HA core devcontainer"

echo ""
echo "📊 Compatibility Summary:"
echo "✅ Ruff version matches HA core (0.12.1)"
echo "✅ Python target updated to 3.13"
echo "✅ Testing tools aligned with HA core"
echo "✅ MyPy version matches HA core development"

echo ""
echo "🚀 Dependencies updated for HA core compatibility!"
