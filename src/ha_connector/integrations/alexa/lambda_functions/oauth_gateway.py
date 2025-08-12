"""
🔐 CLOUDFLARE OAUTH GATEWAY: Dedicated OAuth Authentication Service 🌐

Handles OAuth token exchange for Alexa Smart Home account linking.
Provides optional CloudFlare protection for enhanced security.

Original work: Copyright 2019 Jason Hu <awaregit at gmail.com>
Enhanced by: Jeff Hessenflow <jeff.hessenflow@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# pylint: disable=too-many-lines,too-many-branches

# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import base64
import configparser
import json
import logging
import os
import urllib.parse
from typing import Any

import boto3
import urllib3
from botocore.exceptions import ClientError

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import create_lambda_logger

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === LOGGING CONFIGURATION ===
_debug = bool(os.environ.get("DEBUG"))

# Use shared configuration logger instead of local setup
_logger = create_lambda_logger("OAuthGateway")
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize boto3 client at global scope for connection reuse
client = boto3.client("ssm")  # pyright: ignore[reportUnknownMemberType]
app_config_path = os.environ.get("APP_CONFIG_PATH", "/alexa/auth/")

log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)


class HAConfig:
    """Configuration class for Home Assistant settings."""

    def __init__(self, config: configparser.ConfigParser) -> None:
        """
        Construct new app with configuration
        :param config: application configuration
        """
        self.config = config

    def get_config(self):
        return self.config


# Initialize app at global scope for reuse across invocations
def load_config(ssm_parameter_path: str) -> configparser.ConfigParser:
    """
    Load configparser from config stored in SSM Parameter Store
    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser holding loaded config
    """
    configuration = configparser.ConfigParser()
    try:
        # Get all parameters for this app
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        # Loop through the returned parameters and populate the ConfigParser
        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            for param in param_details.get("Parameters"):
                param_name = param.get("Name")
                param_value = param.get("Value")

                if param_name is None:
                    raise ValueError("SSM parameter 'Name' is missing")
                if param_value is None:
                    raise ValueError(f"SSM parameter '{param_name}' value is missing")

                param_path_array = param_name.split("/")
                section_position = len(param_path_array) - 1
                section_name = param_path_array[section_position]
                config_values = json.loads(param_value)
                config_dict = {section_name: config_values}
                configuration.read_dict(config_dict)
    except (ClientError, ValueError, KeyError) as err:
        print("Encountered an error loading config from SSM.")
        print(str(err))

    return configuration


def get_app_config() -> HAConfig:
    """
    Load and return the HAConfig instance.
    :return: HAConfig instance
    """
    config = load_config(app_config_path)
    return HAConfig(config)


def lambda_handler(event: dict[str, Any]) -> dict[str, Any]:
    _logger.debug("Event: %s", event)

    print("Loading config and creating persistence object...")
    app = get_app_config()

    app_config = app.get_config()["appConfig"]

    destination_url = app_config.get("HA_BASE_URL")
    cf_client_id = app_config.get("CF_CLIENT_ID")
    cf_client_secret = app_config.get("CF_CLIENT_SECRET")
    wrapper_secret = app_config.get("WRAPPER_SECRET")

    if not destination_url:
        raise ValueError("Please set BASE_URL parameter")
    destination_url = destination_url.strip("/")

    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED", timeout=urllib3.Timeout(connect=2.0, read=10.0)
    )

    # Get request body with proper validation
    event_body = event.get("body")
    if event_body is None:
        raise ValueError("Request body is missing")

    req_body = (
        base64.b64decode(event_body) if event.get("isBase64Encoded") else event_body
    )

    _logger.debug(req_body)

    req_dict = urllib.parse.parse_qs(req_body)
    client_secret = req_dict[b"client_secret"][0].decode("utf-8")

    # Validate wrapper secret
    if not wrapper_secret:
        raise ValueError("WRAPPER_SECRET is missing from configuration")

    if client_secret != wrapper_secret:
        raise ValueError("Client secret mismatch")

    # Validate all required config values
    if not cf_client_id:
        raise ValueError("CF_CLIENT_ID is missing from configuration")
    if not cf_client_secret:
        raise ValueError("CF_CLIENT_SECRET is missing from configuration")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "CF-Access-Client-Id": str(cf_client_id),
        "CF-Access-Client-Secret": str(cf_client_secret),
    }

    response = http.request(
        "POST", f"{destination_url}/auth/token", headers=headers, body=req_body
    )

    if response.status >= 400:
        _logger.debug("ERROR %s %s", response.status, response.data.decode("utf-8"))
        return {
            "event": {
                "payload": {
                    "type": (
                        "INVALID_AUTHORIZATION_CREDENTIAL"
                        if response.status in (401, 403)
                        else f"INTERNAL_ERROR {response.status}"
                    ),
                    "message": response.data.decode("utf-8"),
                }
            }
        }
    _logger.debug("Response: %s", response.data.decode("utf-8"))
    return json.loads(response.data.decode("utf-8"))


# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
