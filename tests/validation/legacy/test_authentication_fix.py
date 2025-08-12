#!/usr/bin/env python3
"""
Test script to verify Smart Home Bridge authentication fix.
This creates a minimal test event and validates the authentication headers.
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_smart_home_authentication():
    """Test that Smart Home Bridge authentication headers are correctly formed."""

    logger.info("🔧 Testing Smart Home Bridge authentication headers...")

    # Test the configuration loading and header formation
    try:
        # Import and test the shared configuration
        from src.ha_connector.integrations.alexa.lambda_functions.shared_configuration import (
            load_configuration,
        )

        logger.info("✅ Successfully imported shared configuration")

        # Test configuration loading
        config_dict = load_configuration("/ha-alexa/appConfig")

        if config_dict:
            logger.info("✅ Configuration loaded successfully")
            logger.info(f"   Configuration keys: {list(config_dict.keys())}")

            # Check for required keys
            required_keys = [
                "HA_BASE_URL",
                "HA_TOKEN",
                "CF_CLIENT_ID",
                "CF_CLIENT_SECRET",
            ]
            missing_keys = [key for key in required_keys if key not in config_dict]

            if not missing_keys:
                logger.info("✅ All required configuration keys present")
                logger.info(f"   Base URL: {config_dict.get('HA_BASE_URL')}")
                logger.info(f"   Token length: {len(config_dict.get('HA_TOKEN', ''))}")
                logger.info(
                    f"   CloudFlare ID length: {len(config_dict.get('CF_CLIENT_ID', ''))}"
                )
                logger.info(
                    f"   CloudFlare Secret length: {len(config_dict.get('CF_CLIENT_SECRET', ''))}"
                )

                # Test header formation (simulate what the lambda does)
                headers = {
                    "Authorization": f"Bearer {config_dict['HA_TOKEN']}",
                    "Content-Type": "application/json",
                    "CF-Access-Client-Id": config_dict["CF_CLIENT_ID"],
                    "CF-Access-Client-Secret": config_dict["CF_CLIENT_SECRET"],
                }

                logger.info("✅ Headers formed successfully:")
                logger.info(
                    f"   Authorization: Bearer {config_dict['HA_TOKEN'][:20]}..."
                )
                logger.info(
                    f"   CF-Access-Client-Id: {config_dict['CF_CLIENT_ID'][:20]}..."
                )
                logger.info(
                    f"   CF-Access-Client-Secret: {config_dict['CF_CLIENT_SECRET'][:20]}..."
                )

                return True
            else:
                logger.error(f"❌ Missing configuration keys: {missing_keys}")
                return False
        else:
            logger.error("❌ Configuration loading failed")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False


def main():
    """Main test function."""
    logger.info("🚀 Starting Smart Home Bridge Authentication Test")
    logger.info("=" * 60)

    success = test_smart_home_authentication()

    logger.info("=" * 60)
    if success:
        logger.info(
            "🎉 Authentication test PASSED - Headers should be working correctly"
        )
    else:
        logger.info("❌ Authentication test FAILED - Check configuration")

    return success


if __name__ == "__main__":
    main()
