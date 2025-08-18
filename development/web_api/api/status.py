"""System status API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SystemStatus(BaseModel):
    """Model for overall system status."""

    status: str  # 'healthy', 'warning', 'error'
    version: str
    uptime: str
    active_integrations: int
    total_integrations: int


class ServiceHealth(BaseModel):
    """Model for individual service health."""

    service: str
    status: str
    last_check: str
    response_time_ms: int | None = None
    error_message: str | None = None


@router.get("/", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    """Get overall system status."""
    return SystemStatus(
        status="healthy",
        version="3.0.0",
        uptime="2 days, 4 hours",
        active_integrations=1,
        total_integrations=2,
    )


@router.get("/health", response_model=list[ServiceHealth])
async def get_health_status() -> list[ServiceHealth]:
    """Get detailed health status for all services."""
    return [
        ServiceHealth(
            service="AWS Lambda",
            status="healthy",
            last_check="2024-01-15T10:30:00Z",
            response_time_ms=150,
        ),
        ServiceHealth(
            service="Home Assistant",
            status="healthy",
            last_check="2024-01-15T10:30:00Z",
            response_time_ms=200,
        ),
        ServiceHealth(
            service="CloudFlare DNS",
            status="warning",
            last_check="2024-01-15T10:30:00Z",
            response_time_ms=500,
            error_message="High latency detected",
        ),
    ]


@router.get("/logs")
async def get_recent_logs() -> dict[str, Any]:
    """Get recent system logs."""
    return {
        "logs": [
            {
                "timestamp": "2024-01-15T10:30:00Z",
                "level": "INFO",
                "message": "Alexa integration enabled successfully",
            },
            {
                "timestamp": "2024-01-15T10:25:00Z",
                "level": "WARN",
                "message": "CloudFlare DNS response time elevated",
            },
            {
                "timestamp": "2024-01-15T10:20:00Z",
                "level": "INFO",
                "message": "System startup completed",
            },
        ]
    }
