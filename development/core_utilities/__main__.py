"""
Main entry point for the ha-connector CLI.

This allows the module to be executed directly:
    python -m ha_connector
"""

from .cli import app

if __name__ == "__main__":
    app()
