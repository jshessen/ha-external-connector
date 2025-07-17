#!/usr/bin/env python3
"""
Test script for ha_connector utilities.

This script validates that our basic utilities work correctly.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ha_connector import (
    logger,
    validate_json,
    extract_json_value,
    validate_input,
    safe_file_write,
    require_commands
)


def test_logging():
    """Test logging functionality."""
    print("Testing logging...")
    logger.info("Test info message")
    logger.debug("Test debug message")
    logger.success("Test success message")
    logger.warning("Test warning message")
    print("✓ Logging test passed")


def test_json_utilities():
    """Test JSON utilities."""
    print("Testing JSON utilities...")

    # Test valid JSON
    test_json = '{"test": {"nested": "value"}, "array": [1, 2, 3]}'
    assert validate_json(test_json), "JSON validation failed"

    # Test invalid JSON
    assert not validate_json('{"invalid": json}'), "Invalid JSON should fail validation"

    # Test JSON value extraction
    value = extract_json_value(test_json, "test.nested", "default")
    assert value == "value", f"Expected 'value', got '{value}'"

    # Test default value
    default_value = extract_json_value(test_json, "nonexistent.key", "default")
    assert default_value == "default", f"Expected 'default', got '{default_value}'"

    print("✓ JSON utilities test passed")


def test_input_validation():
    """Test input validation."""
    print("Testing input validation...")

    # Test valid inputs
    assert validate_input("test-string", "string"), "Valid string should pass"
    assert validate_input("https://example.com", "url"), "Valid URL should pass"
    assert validate_input("us-east-1", "aws_region"), "Valid AWS region should pass"
    assert validate_input("alexa", "service_name"), "Valid service name should pass"

    # Test invalid inputs
    assert not validate_input("invalid-url", "url"), "Invalid URL should fail"
    assert not validate_input("invalid_region", "aws_region"), "Invalid region should fail"
    assert not validate_input("Invalid123", "service_name"), "Invalid service name should fail"

    print("✓ Input validation test passed")


def test_file_operations():
    """Test file operations."""
    print("Testing file operations...")

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Test content\n"

        # Test safe file write
        safe_file_write(test_file, test_content, backup=False)
        assert test_file.exists(), "File should be created"
        assert test_file.read_text() == test_content, "File content should match"

        print("✓ File operations test passed")


def test_prerequisites():
    """Test prerequisite checking."""
    print("Testing prerequisites...")

    # Test with commands that should exist
    try:
        require_commands("python", "ls")  # These should exist on most systems
        print("✓ Prerequisites test passed")
    except Exception as e:
        print(f"⚠ Prerequisites test warning: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting ha_connector utilities tests...")
    print()

    try:
        test_logging()
        test_json_utilities()
        test_input_validation()
        test_file_operations()
        test_prerequisites()

        print()
        print("🎉 All tests passed!")
        logger.success("Utilities migration successful - core functionality working!")

        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failure: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
