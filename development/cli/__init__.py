"""
CLI Package

This package provides the command-line interface for Home Assistant External Connector.
Implements all CLI functionality using modern Python and Typer.
"""

from .main import app, main

__all__ = [
    "app",
    "main",
]
