"""
🧹 SMAPI TOKEN CLEANUP: OAuth Token Revocation & Security Profile Management

This module provides comprehensive cleanup capabilities for SMAPI authentication,
including token revocation and guidance for security profile removal.

=== CLEANUP CAPABILITIES ===

1. 🔐 Token Revocation
   - Revoke access tokens via Amazon LWA API
   - Revoke refresh tokens to prevent renewal
   - Clear local credential storage

2. 🗑️ Security Profile Cleanup
   - Guidance for Amazon Developer Console cleanup
   - Remove redirect URIs and client credentials
   - Delete security profile if no longer needed

3. 🔒 Permission Revocation
   - Remove application permissions from Amazon account
   - Clear authorized app access
   - Audit trail for security compliance
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


@dataclass
class SMAPICleanupCredentials:
    """Credentials for SMAPI cleanup operations."""

    client_id: str
    client_secret: str
    access_token: str = ""
    refresh_token: str = ""


class SMAPITokenCleanup:
    """Amazon SMAPI token cleanup and revocation utility."""

    REVOKE_URL = "https://api.amazon.com/auth/o2/revoke"

    def __init__(self):
        self.credentials: SMAPICleanupCredentials | None = None

    def load_credentials_from_file(self, file_path: str) -> None:
        """Load credentials from saved token file."""
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]❌ Credentials file not found: {file_path}[/red]")
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                creds_data = json.load(f)

            self.credentials = SMAPICleanupCredentials(
                client_id=creds_data.get("client_id", ""),
                client_secret=creds_data.get("client_secret", ""),
                access_token=creds_data.get("access_token", ""),
                refresh_token=creds_data.get("refresh_token", ""),
            )
            console.print(f"[green]✅ Loaded credentials from {file_path}[/green]")

        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[red]❌ Error loading credentials: {e}[/red]")

    def load_credentials_from_input(self) -> None:
        """Load credentials from user input."""
        console.print(
            Panel(
                "🔐 [bold]SMAPI Cleanup Credential Collection[/bold]\n\n"
                "To revoke tokens, we need your LWA credentials.\n"
                "These will only be used for cleanup and not stored.",
                title="Credential Collection",
            )
        )

        client_id = Prompt.ask("Enter your LWA Client ID")
        client_secret = Prompt.ask("Enter your LWA Client Secret", password=True)
        access_token = Prompt.ask("Enter your Access Token (optional)", default="")
        refresh_token = Prompt.ask("Enter your Refresh Token (optional)", default="")

        self.credentials = SMAPICleanupCredentials(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def revoke_access_token(self) -> bool:
        """Revoke the access token."""
        if not self.credentials or not self.credentials.access_token:
            console.print("[red]❌ No access token available for revocation[/red]")
            return False

        console.print("🔄 Revoking access token...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.REVOKE_URL,
                    data={
                        "token": self.credentials.access_token,
                        "client_id": self.credentials.client_id,
                        "client_secret": self.credentials.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    console.print("[green]✅ Access token revoked successfully[/green]")
                    return True
                console.print(
                    f"[red]❌ Token revocation failed: {response.status_code}[/red]"
                )
                console.print(f"Response: {response.text}")
                return False

            except httpx.RequestError as e:
                console.print(
                    f"[red]❌ Network error during token revocation: {e}[/red]"
                )
                return False

    async def revoke_refresh_token(self) -> bool:
        """Revoke the refresh token."""
        if not self.credentials or not self.credentials.refresh_token:
            console.print("[red]❌ No refresh token available for revocation[/red]")
            return False

        console.print("🔄 Revoking refresh token...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.REVOKE_URL,
                    data={
                        "token": self.credentials.refresh_token,
                        "client_id": self.credentials.client_id,
                        "client_secret": self.credentials.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    console.print(
                        "[green]✅ Refresh token revoked successfully[/green]"
                    )
                    return True
                console.print(
                    f"[red]❌ Refresh token revocation failed: "
                    f"{response.status_code}[/red]"
                )
                console.print(f"Response: {response.text}")
                return False

            except httpx.RequestError as e:
                console.print(
                    f"[red]❌ Network error during refresh token revocation: {e}[/red]"
                )
                return False

    def clear_local_storage(self) -> None:
        """Clear any locally stored credentials."""
        console.print("🧹 Clearing local credential storage...")

        # Check for common credential storage locations
        locations_checked: list[str] = []
        locations_cleared: list[str] = []

        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            locations_checked.append(".env")
            content = env_file.read_text(encoding="utf-8")
            tokens_present = any(
                token in content
                for token in [
                    "LWA_ACCESS_TOKEN",
                    "LWA_REFRESH_TOKEN",
                    "AMAZON_VENDOR_ID",
                ]
            )
            if tokens_present and Confirm.ask("Clear SMAPI tokens from .env file?"):
                lines = content.split("\n")
                cleaned_lines = [
                    line
                    for line in lines
                    if not any(
                        line.startswith(prefix)
                        for prefix in [
                            "LWA_ACCESS_TOKEN=",
                            "LWA_REFRESH_TOKEN=",
                            "AMAZON_VENDOR_ID=",
                        ]
                    )
                ]
                env_file.write_text("\n".join(cleaned_lines), encoding="utf-8")
                locations_cleared.append(".env")  # Report cleanup results
        table = Table(title="🧹 Local Storage Cleanup Results")
        table.add_column("Location", style="cyan")
        table.add_column("Status", style="green")

        for location in locations_checked:
            status = "✅ Cleared" if location in locations_cleared else "📝 Skipped"
            table.add_row(location, status)

        if not locations_checked:
            table.add_row("No credential files found", "✅ Clean")

        console.print(table)

    def show_security_profile_cleanup_guidance(self) -> None:
        """
        Show guidance for cleaning up the Amazon Developer Console
        security profile.
        """
        console.print(
            Panel(
                "🗑️ [bold]Security Profile Cleanup Guide[/bold]\n\n"
                "[cyan]Step 1: Remove Application Permissions[/cyan]\n"
                "• Visit: https://www.amazon.com/ap/adam\n"
                "• Look for 'Home Assistant SMAPI Integration'\n"
                "• Click 'Remove' to revoke app permissions\n\n"
                "[cyan]Step 2: Clean Up LWA Security Profile[/cyan]\n"
                "• Visit: https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html\n"
                "• Find 'Home Assistant SMAPI Integration' security profile\n"
                "• Option A: Edit → Remove redirect URI (http://127.0.0.1:9090/cb)\n"
                "• Option B: Delete entire security profile if no longer needed\n\n"
                "[cyan]Step 3: Verify Cleanup[/cyan]\n"
                "• Check Amazon account settings for remaining permissions\n"
                "• Verify security profile removal in LWA console\n"
                "• Test that old tokens no longer work",
                title="Manual Cleanup Steps",
            )
        )

    async def run_complete_cleanup(self, skip_confirmation: bool = False) -> None:
        """Run the complete cleanup process."""
        if not skip_confirmation:
            console.print(
                Panel(
                    "🧹 [bold red]SMAPI Authentication Cleanup[/bold red]\n\n"
                    "This will:\n"
                    "• Revoke access and refresh tokens\n"
                    "• Clear local credential storage\n"
                    "• Provide guidance for security profile cleanup\n\n"
                    "[yellow]⚠️ This action cannot be undone![/yellow]",
                    title="Cleanup Confirmation",
                )
            )

            if not Confirm.ask("Continue with cleanup?"):
                console.print("[yellow]Cleanup cancelled by user[/yellow]")
                return

        # Load credentials if not already loaded
        if not self.credentials:
            self.load_credentials_from_input()

        # Revoke tokens
        access_revoked = await self.revoke_access_token()
        refresh_revoked = await self.revoke_refresh_token()

        # Clear local storage
        self.clear_local_storage()

        # Show manual cleanup guidance
        self.show_security_profile_cleanup_guidance()

        # Summary
        console.print(
            Panel(
                (
                    f"🎯 [bold]Cleanup Summary[/bold]\n\n"
                    f"Access Token: "
                    f"{'✅ Revoked' if access_revoked else '❌ Failed/Skipped'}\n"
                    f"Refresh Token: "
                    f"{'✅ Revoked' if refresh_revoked else '❌ Failed/Skipped'}\n"
                    f"Local Storage: 🧹 Processed\n"
                    f"Manual Steps: 📋 Guidance provided\n\n"
                    "[green]Cleanup process completed![/green]"
                ),
                title="Results",
            )
        )


async def main() -> None:
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description="SMAPI Token Cleanup")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run interactive cleanup"
    )
    parser.add_argument(
        "--guidance-only", "-g", action="store_true", help="Show guidance only"
    )
    parser.add_argument(
        "--tokens",
        "-t",
        type=str,
        help="Load tokens from saved file for automated cleanup",
    )

    args = parser.parse_args()

    cleanup = SMAPITokenCleanup()

    if args.guidance_only:
        cleanup.show_security_profile_cleanup_guidance()
    elif args.tokens:
        # Load tokens from file and run automated cleanup
        cleanup.load_credentials_from_file(args.tokens)
        if cleanup.credentials:
            # Skip manual confirmation since we have tokens from file
            await cleanup.run_complete_cleanup(skip_confirmation=True)
        else:
            console.print("[red]❌ Could not load credentials from file[/red]")
    else:
        await cleanup.run_complete_cleanup(skip_confirmation=False)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
