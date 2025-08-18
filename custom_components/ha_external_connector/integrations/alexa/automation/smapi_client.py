"""Amazon SMAPI (Skill Management API) client for programmatic skill management.

This module provides direct integration with Amazon's official Skill Management
API for automated skill creation, configuration, validation, and deployment.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
import urllib.parse
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError

from .models import SkillDeploymentStage, SkillValidationResult, SMAPICredentials

# Handle aiohttp imports - will be available at runtime in Home Assistant
try:
    from aiohttp import ClientError
except ImportError:
    # Fallback for development environment - create a specific exception type
    class ClientError(Exception):
        """Fallback ClientError for development environment."""

if TYPE_CHECKING:
    from aiohttp import ClientSession


_LOGGER = logging.getLogger(__name__)


# Custom exception classes for SMAPI operations
class ValidationError(HomeAssistantError):
    """Error to indicate validation failures."""


class AmazonSMAPIClient:
    """Amazon SMAPI REST API client for programmatic skill management.

    This class provides direct integration with Amazon's official Skill Management
    API (SMAPI) for automated skill creation, configuration, validation, and
    deployment operations.

    Business Metaphor: "Digital Embassy to Amazon"
    Acts as a sophisticated diplomatic embassy that handles all official
    communications with Amazon's skill management systems using proper
    protocols, authentication, and formal procedures.
    """

    # Amazon SMAPI endpoints
    SMAPI_BASE_URL = "https://api.amazonalexa.com"
    OAUTH_BASE_URL = "https://www.amazon.com/ap/oa"

    def __init__(
        self,
        credentials: SMAPICredentials,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize Amazon SMAPI client.

        Args:
            credentials: SMAPI OAuth credentials
        """
        self.credentials = credentials
        self.session = session
        self.logger = _LOGGER
        self._should_close_session = session is None

    async def __aenter__(self) -> AmazonSMAPIClient:
        """Async context manager entry."""
        if self.session is None:
            # This should be set by Home Assistant integration before use
            msg = "Session must be provided by Home Assistant integration"
            raise HomeAssistantError(msg)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        if self._should_close_session and self.session:
            await self.session.close()

    def generate_oauth_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Generate Amazon OAuth 2.0 authorization URL.

        Args:
            redirect_uri: OAuth redirect URI for callback
            state: Optional state parameter for CSRF protection

        Returns:
            Complete OAuth authorization URL
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.credentials.client_id,
            "scope": " ".join(self.credentials.scope),
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
        }

        url = f"{self.OAUTH_BASE_URL}?{urllib.parse.urlencode(params)}"
        self.logger.info("Generated OAuth URL for Amazon SMAPI authentication")
        return url

    async def exchange_code_for_token(
        self,
        authorization_code: str,
        redirect_uri: str,
    ) -> bool:
        """Exchange OAuth authorization code for access token.

        Args:
            authorization_code: OAuth authorization code from callback
            redirect_uri: OAuth redirect URI used in authorization

        Returns:
            True if token exchange succeeded

        Raises:
            ValidationError: If token exchange fails
        """
        if not self.session:
            raise ValidationError("HTTP session not initialized")

        token_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
        }

        try:
            async with self.session.post(
                "https://api.amazon.com/auth/o2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    self.logger.error("OAuth token exchange failed: %s", error_data)
                    raise ValidationError(f"Token exchange failed: {error_data}")

                token_response = await response.json()

                # Update credentials with new tokens
                self.credentials.access_token = token_response["access_token"]
                self.credentials.refresh_token = token_response.get("refresh_token")
                self.credentials.expires_at = int(time.time()) + token_response.get(
                    "expires_in", 3600
                )

                self.logger.info("Successfully obtained SMAPI access token")
                return True

        except Exception as e:
            self.logger.error("OAuth token exchange error: %s", e)
            raise ValidationError(f"Token exchange error: {e}") from e

    async def _make_smapi_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated SMAPI API request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: SMAPI endpoint path
            data: Optional request body data
            params: Optional query parameters

        Returns:
            API response data

        Raises:
            ValidationError: If API request fails
        """
        if not self.session:
            raise ValidationError("HTTP session not initialized")

        url = f"{self.SMAPI_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.credentials.access_token}",
            "Content-Type": "application/json",
        }

        # Retry logic for rate limiting and transient errors
        for attempt in range(3):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                ) as response:
                    response_data: dict[str, Any] = (
                        await response.json() if response.content_length else {}
                    )

                    if response.status == 200:
                        return response_data
                    if response.status == 429:  # Rate limited
                        wait_time = 2**attempt
                        self.logger.warning(
                            "Rate limited, waiting %s seconds", wait_time
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    error_msg = response_data.get("message", f"HTTP {response.status}")
                    raise ValidationError(f"SMAPI request failed: {error_msg}")

            except ClientError as e:
                if attempt == 2:  # Last attempt
                    raise ValidationError(f"SMAPI request error: {e}") from e
                await asyncio.sleep(2**attempt)

        raise ValidationError("SMAPI request failed after all retries")

    async def create_skill(
        self,
        skill_manifest: dict[str, Any],
        vendor_id: str | None = None,
    ) -> str:
        """Create new Alexa skill using SMAPI.

        Args:
            skill_manifest: Complete skill manifest definition
            vendor_id: Optional vendor ID for organization skills

        Returns:
            Skill ID of created skill

        Raises:
            ValidationError: If skill creation fails
        """
        endpoint = "/v1/skills"

        create_data: dict[str, Any] = {"manifest": skill_manifest}
        if vendor_id:
            create_data["vendorId"] = vendor_id  # Correct: vendorId is a top-level key

        try:
            response = await self._make_smapi_request(
                "POST", endpoint, data=create_data
            )
            skill_id = response.get("skillId")

            if not skill_id:
                raise ValidationError(
                    "Skill creation succeeded but no skill ID returned"
                )

            self.logger.info("Successfully created Alexa skill: %s", skill_id)
            return skill_id

        except Exception as e:
            self.logger.error("Skill creation failed: %s", e)
            raise ValidationError(f"Failed to create skill: {e}") from e

    async def validate_skill(
        self,
        skill_id: str,
        stage: SkillDeploymentStage = SkillDeploymentStage.DEVELOPMENT,
    ) -> SkillValidationResult:
        """Validate skill configuration and manifest.

        Args:
            skill_id: Target skill identifier
            stage: Deployment stage to validate

        Returns:
            Validation result with detailed feedback

        Raises:
            ValidationError: If validation request fails
        """
        # Start validation
        endpoint = f"/v1/skills/{skill_id}/stages/{stage.value}/validations"

        try:
            response = await self._make_smapi_request("POST", endpoint)
            validation_id = response.get("id")

            if not validation_id:
                raise ValidationError(
                    "Validation request succeeded but no validation ID returned"
                )

            # Poll validation status
            status_endpoint = (
                f"/v1/skills/{skill_id}/stages/{stage.value}/validations/"
                f"{validation_id}"
            )

            for _ in range(30):  # 5 minute timeout
                status_response = await self._make_smapi_request("GET", status_endpoint)
                status = status_response.get("status", "UNKNOWN")

                if status in ["SUCCEEDED", "FAILED"]:
                    result = SkillValidationResult(
                        validation_id=validation_id,
                        status=status,
                        result=status_response.get("result"),
                        error_count=len(
                            status_response.get("result", {}).get("validations", [])
                        ),
                        warning_count=0,  # Will be calculated from result details
                    )

                    if status == "SUCCEEDED":
                        self.logger.info("Skill validation succeeded: %s", skill_id)
                    else:
                        self.logger.warning(
                            "Skill validation failed: %s errors", result.error_count
                        )

                    return result

                await asyncio.sleep(10)  # Check every 10 seconds

            raise ValidationError("Skill validation timed out")

        except Exception as e:
            self.logger.error("Skill validation error: %s", e)
            raise ValidationError(f"Skill validation failed: {e}") from e
