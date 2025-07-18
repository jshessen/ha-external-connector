"""
Main CLI Application

This module provides the main command-line interface using Typer.
Modern Python CLI for Home Assistant External Connector.
"""


import os

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..utils import HAConnectorLogger

# Initialize console and logger
console = Console()
logger = HAConnectorLogger("ha-connector-cli")

# Create main Typer app
app = typer.Typer(
    name="ha-connector",
    help=(
        "Home Assistant External Connector - Bridging the gap between external "
        "services and your Home Assistant instance"
    ),
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


# Version information
__version__ = "3.0.0"


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print(f"Home Assistant External Connector v{__version__}")
        console.print(
            "Comprehensive framework for secure external connectivity "
            "with automated deployment"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """
    Home Assistant External Connector CLI

    Bridging the gap between external services and your Home Assistant instance.
    Comprehensive framework for secure external connectivity with automated deployment.
    """
    # Set global options
    if verbose:
        logger.verbose = True
        # Use standard logging levels
        logger.logger.setLevel(10 if verbose else 20)  # 10=DEBUG, 20=INFO

    if dry_run:
        os.environ['DRY_RUN'] = 'true'

    # Show welcome banner
    if not version:
        welcome_text = Text()
        welcome_text.append("Home Assistant External Connector", style="bold blue")
        welcome_text.append(f" v{__version__}", style="dim")

        welcome_panel = Panel(
            welcome_text,
            title="🏠 HA External Connector",
            border_style="blue",
            padding=(1, 2),
        )

        console.print(welcome_panel)


if __name__ == "__main__":
    app()
