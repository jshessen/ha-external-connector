"""Centralized test fixtures for the HA External Connector test suite.

This module provides a unified approach to test fixtures, reducing duplication
and ensuring consistency across all test files.
"""

# Import submodules to make them available through tests.fixtures
from tests.fixtures import aws_fixtures, cloudflare_fixtures, test_secrets

# Import commonly used functions for convenience
from tests.fixtures.test_secrets import (
    generate_alexa_secret,
    generate_api_token,
    generate_cf_client_secret,
    generate_test_secret,
    get_deterministic_secret,
)

try:
    from tests.fixtures.aws_fixtures import AWS_MANAGER_TEST_PARAMS
except ImportError:
    # AWS fixtures may not be available in all environments
    AWS_MANAGER_TEST_PARAMS = None

try:
    from tests.fixtures.cloudflare_fixtures import CLOUDFLARE_MANAGER_TEST_PARAMS
except ImportError:
    # CloudFlare fixtures may not be available in all environments
    CLOUDFLARE_MANAGER_TEST_PARAMS = None

__all__ = [
    # Submodules
    "test_secrets",
    "aws_fixtures",
    "cloudflare_fixtures",
    # Common functions
    "generate_alexa_secret",
    "generate_api_token",
    "generate_cf_client_secret",
    "generate_test_secret",
    "get_deterministic_secret",
    "AWS_MANAGER_TEST_PARAMS",
    "CLOUDFLARE_MANAGER_TEST_PARAMS",
]
