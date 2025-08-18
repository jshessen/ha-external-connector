"""API routers for the web interface."""

from .integrations import router as integration_router
from .setup import router as setup_router
from .status import router as status_router

__all__ = ["integration_router", "status_router", "setup_router"]
