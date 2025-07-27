"""
CLI Commands Module

This module provides all the CLI commands for the Home Assistant External Connector.
Enhanced with Phase 4.2 interactive installation wizard and progress tracking.
"""

# pylint: disable=too-many-lines,too-many-locals
# Note: Large module size is acceptable for comprehensive CLI interface

import os
import traceback

# Note: Using Optional[X] instead of X | None for Typer compatibility
# Typer does not yet support the modern union syntax (str | None) from Python 3.10
# This prevents "Parameter.make_metavar() missing ctx" error with Click/Typer
from typing import Annotated, Any, Optional

import typer
from botocore.exceptions import ClientError
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..adapters.aws_manager import AWSResourceManager
from ..aws.alexa_skill_manager import AlexaSkillManager
from ..config import ConfigurationManager, InstallationScenario
from ..deployment import (
    DeploymentConfig,
    DeploymentManager,
    DeploymentStrategy,
    ServiceInstaller,
    ServiceType,
)
from ..utils import HAConnectorLogger, ValidationError

console = Console()
logger = HAConnectorLogger("ha-connector-cli")

# Helper for AWS access validation


def validate_aws_access(region: str = "us-east-1") -> dict[str, Any]:
    """
    Validate AWS access for the given region and return the result as a dictionary.
    """
    manager = AWSResourceManager(region)
    resp = manager.validate_aws_access()
    return resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)


# Enhanced Interactive Installation Wizard


def _interactive_scenario_selection() -> InstallationScenario:
    """Interactive scenario selection with enhanced user experience"""
    console.print(
        Panel(
            "[bold blue]Home Assistant External Connector - "
            "Installation Wizard[/bold blue]",
            title="🏠 Welcome",
            border_style="blue",
        )
    )

    console.print("\n[bold]Select your integration scenario:[/bold]\n")

    # Display scenario options
    console.print("🎯 [bold cyan]SCENARIO 1: Direct Alexa Integration[/bold cyan]")
    console.print("   • Basic Alexa Smart Home skill → AWS Lambda → Home Assistant")
    console.print("   • No CloudFlare proxy required")
    console.print("   • Simplest setup for Alexa voice commands\n")

    console.print(
        "🔒 [bold green]SCENARIO 2: CloudFlare-Proxied Alexa Integration[/bold green]"
    )
    console.print(
        "   • Alexa Smart Home skill → AWS Lambda → CloudFlare Access → Home Assistant"
    )
    console.print("   • Adds CloudFlare Access security layer")
    console.print("   • Requires CloudFlare domain and Access setup\n")

    console.print(
        "📱 [bold magenta]SCENARIO 3: iOS Companion with CloudFlare[/bold magenta]"
    )
    console.print(
        "   • iOS Home Assistant app → AWS Lambda → CloudFlare Access → Home Assistant"
    )
    console.print("   • Enables secure external access for iOS app")
    console.print("   • Requires existing CloudFlare Access setup\n")

    # Scenario mapping
    scenario_map = {
        "1": InstallationScenario.DIRECT_ALEXA,
        "2": InstallationScenario.CLOUDFLARE_ALEXA,
        "3": InstallationScenario.CLOUDFLARE_IOS,
    }

    while True:
        choice = Prompt.ask(
            "[bold]Choose scenario[/bold]", choices=["1", "2", "3"], default="1"
        )

        if choice in scenario_map:
            selected_scenario = scenario_map[choice]

            # Display confirmation
            scenario_names = {
                InstallationScenario.DIRECT_ALEXA: "Direct Alexa Integration",
                InstallationScenario.CLOUDFLARE_ALEXA: (
                    "CloudFlare-Proxied Alexa Integration"
                ),
                InstallationScenario.CLOUDFLARE_IOS: ("iOS Companion with CloudFlare"),
            }

            console.print(
                f"\n✅ [bold green]Selected:[/bold green] "
                f"{scenario_names[selected_scenario]}"
            )
            return selected_scenario

        console.print("[red]❌ Invalid choice. Please select 1, 2, or 3.[/red]")


def _enhanced_installation_wizard(
    scenario: InstallationScenario,
    region: str,
    dry_run: bool = False,
    force: bool = False,
) -> None:
    """Enhanced installation wizard with progress tracking and user interaction"""

    console.print(
        Panel(
            f"[bold]Installation Scenario:[/bold] {scenario.value}\n"
            f"[bold]AWS Region:[/bold] {region}",
            title="🚀 Installation Configuration",
            border_style="green",
        )
    )

    # Step 1: Pre-installation checks
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Running pre-installation checks...", total=None)

        # Validate AWS access
        aws_validation = validate_aws_access(region)
        if not aws_validation.get("valid", False):
            console.print("[red]❌ AWS access validation failed[/red]")
            raise typer.Exit(1)

        console.print(
            f"[green]✅ AWS access validated[/green] "
            f"(Account: {aws_validation.get('account_id', 'unknown')})"
        )

    # Step 2: Configuration setup
    config_manager = ConfigurationManager()
    config_manager.init_config(scenario)

    # Check if configuration is valid
    if not config_manager.validate_scenario_setup(scenario):
        console.print(
            "[yellow]⚠ Configuration incomplete or invalid. "
            "Entering interactive setup...[/yellow]"
        )
        _enhanced_interactive_configuration_setup(config_manager)

    # Step 3: Installation planning
    console.print("\n[bold]🔍 Analyzing existing resources...[/bold]")

    service_installer = ServiceInstaller(region=region, dry_run=dry_run, verbose=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating installation plan...", total=None)
        installation_plan = service_installer.plan_enhanced_installation(scenario)
        progress.update(task, completed=100)

    # Display installation plan
    _display_installation_plan(installation_plan)

    # Step 4: Handle conflicts and user decisions
    user_choices = {}
    if installation_plan.get("user_decisions_needed"):
        console.print("\n[bold yellow]⚠ User decisions required:[/bold yellow]")
        user_choices = _handle_user_decisions(
            installation_plan["user_decisions_needed"]
        )

    # Step 5: Final confirmation
    if not force and not dry_run:
        proceed = Confirm.ask("\n[bold]Proceed with installation?[/bold]", default=True)
        if not proceed:
            console.print("[yellow]Installation cancelled by user[/yellow]")
            raise typer.Exit(0)

    # Step 6: Execute installation
    console.print("\n[bold]🚀 Executing installation...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing services...", total=None)

        try:
            result = service_installer.execute_enhanced_installation(
                installation_plan, user_choices
            )
            progress.update(task, completed=100)

            if result.success:
                _display_installation_success(result, scenario)
            else:
                _display_installation_errors(result)
                raise typer.Exit(1)

        except Exception as e:
            progress.update(task, completed=100)
            console.print(f"[red]❌ Installation failed: {str(e)}[/red]")
            raise typer.Exit(1) from e


def _enhanced_interactive_configuration_setup(
    config_manager: ConfigurationManager,
) -> None:
    """Enhanced interactive configuration setup with validation"""
    console.print(
        Panel(
            "[bold]Interactive Configuration Setup[/bold]",
            title="🔧 Configuration",
            border_style="yellow",
        )
    )

    # HA Base URL
    if not os.getenv("HA_BASE_URL"):
        console.print("[bold]1. Home Assistant Configuration[/bold]")
        ha_url = Prompt.ask(
            "Enter your Home Assistant base URL", default="https://ha.example.com"
        )

        # Basic URL validation
        if not ha_url.startswith(("http://", "https://")):
            ha_url = f"https://{ha_url}"

        os.environ["HA_BASE_URL"] = ha_url.rstrip("/")
        console.print(f"✅ Home Assistant URL: {ha_url}")

    # Alexa secret
    if not os.getenv("ALEXA_SECRET"):
        console.print("\n[bold]2. Alexa Configuration[/bold]")

        use_generated = Confirm.ask(
            "Generate secure Alexa secret automatically?", default=True
        )

        if use_generated:
            alexa_secret = config_manager.generate_secure_secret()
            console.print(f"✅ Generated Alexa secret: [bold]{alexa_secret}[/bold]")
        else:
            alexa_secret = Prompt.ask(
                "Enter your Alexa secret (minimum 32 characters)", password=True
            )

        os.environ["ALEXA_SECRET"] = alexa_secret

    # AWS region confirmation
    if not os.getenv("AWS_REGION"):
        console.print("\n[bold]3. AWS Configuration[/bold]")
        aws_region = Prompt.ask("Enter AWS region", default="us-east-1")
        os.environ["AWS_REGION"] = aws_region
        console.print(f"✅ AWS Region: {aws_region}")

    console.print("[green]✅ Interactive configuration completed[/green]")


def _display_installation_plan(plan: dict[str, Any]) -> None:
    """Display installation plan in a user-friendly format"""
    console.print(
        Panel(
            f"[bold]Scenario:[/bold] {plan['scenario']}\n"
            f"[bold]AWS Region:[/bold] {plan['region']}\n"
            f"[bold]Requirements:[/bold] {plan['requirements']}\n"
            f"[bold]Resources Found:[/bold] {plan['matched_resources']}\n"
            f"[bold]Installation Steps:[/bold] {len(plan['installation_steps'])}",
            title="📋 Installation Plan",
            border_style="blue",
        )
    )

    # Display conflicts if any
    if plan.get("conflicts"):
        console.print("\n[bold red]⚠ Resource Conflicts Detected:[/bold red]")
        table = Table()
        table.add_column("Resource", style="cyan")
        table.add_column("Issue", style="red")
        table.add_column("Type", style="yellow")

        for conflict in plan["conflicts"]:
            table.add_row(
                conflict["resource"], conflict["issue"], conflict["resource_type"]
            )
        console.print(table)

    # Display installation steps
    if plan.get("installation_steps"):
        console.print("\n[bold green]📝 Installation Steps:[/bold green]")
        for i, step in enumerate(plan["installation_steps"], 1):
            console.print(
                f"{i}. [cyan]{step['action'].title()}[/cyan] "
                f"{step['resource_type']} [bold]{step['resource_id']}[/bold]"
            )


def _handle_user_decisions(decisions: list[dict[str, Any]]) -> dict[str, str]:
    """Handle user decisions for conflicts and choices"""
    user_choices: dict[str, str] = {}

    for decision in decisions:
        console.print(f"\n[yellow]❓ {decision['message']}[/yellow]")

        if "options" in decision:
            choice = Prompt.ask(
                "Choose option",
                choices=decision["options"],
                default=decision["options"][0],
            )

            # Generate key for the choice
            resource_key = f"conflict_{decision.get('message', '').split()[1]}"
            user_choices[resource_key] = choice

            console.print(f"✅ Selected: [bold]{choice}[/bold]")

    return user_choices


def _display_installation_success(result: Any, scenario: InstallationScenario) -> None:
    """Display installation success with next steps"""
    console.print(
        Panel(
            "[bold green]🎉 Installation completed successfully![/bold green]",
            title="✅ Success",
            border_style="green",
        )
    )

    # Display deployment summary
    if hasattr(result, "metadata") and result.metadata:
        summary = result.metadata.get("summary", "Installation completed")
        console.print(f"\n[bold]Summary:[/bold] {summary}")

    # Show next steps based on scenario
    _display_next_steps(scenario)


def _display_installation_errors(result: Any) -> None:
    """Display installation errors"""
    console.print(
        Panel(
            "[bold red]❌ Installation failed![/bold red]",
            title="💥 Error",
            border_style="red",
        )
    )

    if hasattr(result, "errors") and result.errors:
        console.print("\n[bold red]Errors encountered:[/bold red]")
        for error in result.errors:
            console.print(f"  • [red]{error}[/red]")

    if hasattr(result, "warnings") and result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  • [yellow]{warning}[/yellow]")


def _display_next_steps(scenario: InstallationScenario) -> None:
    """Display scenario-specific next steps"""
    console.print("\n[bold]📋 Next Steps:[/bold]")

    if scenario == InstallationScenario.DIRECT_ALEXA:
        console.print(
            "1. Go to Amazon Developer Console (developer.amazon.com)\n"
            "2. Create/edit your Alexa Smart Home skill\n"
            "3. Set the endpoint URL to your Lambda function URL\n"
            "4. Configure account linking (optional for basic setup)\n"
            "5. Test with: 'Alexa, discover devices'"
        )
    elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
        console.print(
            "1. Configure CloudFlare Access application\n"
            "2. Set up Alexa Smart Home skill with CloudFlare endpoint\n"
            "3. Configure OAuth flow for account linking\n"
            "4. Test device discovery and voice commands"
        )
    elif scenario == InstallationScenario.CLOUDFLARE_IOS:
        console.print(
            "1. Configure CloudFlare Access policies\n"
            "2. Update iOS Home Assistant app with external URL\n"
            "3. Test connectivity from iOS app\n"
            "4. Verify secure authentication flow"
        )

    console.print(
        "\n[dim]💡 For detailed guidance, run: [bold]ha-connector status[/bold][/dim]"
    )


# Helper functions for the install command


def _print_installation_header(
    scenario: str, region: str, environment: str, dry_run: bool
) -> None:
    """Print installation header information."""
    console.print("🚀 Starting Home Assistant External Connector installation...")
    console.print(f"Scenario: [bold]{scenario}[/bold]")
    console.print(f"Region: [bold]{region}[/bold]")
    console.print(f"Environment: [bold]{environment}[/bold]")

    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")


def _validate_and_get_scenario(scenario: str) -> InstallationScenario:
    """Validate scenario string and return InstallationScenario enum."""
    scenario_mapping = {
        "direct_alexa": InstallationScenario.DIRECT_ALEXA,
        "cloudflare_alexa": InstallationScenario.CLOUDFLARE_ALEXA,
        "cloudflare_ios": InstallationScenario.CLOUDFLARE_IOS,
        "all": InstallationScenario.ALL,
    }

    if scenario not in scenario_mapping:
        console.print(f"[red]❌ Invalid scenario: {scenario}[/red]")
        console.print(f"Supported scenarios: {', '.join(scenario_mapping.keys())}")
        raise typer.Exit(1)

    return scenario_mapping[scenario]


def _setup_configuration(
    installation_scenario: InstallationScenario,
) -> ConfigurationManager:
    """Set up and validate configuration."""
    config_manager = ConfigurationManager()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading configuration...", total=None)

        config_manager.init_config(installation_scenario)
        # If config is missing, enter interactive setup
        if not config_manager.config or not config_manager.validate_scenario_setup(
            installation_scenario
        ):
            console.print(
                "[yellow]⚠ Some configuration missing or invalid, "
                "entering interactive setup[/yellow]"
            )
            _interactive_configuration_setup(config_manager)
            # Re-validate after interactive setup
            if not config_manager.validate_scenario_setup(installation_scenario):
                console.print(
                    "[red]❌ Configuration validation failed after "
                    "interactive setup[/red]"
                )
                raise typer.Exit(1)

    console.print("[green]✓ Configuration validated successfully[/green]")
    return config_manager


def _print_services_to_install(services_to_install: list[ServiceType]) -> None:
    """Print services that will be installed."""
    services_str = ", ".join([s.value for s in services_to_install])
    console.print(f"Services to install: [bold]{services_str}[/bold]")


def _create_deployment_config(
    services_to_install: list[ServiceType],
    config_params: dict[str, Any],
) -> DeploymentConfig:
    """Create deployment configuration."""
    return DeploymentConfig(
        environment=config_params["environment"],
        version=config_params["version"],
        strategy=DeploymentStrategy.ROLLING,
        services=services_to_install,
        region=config_params["region"],
        dry_run=config_params["dry_run"],
        verbose=config_params["verbose"],
        force=config_params["force"],
        cloudflare_setup=config_params["auto_setup_cloudflare"],
        cloudflare_domain=config_params["cloudflare_domain"],
        service_overrides=None,
        tags=None,
    )


def _execute_deployment(deployment_config: DeploymentConfig) -> dict[str, Any]:
    """Execute the deployment and return results."""
    deployment_manager = DeploymentManager(deployment_config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Executing deployment...", total=None)
        return deployment_manager.execute_deployment()


def _handle_deployment_result(deployment_result: dict[str, Any]) -> None:
    """Handle deployment results and display appropriate messages."""
    if deployment_result["success"]:
        console.print("\n[green]🎉 Installation completed successfully![/green]")
        _display_installation_results(deployment_result)
    else:
        console.print("\n[red]💥 Installation failed![/red]")
        for error in deployment_result["errors"]:
            console.print(f"[red]  • {error}[/red]")
        raise typer.Exit(1)


def install_wizard() -> None:
    """
    Interactive installation wizard with enhanced user experience.

    This function provides a guided installation process using the
    interactive helper functions for scenario selection, configuration,
    and installation with progress tracking.
    """
    try:
        # Step 1: Interactive scenario selection
        scenario = _interactive_scenario_selection()

        # Step 2: Enhanced installation wizard (returns None but shows progress)
        _enhanced_installation_wizard(scenario, region="us-east-1")

        # Step 3: Display completion message and next steps
        console.print(
            "\n✅ [bold green]Installation completed successfully![/bold green]"
        )

        # Show next steps
        console.print(
            Panel(
                "[bold]Next Steps:[/bold]\n\n"
                "1. 🎯 Test your Alexa integration with voice commands\n"
                "2. 📱 Configure iOS Home Assistant app if applicable\n"
                "3. 🔧 Review AWS Lambda logs for troubleshooting\n"
                "4. 📖 Check documentation for advanced configuration",
                title="🎉 Installation Complete",
                border_style="green",
            )
        )

    except KeyboardInterrupt as e:
        console.print("\n[yellow]⚠ Installation wizard interrupted by user[/yellow]")
        raise typer.Exit(130) from e
    except Exception as e:
        console.print(f"\n[red]💥 Installation wizard failed: {str(e)}[/red]")
        raise typer.Exit(1) from e


def install(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    scenario: str = typer.Argument(
        "direct_alexa",
        help="Installation scenario: direct_alexa|cloudflare_alexa|cloudflare_ios|all",
    ),
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region for deployment"
    ),
    environment: str = typer.Option(
        "prod", "--environment", "-e", help="Deployment environment"
    ),
    version: str = typer.Option("1.0.0", "--version", help="Service version to deploy"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation without confirmation"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    auto_setup_cloudflare: bool = typer.Option(
        False,
        "--auto-setup-cloudflare",
        help="Automatically setup CloudFlare configuration",
    ),
    cloudflare_domain: Optional[str] = typer.Option(  # noqa: UP045
        None, "--cloudflare-domain", help="CloudFlare domain for configuration"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Launch interactive installation wizard"
    ),
) -> None:
    """
    Install Home Assistant External Connector services.

    This command sets up the complete infrastructure for connecting external
    services to your Home Assistant instance with automated deployment.

    Supported scenarios:
    - direct_alexa: Direct Alexa integration
    - cloudflare_alexa: Alexa integration via CloudFlare Access
    - cloudflare_ios: iOS Companion via CloudFlare Access
    - all: Install all supported integrations

    Use --interactive for guided installation with enhanced user experience.
    """
    # Launch interactive wizard if requested
    if interactive:
        install_wizard()
        return

    _print_installation_header(scenario, region, environment, dry_run)

    try:
        installation_scenario = _validate_and_get_scenario(scenario)
        _setup_configuration(installation_scenario)
        services_to_install = _get_services_for_scenario(installation_scenario)

        _print_services_to_install(services_to_install)

        deployment_config = _create_deployment_config(
            services_to_install,
            {
                "environment": environment,
                "version": version,
                "region": region,
                "dry_run": dry_run,
                "verbose": verbose,
                "force": force,
                "auto_setup_cloudflare": auto_setup_cloudflare,
                "cloudflare_domain": cloudflare_domain,
            },
        )

        deployment_result = _execute_deployment(deployment_config)
        _handle_deployment_result(deployment_result)

    except KeyboardInterrupt as exc:
        console.print("\n[yellow]⚠ Installation interrupted by user[/yellow]")
        raise typer.Exit(130) from exc
    except (ValueError, ValidationError) as e:
        console.print(f"\n[red]💥 Configuration error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except (FileNotFoundError, OSError) as e:
        console.print(f"\n[red]💥 File system error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Installation failed: {str(e)}[/red]")
        if verbose:
            console.print(traceback.format_exc())
        raise typer.Exit(1) from e


_DEFAULT_SERVICES = ["alexa", "ios_companion", "cloudflare_proxy"]


def wizard() -> None:
    """
    Launch the interactive installation wizard.

    This command provides a guided installation experience with:
    - Interactive scenario selection
    - Automated configuration setup
    - Progress tracking with visual feedback
    - Enhanced user experience with Rich UI components

    Equivalent to: ha-connector install --interactive
    """
    install_wizard()


def deploy(
    service: Annotated[
        str, typer.Argument(..., help="Service to deploy (e.g., alexa, cloudflare)")
    ],
    strategy: str = typer.Option(
        "rolling", "--strategy", "-s", help="Deployment strategy"
    ),
    cloudflare_domain: Optional[str] = typer.Option(  # noqa: UP045
        None, "--domain", "-d", help="CloudFlare domain for deployment"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be deployed without executing"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """
    Deploy specific services to AWS Lambda.

    This command deploys individual services without full installation setup.
    Useful for updates and targeted deployments.

    Examples:
        ha-connector deploy alexa
        ha-connector deploy alexa ios_companion --strategy rolling
        ha-connector deploy cloudflare_proxy --region us-west-2

    Available services: alexa, ios_companion, cloudflare_proxy
    """
    console.print(f"🚀 Deploying service: [bold]{service}[/bold]")

    try:
        # Validate service
        service_mapping = {
            "alexa": ServiceType.ALEXA,
            "ios_companion": ServiceType.IOS_COMPANION,
            "cloudflare_proxy": ServiceType.CLOUDFLARE_PROXY,
        }

        if service not in service_mapping:
            console.print(f"[red]❌ Invalid service: {service}[/red]")
            console.print(f"Supported services: {', '.join(service_mapping.keys())}")
            raise typer.Exit(1)

        service_type = service_mapping[service]

        # Validate strategy
        strategy_mapping = {
            "rolling": DeploymentStrategy.ROLLING,
            "blue-green": DeploymentStrategy.BLUE_GREEN,
            "canary": DeploymentStrategy.CANARY,
            "immediate": DeploymentStrategy.IMMEDIATE,
        }

        if strategy not in strategy_mapping:
            console.print(f"[red]❌ Invalid strategy: {strategy}[/red]")
            console.print(f"Supported strategies: {', '.join(strategy_mapping.keys())}")
            raise typer.Exit(1)

        deployment_strategy = strategy_mapping[strategy]

        # Create deployment configuration with defaults
        deployment_config = DeploymentConfig(
            environment="prod",
            version="1.0.0",
            strategy=deployment_strategy,
            services=[service_type],
            region="us-east-1",
            dry_run=dry_run,
            verbose=verbose,
            cloudflare_domain=cloudflare_domain,
            service_overrides=None,
            tags=None,
        )

        # Execute deployment
        deployment_manager = DeploymentManager(deployment_config)
        deployment_result = deployment_manager.execute_deployment()

        if deployment_result["success"]:
            console.print("\n[green]🎉 Deployment completed successfully![/green]")
            _display_deployment_results(deployment_result)
        else:
            console.print("\n[red]💥 Deployment failed![/red]")
            for error in deployment_result["errors"]:
                console.print(f"[red]  • {error}[/red]")
            raise typer.Exit(1)

    except (ValueError, ValidationError) as e:
        console.print(f"\n[red]💥 Configuration error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except (FileNotFoundError, OSError) as e:
        console.print(f"\n[red]💥 File system error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Deployment failed: {str(e)}[/red]")
        raise typer.Exit(1) from e


def configure(
    scenario: Optional[str] = typer.Option(  # noqa: UP045
        None, "--scenario", "-s", help="Configuration scenario"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Enable interactive configuration"
    ),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate without making changes"
    ),
) -> None:
    """
    Configure Home Assistant External Connector settings.

    This command helps set up and validate configuration for the connector.
    """
    console.print("🔧 Configuration Management")

    try:
        if scenario:
            scenario_mapping = {
                "direct_alexa": InstallationScenario.DIRECT_ALEXA,
                "cloudflare_alexa": InstallationScenario.CLOUDFLARE_ALEXA,
                "cloudflare_ios": InstallationScenario.CLOUDFLARE_IOS,
                "all": InstallationScenario.ALL,
            }

            if scenario not in scenario_mapping:
                console.print(f"[red]❌ Invalid scenario: {scenario}[/red]")
                raise typer.Exit(1)

            installation_scenario = scenario_mapping[scenario]
        else:
            installation_scenario = InstallationScenario.DIRECT_ALEXA

        config_manager = ConfigurationManager()

        if interactive:
            _interactive_configuration_setup(config_manager)

        if validate_only or not interactive:
            console.print("Validating configuration...")
            is_valid = config_manager.validate_scenario_setup(installation_scenario)
            if is_valid:
                console.print("[green]✓ Configuration is valid[/green]")
                _display_configuration_summary(config_manager)
            else:
                console.print("[red]❌ Configuration validation failed[/red]")
                raise typer.Exit(1)

    except (ValueError, ValidationError) as e:
        console.print(f"\n[red]💥 Configuration error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except (FileNotFoundError, OSError) as e:
        console.print(f"\n[red]💥 File system error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Configuration failed: {str(e)}[/red]")
        raise typer.Exit(1) from e


def status(
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region to check"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """
    Check status of deployed services.

    This command provides information about the current state of deployed
    Home Assistant External Connector services.
    """
    console.print("📊 Service Status")

    try:
        # Check AWS connectivity
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Checking AWS connectivity...", total=None)

            aws_result = validate_aws_access(region)

            if aws_result.get("status") != "success":
                console.print("[red]❌ AWS connectivity failed[/red]")
                raise typer.Exit(1)

        console.print("[green]✓ AWS connectivity OK[/green]")

        # Check deployed services
        service_installer = ServiceInstaller(region=region, verbose=verbose)
        deployed_services = service_installer.list_deployed_services()

        if deployed_services:
            _display_service_status(deployed_services, verbose)
        else:
            console.print("[yellow]ℹ No services currently deployed[/yellow]")

    except (ValueError, ValidationError) as e:
        console.print(f"\n[red]💥 Configuration error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except (ConnectionError, OSError) as e:
        console.print(f"\n[red]💥 Network connectivity error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Status check failed: {str(e)}[/red]")
        raise typer.Exit(1) from e


def remove(
    services: Annotated[list[str], typer.Argument(..., help="Services to remove")],
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region to remove from"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force removal without confirmation"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be removed without executing"
    ),
) -> None:
    """
    Remove deployed services.

    This command removes Home Assistant External Connector services
    from AWS Lambda and associated resources.

    Examples:
        ha-connector remove alexa
        ha-connector remove alexa ios_companion --force
        ha-connector remove cloudflare_proxy --dry-run

    Available services: alexa, ios_companion, cloudflare_proxy
    """
    console.print(f"🗑️ Removing services: [bold]{', '.join(services)}[/bold]")

    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")

    try:
        service_mapping = {
            "alexa": "ha-alexa-proxy",
            "ios_companion": "ha-ios-companion",
            "cloudflare_proxy": "ha-cloudflare-proxy",
        }

        functions_to_remove: list[str] = []
        for service in services:
            if service not in service_mapping:
                console.print(f"[red]❌ Invalid service: {service}[/red]")
                console.print(
                    f"Supported services: {', '.join(service_mapping.keys())}"
                )
                raise typer.Exit(1)

            functions_to_remove.append(service_mapping[service])

        # Remove duplicates
        functions_to_remove = list(set(functions_to_remove))

        if (
            not force
            and not dry_run
            and not Confirm.ask(
                f"Are you sure you want to remove {len(functions_to_remove)} "
                "service(s)?"
            )
        ):
            console.print("Operation cancelled")
            raise typer.Exit(0)

        service_installer = ServiceInstaller(region=region, dry_run=dry_run)

        removed_count = 0
        for function_name in functions_to_remove:
            if service_installer.remove_service(function_name):
                removed_count += 1
                console.print(f"[green]✓ Removed {function_name}[/green]")
            else:
                console.print(f"[red]✗ Failed to remove {function_name}[/red]")

        console.print(
            f"\n[green]🎉 Successfully removed {removed_count}/"
            f"{len(functions_to_remove)} services[/green]"
        )

    except (ValueError, ValidationError) as e:
        console.print(f"\n[red]💥 Configuration error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except (ConnectionError, OSError) as e:
        console.print(f"\n[red]💥 Network connectivity error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Removal failed: {str(e)}[/red]")
        raise typer.Exit(1) from e


# Helper functions


def _get_services_for_scenario(scenario: InstallationScenario) -> list[ServiceType]:
    """Get list of services for installation scenario"""
    if scenario == InstallationScenario.DIRECT_ALEXA:
        return [ServiceType.ALEXA]
    if scenario == InstallationScenario.CLOUDFLARE_ALEXA:
        return [ServiceType.ALEXA, ServiceType.CLOUDFLARE_PROXY]
    if scenario == InstallationScenario.CLOUDFLARE_IOS:
        return [ServiceType.IOS_COMPANION, ServiceType.CLOUDFLARE_PROXY]
    if scenario == InstallationScenario.ALL:
        return [
            ServiceType.ALEXA,
            ServiceType.IOS_COMPANION,
            ServiceType.CLOUDFLARE_PROXY,
        ]

    # This should never happen, but provide explicit handling
    raise ValueError(f"Unknown installation scenario: {scenario}")


def _interactive_configuration_setup(config_manager: ConfigurationManager) -> None:
    """Interactive configuration setup"""
    console.print("\n[bold]Interactive Configuration Setup[/bold]")

    # HA Base URL
    if not os.getenv("HA_BASE_URL"):
        ha_url = Prompt.ask(
            "Enter your Home Assistant base URL", default="https://ha.example.com"
        )
        os.environ["HA_BASE_URL"] = ha_url

    # Alexa secret
    if not os.getenv("ALEXA_SECRET"):
        alexa_secret = config_manager.generate_secure_secret()
        console.print(f"Generated Alexa secret: [bold]{alexa_secret}[/bold]")
        os.environ["ALEXA_SECRET"] = alexa_secret

    # AWS region
    if not os.getenv("AWS_REGION"):
        aws_region = Prompt.ask("Enter AWS region", default="us-east-1")
        os.environ["AWS_REGION"] = aws_region

    console.print("[green]✓ Interactive configuration completed[/green]")


def _display_installation_results(result: dict[str, Any]) -> None:
    """Display installation results"""
    table = Table(title="Installation Results")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Function ARN", style="blue")
    table.add_column("URL", style="magenta")

    for svc in result["services"]:
        svc_status = "✓ Success" if svc["success"] else "✗ Failed"
        status_style = "green" if svc["success"] else "red"

        table.add_row(
            svc["function_name"],
            f"[{status_style}]{svc_status}[/{status_style}]",
            svc.get("function_arn", "N/A"),
            svc.get("function_url", "N/A"),
        )

    console.print(table)

    if result.get("cloudflare"):
        cf_panel = Panel(
            f"CloudFlare Access URL: [bold]{result['cloudflare']['access_url']}[/bold]",
            title="🌤️ CloudFlare Setup",
            border_style="blue",
        )
        console.print(cf_panel)


def _display_deployment_results(result: dict[str, Any]) -> None:
    """Display deployment results"""
    _display_installation_results(result)

    console.print(
        f"\nDeployment completed in [bold]{result['deployment_time']:.2f}s[/bold]"
    )
    console.print(f"Strategy: [bold]{result['strategy']}[/bold]")
    console.print(f"Environment: [bold]{result['environment']}[/bold]")


def _display_configuration_summary(_config_manager: ConfigurationManager) -> None:
    """Display configuration summary"""
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # This would need to access config_manager's internal configuration
    # For now, show basic environment variables
    env_vars = ["HA_BASE_URL", "AWS_REGION", "ALEXA_SECRET"]
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if var == "ALEXA_SECRET" and value != "Not set":
            value = "***hidden***"
        table.add_row(var, value)

    console.print(table)


def _display_service_status(services: list[dict[str, Any]], verbose: bool) -> None:
    """Display service status"""
    table = Table(title="Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Modified", style="blue")

    if verbose:
        table.add_column("Runtime", style="magenta")
        table.add_column("Memory", style="yellow")

    # This is a placeholder - in reality you'd query AWS Lambda
    # for actual service information
    for service in services:
        if verbose:
            table.add_row(
                service.get("name", "Unknown"),
                service.get("status", "Unknown"),
                service.get("last_modified", "Unknown"),
                service.get("runtime", "Unknown"),
                service.get("memory", "Unknown"),
            )
        else:
            table.add_row(
                service.get("name", "Unknown"),
                service.get("status", "Unknown"),
                service.get("last_modified", "Unknown"),
            )

    console.print(table)


class AlexaSetupConfig(BaseModel):
    """Configuration for Alexa setup command."""

    function_name: str
    skill_id: Optional[str] = None  # noqa: UP045
    region: str
    generate_test_data: bool
    generate_guide: bool
    lambda_function_url: Optional[str] = None  # noqa: UP045
    oauth_gateway_url: Optional[str] = None  # noqa: UP045
    ha_base_url: Optional[str] = None  # noqa: UP045
    verbose: bool


def _validate_alexa_region(alexa_manager: AlexaSkillManager, region: str) -> None:
    """Validate AWS region compatibility for Alexa."""
    console.print("📍 [blue]Step 1: Validating AWS region compatibility[/blue]")
    is_valid, region_message = alexa_manager.validate_alexa_region_compatibility(region)

    if not is_valid:
        console.print(f"[red]❌ {region_message}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✅ {region_message}[/green]")


def _setup_alexa_trigger(
    alexa_manager: AlexaSkillManager, config: AlexaSetupConfig
) -> None:
    """Setup Alexa Smart Home trigger for Lambda function."""
    console.print(
        f"\n🔗 [blue]Step 2: Setting up Alexa Smart Home trigger for "
        f"{config.function_name}[/blue]"
    )

    try:
        trigger_result = alexa_manager.setup_alexa_smart_home_trigger(
            function_name=config.function_name, skill_id=config.skill_id
        )

        if trigger_result["status"] == "created":
            console.print(
                "[green]✅ Alexa Smart Home trigger successfully configured[/green]"
            )
            if config.verbose:
                console.print(
                    f"   Function ARN: {trigger_result.get('function_arn', 'N/A')}"
                )
                console.print(
                    f"   Statement ID: {trigger_result.get('statement_id', 'N/A')}"
                )
        elif trigger_result["status"] == "exists":
            console.print("[yellow]⚠️  Alexa Smart Home trigger already exists[/yellow]")

    except (ValidationError, ClientError) as e:
        console.print(f"[red]❌ Failed to setup Alexa trigger: {str(e)}[/red]")
        if not config.verbose:
            console.print("   Use --verbose for more details")
        else:
            console.print(f"   Error details: {traceback.format_exc()}")


def _generate_test_data(
    alexa_manager: AlexaSkillManager, config: AlexaSetupConfig
) -> None:
    """Generate Alexa test data if requested."""
    if not config.generate_test_data:
        return

    console.print("\n🧪 [blue]Step 3: Generating Alexa test data[/blue]")
    test_file = "alexa-discovery-test.json"

    try:
        test_result = alexa_manager.generate_alexa_test_data(test_file)
        console.print(
            f"[green]✅ Test data generated: " f"{test_result['output_file']}[/green]"
        )
        if config.verbose:
            console.print(
                f"   Purpose: {test_result['test_data']['metadata']['purpose']}"
            )
            console.print(f"   Usage: {test_result['test_data']['metadata']['usage']}")
    except (ValidationError, OSError, KeyError) as e:
        console.print(f"[red]❌ Failed to generate test data: {str(e)}[/red]")


def _generate_configuration_guide(
    alexa_manager: AlexaSkillManager, config: AlexaSetupConfig
) -> None:
    """Generate configuration guide if requested."""
    if not config.generate_guide:
        return

    console.print("\n📋 [blue]Step 4: Generating configuration guide[/blue]")

    # Use provided URLs or generate placeholder ones
    guide_lambda_url = (
        config.lambda_function_url
        or f"https://example-{config.function_name}.lambda-url.{config.region}.on.aws/"
    )

    try:
        guide_content = alexa_manager.generate_configuration_guide(
            lambda_function_url=guide_lambda_url,
            oauth_gateway_url=config.oauth_gateway_url,
            ha_base_url=config.ha_base_url,
            skill_id=config.skill_id,
        )

        guide_file = "alexa-skill-configuration-guide.md"
        with open(guide_file, "w", encoding="utf-8") as f:
            f.write(guide_content)

        console.print(f"[green]✅ Configuration guide generated: {guide_file}[/green]")

        # Display key next steps
        console.print("\n📋 [bold]Key Next Steps:[/bold]")
        console.print("   1. Go to Amazon Developer Console (developer.amazon.com)")
        console.print(f"   2. Set Default Endpoint to: {guide_lambda_url}")
        console.print("   3. Configure Account Linking with the provided OAuth URLs")
        console.print("   4. Test device discovery with 'Alexa, discover devices'")

    except (ValidationError, OSError) as e:
        console.print(f"[red]❌ Failed to generate configuration guide: {str(e)}[/red]")


def _validate_home_assistant_config(
    alexa_manager: AlexaSkillManager, config: AlexaSetupConfig
) -> None:
    """Validate Home Assistant configuration if URL provided."""
    if not config.ha_base_url:
        return

    console.print("\n🏠 [blue]Step 5: Validating Home Assistant configuration[/blue]")

    try:
        ha_validation = alexa_manager.validate_home_assistant_config(config.ha_base_url)

        if ha_validation["status"] == "error":
            console.print("[red]❌ Home Assistant validation failed[/red]")
            for rec in ha_validation["recommendations"]:
                console.print(f"   • {rec}")
        else:
            console.print("[green]✅ Home Assistant URL format valid[/green]")
            console.print("[yellow]ℹ️  Additional recommendations:[/yellow]")
            for rec in ha_validation["recommendations"]:
                console.print(f"   • {rec}")

    except (ValidationError, ValueError) as e:
        console.print(
            f"[red]❌ Failed to validate Home Assistant config: {str(e)}[/red]"
        )


def _display_alexa_setup_summary(config: AlexaSetupConfig) -> None:
    """Display final summary of Alexa setup."""
    console.print("\n🎉 [bold green]Alexa automation setup complete![/bold green]")
    console.print("\n📚 [bold]Generated Files:[/bold]")
    if config.generate_test_data:
        console.print("   • alexa-discovery-test.json - Test data for Lambda function")
    if config.generate_guide:
        console.print("   • alexa-skill-configuration-guide.md - Complete setup guide")

    console.print("\n🔗 [bold]Manual Steps Remaining:[/bold]")
    console.print(
        "   • Create/configure Alexa Smart Home Skill at developer.amazon.com"
    )
    console.print("   • Enable account linking with generated OAuth configuration")
    console.print("   • Test integration with Alexa app and voice commands")


def alexa_setup(  # pylint: disable=too-many-positional-arguments,too-many-arguments
    function_name: str = typer.Argument(
        "ha-alexa-proxy", help="Lambda function name for Alexa integration"
    ),
    skill_id: Optional[str] = typer.Option(  # noqa: UP045
        None, "--skill-id", help="Alexa Skill ID (if known)"
    ),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
    generate_test_data: bool = typer.Option(
        True, "--generate-test-data/--no-test-data", help="Generate test JSON files"
    ),
    generate_guide: bool = typer.Option(
        True, "--generate-guide/--no-guide", help="Generate configuration guide"
    ),
    lambda_function_url: Optional[str] = typer.Option(  # noqa: UP045
        None, "--lambda-url", help="Lambda function URL (if known)"
    ),
    oauth_gateway_url: Optional[str] = typer.Option(  # noqa: UP045
        None, "--oauth-url", help="OAuth Gateway Lambda URL (if using CloudFlare)"
    ),
    ha_base_url: Optional[str] = typer.Option(  # noqa: UP045
        None, "--ha-url", help="Home Assistant base URL"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """
    Setup missing Alexa Smart Home Skill automation components.

    This command automates the missing pieces that prevent Alexa Smart Home Skills
    from working after AWS Lambda deployment, including:

    • Alexa Smart Home trigger setup for Lambda functions
    • Configuration guide generation for Amazon Developer Console
    • Test data generation for Alexa integration testing
    • Region compatibility validation
    • Home Assistant configuration validation

    Examples:
        ha-connector alexa-setup
        ha-connector alexa-setup --skill-id amzn1.ask.skill.xxxxx
        ha-connector alexa-setup my-lambda --region us-west-2
        ha-connector alexa-setup --lambda-url https://xyz.lambda-url.us-east-1.on.aws/
    """
    console.print("🎯 [bold]Alexa Smart Home Skill Automation Setup[/bold]")
    console.print("Setting up missing automation components for Alexa integration...\n")

    try:
        # Create configuration object
        config = AlexaSetupConfig(
            function_name=function_name,
            skill_id=skill_id,
            region=region,
            generate_test_data=generate_test_data,
            generate_guide=generate_guide,
            lambda_function_url=lambda_function_url,
            oauth_gateway_url=oauth_gateway_url,
            ha_base_url=ha_base_url,
            verbose=verbose,
        )

        # Initialize Alexa Skill Manager
        alexa_manager = AlexaSkillManager(region=region)

        # Execute setup steps
        _validate_alexa_region(alexa_manager, region)
        _setup_alexa_trigger(alexa_manager, config)
        _generate_test_data(alexa_manager, config)
        _generate_configuration_guide(alexa_manager, config)
        _validate_home_assistant_config(alexa_manager, config)

        # Display summary
        _display_alexa_setup_summary(config)

    except ValidationError as e:
        console.print(f"\n[red]💥 Validation error: {str(e)}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"\n[red]💥 Alexa setup failed: {str(e)}[/red]")
        if verbose:
            console.print(f"Details: {traceback.format_exc()}")
        raise typer.Exit(1) from e


# Export commands for testing
install_command = install
deploy_command = deploy
configure_command = configure
status_command = status
remove_command = remove
alexa_setup_command = alexa_setup
