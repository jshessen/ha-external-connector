"""
🎯 AMAZON DEVELOPER CONSOLE CLI COMMANDS

CLI interface for Amazon Developer Console automation, providing both
SMAPI API integration and guided browser automation for complete
Alexa Smart Home skill setup.
"""

import json
import logging
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from custom_components.ha_external_connector.integrations.alexa.amazon_developer_console import (
    AmazonDeveloperConsoleIntegration,
    AutomationConfig,
    BrowserAutomationDriver,
    OAuthConfiguration,
    SkillConfiguration,
    SkillMetadata,
)
from custom_components.ha_external_connector.integrations.alexa.smapi_client import SMAPICredentials

if TYPE_CHECKING:
    pass

console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="developer-console", help="Amazon Developer Console automation commands"
)


@app.command()
def setup_smapi_credentials(  # pylint: disable=too-many-branches  # CLI functions need many branches for user interaction
    interactive: bool = typer.Option(
        True, "--interactive/--non-interactive", help="Interactive credential setup"
    ),
    client_id: str = typer.Option("", help="Login with Amazon Client ID"),
    client_secret: str = typer.Option("", help="Login with Amazon Client Secret"),
    save_to_env: bool = typer.Option(True, help="Save credentials to environment file"),
) -> None:
    """Setup SMAPI (Skill Management API) credentials for automation."""

    console.print(
        Panel(
            "[bold blue]🔐 SMAPI Credentials Setup[/bold blue]\n\n"
            "To use SMAPI automation, you need Login with Amazon (LWA) credentials.\n\n"
            "[bold]Steps to get credentials:[/bold]\n"
            "1. Go to Amazon Developer Console → Login with Amazon\n"
            "2. Create a new Security Profile\n"
            "3. Note the Client ID and Client Secret\n"
            "4. Add redirect URI: http://localhost:3000/auth/callback",
            title="🏢 Amazon Developer Console",
            border_style="blue",
        )
    )

    if interactive:
        if not client_id:
            client_id = Prompt.ask("Login with Amazon Client ID")
        if not client_secret:
            client_secret = Prompt.ask("Login with Amazon Client Secret", password=True)

        if save_to_env:
            save_credentials = Confirm.ask(
                "Save credentials to .env file?", default=True
            )
        else:
            save_credentials = False
    else:
        save_credentials = save_to_env

    # Validate credentials
    if not client_id or not client_secret:
        rprint("[red]❌ Client ID and Client Secret are required[/red]")
        raise typer.Exit(1)

    # Test credentials by creating SMAPI client
    credentials = SMAPICredentials(client_id=client_id, client_secret=client_secret)

    console_integration = AmazonDeveloperConsoleIntegration(credentials)

    # Generate authentication URL
    auth_url = console_integration.authenticate_smapi()

    if save_credentials:
        env_file = Path(".env")
        env_content = ""

        if env_file.exists():
            env_content = env_file.read_text(encoding="utf-8")

        # Update or add credentials
        lines = env_content.split("\n")
        updated_lines: list[str] = []
        found_client_id = False
        found_client_secret = False

        for line in lines:
            if line.startswith("LWA_CLIENT_ID="):
                updated_lines.append(f"LWA_CLIENT_ID={client_id}")
                found_client_id = True
            elif line.startswith("LWA_CLIENT_SECRET="):
                updated_lines.append(f"LWA_CLIENT_SECRET={client_secret}")
                found_client_secret = True
            else:
                updated_lines.append(line)

        if not found_client_id:
            updated_lines.append(f"LWA_CLIENT_ID={client_id}")
        if not found_client_secret:
            updated_lines.append(f"LWA_CLIENT_SECRET={client_secret}")

        env_file.write_text("\n".join(updated_lines), encoding="utf-8")
        rprint(f"[green]✅ Credentials saved to {env_file}[/green]")

    rprint("\n[bold green]🎉 SMAPI credentials configured successfully![/bold green]")
    rprint("\n[bold]Next step:[/bold] Complete authentication by visiting:")
    rprint(f"[link]{auth_url}[/link]")

    if Confirm.ask("\nOpen authentication URL in browser?", default=True):
        webbrowser.open(auth_url)


@app.command()
def complete_authentication(  # pylint: disable=too-many-branches  # CLI functions need many branches for user interaction
    auth_code: str = typer.Option("", help="Authorization code from callback"),
    redirect_uri: str = typer.Option(
        "http://localhost:3000/auth/callback", help="Redirect URI used in auth"
    ),
) -> None:
    """Complete SMAPI authentication with authorization code."""

    if not auth_code:
        auth_code = Prompt.ask("Authorization code from callback URL")

    # Load credentials
    credentials = SMAPICredentials.from_environment()
    if not credentials.client_id or not credentials.client_secret:
        rprint(
            "[red]❌ SMAPI credentials not found. "
            "Run setup-smapi-credentials first.[/red]"
        )
        raise typer.Exit(1)

    console_integration = AmazonDeveloperConsoleIntegration(credentials)

    with Progress() as progress:
        task = progress.add_task("Completing authentication...", total=100)

        progress.update(task, advance=30)
        success = console_integration.complete_smapi_authentication(
            auth_code, redirect_uri
        )

        progress.update(task, advance=70)
        if success:
            if console_integration.smapi_client is not None:
                vendor_id = console_integration.smapi_client.get_vendor_id()
                if vendor_id:
                    rprint("[green]✅ Authentication successful![/green]")
                    rprint(f"[bold]Vendor ID:[/bold] {vendor_id}")
                    # Store vendor ID in credentials
                    console_integration.credentials.vendor_id = vendor_id
                else:
                    rprint(
                        "[yellow]⚠️ Authentication successful but could not get "
                        "vendor ID[/yellow]"
                    )
            # Save tokens to environment
            env_file = Path(".env")
            if env_file.exists():
                env_content = env_file.read_text(encoding="utf-8")
                lines = env_content.split("\n")
                updated_lines: list[str] = []

                for line in lines:
                    if line.startswith("LWA_ACCESS_TOKEN="):
                        updated_lines.append(
                            f"LWA_ACCESS_TOKEN={credentials.access_token}"
                        )
                    elif line.startswith("LWA_REFRESH_TOKEN="):
                        updated_lines.append(
                            f"LWA_REFRESH_TOKEN={credentials.refresh_token}"
                        )
                    elif line.startswith("AMAZON_VENDOR_ID="):
                        updated_lines.append(
                            f"AMAZON_VENDOR_ID={credentials.vendor_id}"
                        )
                    else:
                        updated_lines.append(line)

                # Add tokens if not found
                if f"LWA_ACCESS_TOKEN={credentials.access_token}" not in updated_lines:
                    updated_lines.append(f"LWA_ACCESS_TOKEN={credentials.access_token}")
                if (
                    f"LWA_REFRESH_TOKEN={credentials.refresh_token}"
                    not in updated_lines
                ):
                    updated_lines.append(
                        f"LWA_REFRESH_TOKEN={credentials.refresh_token}"
                    )
                if f"AMAZON_VENDOR_ID={credentials.vendor_id}" not in updated_lines:
                    updated_lines.append(f"AMAZON_VENDOR_ID={credentials.vendor_id}")

                env_file.write_text("\n".join(updated_lines), encoding="utf-8")
                rprint("[green]🔑 Access tokens saved to .env file[/green]")
        else:
            rprint("[red]❌ Authentication failed[/red]")
            raise typer.Exit(1)


def _gather_skill_parameters(  # pylint: disable=too-many-arguments,too-many-positional-arguments  # Parameter gathering function
    skill_name: str,
    lambda_arn: str,
    oauth_auth_uri: str,
    oauth_token_uri: str,
    oauth_client_id: str,
    skill_description: str,
) -> SkillConfiguration:
    """Gather and validate skill parameters, prompting user for missing values."""
    # Interactive prompts for missing information
    if not skill_name:
        skill_name = Prompt.ask("Skill name", default="Home Assistant Smart Home")

    if not lambda_arn:
        lambda_arn = Prompt.ask("Lambda function ARN")

    if not oauth_auth_uri:
        oauth_auth_uri = Prompt.ask("OAuth authorization URI")

    if not oauth_token_uri:
        oauth_token_uri = Prompt.ask("OAuth token URI")

    # Extract domain from OAuth URIs
    try:
        auth_domain = urlparse(oauth_auth_uri).netloc
        token_domain = urlparse(oauth_token_uri).netloc
        domain_list = list(set([auth_domain, token_domain]))
    except ValueError:
        domain_list = []

    # Create skill configuration
    oauth_config = OAuthConfiguration(
        web_auth_uri=oauth_auth_uri,
        access_token_uri=oauth_token_uri,
        client_id=oauth_client_id,
        domain_list=domain_list,
    )

    metadata = SkillMetadata(
        name=skill_name,
        description=skill_description or f"{skill_name} Smart Home integration",
    )

    return SkillConfiguration(
        lambda_function_arn=lambda_arn,
        oauth_config=oauth_config,
        metadata=metadata,
    )


def _handle_successful_creation(
    result: dict[str, str | list[str]],
    output_file: str,
    console_integration: "AmazonDeveloperConsoleIntegration",
    skill_config: "SkillConfiguration",
) -> None:
    """Handle successful skill creation results."""
    rprint("[green]✅ Skill created successfully![/green]")
    rprint(f"[bold]Skill ID:[/bold] {result['skill_id']}")
    rprint(f"[bold]Method:[/bold] {result['method']}")
    completed_steps = result.get("steps_completed", [])
    if isinstance(completed_steps, list):
        rprint(f"[bold]Steps completed:[/bold] {', '.join(completed_steps)}")

    if output_file:
        output_path = Path(output_file)
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        rprint(f"[green]📄 Results saved to {output_path}[/green]")

    # Generate setup instructions
    skill_id = str(result["skill_id"])
    instructions = console_integration.generate_setup_instructions(
        skill_config, skill_id
    )

    instructions_file = Path(f"alexa-skill-{skill_id}-setup.md")
    instructions_file.write_text(instructions, encoding="utf-8")
    rprint(f"[green]📋 Setup instructions saved to {instructions_file}[/green]")


def _handle_partial_creation(
    result: dict[str, str | list[str]],
    console_integration: "AmazonDeveloperConsoleIntegration",
) -> None:
    """Handle partial skill creation results."""
    rprint("[yellow]⚠️ Skill partially created[/yellow]")
    rprint(f"[bold]Skill ID:[/bold] {result['skill_id']}")

    completed_steps = result.get("steps_completed", [])
    if isinstance(completed_steps, list):
        rprint(f"[bold]Steps completed:[/bold] {', '.join(completed_steps)}")

    errors = result.get("errors", [])
    if isinstance(errors, list):
        rprint(f"[bold]Errors:[/bold] {', '.join(errors)}")

    # Open Developer Console for manual completion
    if Confirm.ask("Open Developer Console to complete setup manually?"):
        skill_id = str(result["skill_id"])
        console_integration.open_developer_console_for_manual_steps(skill_id)


def _handle_failed_creation(
    result: dict[str, str | list[str]], use_browser_fallback: bool
) -> None:
    """Handle failed skill creation results."""
    rprint("[red]❌ Skill creation failed[/red]")

    errors = result.get("errors", [])
    if isinstance(errors, list):
        rprint(f"[bold]Errors:[/bold] {', '.join(errors)}")

    if use_browser_fallback and result.get("method") != "browser":
        rprint("\n[yellow]💡 Try again with browser automation:[/yellow]")
        rprint("ha-connector developer-console create-skill --use-browser-fallback")

    raise typer.Exit(1)


@app.command()
def create_skill(  # pylint: disable=too-many-positional-arguments,too-many-arguments,too-many-locals  # CLI functions need many parameters and locals
    skill_name: str = typer.Option("", help="Name for the Alexa skill"),
    lambda_arn: str = typer.Option("", help="Lambda function ARN"),
    oauth_auth_uri: str = typer.Option("", help="OAuth authorization URI"),
    oauth_token_uri: str = typer.Option("", help="OAuth token URI"),
    oauth_client_id: str = typer.Option(
        "https://pitangui.amazon.com", help="OAuth client ID"
    ),
    skill_description: str = typer.Option("", help="Skill description"),
    use_browser_fallback: bool = typer.Option(
        True, help="Use browser automation if SMAPI fails"
    ),
    headless: bool = typer.Option(False, help="Run browser in headless mode"),
    output_file: str = typer.Option("", help="Save skill configuration to file"),
) -> None:
    """Create and configure a complete Alexa Smart Home skill."""

    console.print(
        Panel(
            "[bold blue]🏗️ Alexa Smart Home Skill Creation[/bold blue]\n\n"
            "This will create a complete Alexa Smart Home skill with:\n"
            "• Skill manifest and configuration\n"
            "• Smart Home endpoint setup\n"
            "• OAuth account linking\n"
            "• Skill validation and testing enablement",
            title="🎯 Skill Automation",
            border_style="blue",
        )
    )

    # Gather skill parameters and create configuration
    skill_config = _gather_skill_parameters(
        skill_name,
        lambda_arn,
        oauth_auth_uri,
        oauth_token_uri,
        oauth_client_id,
        skill_description,
    )

    # Load SMAPI credentials and create console integration
    credentials = SMAPICredentials.from_environment()
    automation_config = AutomationConfig(
        use_browser_fallback=use_browser_fallback,
        headless_browser=headless,
    )
    console_integration = AmazonDeveloperConsoleIntegration(
        credentials=credentials,
        automation_config=automation_config,
    )

    with Progress() as progress:
        task = progress.add_task("Creating Alexa skill...", total=100)

        try:
            # Attempt skill creation
            progress.update(task, description="Starting skill creation...")
            result = console_integration.create_skill_complete(skill_config)
            progress.update(task, advance=100)

            # Display results
            console.print("\n" + "=" * 60)
            console.print("[bold]Skill Creation Results[/bold]")
            console.print("=" * 60)

            if result["status"] == "completed":
                _handle_successful_creation(
                    result, output_file, console_integration, skill_config
                )
            elif result["status"] == "partial":
                _handle_partial_creation(result, console_integration)
            else:
                _handle_failed_creation(result, use_browser_fallback)

        except (ValueError, RuntimeError) as e:
            progress.update(task, description="Error occurred...")
            rprint(f"[red]❌ Error creating skill: {e}[/red]")
            logger.exception("Skill creation failed")


@app.command()
def list_skills() -> None:
    """List all skills in your Amazon Developer account."""

    credentials = SMAPICredentials.from_environment()
    if not credentials.access_token:
        rprint(
            "[red]❌ SMAPI authentication required. Run "
            "complete-authentication first.[/red]"
        )
        raise typer.Exit(1)

    console_integration = AmazonDeveloperConsoleIntegration(credentials)

    with Progress() as progress:
        task = progress.add_task("Fetching skills...", total=100)

        if console_integration.smapi_client is None:
            rprint(
                "[red]❌ SMAPI client not initialized. "
                "Please complete authentication first.[/red]"
            )
            raise typer.Exit(1)

        skills = console_integration.smapi_client.list_skills()
        progress.update(task, advance=100)

    if skills:
        console.print(f"\n[bold]Found {len(skills)} skills:[/bold]\n")

        for i, skill in enumerate(skills, 1):
            status = skill.get("status", "unknown")
            status_color = "green" if status == "LIVE" else "yellow"

            skill_name = skill.get("nameByLocale", {}).get("en-US", "Unnamed")
            console.print(f"[bold]{i}.[/bold] {skill_name}")
            console.print(
                f"   [bold]Skill ID:[/bold] {skill.get('skillId', 'Unknown')}"
            )
            console.print(
                f"   [bold]Status:[/bold] [{status_color}]{status}[/{status_color}]"
            )
            console.print(f"   [bold]Stage:[/bold] {skill.get('stage', 'Unknown')}")
            console.print()
    else:
        rprint("[yellow]No skills found in your account.[/yellow]")


@app.command()
def guided_setup(  # pylint: disable=too-many-branches,too-many-statements  # CLI functions need complexity for user interaction
    lambda_arn: str = typer.Option("", help="Lambda function ARN"),
    oauth_auth_uri: str = typer.Option("", help="OAuth authorization URI"),
    oauth_token_uri: str = typer.Option("", help="OAuth token URI"),
) -> None:
    """Launch guided browser automation for manual skill setup."""

    console.print(
        Panel(
            "[bold blue]🌐 Guided Browser Setup[/bold blue]\n\n"
            "This will open the Amazon Developer Console in a browser\n"
            "and guide you through the skill setup process.\n\n"
            "[bold yellow]Note:[/bold yellow] You will need to log in manually.",
            title="🎯 Browser Automation",
            border_style="blue",
        )
    )

    if not Confirm.ask("Continue with guided setup?", default=True):
        raise typer.Exit(0)

    # Get required information
    if not lambda_arn:
        lambda_arn = Prompt.ask("Lambda function ARN")

    if not oauth_auth_uri:
        oauth_auth_uri = Prompt.ask("OAuth authorization URI")

    if not oauth_token_uri:
        oauth_token_uri = Prompt.ask("OAuth token URI")

    skill_name = Prompt.ask("Skill name", default="Home Assistant Smart Home")

    # Create skill configuration
    oauth_config = OAuthConfiguration(
        web_auth_uri=oauth_auth_uri,
        access_token_uri=oauth_token_uri,
    )

    metadata = SkillMetadata(
        name=skill_name,
    )

    skill_config = SkillConfiguration(
        lambda_function_arn=lambda_arn,
        oauth_config=oauth_config,
        metadata=metadata,
    )

    try:
        with BrowserAutomationDriver(headless=False) as browser:
            console.print("[bold]🌐 Opening Amazon Developer Console...[/bold]")

            if browser.navigate_to_developer_console():
                console.print("[green]✅ Developer Console opened[/green]")
                console.print(
                    "[yellow]👤 Please log in to your Amazon Developer account[/yellow]"
                )

                if browser.wait_for_login():
                    console.print("[green]✅ Login successful[/green]")
                    console.print("[bold]🔧 Starting guided skill creation...[/bold]")

                    skill_id = browser.guided_skill_creation(skill_config)

                    if skill_id:
                        console.print(
                            f"[green]✅ Skill created with ID: {skill_id}[/green]"
                        )

                        console.print(
                            "[bold]🔗 Configuring Smart Home endpoint...[/bold]"
                        )
                        if browser.configure_endpoint(skill_config):
                            console.print("[green]✅ Endpoint configured[/green]")
                        else:
                            console.print(
                                "[yellow]⚠️ Manual endpoint "
                                "configuration required[/yellow]"
                            )

                        console.print("[bold]🔐 Configuring account linking...[/bold]")
                        if browser.configure_account_linking_ui(skill_config):
                            console.print(
                                "[green]✅ Account linking configured[/green]"
                            )
                        else:
                            console.print(
                                "[yellow]⚠️ Manual account linking "
                                "configuration required[/yellow]"
                            )

                        # Take final screenshot
                        screenshot_path = f"skill-{skill_id}-final.png"
                        if browser.take_screenshot(screenshot_path):
                            console.print(
                                f"[green]📸 Screenshot saved: {screenshot_path}[/green]"
                            )

                        console.print(
                            "\n[bold green]🎉 Skill setup completed![/bold green]"
                        )
                        console.print(f"[bold]Skill ID:[/bold] {skill_id}")
                        console.print("[bold]Next steps:[/bold]")
                        console.print("1. Test your skill in the Alexa app")
                        console.print("2. Enable the skill for testing")
                        console.print("3. Try voice commands with your devices")

                    else:
                        console.print("[red]❌ Skill creation failed[/red]")
                        raise typer.Exit(1)
                else:
                    console.print("[red]❌ Login timeout or failed[/red]")
                    raise typer.Exit(1)
            else:
                console.print("[red]❌ Failed to open Developer Console[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Browser automation failed: {e}[/red]")
        logger.exception("Guided setup failed")
        raise typer.Exit(1) from e


@app.command()
def integrate_with_deployment(  # pylint: disable=too-many-locals  # CLI functions need many locals for parameter processing
    deployment_result_file: str = typer.Argument(
        help="JSON file with Lambda deployment results"
    ),
    skill_name: str = typer.Option("", help="Custom skill name"),
    use_cloudflare: bool = typer.Option(
        True, help="Use CloudFlare Security Gateway for OAuth"
    ),
) -> None:
    """Integrate with existing Lambda deployment for complete automation."""

    deployment_file = Path(deployment_result_file)
    if not deployment_file.exists():
        rprint(f"[red]❌ Deployment file not found: {deployment_file}[/red]")
        raise typer.Exit(1)

    try:
        deployment_data = json.loads(deployment_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rprint(f"[red]❌ Invalid JSON in deployment file: {e}[/red]")
        raise typer.Exit(1) from e

    # Extract deployment information
    lambda_functions = deployment_data.get("lambda_functions", {})

    smart_home_bridge = lambda_functions.get("smart_home_bridge", {})
    cloudflare_gateway = lambda_functions.get("cloudflare_security_gateway", {})

    if not smart_home_bridge.get("function_arn"):
        rprint(
            "[red]❌ Smart Home Bridge Lambda function not found in deployment[/red]"
        )
        raise typer.Exit(1)

    # Configure OAuth endpoints
    if use_cloudflare and cloudflare_gateway.get("function_url"):
        oauth_auth_uri = (
            deployment_data.get("home_assistant_url", "") + "/auth/authorize"
        )
        oauth_token_uri = cloudflare_gateway["function_url"]
        console.print("[bold]Using CloudFlare Security Gateway for OAuth[/bold]")
    else:
        ha_url = deployment_data.get("home_assistant_url", "")
        if not ha_url:
            ha_url = Prompt.ask("Home Assistant URL")
        oauth_auth_uri = f"{ha_url}/auth/authorize"
        oauth_token_uri = f"{ha_url}/auth/token"
        console.print("[bold]Using direct Home Assistant OAuth[/bold]")

    # Create skill configuration
    if not skill_name:
        skill_name = Prompt.ask("Skill name", default="Home Assistant Smart Home")

    oauth_config = OAuthConfiguration(
        web_auth_uri=oauth_auth_uri,
        access_token_uri=oauth_token_uri,
    )

    metadata = SkillMetadata(
        name=skill_name,
    )

    skill_config = SkillConfiguration(
        lambda_function_arn=smart_home_bridge["function_arn"],
        oauth_config=oauth_config,
        metadata=metadata,
    )

    # Create skill using main create_skill logic
    console.print("[bold]🏗️ Creating Alexa skill with deployment integration...[/bold]")

    # Load SMAPI credentials
    credentials = SMAPICredentials.from_environment()
    console_integration = AmazonDeveloperConsoleIntegration(credentials)

    result = console_integration.create_skill_complete(skill_config)

    if result["status"] == "completed":
        console.print("[green]✅ Alexa skill integration completed![/green]")
        console.print(f"[bold]Skill ID:[/bold] {result['skill_id']}")

        # Add skill ID to deployment data
        deployment_data["alexa_skill"] = {
            "skill_id": result["skill_id"],
            "skill_name": skill_name,
            "oauth_configuration": {
                "auth_uri": oauth_auth_uri,
                "token_uri": oauth_token_uri,
            },
            "creation_method": result["method"],
        }

        # Update deployment file
        updated_file = deployment_file.with_name(
            deployment_file.stem + "_with_alexa" + deployment_file.suffix
        )
        updated_file.write_text(json.dumps(deployment_data, indent=2), encoding="utf-8")

        console.print(
            f"[green]📄 Updated deployment data saved to {updated_file}[/green]"
        )

    else:
        console.print(f"[red]❌ Skill creation failed: {result['errors']}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
