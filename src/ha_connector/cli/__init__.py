"""
CLI Package

This package provides the command-line interface for Home Assistant External Connector.
Replaces the bash install.sh and related CLI scripts with a modern Python implementation using Typer.
"""

from .main import app, main
from .commands import (
    install_command,
    deploy_command,
    configure_command,
    status_command,
    remove_command,
)

__all__ = [
    "app",
    "main",
    "install_command",
    "deploy_command",
    "configure_command",
    "status_command",
    "remove_command",
]
