"""Constants for the Home Assistant External Connector integration."""

from typing import Any

DOMAIN = "ha_external_connector"

# Integration Types
INTEGRATION_ALEXA = "alexa"
INTEGRATION_GOOGLE = "google"
INTEGRATION_IOS = "ios"

# AWS Configuration Defaults
DEFAULT_AWS_REGION = "us-east-1"

# Standard AWS Lambda Assume Role Policy
LAMBDA_ASSUME_ROLE_POLICY: dict[str, Any] = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}

# Platform Service Names
SERVICE_AWS = "aws"
SERVICE_CLOUDFLARE = "cloudflare"
SERVICE_SECURITY = "security"

# Update Intervals
COORDINATOR_UPDATE_INTERVAL_MINUTES = 5
HEALTH_CHECK_INTERVAL_MINUTES = 15
