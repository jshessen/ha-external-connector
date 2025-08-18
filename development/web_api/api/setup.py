"""Setup and configuration wizard API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SetupStep(BaseModel):
    """Model for setup step information."""

    step: int
    title: str
    description: str
    completed: bool
    required: bool = True


class AWSCredentials(BaseModel):
    """Model for AWS credentials configuration."""

    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"


class HomeAssistantConfig(BaseModel):
    """Model for Home Assistant configuration."""

    url: str
    token: str
    verify_ssl: bool = True


@router.get("/steps", response_model=list[SetupStep])
async def get_setup_steps() -> list[SetupStep]:
    """Get all setup steps and their completion status."""
    return [
        SetupStep(
            step=1,
            title="AWS Configuration",
            description="Configure AWS credentials and region",
            completed=False,
        ),
        SetupStep(
            step=2,
            title="Home Assistant Connection",
            description="Connect to your Home Assistant instance",
            completed=False,
        ),
        SetupStep(
            step=3,
            title="Integration Selection",
            description="Choose which integrations to enable",
            completed=False,
        ),
        SetupStep(
            step=4,
            title="Testing & Validation",
            description="Verify all connections are working",
            completed=False,
        ),
    ]


@router.post("/aws")
async def configure_aws(
    credentials: AWSCredentials,  # pylint: disable=unused-argument
) -> dict[str, str]:
    """Configure AWS credentials."""
    # TODO: Implement AWS credential validation and storage
    return {"message": "AWS credentials configured successfully"}


@router.post("/homeassistant")
async def configure_homeassistant(
    config: HomeAssistantConfig,  # pylint: disable=unused-argument
) -> dict[str, str]:
    """Configure Home Assistant connection."""
    # TODO: Implement Home Assistant connection validation
    return {"message": "Home Assistant connection configured successfully"}


@router.post("/validate")
async def validate_setup() -> dict[str, Any]:
    """Validate the current setup configuration."""
    # TODO: Implement comprehensive validation
    return {
        "valid": True,
        "checks": [
            {"name": "AWS Connection", "status": "pass"},
            {"name": "Home Assistant Connection", "status": "pass"},
            {"name": "Required Permissions", "status": "pass"},
        ],
    }


@router.post("/complete")
async def complete_setup() -> dict[str, str]:
    """Mark setup as complete and initialize services."""
    # TODO: Implement setup completion logic
    return {"message": "Setup completed successfully", "redirect": "/dashboard"}
