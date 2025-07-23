# Makefile for ha-external-connector development

.PHONY: help install lint lint-fix format test clean dev-setup quality-report

# Default target
help:
	@echo "🚀 ha-external-connector Development Commands"
	@echo "============================================="
	@echo ""
	@echo "Setup:"
	@echo "  install      Install dependencies with Poetry"
	@echo "  dev-setup    Complete development environment setup"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run all linters (non-destructive)"
	@echo "  lint-fix     Run linters with auto-fix where possible"
	@echo "  format       Format code with black and isort"
	@echo "  quality-report  Generate comprehensive quality report"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  test-cov-unit        Run unit tests with coverage"
	@echo "  test-cov-integration Run integration tests with coverage"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Clean up cache and temp files"

# Installation and setup
install:
	@echo "📦 Installing dependencies..."
	poetry install --with dev

dev-setup: install
	@echo "🔧 Setting up development environment..."
	poetry run pre-commit install
	@echo "✅ Development environment ready!"

# Code quality targets
lint:
	@echo "🔍 Running comprehensive code quality analysis..."
	@echo "==============================================="
	@echo ""
	@echo "🔍 Pylint Analysis:"
	@echo "-------------------"
	-poetry run pylint src/ha_connector/ --recursive=y
	@echo ""
	@echo "🦀 Ruff Analysis:"
	@echo "-----------------"
	-poetry run ruff check src/
	@echo ""
	@echo "🐍 Flake8 Analysis:"
	@echo "-------------------"
	-poetry run flake8 src/
	@echo ""
	@echo "🔎 MyPy Type Checking:"
	@echo "----------------------"
	-poetry run mypy src/ha_connector/
	@echo ""
	@echo "🛡️ Bandit Security Analysis:"
	@echo "-----------------------------"
	-poetry run bandit -r src/
	@echo ""
	@echo "🦅 Vulture Dead Code Detection:"
	@echo "--------------------------------"
	-poetry run vulture src/
	@echo ""
	@echo "🔒 OWASP Dependency Check:"
	@echo "---------------------------"
	-poetry run pip-audit
	@echo ""
	@echo "🛡️ Safety Dependency Check:"
	@echo "-----------------------------"
	-poetry run safety check
	@echo ""
	@echo "✅ Code quality analysis complete!"

lint-fix:
	@echo "🔧 Running linters with auto-fix..."
	@echo "Fixing with Ruff..."
	-poetry run ruff check src/ --fix
	@echo "Formatting with Black..."
	-poetry run black src/
	@echo "Sorting imports with isort..."
	-poetry run isort src/
	@echo "✅ Auto-fixes applied!"

format:
	@echo "🎨 Formatting code..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "✅ Code formatted!"

# Generate comprehensive quality report
quality-report:
	@echo "📊 Generating comprehensive code quality report..."
	@echo "=================================================="
	@mkdir -p reports
	@echo "# Code Quality Report" > reports/quality_report.md
	@echo "Generated: $$(date)" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## Pylint Analysis" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run pylint src/ha_connector/ --recursive=y >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## Ruff Analysis" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run ruff check src/ >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## MyPy Analysis" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run mypy src/ha_connector/ >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## Bandit Security Analysis" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run bandit -r src/ >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## Vulture Dead Code Detection" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run vulture src/ >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## OWASP Dependency Check" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run pip-audit --format=text >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "" >> reports/quality_report.md
	@echo "## Safety Dependency Check" >> reports/quality_report.md
	@echo "\`\`\`" >> reports/quality_report.md
	-poetry run safety check >> reports/quality_report.md 2>&1
	@echo "\`\`\`" >> reports/quality_report.md
	@echo "📄 Report saved to reports/quality_report.md"

# Testing
test:
	@echo "🧪 Running tests..."
	poetry run pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

test-cov-unit:
	@echo "🧪 Running unit tests with coverage..."
	poetry run pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing

test-cov-integration:
	@echo "🧪 Running integration tests with coverage..."
	poetry run pytest tests/integration/ --cov=src --cov-report=html --cov-report=term-missing

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist/ build/ htmlcov/ .coverage reports/
	@echo "✅ Cleanup complete!"

# Quick development shortcuts
quick-check: format lint-fix
	@echo "🚀 Quick quality check complete!"

full-quality: clean format lint test
	@echo "🎯 Full quality pipeline complete!"
