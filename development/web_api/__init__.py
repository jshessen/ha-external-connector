"""FastAPI web application for HA External Connector.

This module provides a web-based interface for configuring and managing
Home Assistant external integrations, transforming the CLI-based tool
into a user-friendly web interface.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ha_connector.web.api import integration_router, setup_router, status_router
from ha_connector.web.api.alexa import router as alexa_router
from ha_connector.web.api.integrations_selection import (
    router as integrations_selection_router,
)

# Get the current file's directory to build paths
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    web_app = FastAPI(
        title="HA External Connector",
        description="Home Assistant External Service Integration Manager",
        version="3.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Static files (CSS, JS, images)
    web_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # API Routes
    web_app.include_router(
        integration_router, prefix="/api/integrations", tags=["integrations"]
    )
    web_app.include_router(status_router, prefix="/api/status", tags=["status"])
    web_app.include_router(setup_router, prefix="/api/setup", tags=["setup"])
    web_app.include_router(alexa_router, prefix="/api", tags=["alexa"])
    web_app.include_router(
        integrations_selection_router, prefix="/api", tags=["integration-selection"]
    )

    return web_app


# Global templates instance
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Application instance
app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - redirect to web interface."""
    return {"message": "HA External Connector Web Interface", "docs": "/api/docs"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request) -> HTMLResponse:
    """Integrations management page."""
    return templates.TemplateResponse("integrations.html", {"request": request})


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request) -> HTMLResponse:
    """Setup wizard page."""
    return templates.TemplateResponse("setup.html", {"request": request})


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "ha-external-connector-web"}
