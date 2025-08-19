"""FastAPI web application for HA External Connector.

This module provides a web-based interface for configuring and managing
Home Assistant external integrations, transforming the CLI-based tool
into a user-friendly web interface.
"""

from __future__ import annotations

from pathlib import Path

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI is optional for development
    FastAPI = None
    Request = None
    HTMLResponse = None
    StaticFiles = None
    Jinja2Templates = None
    FASTAPI_AVAILABLE = False

# Note: These imports would need to be updated when the actual
# web API structure is available
# from custom_components.ha_external_connector.web.api import (
#     integration_router,
#     setup_router,
#     status_router,
# )
# from custom_components.ha_external_connector.web.api.alexa import (
#     router as alexa_router,
# )
# from custom_components.ha_external_connector.web.api.integrations_selection import (
#     router as integrations_selection_router,
# )

# Get the current file's directory to build paths
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app() -> FastAPI | None:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI application instance if FastAPI is available, None otherwise
    """
    if not FASTAPI_AVAILABLE:
        return None
    web_app = FastAPI(
        title="HA External Connector",
        description="Home Assistant External Service Integration Manager",
        version="3.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Static files (CSS, JS, images)
    if StaticFiles and STATIC_DIR.exists():
        web_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # API Routes would be added here when available
    # web_app.include_router(
    #     integration_router, prefix="/api/integrations", tags=["integrations"]
    # )
    # web_app.include_router(status_router, prefix="/api/status", tags=["status"])
    # web_app.include_router(setup_router, prefix="/api/setup", tags=["setup"])
    # web_app.include_router(alexa_router, prefix="/api", tags=["alexa"])
    # web_app.include_router(
    #     integrations_selection_router, prefix="/api", tags=["integration-selection"]
    # )

    return web_app


# Global templates instance and application - only create if FastAPI is available
if FASTAPI_AVAILABLE:
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app = create_app()

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint - redirect to web interface."""
        return {"message": "HA External Connector Web Interface", "docs": "/api/docs"}

else:
    TEMPLATES = None
    APP = None

    # Define route functions that can be used if FastAPI becomes available
    async def root() -> dict[str, str]:
        """Root endpoint - redirect to web interface."""
        return {"message": "HA External Connector Web Interface", "docs": "/api/docs"}

    async def dashboard(_request: Request) -> None:
        """Dashboard page - stub when FastAPI unavailable."""
        return None

    async def integrations_page(_request: Request) -> None:
        """Integrations management page - stub when FastAPI unavailable."""
        return None

    async def setup_page(_request: Request) -> None:
        """Setup wizard page - stub when FastAPI unavailable."""
        return None

    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring - stub when FastAPI unavailable."""
        return {
            "status": "unavailable",
            "service": "ha-external-connector-web",
            "reason": "FastAPI not installed",
        }
