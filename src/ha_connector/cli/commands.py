"""
CLI Commands Module

This module provides all the CLI commands for the Home Assistant External Connector.
Replaces the various bash command functions with modern Python implementations.
"""

import traceback

import os
from typing import List, Optional, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from .main import app
from ..utils import HAConnectorLogger
from ..config import ConfigurationManager, InstallationScenario
from ..deployment import (
    ServiceInstaller,
    ServiceType,
    DeploymentManager,
    DeploymentConfig,
    DeploymentStrategy,
)
from ..adapters import validate_aws_access

# Initialize console and logger
console = Console()
logger = HAConnectorLogger("ha-connector-cli")


@app.command()
def install(
    scenario: str = typer.Argument(
        ...,
        help="Installation scenario: direct_alexa, cloudflare_alexa, cloudflare_ios, or all",
    ),
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region for deployment"
    ),
    environment: str = typer.Option(
        "prod",
        "--environment",
        "-e",
        help="Deployment environment (dev, staging, prod)",
    ),
    version: str = typer.Option("1.0.0", "--version", help="Version to deploy"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force installation even if resources exist"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
    auto_setup_cloudflare: bool = typer.Option(
        False, "--auto-setup-cloudflare", help="Automatically set up CloudFlare Access"
    ),
    cloudflare_domain: Optional[str] = typer.Option(
        None, "--cloudflare-domain", help="Domain for CloudFlare Access setup"
    ),
):
    """
    Install Home Assistant External Connector services.

    This command sets up the complete infrastructure for connecting external
    services to your Home Assistant instance with automated deployment.

    Supported scenarios:
    - direct_alexa: Direct Alexa integration
    - cloudflare_alexa: Alexa integration via CloudFlare Access
    - cloudflare_ios: iOS Companion via CloudFlare Access
    - all: Install all supported integrations
    """
    console.print("🚀 Starting Home Assistant External Connector installation...")
    console.print(f"Scenario: [bold]{scenario}[/bold]")
    console.print(f"Region: [bold]{region}[/bold]")
    console.print(
        f"Environment: [bold]{environment}[/bold]"
    )

    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")

    try:
        # Validate scenario
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

        installation_scenario = scenario_mapping[scenario]

        # Initialize configuration manager
        config_manager = ConfigurationManager(installation_scenario)

        # Load and validate configuration
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
                    "[yellow]⚠ Some configuration missing or invalid, entering interactive setup[/yellow]"
                )
                _interactive_configuration_setup(config_manager)
                # Re-validate after interactive setup
                if not config_manager.validate_scenario_setup(installation_scenario):
                    console.print(
                        "[red]❌ Configuration validation failed after interactive setup[/red]"
                    )
                    raise typer.Exit(1)

        console.print("[green]✓ Configuration validated successfully[/green]")

        # Determine services to install
        services_to_install = _get_services_for_scenario(installation_scenario)
        services_str = ', '.join([s.value for s in services_to_install])
        console.print(
            f"Services to install: [bold]{services_str}[/bold]"
        )

        # Create deployment configuration
        deployment_config = DeploymentConfig(
            environment=environment,
            version=version,
            strategy=DeploymentStrategy.ROLLING,
            services=services_to_install,
            region=region,
            dry_run=dry_run,
            verbose=verbose,
            force=force,
            cloudflare_setup=auto_setup_cloudflare,
            cloudflare_domain=cloudflare_domain,
            service_overrides=None,
            tags=None,
        )

        # Execute deployment
        deployment_manager = DeploymentManager(deployment_config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Executing deployment...", total=None)

            deployment_result = deployment_manager.execute_deployment()

            if deployment_result["success"]:
                console.print(
                    "\n[green]🎉 Installation completed successfully![/green]"
                )

                # Display results
                _display_installation_results(deployment_result)

            else:
                console.print("\n[red]💥 Installation failed![/red]")
                for error in deployment_result["errors"]:
                    console.print(f"[red]  • {error}[/red]")
                raise typer.Exit(1)

    except KeyboardInterrupt as exc:
        console.print("\n[yellow]⚠ Installation interrupted by user[/yellow]")
        raise typer.Exit(130) from exc
    except Exception as e:
        console.print(f"\n[red]💥 Installation failed: {str(e)}[/red]")
        if verbose:
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def deploy(
    services: List[str] = typer.Argument(
        ..., help="Services to deploy (alexa, ios_companion, cloudflare_proxy)"
    ),
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region for deployment"
    ),
    environment: str = typer.Option(
        "prod", "--environment", "-e", help="Deployment environment"
    ),
    version: str = typer.Option("1.0.0", "--version", help="Version to deploy"),
    strategy: str = typer.Option(
        "rolling",
        "--strategy",
        "-s",
        help="Deployment strategy (rolling, blue-green, canary, immediate)",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
):
    """
    Deploy specific services to AWS Lambda.

    This command deploys individual services without full installation setup.
    Useful for updates and targeted deployments.
    """
    console.print(f"🚀 Deploying services: [bold]{', '.join(services)}[/bold]")

    try:
        # Validate services
        service_mapping = {
            "alexa": ServiceType.ALEXA,
            "ios_companion": ServiceType.IOS_COMPANION,
            "cloudflare_proxy": ServiceType.CLOUDFLARE_PROXY,
        }

        service_types = []
        for service in services:
            if service not in service_mapping:
                console.print(f"[red]❌ Invalid service: {service}[/red]")
                console.print(
                    f"Supported services: {', '.join(service_mapping.keys())}"
                )
                raise typer.Exit(1)
            service_types.append(service_mapping[service])

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

        # Create deployment configuration
        deployment_config = DeploymentConfig(
            environment=environment,
            version=version,
            strategy=deployment_strategy,
            services=service_types,
            region=region,
            dry_run=dry_run,
            verbose=verbose,
            cloudflare_domain=None,
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

    except Exception as e:
        console.print(f"\n[red]💥 Deployment failed: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def configure(
    scenario: Optional[str] = typer.Option(
        None, "--scenario", "-s", help="Installation scenario to configure"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive configuration mode"
    ),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate current configuration"
    ),
):
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

        config_manager = ConfigurationManager(installation_scenario)

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

    except Exception as e:
        console.print(f"\n[red]💥 Configuration failed: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def status(
    region: str = typer.Option(
        "us-east-1", "--region", "-r", help="AWS region to check"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", help="Show detailed status information"
    ),
):
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

    except Exception as e:
        console.print(f"\n[red]💥 Status check failed: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def remove(
    services: List[str] = typer.Argument(
        ..., help="Services to remove (alexa, ios_companion, cloudflare_proxy, all)"
    ),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force removal without confirmation"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be removed without making changes"
    ),
):
    """
    Remove deployed services.

    This command removes Home Assistant External Connector services
    from AWS Lambda and associated resources.
    """
    console.print(f"🗑️ Removing services: [bold]{', '.join(services)}[/bold]")

    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")

    try:
        service_mapping = {
            "alexa": "ha-alexa-proxy",
            "ios_companion": "ha-ios-companion",
            "cloudflare_proxy": "ha-cloudflare-proxy",
            "all": ["ha-alexa-proxy", "ha-ios-companion", "ha-cloudflare-proxy"],
        }

        functions_to_remove = []
        for service in services:
            if service not in service_mapping:
                console.print(f"[red]❌ Invalid service: {service}[/red]")
                raise typer.Exit(1)

            if service == "all":
                functions_to_remove.extend(service_mapping[service])
            else:
                functions_to_remove.append(service_mapping[service])

        # Remove duplicates
        functions_to_remove = list(set(functions_to_remove))

        if not force and not dry_run:
            if not Confirm.ask(
                f"Are you sure you want to remove {len(functions_to_remove)} service(s)?"
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

    except Exception as e:
        console.print(f"\n[red]💥 Removal failed: {str(e)}[/red]")
        raise typer.Exit(1)


# Helper functions


def _get_services_for_scenario(scenario: InstallationScenario) -> List[ServiceType]:
    """Get list of services for installation scenario"""
    if scenario == InstallationScenario.DIRECT_ALEXA:
        return [ServiceType.ALEXA]
    elif scenario == InstallationScenario.CLOUDFLARE_ALEXA:
        return [ServiceType.ALEXA, ServiceType.CLOUDFLARE_PROXY]
    elif scenario == InstallationScenario.CLOUDFLARE_IOS:
        return [ServiceType.IOS_COMPANION, ServiceType.CLOUDFLARE_PROXY]
    elif scenario == InstallationScenario.ALL:
        return [
            ServiceType.ALEXA,
            ServiceType.IOS_COMPANION,
            ServiceType.CLOUDFLARE_PROXY,
        ]
    else:
        return [ServiceType.ALEXA]


def _interactive_configuration_setup(config_manager: ConfigurationManager):
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


def _display_installation_results(result: Dict[str, Any]):
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


def _display_deployment_results(result: Dict[str, Any]):
    """Display deployment results"""
    _display_installation_results(result)

    console.print(
        f"\nDeployment completed in [bold]{result['deployment_time']:.2f}s[/bold]"
    )
    console.print(f"Strategy: [bold]{result['strategy']}[/bold]")
    console.print(f"Environment: [bold]{result['environment']}[/bold]")


def _display_configuration_summary(_config_manager: ConfigurationManager):
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


def _display_service_status(services: List[Dict[str, Any]], verbose: bool):
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
        table.add_row(
            service.get("name", "Unknown"),
            service.get("status", "Unknown"),
            service.get("last_modified", "Unknown"),
            *(
                (
                    [
                        service.get("runtime", "Unknown"),
                        service.get("memory", "Unknown"),
                    ]
                    if verbose
                    else []
                )
            ),
        )

    console.print(table)


# Export commands for testing
install_command = install
deploy_command = deploy
configure_command = configure
status_command = status
remove_command = remove
