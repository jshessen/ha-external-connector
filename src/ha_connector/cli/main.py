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
from .commands import (
    configure_command,
    deploy_command,
    install_command,
    remove_command,
    status_command,
)

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


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
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
        os.environ["DRY_RUN"] = "true"

    # Show welcome banner
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


# Add version as a separate command instead of a callback
@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"Home Assistant External Connector v{__version__}")
    console.print(
        "Comprehensive framework for secure external connectivity "
        "with automated deployment"
    )


# Register commands with the main app
app.command(name="install")(install_command)
app.command(name="deploy")(deploy_command)
app.command(name="configure")(configure_command)
app.command(name="status")(status_command)
app.command(name="remove")(remove_command)


if __name__ == "__main__":
    app()
