"""
CLI Package

This package provides the command-line interface for Home Assistant External Connector.
Implements all CLI functionality using modern Python and Typer.
"""

from .commands import (
    configure_command,
    deploy_command,
    install_command,
    remove_command,
    status_command,
)
from .main import app, main

__all__ = [
    "app",
    "main",
    "install_command",
    "deploy_command",
    "configure_command",
    "status_command",
    "remove_command",
]
