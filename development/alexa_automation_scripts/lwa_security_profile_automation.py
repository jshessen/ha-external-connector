"""
🔐 LWA Security Profile Browser Automation

This module provides ethical browser automation for Login with Amazon (LWA)
Security Profile creation and configuration, complementing the SMAPI token
helper for seamless user experience.

=== ETHICAL AUTOMATION PRINCIPLES ===

- Keep browser visible for user oversight and control
- Automate tedious form-filling, not decision-making
- Let user review and approve all changes
- Provide clear feedback on automation progress
- Allow manual intervention at any step

=== SECURITY PROFILE AUTOMATION ===

Automates the complex LWA Security Profile setup process:
- Navigate to LWA Console with user login
- Fill form fields automatically with proper values
- Set required redirect URLs for SMAPI compatibility
- Configure proper scopes and settings
- Let user review and save when ready

=== INTEGRATION WITH SMAPI TOKEN HELPER ===

This component integrates seamlessly with the existing SMAPITokenHelper:
- Uses same redirect URIs (127.0.0.1:9090/cb, ask-cli-static-content.s3)
- Applies same security standards and naming conventions
- Returns to SMAPITokenHelper for OAuth flow completion
- Maintains consistent user experience throughout

=== BROWSER AUTOMATION FEATURES ===

- Selenium WebDriver integration using established patterns
- Visible browser with user control maintained
- Automatic form population with SMAPI-compatible values
- Error detection and recovery with user guidance
- Screenshot capture for verification and debugging
"""

import re
import time
from typing import Any

from ha_connector.utils import HAConnectorLogger
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .browser_automation import BrowserAutomationDriver


class LWASecurityProfileAutomation:
    """Ethical browser automation for LWA Security Profile creation."""

    # LWA Console URLs
    LWA_CONSOLE_URL = (
        "https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html"
    )
    LWA_CREATE_PROFILE_URL = (
        "https://developer.amazon.com/loginwithamazon/console/site/lwa/"
        "create-security-profile.html"
    )

    # Required redirect URIs for SMAPI compatibility (from SMAPITokenHelper)
    REQUIRED_REDIRECT_URIS = [
        "http://127.0.0.1:9090/cb",
        "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/"
        "ask-cli-no-browser.html",
    ]

    # Default security profile values for Home Assistant integration
    DEFAULT_PROFILE_NAME = "Home Assistant SMAPI Integration"
    DEFAULT_PROFILE_DESCRIPTION = "SMAPI access for Home Assistant skill automation"
    DEFAULT_PRIVACY_URL = "https://www.home-assistant.io/privacy/"

    def __init__(self, headless: bool = False) -> None:
        """Initialize LWA Security Profile automation."""
        self.headless: bool = headless
        self.browser_driver: BrowserAutomationDriver | None = None
        self.logger: HAConnectorLogger = HAConnectorLogger(
            "lwa_security_profile_automation"
        )

    def __enter__(self) -> "LWASecurityProfileAutomation":
        """Context manager entry."""
        self.browser_driver = BrowserAutomationDriver(headless=self.headless)
        self.browser_driver.start_browser()
        return self

    def __exit__(self, exc_type: type[Any] | None, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self.browser_driver:
            self.browser_driver.stop_browser()

    def guide_security_profile_creation(self) -> dict[str, str] | None:
        """
        Guide user through automated Security Profile creation.

        Returns:
            Dictionary with profile details if successful, None if failed
        """
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None

        try:
            # Step 1: Check for existing profiles first
            existing_profile = self._check_existing_profiles()
            if existing_profile:
                msg = f"✅ Found existing profile: {existing_profile['name']}"
                self.logger.info(msg)
                return existing_profile

            # Step 2: Execute automation steps sequentially
            success = (
                self._execute_navigation_steps()
                and self._execute_profile_creation_steps()
            )

            if success:
                # Step 3: Let user review and save
                msg = (
                    "👀 Form is pre-filled. Please review and click 'Save' "
                    "when ready..."
                )
                self.logger.info(msg)
                profile_id = self._wait_for_profile_creation()

                if profile_id:
                    # Step 4: Configure web settings
                    self.logger.info("⚙️ Configuring web settings...")
                    if self._configure_web_settings(profile_id):
                        return self._get_profile_credentials(profile_id)

        except (WebDriverException, TimeoutException, RuntimeError) as e:
            self.logger.error(f"Security Profile automation failed: {e}")

        return None

    def _execute_navigation_steps(self) -> bool:
        """Execute navigation and login steps."""
        # Step 1: Navigate to LWA Console
        self.logger.info("🌐 Navigating to LWA Console...")
        if not self._navigate_to_lwa_console():
            return False

        # Step 2: Wait for user login
        self.logger.info("🔐 Please log in to your Amazon Developer account...")
        return self._wait_for_user_login()

    def _check_existing_profiles(self) -> dict[str, str] | None:
        """Check if suitable existing LWA Security Profile exists."""
        if not (
            self.browser_driver
            and self.browser_driver.driver
            and self.browser_driver.wait
        ):
            return None

        try:
            # Navigate to LWA Console main page first
            self.browser_driver.driver.get(self.LWA_CONSOLE_URL)

            # Wait for the page to load
            self.browser_driver.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//h1 | //table | //div[@class='content']")
                )
            )

            # Look for existing profiles table or list
            profile_links = self.browser_driver.driver.find_elements(
                By.XPATH,
                "//a[contains(@href, 'security-profile')] | "
                "//td[contains(text(), 'Home Assistant')] | "
                "//td[contains(text(), 'SMAPI')]",
            )

            if profile_links:
                for link in profile_links:
                    profile_text = link.text.strip()
                    if "Home Assistant" in profile_text or "SMAPI" in profile_text:
                        self.logger.info(
                            f"🔍 Found potential existing profile: {profile_text}"
                        )

                        # Extract profile ID if possible
                        href = link.get_attribute(  # pyright: ignore[reportUnknownMemberType]
                            "href"
                        )
                        if href and "security-profile" in href:
                            match = re.search(r"profile[/=]([^/&?]+)", href)
                            if match:
                                profile_id = match.group(1)
                                return {
                                    "name": profile_text,
                                    "profile_id": profile_id,
                                    "existing": "true",
                                }

            self.logger.info("🔍 No suitable existing profiles found")
            return None

        except (TimeoutException, WebDriverException) as e:
            self.logger.info(f"ℹ️ Could not check existing profiles: {e}")
            return None

    def _execute_profile_creation_steps(self) -> bool:
        """Execute profile creation form steps."""
        # Step 3: Navigate to create profile
        self.logger.info("➕ Navigating to Security Profile creation...")
        if not self._navigate_to_create_profile():
            return False

        # Step 4: Fill security profile form
        self.logger.info("📝 Filling Security Profile form...")
        return self._fill_security_profile_form()

    def _navigate_to_lwa_console(self) -> bool:
        """Navigate to LWA Console."""
        if not (self.browser_driver and self.browser_driver.driver):
            return False

        try:
            self.browser_driver.driver.get(self.LWA_CONSOLE_URL)
            self.logger.info("✅ Navigated to LWA Console")
            return True

        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"❌ Failed to navigate to LWA Console: {e}")
            return False

    def _wait_for_user_login(self, timeout: int = 300) -> bool:
        """Wait for user to complete login process."""
        if not (
            self.browser_driver
            and self.browser_driver.driver
            and self.browser_driver.wait
        ):
            return False

        self.logger.info(f"⏳ Waiting for user login (timeout: {timeout} seconds)")

        try:
            # Look for indicators that user is logged in
            login_indicator_xpath = (
                "//a[contains(@href, 'create-security-profile')] | "
                "//button[contains(text(), 'Create')] | "
                "//h1[contains(text(), 'Login with Amazon')]"
            )

            wait = WebDriverWait(self.browser_driver.driver, timeout)
            wait.until(
                EC.presence_of_element_located((By.XPATH, login_indicator_xpath))
            )
            self.logger.info("✅ User login detected")
            return True

        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"❌ Login timeout or error: {e}")
            return False

    def _navigate_to_create_profile(self) -> bool:
        """Navigate to Security Profile creation page."""
        if not (
            self.browser_driver
            and self.browser_driver.driver
            and self.browser_driver.wait
        ):
            return False

        try:
            # Navigate to create profile page
            self.browser_driver.driver.get(self.LWA_CREATE_PROFILE_URL)

            # Wait for form to load
            form_xpath = (
                "//input[@name='appName'] | "
                "//input[@name='profileName'] | "
                "//form[contains(@action, 'security-profile')]"
            )
            self.browser_driver.wait.until(
                EC.presence_of_element_located((By.XPATH, form_xpath))
            )
            self.logger.info("✅ Security Profile creation form loaded")
            return True

        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"❌ Failed to navigate to creation form: {e}")
            return False

    def _fill_security_profile_form(self) -> bool:
        """Fill the Security Profile creation form."""
        if not (self.browser_driver and self.browser_driver.driver):
            return False

        try:
            # Fill profile name
            name_selectors = [
                "input[name='appName']",
                "input[name='profileName']",
                "input[id='appName']",
            ]
            for selector in name_selectors:
                try:
                    name_field = self.browser_driver.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    name_field.clear()
                    name_field.send_keys(self.DEFAULT_PROFILE_NAME)
                    self.logger.info(
                        f"📝 Filled profile name: {self.DEFAULT_PROFILE_NAME}"
                    )
                    break
                except WebDriverException:
                    continue

            # Fill description
            desc_selectors = [
                "textarea[name='appDescription']",
                "textarea[name='description']",
                "input[name='appDescription']",
            ]
            for selector in desc_selectors:
                try:
                    desc_field = self.browser_driver.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    desc_field.clear()
                    desc_field.send_keys(self.DEFAULT_PROFILE_DESCRIPTION)
                    self.logger.info("📝 Filled profile description")
                    break
                except WebDriverException:
                    continue

            # Fill privacy notice URL if present
            privacy_selectors = [
                "input[name='privacyNoticeUrl']",
                "input[name='privacyUrl']",
            ]
            for selector in privacy_selectors:
                try:
                    privacy_field = self.browser_driver.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    privacy_field.clear()
                    privacy_field.send_keys(self.DEFAULT_PRIVACY_URL)
                    self.logger.info(
                        f"📝 Filled privacy notice URL: {self.DEFAULT_PRIVACY_URL}"
                    )
                    break
                except WebDriverException:
                    continue

            self.logger.info("✅ Security Profile form filled successfully")
            return True

        except (WebDriverException, TimeoutException) as e:
            self.logger.error(f"❌ Failed to fill form: {e}")
            return False

    def _wait_for_profile_creation(self, timeout: int = 60) -> str | None:
        """Wait for user to save profile and extract profile ID."""
        if not (
            self.browser_driver
            and self.browser_driver.driver
            and self.browser_driver.wait
        ):
            return None

        self.logger.info(
            f"⏳ Waiting for profile creation (timeout: {timeout} seconds)"
        )
        self.logger.info("💡 Click 'Save' to continue or 'Cancel' to abort...")

        try:
            # Monitor for both success and cancellation
            wait = WebDriverWait(self.browser_driver.driver, timeout)

            # Check for URL changes indicating save or cancel
            start_url = self.browser_driver.driver.current_url

            # Wait for URL to change (indicating user action)
            wait.until(lambda driver: driver.current_url != start_url)

            current_url = self.browser_driver.driver.current_url

            # Check if user cancelled (URL goes back to main console)
            if (
                "create-security-profile" not in current_url
                and "overview" in current_url
            ):
                self.logger.info("🚫 Profile creation cancelled by user")
                return None

            # Check if profile was created successfully
            if "security-profile" in current_url:
                # Extract profile ID from URL
                match = re.search(r"profile[/=]([^/&?]+)", current_url)
                if match:
                    profile_id = match.group(1)
                    self.logger.info(f"✅ Security Profile created: {profile_id}")
                    return profile_id

            # Alternative success detection - look for success indicators
            success_indicators = [
                "//div[contains(@class, 'success')]",
                "//h1[contains(text(), 'Security Profile')]",
                "//div[contains(text(), 'successfully')]",
            ]

            for indicator in success_indicators:
                try:
                    self.browser_driver.driver.find_element(By.XPATH, indicator)
                    # If we find success indicator, try to extract ID from URL
                    match = re.search(r"profile[/=]([^/&?]+)", current_url)
                    if match:
                        return match.group(1)
                except WebDriverException:
                    continue

            return None

        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"❌ Profile creation timeout or error: {e}")
            return None

    def _configure_web_settings(self, _profile_id: str) -> bool:
        """Configure web settings with required redirect URIs.

        Args:
            _profile_id: Security Profile ID (reserved for future use)
        """
        if not (
            self.browser_driver
            and self.browser_driver.driver
            and self.browser_driver.wait
        ):
            return False

        try:
            # Look for "Web Settings" link or gear icon
            web_settings_xpath = (
                "//a[contains(text(), 'Web Settings')] | "
                "//a[contains(@title, 'Web Settings')]"
            )
            web_settings_link = self.browser_driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, web_settings_xpath))
            )
            web_settings_link.click()

            # Wait for web settings page to load
            edit_xpath = (
                "//button[contains(text(), 'Edit')] | "
                "//input[@name='allowedReturnUrls']"
            )
            self.browser_driver.wait.until(
                EC.presence_of_element_located((By.XPATH, edit_xpath))
            )

            # Click Edit if needed
            try:
                edit_button = self.browser_driver.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Edit')]"
                )
                if edit_button.is_displayed():
                    edit_button.click()
                    time.sleep(1)  # Allow form to activate
            except WebDriverException:
                pass  # Edit might already be active

            # Fill redirect URIs
            return self._fill_redirect_uris()

        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"❌ Failed to configure web settings: {e}")
            return False

    def _fill_redirect_uris(self) -> bool:
        """Fill the Allowed Return URLs field with required redirect URIs."""
        if not (self.browser_driver and self.browser_driver.driver):
            return False

        try:
            # Find the redirect URIs field
            uri_selectors = [
                "textarea[name='allowedReturnUrls']",
                "input[name='allowedReturnUrls']",
                "textarea[name='redirectUris']",
            ]

            uri_field = None
            for selector in uri_selectors:
                try:
                    uri_field = self.browser_driver.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    break
                except WebDriverException:
                    continue

            if uri_field:
                # Clear and fill with required URIs
                uri_field.clear()
                uri_text = "\n".join(self.REQUIRED_REDIRECT_URIS)
                uri_field.send_keys(uri_text)

                self.logger.info("✅ Filled redirect URIs:")
                for uri in self.REQUIRED_REDIRECT_URIS:
                    self.logger.info(f"  • {uri}")

            return True

        except (WebDriverException, TimeoutException) as e:
            self.logger.error(f"❌ Failed to fill redirect URIs: {e}")
            return False

    def _get_profile_credentials(self, profile_id: str) -> dict[str, str] | None:
        """Extract Client ID and Client Secret from the profile page."""
        if not (self.browser_driver and self.browser_driver.driver):
            return None

        try:
            # Try to find Client ID
            client_id_xpath = (
                "//label[contains(text(), 'Client ID')]/following-sibling::*//text() | "
                "//span[contains(@class, 'client-id')]"
            )
            client_id_element = self.browser_driver.driver.find_element(
                By.XPATH, client_id_xpath
            )
            client_id = client_id_element.text.strip()

            # Try to find Client Secret using XPath selector
            client_secret_label_xpath = (  # nosec B105: XPath selector for DOM navigation, not hardcoded password
                "//label[contains(text(), 'Client Secret')]"
                "/following-sibling::*//text() | "
                "//span[contains(@class, 'client-secret')]"
            )
            client_secret_element = self.browser_driver.driver.find_element(
                By.XPATH, client_secret_label_xpath
            )
            client_secret = client_secret_element.text.strip()

            if client_id and client_secret:
                self.logger.info("✅ Successfully extracted credentials")
                return {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "profile_id": profile_id,
                }

        except (WebDriverException, TimeoutException) as e:
            self.logger.error(f"❌ Failed to extract credentials: {e}")

        # Fallback: Guide user to manual credential collection
        self.logger.info(
            "📋 Please manually copy Client ID and Client Secret from the page"
        )
        return {
            "profile_id": profile_id,
        }

    # Public API methods
    def navigate_to_lwa_console(self) -> bool:
        """Public method to navigate to LWA Console."""
        return self._navigate_to_lwa_console()

    def get_browser_status(self) -> dict[str, Any]:
        """Get current browser automation status."""
        if not self.browser_driver:
            return {"status": "not_initialized", "browser": None}

        if self.browser_driver.driver:
            try:
                current_url = self.browser_driver.driver.current_url
                return {
                    "status": "active",
                    "browser": "running",
                    "current_url": current_url,
                }
            except WebDriverException:
                return {"status": "error", "browser": "disconnected"}

        return {"status": "initialized", "browser": "not_started"}

    def take_screenshot(self, filename: str | None = None) -> str | None:
        """Take a screenshot of the current browser state."""
        if not (self.browser_driver and self.browser_driver.driver):
            return None

        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"lwa_automation_{timestamp}.png"

            screenshot_path = f"/tmp/{filename}"  # nosec B108
            self.browser_driver.driver.save_screenshot(  # pyright: ignore[reportUnknownMemberType]
                screenshot_path
            )
            self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path

        except WebDriverException as e:
            self.logger.error(f"❌ Failed to take screenshot: {e}")
            return None


def automate_security_profile_creation(headless: bool = False) -> dict[str, str] | None:
    """
    Standalone function to automate Security Profile creation.

    Args:
        headless: Whether to run browser in headless mode

    Returns:
        Dictionary with profile details if successful, None if failed
    """
    try:
        with LWASecurityProfileAutomation(headless=headless) as automation:
            return automation.guide_security_profile_creation()
    except (WebDriverException, TimeoutException, RuntimeError) as e:
        # Use module-level logger for standalone function
        module_logger = HAConnectorLogger("lwa_security_profile_automation")
        module_logger.error(f"Security Profile automation failed: {e}")
        return None
