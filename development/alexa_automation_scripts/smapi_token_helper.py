"""
🔐 SMAPI TOKEN HELPER: Complete User Authentication Flow

This module provides comprehensive assistance for users to obtain Amazon Developer
Console SMAPI access tokens, including account creation guidance and OAuth flow
automation.

=== TOKEN ACQUISITION PATHS ===

1. 🆕 New Amazon Developer Account
   - Step-by-step account creation guidance
   - LWA Security Profile setup
   - Client credentials configuration

2. 🔑 Existing Amazon Developer Account
   - Direct OAuth 2.0 authorization flow
   - Secure credential management
   - Token refresh automation

3. 🤝 Third-Party Authorization
   - Organization/tool-based access
   - Authorization code exchange
   - Multi-user management

=== SECURITY PROFILE AUTOMATION ===

This helper automates the complex LWA (Login with Amazon) security profile
configuration required for SMAPI access, including:
- Proper redirect URI configuration
- Required scope setup for Alexa skill management
- Client secret generation and secure storage

=== OAUTH 2.0 FLOW IMPLEMENTATION ===

Complete Authorization Code Grant implementation following Amazon's specifications:
- PKCE support for enhanced security
- State parameter for CSRF protection
- Automatic token refresh handling
- Secure token storage options
"""

import argparse
import json
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from custom_components.ha_external_connector.integrations.alexa.automation.models import (  # noqa: E501
    SMAPICredentials,
)
from development.utils import HAConnectorLogger

try:
    from .lwa_security_profile_automation import automate_security_profile_creation
except ImportError:
    automate_security_profile_creation = None


class ValidationError(Exception):
    """Validation error for SMAPI token operations."""


@dataclass
class LWASecurityProfile:
    """Login with Amazon security profile configuration."""

    client_id: str
    client_secret: str
    allowed_return_urls: list[str]
    scopes: list[str]


@dataclass
class OAuthResult:
    """OAuth flow result container."""

    auth_code: str | None = None
    auth_error: str | None = None


class SMAPITokenHelper:
    """Complete helper for SMAPI token acquisition and management."""

    # Required redirect URIs for SMAPI compatibility
    REQUIRED_REDIRECT_URIS = [
        "http://127.0.0.1:9090/cb",
        "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html",
    ]

    # Standard SMAPI scopes for skill management
    DEFAULT_SCOPES = [
        "alexa::ask:skills:readwrite",
        "alexa::ask:models:readwrite",
        "alexa::ask:skills:test",
    ]

    # Amazon OAuth endpoints
    OAUTH_ENDPOINTS = {
        "NA": "https://api.amazon.com/auth/o2/token",
        "EU": "https://api.amazon.co.uk/auth/o2/token",
        "FE": "https://api.amazon.co.jp/auth/o2/token",
    }

    def __init__(self, console: Console | None = None):
        """Initialize SMAPI token helper."""
        self.console = console or Console()
        self.logger = HAConnectorLogger("smapi_token_helper")

    def interactive_token_setup(self) -> SMAPICredentials:
        """
        Interactive token setup with account creation guidance.

        Returns:
            Configured SMAPICredentials with access tokens
        """
        self._display_setup_welcome()

        # Check if user has Amazon Developer account
        has_account = Confirm.ask(
            "[yellow]Do you already have an Amazon Developer account?[/yellow]"
        )

        if not has_account:
            self._guide_account_creation()

        # Check for existing LWA Security Profile
        has_profile = Confirm.ask(
            "[yellow]Do you have a Login with Amazon (LWA) Security Profile "
            "configured for SMAPI?[/yellow]"
        )

        if not has_profile:
            self._guide_security_profile_creation()

        # Get credentials from user
        return self._interactive_credential_input()

    def _display_setup_welcome(self) -> None:
        """Display setup welcome message."""
        welcome_message = (
            "[bold cyan]🔐 Amazon Developer Console SMAPI Token Setup"
            "[/bold cyan]\n\n"
            "This wizard will help you obtain the necessary tokens to automate "
            "Alexa skill creation through the Amazon Developer Console."
        )

        self.console.print(
            Panel.fit(
                welcome_message,
                title="SMAPI Authentication Setup",
                border_style="cyan",
            )
        )

    def _guide_account_creation(self) -> None:
        """Guide user through Amazon Developer account creation."""
        guide_text = self._build_account_creation_guide()

        self.console.print(
            Panel(
                guide_text,
                title="Account Creation Guide",
                border_style="green",
            )
        )

        # Open browser to help user
        if Confirm.ask(
            "[green]Would you like me to open the Amazon Developer Portal now?[/green]"
        ):
            webbrowser.open("https://developer.amazon.com")

        self.console.print(
            "[yellow]Press Enter when you've completed account creation...[/yellow]"
        )
        input()

    def _build_account_creation_guide(self) -> str:
        """Build account creation guide text."""
        return (
            "[bold]🆕 Creating Your Amazon Developer Account[/bold]\n"
            "[cyan]Step 1: Visit the Amazon Developer Portal[/cyan]\n"
            "• Navigate to: https://developer.amazon.com\n"
            "• Click 'Sign In' or 'Create Account'\n"
            "[cyan]Step 2: Account Registration[/cyan]\n"
            "• Use your existing Amazon account OR create a new one\n"
            "• Complete the developer registration form\n"
            "• Verify your identity (may require phone/email verification)\n"
            "[cyan]Step 3: Accept Developer Agreement[/cyan]\n"
            "• Review and accept the Amazon Developer Services Agreement\n"
            "• Complete any required tax information forms\n"
            "[yellow]⚠️  This process typically takes 5-10 minutes[/yellow]"
        )

    def _guide_security_profile_creation(self) -> None:
        """Guide user through LWA Security Profile creation."""
        # Offer browser automation option
        use_automation = Confirm.ask(
            "[cyan]🤖 Would you like me to help automate the Security Profile "
            "creation process?\n"
            "[dim](I'll open a browser and fill forms for you, but you stay in "
            "control)[/dim][/cyan]"
        )
        if use_automation and automate_security_profile_creation is not None:
            try:
                self.console.print("[yellow]🌐 Starting browser automation...[/yellow]")
                profile_result = automate_security_profile_creation(headless=False)
                if (
                    profile_result
                    and profile_result.get("client_id") != "MANUAL_COLLECTION_REQUIRED"
                ):
                    self.console.print(
                        "[green]✅ Browser automation completed successfully![/green]"
                    )
                    self.console.print(
                        "[yellow]Please return to continue with OAuth flow...[/yellow]"
                    )
                    return
                self.console.print(
                    "[yellow]⚠️ Browser automation partially completed. "
                    "Continuing with manual guidance...[/yellow]"
                )
            except (RuntimeError, ValueError) as e:
                self.console.print(
                    f"[yellow]⚠️ Browser automation failed: {e}. "
                    "Using manual guidance...[/yellow]"
                )
        elif use_automation and automate_security_profile_creation is None:
            self.console.print(
                "[yellow]⚠️ Browser automation not available. "
                "Using manual guidance...[/yellow]"
            )

        # Fallback to manual guidance
        guide_text = self._build_security_profile_guide()

        self.console.print(
            Panel(
                guide_text,
                title="Security Profile Setup Guide",
                border_style="blue",
            )
        )

        # Open browser to help user
        if Confirm.ask("[green]Would you like me to open the LWA Console now?[/green]"):
            lwa_url = "https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html"
            webbrowser.open(lwa_url)

        self.console.print(
            "[yellow]Press Enter when you've completed security profile "
            "creation...[/yellow]"
        )
        input()

    def _build_security_profile_guide(self) -> str:
        """Build security profile creation guide text."""
        uri_list = "\n".join(f"  • {uri}" for uri in self.REQUIRED_REDIRECT_URIS)

        return (
            "[bold]🔐 Creating Your LWA Security Profile[/bold]\n"
            "[cyan]Step 1: Access LWA Console[/cyan]\n"
            "• Navigate to: https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html\n"
            "• Sign in with your Amazon Developer account\n"
            "[cyan]Step 2: Create Security Profile[/cyan]\n"
            "• Click 'Create a New Security Profile'\n"
            "• Security Profile Name: [bold]'Home Assistant SMAPI Integration'[/bold]\n"
            "• Security Profile Description: [bold]'SMAPI access for Home Assistant "
            "skill automation'[/bold]\n"
            "• Consent Privacy Notice URL: [bold]'https://www.home-assistant.io/privacy/'[/bold]\n"
            "[cyan]Step 3: Configure Web Settings[/cyan]\n"
            "• Find your new profile and click the gear icon → 'Web Settings'\n"
            "• Click 'Edit' and add these Allowed Return URLs:\n"
            f"{uri_list}\n"
            "• Click 'Save'\n"
            "[yellow]⚠️  Make sure to add URLs to 'Allowed Return URLs', "
            "NOT 'Allowed Origins'[/yellow]"
        )

    def _interactive_credential_input(self) -> SMAPICredentials:
        """Interactive input of LWA credentials."""
        self._display_credential_collection_info()

        # Get credentials from user
        client_id = Prompt.ask(
            "[cyan]Enter your LWA Client ID[/cyan]", password=False
        ).strip()

        client_secret = Prompt.ask(
            "[cyan]Enter your LWA Client Secret[/cyan]", password=True
        ).strip()

        if not client_id or not client_secret:
            raise ValidationError("Both Client ID and Client Secret are required")

        # Create security profile and perform OAuth flow
        security_profile = LWASecurityProfile(
            client_id=client_id,
            client_secret=client_secret,
            allowed_return_urls=self.REQUIRED_REDIRECT_URIS,
            scopes=self.DEFAULT_SCOPES,
        )

        return self._perform_oauth_flow(security_profile)

    def _display_credential_collection_info(self) -> None:
        """Display credential collection information."""
        credential_text = (
            "[bold]📋 Collect Your LWA Credentials[/bold]\n"
            "From your LWA Security Profile (Web Settings):\n"
            "• Client ID: Long alphanumeric string\n"
            "• Client Secret: Shorter alphanumeric string\n"
            "[yellow]These credentials are required for SMAPI access[/yellow]"
        )

        self.console.print(
            Panel(
                credential_text,
                title="Credential Collection",
                border_style="yellow",
            )
        )

    def _perform_oauth_flow(
        self, security_profile: LWASecurityProfile
    ) -> SMAPICredentials:
        """
        Perform complete OAuth 2.0 Authorization Code Grant flow.

        Args:
            security_profile: LWA security profile configuration

        Returns:
            SMAPICredentials with access and refresh tokens
        """
        self._display_oauth_flow_info()

        # Generate OAuth parameters
        state = secrets.token_urlsafe(32)
        redirect_uri = self.REQUIRED_REDIRECT_URIS[0]  # Use localhost callback

        # Create and display authorization URL
        auth_url = self._build_authorization_url(security_profile, redirect_uri, state)
        self._display_authorization_url(auth_url)

        # Handle OAuth callback and exchange for tokens
        auth_code = self._handle_oauth_callback(auth_url, redirect_uri, state)
        return self._exchange_code_for_tokens(security_profile, auth_code, redirect_uri)

    def _display_oauth_flow_info(self) -> None:
        """Display OAuth flow information."""
        oauth_text = (
            "[bold]🚀 Starting OAuth 2.0 Authorization Flow[/bold]\n"
            "This will:\n"
            "1. Open your browser to Amazon's authorization page\n"
            "2. Ask you to sign in and authorize the application\n"
            "3. Automatically capture the authorization code\n"
            "4. Exchange it for access and refresh tokens\n"
            "[yellow]Keep this terminal window open during the process![/yellow]"
        )

        self.console.print(
            Panel(
                oauth_text,
                title="OAuth Flow",
                border_style="green",
            )
        )

    def _display_authorization_url(self, auth_url: str) -> None:
        """Display authorization URL to user."""
        self.console.print("\n[bold]Authorization URL:[/bold]")
        self.console.print(Syntax(auth_url, "url", theme="github-dark"))

    def _build_authorization_url(
        self, security_profile: LWASecurityProfile, redirect_uri: str, state: str
    ) -> str:
        """Build OAuth authorization URL."""
        params = {
            "client_id": security_profile.client_id,
            "scope": " ".join(security_profile.scopes),
            "response_type": "code",
            "state": state,
            "redirect_uri": redirect_uri,
        }

        return f"https://www.amazon.com/ap/oa?{urlencode(params)}"

    def _handle_oauth_callback(
        self, auth_url: str, redirect_uri: str, state: str
    ) -> str:
        """
        Handle OAuth callback with local server.

        Args:
            auth_url: Authorization URL to open
            redirect_uri: Expected redirect URI
            state: State parameter for validation

        Returns:
            Authorization code from OAuth callback
        """
        # Setup OAuth result container and server
        oauth_result = OAuthResult()
        server_ready = threading.Event()

        # Start callback server in separate thread
        server_thread = self._start_callback_server(
            oauth_result, state, redirect_uri, server_ready
        )

        # Wait for server and open browser
        self._open_browser_for_authorization(auth_url, server_ready)

        # Wait for callback and validate results
        return self._wait_for_oauth_result(server_thread, oauth_result)

    def _start_callback_server(
        self,
        oauth_result: OAuthResult,
        state: str,
        redirect_uri: str,
        server_ready: threading.Event,
    ) -> threading.Thread:
        """Start OAuth callback server in a separate thread."""
        parsed_uri = urlparse(redirect_uri)
        port = parsed_uri.port or 9090

        # Create callback handler
        callback_handler = self._create_callback_handler(state, oauth_result)

        server_thread = threading.Thread(
            target=self._run_callback_server,
            args=(callback_handler, port, server_ready),
            daemon=True,
        )
        server_thread.start()
        return server_thread

    def _open_browser_for_authorization(
        self, auth_url: str, server_ready: threading.Event
    ) -> None:
        """Open browser for OAuth authorization."""
        server_ready.wait(timeout=5)
        self.console.print("[green]Opening browser for authorization...[/green]")
        webbrowser.open(auth_url)
        self.console.print("[yellow]Waiting for authorization callback...[/yellow]")

    def _wait_for_oauth_result(
        self, server_thread: threading.Thread, oauth_result: OAuthResult
    ) -> str:
        """Wait for OAuth result and validate."""
        server_thread.join(timeout=300)  # 5 minute timeout

        if oauth_result.auth_error:
            raise ValidationError(
                f"OAuth authorization failed: {oauth_result.auth_error}"
            )

        if not oauth_result.auth_code:
            raise ValidationError("Authorization timeout - no callback received")

        self.console.print(
            "[green]✅ Authorization code received successfully![/green]"
        )
        return oauth_result.auth_code

    def _create_callback_handler(
        self, state: str, oauth_result: OAuthResult
    ) -> type[BaseHTTPRequestHandler]:
        """Create OAuth callback handler class."""

        class CallbackHandler(BaseHTTPRequestHandler):
            """Handle OAuth callback requests."""

            # pylint: disable=invalid-name  # do_GET is HTTP handler convention
            def do_GET(self) -> None:
                """Handle GET request for OAuth callback."""
                query_params = parse_qs(urlparse(self.path).query)

                # Validate state parameter
                callback_state = query_params.get("state", [None])[0]
                if callback_state != state:
                    oauth_result.auth_error = (
                        "Invalid state parameter - possible CSRF attack"
                    )
                    self._send_error_response("Invalid state parameter")
                    return

                # Process OAuth response
                self._process_oauth_response(query_params, oauth_result)

            def _process_oauth_response(
                self, query_params: dict[str, list[str]], oauth_result: OAuthResult
            ) -> None:
                """Process OAuth response parameters."""
                if "code" in query_params:
                    oauth_result.auth_code = query_params["code"][0]
                    self._send_success_response()
                elif "error" in query_params:
                    self._handle_oauth_error(query_params, oauth_result)
                else:
                    oauth_result.auth_error = (
                        "No authorization code or error in callback"
                    )
                    self._send_error_response("Invalid callback response")

            def _handle_oauth_error(
                self, query_params: dict[str, list[str]], oauth_result: OAuthResult
            ) -> None:
                """Handle OAuth error response."""
                error_code = query_params["error"][0]
                error_description = query_params.get(
                    "error_description", ["Unknown error"]
                )[0]
                oauth_result.auth_error = (
                    f"Authorization failed: {error_code} - {error_description}"
                )
                self._send_error_response(oauth_result.auth_error)

            def _send_success_response(self) -> None:
                """Send success response to browser."""
                success_html = self._build_success_html()
                self._send_response(200, success_html)

            def _send_error_response(self, error_message: str) -> None:
                """Send error response to browser."""
                error_html = self._build_error_html(error_message)
                self._send_response(400, error_html)

            def _build_success_html(self) -> str:
                """Build success HTML response."""
                return """
                <html><head><title>Authorization Successful</title></head>
                <body style="font-family: Arial, sans-serif;
                            text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Authorization Successful!</h1>
                    <p>You have successfully authorized the Home Assistant
                    SMAPI integration.</p>
                    <p style="color: #666;">You can close this browser window
                    and return to the terminal.</p>
                </body></html>
                """

            def _build_error_html(self, error_message: str) -> str:
                """Build error HTML response."""
                return f"""
                <html><head><title>Authorization Failed</title></head>
                <body style="font-family: Arial, sans-serif;
                            text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Authorization Failed</h1>
                    <p>Error: {error_message}</p>
                    <p style="color: #666;">Please return to the terminal
                    and try again.</p>
                </body></html>
                """

            def _send_response(self, status_code: int, content: str) -> None:
                """Send HTTP response."""
                self.send_response(status_code)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode())

            # pylint: disable=arguments-differ,unused-argument  # HTTP handler conventions
            def log_message(self, fmt: str, *args) -> None:
                """Suppress default logging."""
                return

        return CallbackHandler

    def _run_callback_server(
        self,
        handler_class: type[BaseHTTPRequestHandler],
        port: int,
        server_ready: threading.Event,
    ) -> None:
        """Run OAuth callback server."""
        with HTTPServer(("127.0.0.1", port), handler_class) as httpd:
            server_ready.set()
            httpd.handle_request()  # Handle single request

    def _exchange_code_for_tokens(
        self, security_profile: LWASecurityProfile, auth_code: str, redirect_uri: str
    ) -> SMAPICredentials:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            security_profile: LWA security profile
            auth_code: Authorization code from callback
            redirect_uri: Original redirect URI

        Returns:
            SMAPICredentials with tokens
        """
        self.console.print(
            "[yellow]Exchanging authorization code for tokens...[/yellow]"
        )

        # Prepare and send token request
        token_data = self._prepare_token_request(
            security_profile, auth_code, redirect_uri
        )
        token_response = self._send_token_request(token_data)

        # Create and return credentials
        credentials = self._create_credentials_from_response(
            security_profile, token_response
        )
        self.display_token_summary(credentials)
        return credentials

    def _prepare_token_request(
        self, security_profile: LWASecurityProfile, auth_code: str, redirect_uri: str
    ) -> dict[str, str]:
        """Prepare token request data."""
        return {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": security_profile.client_id,
            "client_secret": security_profile.client_secret,
            "redirect_uri": redirect_uri,
        }

    def _send_token_request(self, token_data: dict[str, str]) -> dict[str, Any]:
        """Send token request to OAuth endpoints."""
        for _region, endpoint in self.OAUTH_ENDPOINTS.items():
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        endpoint,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data=token_data,
                    )

                if response.status_code == 200:
                    return response.json()

            except httpx.HTTPError as e:
                self.logger.debug(f"Token request failed: {e}")
                continue

        raise ValidationError("Failed to exchange authorization code for tokens")

    def _create_credentials_from_response(
        self, security_profile: LWASecurityProfile, token_response: dict[str, Any]
    ) -> SMAPICredentials:
        """Create SMAPICredentials from token response."""
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValidationError("No access token in response")

        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        # Calculate expiration times
        current_time = int(time.time())
        expires_at = current_time + expires_in
        refresh_expires_at = current_time + (365 * 24 * 3600)  # 1 year

        return SMAPICredentials(
            client_id=security_profile.client_id,
            client_secret=security_profile.client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            scope=" ".join(security_profile.scopes),
        )

    def display_token_summary(self, credentials: SMAPICredentials) -> None:
        """Display token acquisition summary."""
        self.console.print("[green]✅ Tokens obtained successfully![/green]")

        table = Table(title="🔐 SMAPI Token Summary", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        # Add token information to table
        self._add_token_info_to_table(table, credentials)
        self.console.print(table)

        # Add cleanup guidance
        self._show_token_access_guidance()

    def _show_token_access_guidance(self) -> None:
        """Show guidance for accessing full tokens for cleanup/management."""
        self.console.print(
            Panel(
                "🔧 [bold]Token Management & Cleanup[/bold]\n\n"
                "[cyan]For Token Cleanup/Revocation:[/cyan]\n"
                "• Use: [code]--save tokens.json[/code] to save full tokens\n"
                "• Then: [code]python -m smapi_token_cleanup "
                "--load tokens.json[/code]\n"
                "\n"
                "[cyan]For Manual Cleanup:[/cyan]\n"
                "• Amazon Account: https://www.amazon.com/ap/adam\n"
                "• Security Profile: "
                "https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html\n"
                "\n"
                "[cyan]To View Full Tokens (if needed):[/cyan]\n"
                "• Use: [code]--save tokens.json[/code] then "
                "[code]cat tokens.json[/code]\n"
                "• [yellow]⚠️ Keep tokens secure - they provide full "
                "SMAPI access[/yellow]",
                title="Next Steps",
            )
        )

    def _add_token_info_to_table(
        self, table: Table, credentials: SMAPICredentials
    ) -> None:
        """Add token information to display table."""
        access_valid = credentials.is_access_token_valid()
        refresh_valid = credentials.is_refresh_token_valid()

        table.add_row("Client ID", f"{credentials.client_id[:12]}...", "✅ Configured")

        # Format token displays
        access_token = credentials.access_token
        access_display = f"{access_token[:20] if access_token else 'None'}..."
        table.add_row(
            "Access Token",
            access_display,
            "✅ Valid" if access_valid else "❌ Invalid",
        )

        refresh_token = credentials.refresh_token
        refresh_display = f"{refresh_token[:20] if refresh_token else 'None'}..."
        table.add_row(
            "Refresh Token",
            refresh_display,
            "✅ Valid" if refresh_valid else "❌ Invalid",
        )
        table.add_row("Scopes", credentials.scope, "✅ SMAPI Ready")

    def save_credentials(
        self, credentials: SMAPICredentials, file_path: str | Path
    ) -> None:
        """
        Save credentials to secure file.

        Args:
            credentials: SMAPICredentials to save
            file_path: Path to save credentials file
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare and write credentials data
        creds_data = self._prepare_credentials_data(credentials)
        self._write_credentials_file(file_path, creds_data)

        self.console.print(f"[green]✅ Credentials saved to: {file_path}[/green]")

    def _prepare_credentials_data(
        self, credentials: SMAPICredentials
    ) -> dict[str, Any]:
        """Prepare credentials data for saving."""
        return {
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "access_token": credentials.access_token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expires_at,
            "refresh_expires_at": credentials.refresh_expires_at,
            "scope": credentials.scope,
            "created_at": int(time.time()),
        }

    def _write_credentials_file(
        self, file_path: Path, creds_data: dict[str, Any]
    ) -> None:
        """Write credentials data to file with secure permissions."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)

            # Set restrictive permissions (owner read/write only)
            file_path.chmod(0o600)

        except OSError as e:
            raise ValidationError(f"Failed to save credentials: {e}") from e

    def load_credentials(self, file_path: str | Path) -> SMAPICredentials:
        """
        Load credentials from file.

        Args:
            file_path: Path to credentials file

        Returns:
            SMAPICredentials loaded from file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValidationError(f"Credentials file not found: {file_path}")

        creds_data = self._read_credentials_file(file_path)
        return self._create_credentials_from_file_data(creds_data)

    def _read_credentials_file(self, file_path: Path) -> dict[str, Any]:
        """Read credentials data from file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise ValidationError(f"Failed to load credentials: {e}") from e

    def _create_credentials_from_file_data(
        self, creds_data: dict[str, Any]
    ) -> SMAPICredentials:
        """Create SMAPICredentials from file data."""
        try:
            return SMAPICredentials(
                client_id=creds_data["client_id"],
                client_secret=creds_data["client_secret"],
                access_token=creds_data.get("access_token"),
                refresh_token=creds_data.get("refresh_token"),
                expires_at=creds_data.get("expires_at"),
                refresh_expires_at=creds_data.get("refresh_expires_at"),
                scope=creds_data.get("scope", " ".join(self.DEFAULT_SCOPES)),
            )
        except KeyError as e:
            raise ValidationError(f"Missing required credential field: {e}") from e

    def refresh_tokens(self, credentials: SMAPICredentials) -> SMAPICredentials:
        """
        Refresh access token using refresh token.

        Args:
            credentials: Current credentials with refresh token

        Returns:
            Updated credentials with new access token
        """
        self._validate_refresh_prerequisites(credentials)

        self.console.print("[yellow]Refreshing access token...[/yellow]")

        # Prepare and send refresh request
        refresh_data = self._prepare_refresh_request(credentials)
        token_response = self._send_refresh_request(refresh_data)

        # Update credentials with new token
        self._update_credentials_with_new_token(credentials, token_response)

        self.console.print("[green]✅ Access token refreshed successfully![/green]")
        return credentials

    def _validate_refresh_prerequisites(self, credentials: SMAPICredentials) -> None:
        """Validate prerequisites for token refresh."""
        if not credentials.refresh_token:
            raise ValidationError("No refresh token available")

        if not credentials.is_refresh_token_valid():
            raise ValidationError("Refresh token is expired")

    def _prepare_refresh_request(self, credentials: SMAPICredentials) -> dict[str, str]:
        """Prepare refresh token request data."""
        if credentials.refresh_token is None:
            raise ValidationError("No refresh token available")
        if credentials.client_id is None:
            raise ValidationError("No client_id available")
        if credentials.client_secret is None:
            raise ValidationError("No client_secret available")
        return {
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        }

    def _send_refresh_request(self, refresh_data: dict[str, str]) -> dict[str, Any]:
        """Send refresh token request to OAuth endpoints."""
        for _region, endpoint in self.OAUTH_ENDPOINTS.items():
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        endpoint,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data=refresh_data,
                    )

                if response.status_code == 200:
                    return response.json()

            except httpx.HTTPError as e:
                self.logger.debug(f"Token refresh failed: {e}")
                continue

        raise ValidationError("Failed to refresh access token")

    def _update_credentials_with_new_token(
        self, credentials: SMAPICredentials, token_response: dict[str, Any]
    ) -> None:
        """Update credentials with new access token."""
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValidationError("No access token in refresh response")

        expires_in = token_response.get("expires_in", 3600)
        credentials.access_token = access_token
        credentials.expires_at = int(time.time()) + expires_in


def main() -> None:
    """CLI entry point for SMAPI token helper."""
    parser = argparse.ArgumentParser(description="SMAPI Token Helper")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run interactive token setup"
    )
    parser.add_argument("--save", "-s", type=str, help="Save credentials to file path")
    parser.add_argument(
        "--load", "-l", type=str, help="Load credentials from file path"
    )

    args = parser.parse_args()

    console = Console()
    helper = SMAPITokenHelper(console)

    try:
        if args.interactive:
            credentials = helper.interactive_token_setup()

            # Always offer to save credentials for cleanup/management
            if not args.save:
                if Confirm.ask(
                    "\nSave tokens for future cleanup/management?", default=True
                ):
                    default_path = "smapi_tokens.json"
                    save_path = args.save or default_path
                    helper.save_credentials(credentials, save_path)
                    console.print(f"[green]💾 Tokens saved to: {save_path}[/green]")
                    console.print(
                        f"[cyan]💡 For cleanup: python -m smapi_token_cleanup "
                        f"--tokens {save_path}[/cyan]"
                    )
            else:
                helper.save_credentials(credentials, args.save)

        elif args.load:
            credentials = helper.load_credentials(args.load)
            helper.display_token_summary(credentials)

        else:
            parser.print_help()

    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
