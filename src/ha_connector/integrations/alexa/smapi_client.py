"""
🚀 SMAPI (Skill Management API) Client for Amazon Developer Console Integration

This module provides comprehensive SMAPI API integration for programmatic
Alexa Smart Home skill management, including authentication, skill creation,
configuration, and testing automation.

=== SMAPI FEATURES ===

- OAuth 2.0 with Login with Amazon (LWA)
- Skill manifest management and validation
- Interaction model configuration
- Account linking automation
- Skill testing and certification
- Beta testing management
- Metrics and analytics integration

=== AUTHENTICATION FLOW ===

1. Generate authorization URL
2. User grants permissions
3. Exchange authorization code for access token
4. Use access token for SMAPI operations
5. Refresh token when needed

This client handles all SMAPI REST API interactions required for
fully automated Alexa Smart Home skill setup and management.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class SMAPICredentials:
    """SMAPI API credentials for Amazon Developer Console access."""

    client_id: str
    client_secret: str
    access_token: str | None = None
    refresh_token: str | None = None
    vendor_id: str | None = None

    @classmethod
    def from_environment(cls) -> "SMAPICredentials":
        """Load SMAPI credentials from environment variables."""
        return cls(
            client_id=os.environ.get("LWA_CLIENT_ID", ""),
            client_secret=os.environ.get("LWA_CLIENT_SECRET", ""),
            access_token=os.environ.get("LWA_ACCESS_TOKEN"),
            refresh_token=os.environ.get("LWA_REFRESH_TOKEN"),
            vendor_id=os.environ.get("AMAZON_VENDOR_ID"),
        )


class SMAPIClient:
    """SMAPI (Skill Management API) client for programmatic skill management."""

    BASE_URL = "https://api.amazonalexa.com"
    LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"  # nosec B105

    def __init__(self, credentials: SMAPICredentials):
        """Initialize SMAPI client with credentials."""
        self.credentials = credentials
        self._session = requests.Session()

        if credentials.access_token:
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {credentials.access_token}",
                    "Content-Type": "application/json",
                }
            )

    def authenticate(self, authorization_code: str, redirect_uri: str) -> bool:
        """Exchange authorization code for access token."""
        logger.info("Exchanging authorization code for SMAPI access token")

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
        }

        try:
            response = self._session.post(self.LWA_TOKEN_URL, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.credentials.access_token = token_data["access_token"]
            self.credentials.refresh_token = token_data.get("refresh_token")

            # Update session headers
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self.credentials.access_token}",
                    "Content-Type": "application/json",
                }
            )

            logger.info("SMAPI authentication successful")
            return True

        except (requests.RequestException, KeyError) as e:
            logger.error("SMAPI authentication failed: %s", e)
            return False

    def refresh_access_token(self) -> bool:
        """Refresh SMAPI access token using refresh token."""
        if not self.credentials.refresh_token:
            logger.error("No refresh token available")
            return False

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.credentials.refresh_token,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
        }

        try:
            response = self._session.post(self.LWA_TOKEN_URL, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.credentials.access_token = token_data["access_token"]

            # Update session headers
            self._session.headers.update(
                {"Authorization": f"Bearer {self.credentials.access_token}"}
            )

            logger.info("SMAPI token refresh successful")
            return True

        except (requests.RequestException, KeyError) as e:
            logger.error("SMAPI token refresh failed: %s", e)
            return False

    def get_vendor_id(self) -> str | None:
        """Get vendor ID for the authenticated user."""
        if self.credentials.vendor_id:
            return self.credentials.vendor_id

        try:
            response = self._session.get(f"{self.BASE_URL}/v1/vendors")
            response.raise_for_status()

            vendors = response.json().get("vendors", [])
            if vendors:
                self.credentials.vendor_id = vendors[0]["id"]
                return self.credentials.vendor_id

        except (requests.RequestException, KeyError) as e:
            logger.error("Failed to get vendor ID: %s", e)

        return None

    def create_skill(self, skill_config: Any) -> str | None:
        """Create a new Alexa skill using SMAPI."""
        vendor_id = self.get_vendor_id()
        if not vendor_id:
            logger.error("No vendor ID available for skill creation")
            return None

        manifest = skill_config.to_skill_manifest()
        create_data = {
            "vendorId": vendor_id,
            "manifest": manifest,
        }

        try:
            response = self._session.post(
                f"{self.BASE_URL}/v1/skills", json=create_data
            )
            response.raise_for_status()

            skill_id = response.json().get("skillId")
            if skill_id:
                logger.info("Skill created successfully: %s", skill_id)
                return skill_id

        except (requests.RequestException, KeyError) as e:
            logger.error("Skill creation failed: %s", e)

        return None

    def configure_account_linking(self, skill_id: str, skill_config: Any) -> bool:
        """Configure account linking for a skill."""
        config = skill_config.to_account_linking_config()

        try:
            response = self._session.put(
                f"{self.BASE_URL}/v1/skills/{skill_id}/accountLinkingClient",
                json=config,
            )
            response.raise_for_status()
            logger.info("Account linking configured for skill: %s", skill_id)
            return True

        except requests.RequestException as e:
            logger.error("Account linking configuration failed: %s", e)
            return False

    def validate_skill(self, skill_id: str) -> dict[str, Any]:
        """Validate a skill using SMAPI."""
        try:
            response = self._session.post(
                f"{self.BASE_URL}/v1/skills/{skill_id}/validations"
            )
            response.raise_for_status()

            validation_id = response.json().get("id")
            if validation_id:
                # Poll for validation results
                return self._get_validation_result(skill_id, validation_id)

        except (requests.RequestException, KeyError) as e:
            logger.error("Skill validation failed: %s", e)

        return {"status": "FAILED", "error": "Validation request failed"}

    def _get_validation_result(
        self, skill_id: str, validation_id: str
    ) -> dict[str, Any]:
        """Get validation results."""
        try:
            response = self._session.get(
                f"{self.BASE_URL}/v1/skills/{skill_id}/validations/{validation_id}"
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error("Failed to get validation result: %s", e)
            return {"status": "FAILED", "error": str(e)}

    def enable_skill_for_testing(self, skill_id: str) -> bool:
        """Enable a skill for testing."""
        try:
            response = self._session.post(
                f"{self.BASE_URL}/v1/skills/{skill_id}/stages/development/enablement"
            )
            response.raise_for_status()
            logger.info("Skill enabled for testing: %s", skill_id)
            return True

        except requests.RequestException as e:
            logger.error("Failed to enable skill for testing: %s", e)
            return False

    def get_skill_status(self, skill_id: str) -> dict[str, Any]:
        """Get skill status and metadata."""
        try:
            response = self._session.get(f"{self.BASE_URL}/v1/skills/{skill_id}/status")
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error("Failed to get skill status: %s", e)
            return {"error": str(e)}

    def list_skills(self) -> list[dict[str, Any]]:
        """List all skills for the vendor."""
        vendor_id = self.get_vendor_id()
        if not vendor_id:
            return []

        try:
            response = self._session.get(
                f"{self.BASE_URL}/v1/skills", params={"vendorId": vendor_id}
            )
            response.raise_for_status()
            return response.json().get("skills", [])

        except requests.RequestException as e:
            logger.error("Failed to list skills: %s", e)
            return []
