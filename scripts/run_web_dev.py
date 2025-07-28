#!/usr/bin/env python3
"""Development server for HA External Connector web interface."""

import logging
import sys
from pathlib import Path

# Add src to path for development
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the development server with module string for reload support
    uvicorn.run(
        "ha_connector.web:app",
        host="127.0.0.1",  # Localhost only for development
        port=8000,
        reload=True,
        log_level="info",
        reload_dirs=[src_path],  # Watch the src directory for changes
    )
