#!/usr/bin/env python3
"""Shared constants for the HA External Connector."""

from typing import Any

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

# Common deployment exports
DEPLOYMENT_EXPORTS = [
    "ServiceInstaller",
    "ServiceType",
    "ServiceConfig",
    "DeploymentResult",
    "DeploymentManager",
    "DeploymentStrategy",
    "DeploymentConfig",
    "orchestrate_deployment",
]
