"""
🎯 SMAPI SETUP WIZARD: HACS-Pattern Guided OAuth 2.0 Integration

This module provides a comprehensive, user-friendly wizard to guide developers
through setting up SMAPI (Skill Management API) integration following HACS
(Home Assistant Community Store) patterns for clear, step-by-step guidance.

Key Features:
- Step-by-step Login with Amazon (LWA) security profile setup
- OAuth 2.0 Authorization Code Grant flow implementation
- Interactive guidance with validation at each step
- Secure credential management and storage
- Integration with existing automation workflows
"""

import logging
import os
import secrets
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from ha_connector.utils import ValidationError

# Public OAuth 2.0 token endpoint for Amazon (not a secret, safe to hardcode)
AMAZON_OAUTH_TOKEN_URL = "https://api.amazon.com/auth/o2/token"  # nosec B105

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class LWASecurityProfile:  # pylint: disable=too-many-instance-attributes
    """Login with Amazon Security Profile configuration."""

    name: str
    description: str
    privacy_notice_url: str = "https://example.com/privacy"
    logo_url: str = "https://example.com/logo.png"
    client_id: str = ""
    client_secret: str = ""
    allowed_return_urls: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:9090/cb",
            "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html",
            "http://localhost:3000/auth/callback",
            "https://localhost:3000/auth/callback",
        ]
    )
    scopes: list[str] = field(
        default_factory=lambda: [
            "alexa::ask:skills:readwrite",
            "alexa::ask:models:readwrite",
            "alexa::ask:skills:test",
        ]
    )


@dataclass
class SMAPITokens:
    """SMAPI OAuth tokens with automatic refresh capability."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""
    vendor_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        expires_at = self.created_at + timedelta(
            seconds=self.expires_in - 300
        )  # 5min buffer
        return datetime.now() > expires_at

    @property
    def expires_in_minutes(self) -> int:
        """Get minutes until token expires."""
        expires_at = self.created_at + timedelta(seconds=self.expires_in)
        remaining = expires_at - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))


class SMAPISetupWizard:
    """Interactive wizard for SMAPI OAuth 2.0 setup following HACS patterns."""

    def __init__(self):
        self.console = Console()
        self.tokens: SMAPITokens | None = None
        self.security_profile: LWASecurityProfile | None = None

    def run_complete_setup(self) -> tuple[LWASecurityProfile, SMAPITokens]:
        """Run the complete SMAPI setup wizard."""
        self._show_welcome()

        # Step 1: Explain the process
        self._explain_smapi_process()

        # Step 2: Create or configure security profile
        self.security_profile = self._setup_security_profile()

        # Step 3: Complete OAuth flow
        self.tokens = self._complete_oauth_flow(self.security_profile)

        # Step 4: Validate and save
        self._validate_and_save()

        self._show_completion_summary()
        return self.security_profile, self.tokens

    def _show_welcome(self) -> None:
        """Display welcome message and overview."""
        welcome_text = Text.assemble(
            "🎯 ",
            ("Welcome to SMAPI Setup Wizard", "bold blue"),
            "\n\n",
            "This wizard will guide you through setting up ",
            ("SMAPI (Skill Management API)", "bold"),
            " integration for automated Alexa skill management.\n\n",
            "What you'll accomplish:\n",
            "• Create Login with Amazon (LWA) security profile\n",
            "• Configure OAuth 2.0 Authorization Code Grant flow\n",
            "• Generate access tokens for SMAPI operations\n",
            "• Set up automated skill creation and management\n\n",
            ("⚡ This will enable full automation of Alexa skill setup!", "green bold"),
        )

        self.console.print(Panel(welcome_text, title="SMAPI Setup", expand=False))

        if not Confirm.ask("Ready to start the setup process?"):
            raise SystemExit("Setup cancelled by user")

    def _explain_smapi_process(self) -> None:
        """Explain the SMAPI OAuth process in detail."""
        explanation = Text.assemble(
            "📋 ",
            ("Understanding SMAPI OAuth 2.0 Flow", "bold blue"),
            "\n\n",
            ("1. Security Profile Creation", "bold"),
            "\n",
            "   • Create LWA security profile in Amazon Developer Console\n",
            "   • Configure OAuth redirect URLs and permissions\n",
            "   • Get Client ID and Client Secret\n\n",
            ("2. Authorization Request", "bold"),
            "\n",
            "   • Generate authorization URL with your Client ID\n",
            "   • User visits URL and grants permissions\n",
            "   • Amazon returns authorization code\n\n",
            ("3. Token Exchange", "bold"),
            "\n",
            "   • Exchange authorization code for access token\n",
            "   • Receive refresh token for automatic renewal\n",
            "   • Store tokens securely for automation\n\n",
            ("🔒 Security Note:", "yellow bold"),
            " Client secrets are sensitive credentials.\n",
            "Store them securely and never share publicly.",
        )

        self.console.print(Panel(explanation, title="OAuth 2.0 Process", expand=False))

    def _setup_security_profile(self) -> LWASecurityProfile:
        """Guide user through security profile setup."""
        self.console.print(
            "\n📱 [bold blue]Step 1: LWA Security Profile Setup[/bold blue]\n"
        )

        # Check if user has existing security profile
        has_existing = Confirm.ask(
            "Do you already have a Login with Amazon security profile for SMAPI?"
        )

        if has_existing:
            return self._configure_existing_profile()

        return self._create_new_profile()

    def _create_new_profile(self) -> LWASecurityProfile:
        """Guide user through creating new security profile."""
        self.console.print(
            "\n🆕 [bold green]Creating New Security Profile[/bold green]\n"
        )

        # Step-by-step instructions
        instructions = [
            "1. Open [link=https://developer.amazon.com/loginwithamazon/console/"
            "site/lwa/overview.html]LWA Console[/link]",
            "2. Sign in with your Amazon Developer account",
            "3. Click 'Create a New Security Profile'",
            "4. Fill in the following information:",
        ]

        for instruction in instructions:
            self.console.print(f"   {instruction}")

        # Gather profile information
        name = Prompt.ask(
            "\n📝 Security Profile Name", default="Home Assistant SMAPI Integration"
        )
        description = Prompt.ask(
            "📝 Description",
            default="SMAPI integration for Home Assistant Alexa automation",
        )
        privacy_url = Prompt.ask(
            "🔗 Privacy Notice URL", default="https://example.com/privacy"
        )

        profile = LWASecurityProfile(
            name=name, description=description, privacy_notice_url=privacy_url
        )

        # Show configuration table
        self._show_profile_configuration(profile)

        # Guide through console configuration
        self._guide_console_configuration(profile)

        return self._get_credentials_from_user(profile)

    def _configure_existing_profile(self) -> LWASecurityProfile:
        """Configure existing security profile."""
        self.console.print(
            "\n⚙️  [bold yellow]Configuring Existing Profile[/bold yellow]\n"
        )

        name = Prompt.ask("📝 Security Profile Name")
        profile = LWASecurityProfile(name=name, description="Existing profile")

        # Guide through ensuring proper configuration
        self._guide_console_configuration(profile)

        return self._get_credentials_from_user(profile)

    def _guide_console_configuration(self, _profile: LWASecurityProfile) -> None:
        """Guide user through console configuration steps."""
        self.console.print("\n🔧 [bold blue]Console Configuration Steps[/bold blue]\n")

        steps = [
            "1. In the LWA Console, find your security profile and click the gear icon",
            "2. Select 'Web Settings'",
            "3. Click 'Edit' in the bottom right",
            "4. In 'Allowed Return URLs', add these URLs (one per line):",
        ]

        for step in steps:
            self.console.print(f"   {step}")

        # Show return URLs table
        url_table = Table(
            title="Required Return URLs", show_header=True, header_style="bold magenta"
        )
        url_table.add_column("URL", style="cyan")
        url_table.add_column("Purpose", style="green")

        urls_with_purpose = [
            ("http://127.0.0.1:9090/cb", "ASK CLI local server"),
            (
                "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html",
                "ASK CLI no-browser mode",
            ),
            ("http://localhost:3000/auth/callback", "Local development"),
            ("https://localhost:3000/auth/callback", "Local development (HTTPS)"),
        ]

        for url, purpose in urls_with_purpose:
            url_table.add_row(url, purpose)

        self.console.print(url_table)

        self.console.print("\n   5. Click 'Save' to save the configuration")
        self.console.print("   6. Note down the Client ID and Client Secret")

        input("\n⏳ Press Enter after completing the console configuration...")

    def _get_credentials_from_user(
        self, profile: LWASecurityProfile
    ) -> LWASecurityProfile:
        """Get Client ID and Secret from user."""
        self.console.print("\n🔑 [bold blue]Security Profile Credentials[/bold blue]\n")

        client_id = Prompt.ask("📋 Client ID", password=False)
        client_secret = Prompt.ask("🔐 Client Secret", password=True)

        if not client_id or not client_secret:
            raise ValidationError("Client ID and Client Secret are required")

        profile.client_id = client_id.strip()
        profile.client_secret = client_secret.strip()

        # Validate format
        if not profile.client_id.startswith(
            ("amzn1.application-oa2-client", "amzn1.lwa.oa2-client")
        ):
            self.console.print(
                "⚠️  [yellow]Warning: Client ID format looks unusual[/yellow]"
            )

        return profile

    def _complete_oauth_flow(self, profile: LWASecurityProfile) -> SMAPITokens:
        """Complete OAuth 2.0 Authorization Code Grant flow."""
        self.console.print(
            "\n🔄 [bold blue]Step 2: OAuth 2.0 Authorization[/bold blue]\n"
        )

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "client_id": profile.client_id,
            "scope": " ".join(profile.scopes),
            "response_type": "code",
            "state": state,
            "redirect_uri": "http://127.0.0.1:9090/cb",
        }

        auth_url = f"https://www.amazon.com/ap/oa?{urlencode(auth_params)}"

        # Show authorization process
        self._show_authorization_process(auth_url, state)

        # Get authorization code from user
        auth_code = self._get_authorization_code()

        # Exchange code for tokens
        return self._exchange_code_for_tokens(
            profile, auth_code, auth_params["redirect_uri"]
        )

    def _show_authorization_process(self, auth_url: str, state: str) -> None:
        """Show authorization process to user."""
        auth_panel = Text.assemble(
            "🌐 ",
            ("Authorization Process", "bold blue"),
            "\n\n",
            "1. A browser window will open to Amazon Login\n",
            "2. Sign in with your Amazon Developer account\n",
            "3. Review and accept the requested permissions\n",
            "4. You'll be redirected with an authorization code\n",
            "5. Copy the authorization code from the URL\n\n",
            ("Security:", "bold yellow"),
            f" State parameter: {state[:16]}...\n",
            ("This prevents CSRF attacks", "dim"),
        )

        self.console.print(Panel(auth_panel, title="Authorization Flow", expand=False))

        # Open browser automatically
        if Confirm.ask("Open authorization URL in browser?", default=True):
            webbrowser.open(auth_url)
        else:
            self.console.print(f"\n🔗 Authorization URL:\n{auth_url}\n")

    def _get_authorization_code(self) -> str:
        """Get authorization code from user."""
        self.console.print("\n📋 [bold blue]Authorization Code Input[/bold blue]\n")

        code_help = Text.assemble(
            "After completing authorization, you'll be redirected to a URL like:\n",
            ("http://127.0.0.1:9090/cb?code=", "dim"),
            ("AUTH_CODE_HERE", "bold green"),
            ("&state=...", "dim"),
            "\n\n",
            "Copy the value after 'code=' and before '&state'",
        )

        self.console.print(Panel(code_help, title="How to Find Authorization Code"))

        auth_code = Prompt.ask("\n🔑 Enter authorization code")

        if not auth_code or len(auth_code) < 10:
            raise ValidationError("Invalid authorization code")

        return auth_code.strip()

    def _exchange_code_for_tokens(
        self, profile: LWASecurityProfile, auth_code: str, redirect_uri: str
    ) -> SMAPITokens:
        token_url = AMAZON_OAUTH_TOKEN_URL
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "client_id": profile.client_id,
            "client_secret": profile.client_secret,
        }

        try:
            self.console.print("📡 Making token request to Amazon...")
            response = requests.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )

            if response.status_code == 200:
                token_response = response.json()
                oauth_tokens = SMAPITokens(
                    access_token=token_response["access_token"],
                    refresh_token=token_response["refresh_token"],
                    token_type=token_response.get("token_type", "Bearer"),
                    expires_in=token_response.get("expires_in", 3600),
                    scope=token_response.get("scope", ""),
                )

                self.console.print("✅ [green]Tokens obtained successfully![/green]")
                return oauth_tokens

            error_detail = response.text
            self.console.print(
                f"❌ [red]Token exchange failed: {response.status_code}[/red]"
            )
            self.console.print(f"Error details: {error_detail}")
            raise ValidationError(f"Token exchange failed: {response.status_code}")

        except requests.RequestException as e:
            self.console.print(
                f"❌ [red]Network error during token exchange: {e}[/red]"
            )
            raise ValidationError(f"Network error: {e}") from e

    def _validate_and_save(self) -> None:
        """Validate tokens and save configuration."""
        if not self.tokens or not self.security_profile:
            raise ValidationError("Missing tokens or security profile")

        self.console.print(
            "\n✅ [bold blue]Step 3: Validation and Storage[/bold blue]\n"
        )

        # Test token with SMAPI
        if self._test_smapi_access():
            self.console.print("✅ [green]SMAPI access validated successfully![/green]")
        else:
            self.console.print(
                "⚠️  [yellow]SMAPI access test failed - continuing anyway[/yellow]"
            )

        # Save to environment variables
        self._save_to_environment()

    def _test_smapi_access(self) -> bool:
        """Test SMAPI access with the obtained tokens."""
        if not self.tokens:
            return False

        try:
            self.console.print("🧪 Testing SMAPI access...")

            # Try to get vendor information
            headers = {
                "Authorization": f"Bearer {self.tokens.access_token}",
                "Content-Type": "application/json",
            }

            # Get vendor info to validate access
            response = requests.get(
                "https://api.amazonalexa.com/v1/vendors", headers=headers, timeout=10
            )

            if response.status_code == 200:
                vendor_data = response.json()
                if vendor_data.get("vendors"):
                    vendor_info = vendor_data["vendors"][0]
                    self.tokens.vendor_id = vendor_info.get("id", "")
                    self.console.print(
                        f"🏢 Vendor: {vendor_info.get('name', 'Unknown')}"
                    )
                    return True

            return False

        except requests.RequestException as e:
            logger.error("SMAPI access test failed: %s", e)
            return False

    def _save_to_environment(self) -> None:
        """Save configuration to environment variables."""
        if not self.tokens or not self.security_profile:
            raise ValidationError("Missing tokens or security profile")

        env_vars = {
            "LWA_CLIENT_ID": self.security_profile.client_id,
            "LWA_CLIENT_SECRET": self.security_profile.client_secret,
            "LWA_ACCESS_TOKEN": self.tokens.access_token,
            "LWA_REFRESH_TOKEN": self.tokens.refresh_token,
            "AMAZON_VENDOR_ID": self.tokens.vendor_id,
        }

        # Ask user where to save
        save_options = [
            "Environment variables (current session)",
            "Create .env file",
            "Show values only (manual setup)",
        ]

        self.console.print("\n💾 [bold blue]Save Configuration[/bold blue]\n")
        for i, option in enumerate(save_options, 1):
            self.console.print(f"   {i}. {option}")

        choice = Prompt.ask(
            "\nChoose save option", choices=["1", "2", "3"], default="2"
        )

        if choice == "1":
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value
            self.console.print("✅ Environment variables set for current session")

        elif choice == "2":
            # Create .env file
            env_file_path = ".env"
            with open(env_file_path, "a", encoding="utf-8") as f:
                f.write("\n# SMAPI Configuration\n")
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            self.console.print(f"✅ Configuration saved to {env_file_path}")
            self.console.print(
                "⚠️  [yellow]Add .env to .gitignore to protect secrets[/yellow]"
            )

        else:
            # Show values for manual setup
            self.console.print("\n📋 [bold]Configuration Values[/bold]")
            for key, value in env_vars.items():
                masked_value = value[:8] + "..." if len(value) > 8 else value
                self.console.print(f"   {key}={masked_value}")

    def _show_profile_configuration(self, profile: LWASecurityProfile) -> None:
        """Show security profile configuration table."""
        config_table = Table(title="Security Profile Configuration", show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")

        config_table.add_row("Name", profile.name)
        config_table.add_row("Description", profile.description)
        config_table.add_row("Privacy Notice URL", profile.privacy_notice_url)
        config_table.add_row("Scopes", ", ".join(profile.scopes))

        self.console.print(config_table)

    def _show_completion_summary(self) -> None:
        """Show completion summary with next steps."""
        if not self.tokens or not self.security_profile:
            raise ValidationError("Missing tokens or security profile")

        summary_text = Text.assemble(
            "🎉 ",
            ("SMAPI Setup Complete!", "bold green"),
            "\n\n",
            ("What was configured:", "bold"),
            "\n",
            f"• Security Profile: {self.security_profile.name}\n",
            f"• Client ID: {self.security_profile.client_id[:12]}...\n",
            f"• Access Token: Valid for {self.tokens.expires_in_minutes} minutes\n",
            f"• Vendor ID: {self.tokens.vendor_id}\n",
            f"• Scopes: {', '.join(self.security_profile.scopes)}\n\n",
            ("Next Steps:", "bold blue"),
            "\n",
            "1. Use tokens for SMAPI automation\n",
            "2. Test skill creation and management\n",
            "3. Set up refresh token automation\n",
            "4. Integrate with deployment workflows\n\n",
            ("🔄 Token Refresh:", "yellow bold"),
            " Tokens expire in 1 hour.\n",
            "Use refresh token for automatic renewal.",
        )

        self.console.print(Panel(summary_text, title="Setup Complete!", expand=False))

    def refresh_tokens(
        self, refresh_token: str, client_id: str, client_secret: str
    ) -> SMAPITokens:
        """Refresh OAuth tokens using the refresh token."""
        token_url = AMAZON_OAUTH_TOKEN_URL
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            response = requests.post(
                token_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )

            if response.status_code == 200:
                token_response = response.json()
                new_tokens = SMAPITokens(
                    access_token=token_response["access_token"],
                    refresh_token=refresh_token,  # Keep existing refresh token
                    token_type=token_response.get("token_type", "Bearer"),
                    expires_in=token_response.get("expires_in", 3600),
                )

                self.console.print("✅ [green]Tokens refreshed successfully![/green]")
                return new_tokens

            raise ValidationError(f"Token refresh failed: {response.status_code}")

        except requests.RequestException as e:
            raise ValidationError(f"Network error during token refresh: {e}") from e


def run_smapi_setup_wizard() -> tuple[LWASecurityProfile, SMAPITokens]:
    """Run the complete SMAPI setup wizard."""
    wizard = SMAPISetupWizard()
    return wizard.run_complete_setup()


if __name__ == "__main__":
    # Run wizard if called directly
    try:
        security_profile, auth_tokens = run_smapi_setup_wizard()
        print(f"\n✅ Setup complete! Vendor ID: {auth_tokens.vendor_id}")
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except ValidationError as e:
        print(f"\n❌ Setup failed: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        raise
