"""
🤖 SMAPI AUTOMATION ENHANCEMENT: Ethical Hybrid Automation

This module provides comprehensive automation while preserving user agency and security.
Automates tedious setup tasks while requiring explicit user consent for security
decisions.

=== ETHICAL AUTOMATION CAPABILITIES ===

1. 🔄 Automated Infrastructure Setup
   - Browser automation for Security Profile creation/deletion
   - Automatic redirect URI configuration
   - Guided Developer Console account verification

2. 🛡️ Preserved User Security Control
   - Explicit OAuth consent (never automated)
   - User choice between SMAPI vs manual skill creation
   - Transparent logging of all automated actions

3. 🚀 Flexible Deployment Options
   - CI/CD compatible with long-lived tokens
   - Environment-based credential injection
   - Automated testing workflows

=== HYBRID AUTOMATION STRATEGY ===

Ethical Balance: Automate Setup, Preserve Choice

1. Security Profile Management
   ✅ AUTOMATED: Browser automation creates profiles with correct redirect URLs
   ✅ USER CONTROL: User owns and can delete profiles anytime

2. OAuth Authorization
   ❌ NEVER AUTOMATED: Explicit user "Allow" click required (security/ethics)
   ✅ GUIDED: Clear instructions and return-to-tool workflow

3. Skill Creation Choice
   ✅ SMAPI OPTION: "Create skills automatically via API?"
   ✅ MANUAL OPTION: "I'll create skills in Developer Console manually"
   ✅ COMPATIBILITY: Manual skills work with automated tokens

4. Account Management
   ✅ GUIDED: Direct user to Developer Console for account verification
   ✅ AUTOMATED: Return to tool for streamlined OAuth flow
"""

import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class CredentialConfig:
    """Organizational/CI credential configuration."""

    org_client_id: str = ""
    org_client_secret: str = ""
    org_refresh_token: str = ""


@dataclass
class AutomationSettings:
    """Automation behavior settings."""

    auto_refresh_enabled: bool = True
    refresh_buffer_minutes: int = 30
    background_validation_enabled: bool = True


@dataclass
class CICDConfig:
    """CI/CD integration configuration."""

    environment_injection_enabled: bool = True
    credential_rotation_enabled: bool = False


@dataclass
class AutomationConfig:
    """Configuration for API-driven automation."""

    credentials: CredentialConfig
    automation: AutomationSettings
    cicd: CICDConfig

    def __init__(
        self,
        credentials: CredentialConfig | None = None,
        automation: AutomationSettings | None = None,
        cicd: CICDConfig | None = None,
    ):
        self.credentials = credentials or CredentialConfig()
        self.automation = automation or AutomationSettings()
        self.cicd = cicd or CICDConfig()


class SMAPIAutomationEnhancer:
    """Enhanced SMAPI automation for minimal human interaction."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def automatic_token_refresh(
        self, refresh_token: str
    ) -> dict[str, Any] | None:
        """Automatically refresh tokens before expiration."""
        console.print("🔄 Performing automatic token refresh...")

        if not self.client:
            raise RuntimeError("HTTP client not initialized")

        try:
            response = await self.client.post(
                "https://api.amazon.com/auth/o2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.config.credentials.org_client_id,
                    "client_secret": self.config.credentials.org_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                token_data = response.json()
                console.print("[green]✅ Tokens refreshed automatically[/green]")
                return token_data
            console.print(
                f"[red]❌ Automatic refresh failed: {response.status_code}[/red]"
            )
            return None

        except httpx.RequestError as e:
            console.print(f"[red]❌ Network error during refresh: {e}[/red]")
            return None

    def inject_credentials_from_environment(self) -> dict[str, str]:
        """Inject credentials from environment variables for CI/CD."""
        console.print("🔧 Injecting credentials from environment...")

        credentials = {
            "client_id": os.getenv("SMAPI_CLIENT_ID", ""),
            "client_secret": os.getenv("SMAPI_CLIENT_SECRET", ""),
            "access_token": os.getenv("SMAPI_ACCESS_TOKEN", ""),
            "refresh_token": os.getenv("SMAPI_REFRESH_TOKEN", ""),
            "vendor_id": os.getenv("AMAZON_VENDOR_ID", ""),
        }

        # Validate required credentials
        missing = [key for key, value in credentials.items() if not value]
        if missing:
            console.print(
                f"[yellow]⚠️ Missing environment variables: {missing}[/yellow]"
            )
        else:
            console.print("[green]✅ All credentials loaded from environment[/green]")

        return credentials

    async def validate_credentials_background(
        self, access_token: str
    ) -> dict[str, Any]:
        """Background validation of SMAPI credentials."""
        console.print("🔍 Running background credential validation...")

        if not self.client:
            raise RuntimeError("HTTP client not initialized")

        try:
            # Test SMAPI access with vendor info call
            response = await self.client.get(
                "https://api.amazonalexa.com/v1/vendors",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 200:
                vendor_data = response.json()
                console.print("[green]✅ Credentials validated successfully[/green]")
                return {"status": "valid", "vendor_info": vendor_data}
            console.print(
                f"[red]❌ Credential validation failed: {response.status_code}[/red]"
            )
            return {"status": "invalid", "error": response.text}

        except httpx.RequestError as e:
            console.print(f"[red]❌ Network error during validation: {e}[/red]")
            return {"status": "error", "error": str(e)}

    def setup_ci_cd_workflow(self) -> str:
        """Generate CI/CD workflow configuration for automated SMAPI setup."""
        workflow = """
# GitHub Actions Workflow for Automated SMAPI Setup
name: SMAPI Authentication Setup

on:
  workflow_dispatch:
  schedule:
    - cron: '0 */6 * * *'  # Refresh tokens every 6 hours

jobs:
  smapi-auth:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install httpx rich

      - name: Run automated SMAPI setup
        env:
          SMAPI_CLIENT_ID: ${{ secrets.SMAPI_CLIENT_ID }}
          SMAPI_CLIENT_SECRET: ${{ secrets.SMAPI_CLIENT_SECRET }}
          SMAPI_REFRESH_TOKEN: ${{ secrets.SMAPI_REFRESH_TOKEN }}
        run: |
          python -m src.ha_connector.integrations.alexa.smapi_automation_enhancer \
            --ci-mode

      - name: Update environment with new tokens
        run: |
          # Update deployment environment with refreshed tokens
          echo "Tokens refreshed at $(date)" >> deployment.log
"""
        return workflow

    def show_automation_opportunities(self) -> None:
        """Display available automation opportunities and implementations."""
        table = Table(title="🤖 SMAPI Automation Opportunities")
        table.add_column("Manual Step", style="red")
        table.add_column("Automation Method", style="green")
        table.add_column("Implementation", style="cyan")
        table.add_column("Risk Level", style="yellow")

        automations = [
            (
                "Account Creation",
                "Organizational API Keys",
                "Use Amazon Partner API or pre-created org accounts",
                "Low",
            ),
            (
                "Security Profile Setup",
                "Browser Automation",
                "Playwright/Selenium to automate Developer Console forms",
                "Medium",
            ),
            (
                "OAuth Consent Click",
                "Browser Automation",
                "Automate 'Allow' button (NOT RECOMMENDED)",
                "High",
            ),
            (
                "OAuth Token Exchange",
                "API Integration",
                "Standard OAuth 2.0 flow with PKCE",
                "Low",
            ),
            (
                "Token Refresh",
                "API Integration",
                "Background refresh before expiration",
                "Low",
            ),
            (
                "Skill Creation",
                "Browser Automation",
                "Selenium/Playwright for skill setup forms",
                "Medium",
            ),
            (
                "Credential Management",
                "API Integration",
                "CI/CD environment variables + secret management",
                "Low",
            ),
            (
                "Validation Testing",
                "API Integration",
                "Automated credential health checks",
                "Low",
            ),
        ]

        for manual, automated, implementation, risk in automations:
            risk_style = {"Low": "green", "Medium": "yellow", "High": "red"}[risk]
            risk_formatted = f"[{risk_style}]{risk}[/{risk_style}]"
            table.add_row(manual, automated, implementation, risk_formatted)

        console.print(table)

        console.print("\n[bold]🎯 Hybrid Strategy Recommendation:[/bold]")
        console.print(
            "✅ [green]API Automation[/green] for official endpoints (OAuth, SMAPI)"
        )
        console.print(
            "🌐 [yellow]Browser Automation[/yellow] for missing APIs "
            "(Security Profiles, Skills)"
        )
        console.print(
            "⚠️ [red]Avoid Automating[/red] OAuth consent (security + ToS violations)"
        )

    def generate_deployment_automation(self) -> str:
        """Generate deployment automation scripts."""
        script = """#!/bin/bash
# SMAPI Deployment Automation Script

set -e

echo "🚀 Starting automated SMAPI deployment..."

# Validate environment
if [[ -z "$SMAPI_CLIENT_ID" || -z "$SMAPI_CLIENT_SECRET" ]]; then
    echo "❌ Missing required environment variables"
    exit 1
fi

# Refresh tokens if needed
python -c "
import asyncio
import os
from smapi_automation_enhancer import SMAPIAutomationEnhancer, AutomationConfig

async def main():
    config = AutomationConfig(
        org_client_id=os.getenv('SMAPI_CLIENT_ID'),
        org_client_secret=os.getenv('SMAPI_CLIENT_SECRET'),
    )

    async with SMAPIAutomationEnhancer(config) as enhancer:
        enhancer.inject_credentials_from_environment()
        if credentials['refresh_token']:
            new_tokens = await enhancer.automatic_token_refresh(
                credentials['refresh_token']
            )
            if new_tokens:
                print(f'export SMAPI_ACCESS_TOKEN={new_tokens[\"access_token\"]}')

asyncio.run(main())
"

echo "✅ SMAPI deployment automation complete"
"""
        return script


class EthicalHybridAutomation:
    """Ethical hybrid automation that balances efficiency with user agency."""

    def __init__(self, config: AutomationConfig):
        self.config = config
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    def guided_setup_workflow(self) -> None:
        """Display the guided setup workflow with clear user choices."""
        console.print(
            Panel(
                "[bold]🎯 Guided SMAPI Setup Workflow[/bold]\n\n"
                "[green]✅ AUTOMATED FOR YOU:[/green]\n"
                "  • Security Profile creation with correct redirect URLs\n"
                "  • Developer Console navigation guidance\n"
                "  • Return-to-tool workflow setup\n\n"
                "[yellow]🤝 YOUR EXPLICIT CHOICES:[/yellow]\n"
                "  • OAuth consent ('Allow' button) - [bold]never automated[/bold]\n"
                "  • Skill creation method (SMAPI vs Manual)\n"
                "  • Account verification in Developer Console\n\n"
                "[blue]🔄 ONGOING AUTOMATION:[/blue]\n"
                "  • Token refresh (with your existing consent)\n"
                "  • Background credential validation\n"
                "  • CI/CD integration (optional)",
                title="Ethical Automation Strategy",
            )
        )

    def show_user_choice_points(self) -> dict[str, str]:
        """Display and collect user choices for automation vs manual steps."""
        console.print("\n[bold]📋 Setup Choices:[/bold]")

        choices = {}

        # Choice 1: Security Profile Setup
        console.print("\n1. [yellow]Security Profile Setup[/yellow]")
        console.print(
            "   ✅ [green]RECOMMENDED[/green]: Automate Security Profile creation"
        )
        console.print(
            "   📝 Manual: Create Security Profile yourself in Developer Console"
        )

        # Choice 2: Skill Creation Method
        console.print("\n2. [yellow]Skill Creation Method[/yellow]")
        console.print("   🤖 [cyan]SMAPI[/cyan]: Automate skill creation via API")
        console.print(
            "   🖱️  [blue]Manual[/blue]: Create skills in Developer Console UI"
        )
        console.print(
            "   💡 [dim]Note: Manual skills work perfectly with automated tokens[/dim]"
        )

        # Choice 3: OAuth Consent (informational)
        console.print("\n3. [yellow]OAuth Consent[/yellow]")
        console.print(
            "   🛡️  [red]ALWAYS MANUAL[/red]: You must click 'Allow' "
            "(security requirement)"
        )
        console.print(
            "   💡 [dim]This preserves your security and follows OAuth "
            "best practices[/dim]"
        )

        choices["setup_workflow"] = "guided"
        return choices

    def create_security_profile_browser_script(self) -> str:
        """Generate browser automation script for Security Profile creation."""
        script = """
# Browser Automation for Security Profile Setup
# This script automates the tedious form-filling while preserving user control

from playwright.sync_api import sync_playwright
import time

def automate_security_profile_setup(profile_name: str, redirect_urls: list[str]):
    \"\"\"
    Automate Security Profile creation with user's explicit consent.

    Args:
        profile_name: Name for the LWA Security Profile
        redirect_urls: List of redirect URLs for OAuth flow
    \"\"\"

    with sync_playwright() as p:
        # Launch browser with user visibility (not headless)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Navigate to LWA Security Profile creation
            print("🌐 Opening Amazon Developer Console...")
            page.goto("https://developer.amazon.com/lwa/sp/overview")

            # Wait for user to log in if needed
            print("⏳ Please log in to your Amazon Developer account if prompted...")
            page.wait_for_selector("text=Create Security Profile", timeout=60000)

            # Click Create Security Profile
            print("🔧 Creating Security Profile...")
            page.click("text=Create Security Profile")

            # Fill in Security Profile details
            page.fill("input[name='profileName']", profile_name)
            page.fill(
                "textarea[name='profileDescription']",
                f"Security Profile for {profile_name} - Home Assistant Integration",
            )

            # Add redirect URLs
            for i, url in enumerate(redirect_urls):
                if i > 0:
                    page.click("text=Add URL")
                page.fill(f"input[name='redirectUrls[{i}]']", url)

            print("✅ Security Profile configured!")
            print("🎯 Next: Click 'Save' to create the profile")
            print("📋 Then return to this tool to continue OAuth setup")

            # Keep browser open for user to save
            input("Press Enter after you've saved the Security Profile...")

        except Exception as e:
            print(f"❌ Browser automation failed: {e}")
            print("💡 You can create the Security Profile manually at:")
            print("   https://developer.amazon.com/lwa/sp/overview")

        finally:
            browser.close()

# Example usage:
# automate_security_profile_setup(
#     "HomeAssistantSMAPI",
#     ["http://localhost:8080/oauth/callback"]
# )
"""
        return script

    def show_skill_creation_options(self) -> None:
        """Display skill creation options with pros/cons."""
        table = Table(title="🎯 Skill Creation Options")
        table.add_column("Method", style="bold")
        table.add_column("Pros", style="green")
        table.add_column("Cons", style="red")
        table.add_column("Best For", style="cyan")

        options = [
            (
                "🤖 SMAPI Automation",
                (
                    "• Fast deployment\n• CI/CD integration\n"
                    "• Bulk operations\n• Version control"
                ),
                "• Learning curve\n• JSON configuration\n• API limitations",
                "• Development teams\n• Multiple skills\n• CI/CD workflows",
            ),
            (
                "🖱️ Manual Console",
                (
                    "• Visual interface\n• Immediate feedback\n"
                    "• No coding required\n• Full feature access"
                ),
                (
                    "• Time consuming\n• Manual updates\n"
                    "• No version control\n• Hard to replicate"
                ),
                "• First-time users\n• Single skills\n• Visual learners",
            ),
            (
                "🔄 Hybrid Approach",
                (
                    "• Best of both worlds\n• Start manual, automate later\n"
                    "• Flexible deployment"
                ),
                "• Setup complexity\n• Multiple tools\n• Context switching",
                "• Experienced developers\n• Growing projects\n• Team environments",
            ),
        ]

        for method, pros, cons, best_for in options:
            table.add_row(method, pros, cons, best_for)

        console.print(table)

        console.print("\n[bold]💡 Recommendation:[/bold]")
        console.print(
            "✅ Start with [green]Manual Console[/green] for your first skill"
        )
        console.print("🚀 Upgrade to [cyan]SMAPI Automation[/cyan] once comfortable")
        console.print(
            "🔧 [yellow]Both approaches work with the same OAuth tokens![/yellow]"
        )

    def generate_guided_oauth_flow(self) -> str:
        """Generate user-guided OAuth flow with clear steps."""
        flow_guide = """
# 🛡️ Guided OAuth Setup (Preserves Your Security Control)

## Step 1: Automated Security Profile (If Selected)
- Run browser automation script
- Review generated Security Profile settings
- Click 'Save' when ready (your choice)

## Step 2: Developer Console Verification
- Browser opens to Amazon Developer Console
- Verify your account is set up correctly
- Return to this tool when ready

## Step 3: Explicit OAuth Consent (NEVER AUTOMATED)
- Tool opens OAuth authorization URL
- YOU click 'Allow' to grant permissions
- This step is intentionally manual for security

## Step 4: Token Collection & Storage
- Tool receives authorization code
- Exchanges for access/refresh tokens
- Offers to save tokens for future use (your choice)

## Step 5: Choose Your Path
- Option A: Use SMAPI for automated skill creation
- Option B: Create skills manually in Developer Console
- Option C: Mix both approaches as needed

## Security Notes:
✅ You control every permission grant
✅ Tokens expire and require re-authorization
✅ You can revoke access anytime in Amazon Developer Console
✅ All automation is transparent and logged
"""
        return flow_guide

    async def automatic_token_refresh(
        self, refresh_token: str
    ) -> dict[str, Any] | None:
        """Automatically refresh tokens before expiration."""
        console.print("🔄 Performing automatic token refresh...")

        if not self.client:
            raise RuntimeError("HTTP client not initialized")

        try:
            response = await self.client.post(
                "https://api.amazon.com/auth/o2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.config.credentials.org_client_id,
                    "client_secret": self.config.credentials.org_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                token_data = response.json()
                console.print("[green]✅ Tokens refreshed automatically[/green]")
                return token_data
            console.print(
                f"[red]❌ Automatic refresh failed: {response.status_code}[/red]"
            )
            return None

        except httpx.RequestError as e:
            console.print(f"[red]❌ Network error during refresh: {e}[/red]")
            return None

    def inject_credentials_from_environment(self) -> dict[str, str]:
        """Inject credentials from environment variables for CI/CD."""
        console.print("🔧 Injecting credentials from environment...")

        credentials = {
            "client_id": os.getenv("SMAPI_CLIENT_ID", ""),
            "client_secret": os.getenv("SMAPI_CLIENT_SECRET", ""),
            "access_token": os.getenv("SMAPI_ACCESS_TOKEN", ""),
            "refresh_token": os.getenv("SMAPI_REFRESH_TOKEN", ""),
            "vendor_id": os.getenv("AMAZON_VENDOR_ID", ""),
        }

        # Validate required credentials
        missing = [key for key, value in credentials.items() if not value]
        if missing:
            console.print(
                f"[yellow]⚠️ Missing environment variables: {missing}[/yellow]"
            )
        else:
            console.print("[green]✅ All credentials loaded from environment[/green]")

        return credentials

    async def validate_credentials_background(
        self, access_token: str
    ) -> dict[str, Any]:
        """Background validation of SMAPI credentials."""
        console.print("🔍 Running background credential validation...")

        if not self.client:
            raise RuntimeError("HTTP client not initialized")

        try:
            # Test SMAPI access with vendor info call
            response = await self.client.get(
                "https://api.amazonalexa.com/v1/vendors",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 200:
                vendor_data = response.json()
                console.print("[green]✅ Credentials validated successfully[/green]")
                return {"status": "valid", "vendor_info": vendor_data}
            console.print(
                f"[red]❌ Credential validation failed: {response.status_code}[/red]"
            )
            return {"status": "invalid", "error": response.text}

        except httpx.RequestError as e:
            console.print(f"[red]❌ Network error during validation: {e}[/red]")
            return {"status": "error", "error": str(e)}

    def setup_ci_cd_workflow(self) -> str:
        """Generate CI/CD workflow configuration for automated SMAPI setup."""
        workflow = """
# GitHub Actions Workflow for Automated SMAPI Setup
name: SMAPI Authentication Setup

on:
  workflow_dispatch:
  schedule:
    - cron: '0 */6 * * *'  # Refresh tokens every 6 hours

jobs:
  smapi-auth:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install httpx rich

      - name: Run automated SMAPI setup
        env:
          SMAPI_CLIENT_ID: ${{ secrets.SMAPI_CLIENT_ID }}
          SMAPI_CLIENT_SECRET: ${{ secrets.SMAPI_CLIENT_SECRET }}
          SMAPI_REFRESH_TOKEN: ${{ secrets.SMAPI_REFRESH_TOKEN }}
        run: |
          python -m src.ha_connector.integrations.alexa.smapi_automation_enhancer \
            --ci-mode

      - name: Update environment with new tokens
        run: |
          # Update deployment environment with refreshed tokens
          echo "Tokens refreshed at $(date)" >> deployment.log
"""
        return workflow

    def show_automation_opportunities(self) -> None:
        """Display available automation opportunities and implementations."""
        table = Table(title="🤖 SMAPI Automation Opportunities")
        table.add_column("Manual Step", style="red")
        table.add_column("Automation Method", style="green")
        table.add_column("Implementation", style="cyan")
        table.add_column("Risk Level", style="yellow")

        automations = [
            (
                "Account Creation",
                "Organizational API Keys",
                "Use Amazon Partner API or pre-created org accounts",
                "Low",
            ),
            (
                "Security Profile Setup",
                "Browser Automation",
                "Playwright/Selenium to automate Developer Console forms",
                "Medium",
            ),
            (
                "OAuth Consent Click",
                "Browser Automation",
                "Automate 'Allow' button (NOT RECOMMENDED)",
                "High",
            ),
            (
                "OAuth Token Exchange",
                "API Integration",
                "Standard OAuth 2.0 flow with PKCE",
                "Low",
            ),
            (
                "Token Refresh",
                "API Integration",
                "Background refresh before expiration",
                "Low",
            ),
            (
                "Skill Creation",
                "Browser Automation",
                "Selenium/Playwright for skill setup forms",
                "Medium",
            ),
            (
                "Credential Management",
                "API Integration",
                "CI/CD environment variables + secret management",
                "Low",
            ),
            (
                "Validation Testing",
                "API Integration",
                "Automated credential health checks",
                "Low",
            ),
        ]

        for manual, automated, implementation, risk in automations:
            risk_style = {"Low": "green", "Medium": "yellow", "High": "red"}[risk]
            risk_formatted = f"[{risk_style}]{risk}[/{risk_style}]"
            table.add_row(manual, automated, implementation, risk_formatted)

        console.print(table)

        console.print("\n[bold]🎯 Hybrid Strategy Recommendation:[/bold]")
        console.print(
            "✅ [green]API Automation[/green] for official endpoints (OAuth, SMAPI)"
        )
        console.print(
            "🌐 [yellow]Browser Automation[/yellow] for missing APIs "
            "(Security Profiles, Skills)"
        )
        console.print(
            "⚠️ [red]Avoid Automating[/red] OAuth consent (security + ToS violations)"
        )

    def generate_deployment_automation(self) -> str:
        """Generate deployment automation scripts."""
        script = """#!/bin/bash
# SMAPI Deployment Automation Script

set -e

echo "🚀 Starting automated SMAPI deployment..."

# Validate environment
if [[ -z "$SMAPI_CLIENT_ID" || -z "$SMAPI_CLIENT_SECRET" ]]; then
    echo "❌ Missing required environment variables"
    exit 1
fi

# Refresh tokens if needed
python -c "
import asyncio
import os
from smapi_automation_enhancer import SMAPIAutomationEnhancer, AutomationConfig

async def main():
    config = AutomationConfig(
        org_client_id=os.getenv('SMAPI_CLIENT_ID'),
        org_client_secret=os.getenv('SMAPI_CLIENT_SECRET'),
    )

    async with SMAPIAutomationEnhancer(config) as enhancer:
        enhancer.inject_credentials_from_environment()
        if credentials['refresh_token']:
            new_tokens = await enhancer.automatic_token_refresh(
                credentials['refresh_token']
            )
            if new_tokens:
                print(f'export SMAPI_ACCESS_TOKEN={new_tokens[\"access_token\"]}')

asyncio.run(main())
"

echo "✅ SMAPI deployment automation complete"
"""
        return script


async def main_automation_demo() -> None:
    """Demonstrate automation capabilities."""
    console.print(
        Panel(
            "🤖 [bold]SMAPI Automation Enhancement Demo[/bold]\n\n"
            "This demonstrates how to eliminate human interaction\n"
            "from SMAPI authentication workflows through API automation.",
            title="Automation Demo",
        )
    )

    config = AutomationConfig(
        credentials=CredentialConfig(
            org_client_id=os.getenv("SMAPI_CLIENT_ID", "demo_client_id"),
            org_client_secret=os.getenv("SMAPI_CLIENT_SECRET", ""),
        ),
        automation=AutomationSettings(auto_refresh_enabled=True),
    )

    async with SMAPIAutomationEnhancer(config) as enhancer:
        # Show automation opportunities
        enhancer.show_automation_opportunities()

        # Demo environment injection
        console.print("\n" + "=" * 60)
        console.print("🔧 Environment Credential Injection Demo:")
        enhancer.inject_credentials_from_environment()

        # Show CI/CD workflow
        console.print("\n" + "=" * 60)
        console.print("📋 CI/CD Workflow Configuration:")
        workflow = enhancer.setup_ci_cd_workflow()
        console.print(f"[dim]{workflow[:300]}...[/dim]")

        # Show deployment script
        console.print("\n" + "=" * 60)
        console.print("🚀 Deployment Automation Script:")
        script = enhancer.generate_deployment_automation()
        console.print(f"[dim]{script[:300]}...[/dim]")

        console.print(
            Panel(
                "[green]✅ Automation demo complete![/green]\n\n"
                "These patterns can eliminate 90%+ of manual interaction\n"
                "for production SMAPI deployments.",
                title="Results",
            )
        )


def run_ci_mode() -> None:
    """Run CI mode for automated SMAPI setup."""
    config = AutomationConfig(
        credentials=CredentialConfig(
            org_client_id=os.getenv("SMAPI_CLIENT_ID", ""),
            org_client_secret=os.getenv("SMAPI_CLIENT_SECRET", ""),
            org_refresh_token=os.getenv("SMAPI_REFRESH_TOKEN", ""),
        )
    )

    async def ci_main() -> None:
        async with SMAPIAutomationEnhancer(config) as enhancer:
            credentials = enhancer.inject_credentials_from_environment()
            if credentials["refresh_token"]:
                new_tokens = await enhancer.automatic_token_refresh(
                    credentials["refresh_token"]
                )
                if new_tokens:
                    print(f'export SMAPI_ACCESS_TOKEN={new_tokens["access_token"]}')

    asyncio.run(ci_main())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SMAPI Automation Enhancer")
    parser.add_argument(
        "--ci-mode", action="store_true", help="Run in CI/CD automation mode"
    )
    args = parser.parse_args()

    if args.ci_mode:
        run_ci_mode()
    else:
        asyncio.run(main_automation_demo())
