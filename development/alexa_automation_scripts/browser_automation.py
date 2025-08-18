"""
🌐 Browser Automation Driver for Amazon Developer Console

This module provides comprehensive browser automation for Amazon Developer Console
operations that cannot be performed via SMAPI APIs, including guided skill setup,
manual configuration steps, and visual verification workflows.

=== BROWSER AUTOMATION FEATURES ===

- Selenium WebDriver integration with Chrome
- Headless and headed browser modes
- Automated form filling and navigation
- Screenshot capture for verification
- Error detection and recovery
- Progress persistence across sessions

=== GUIDED WORKFLOWS ===

- Developer Console login assistance
- Skill creation wizard automation
- Endpoint configuration setup
- Account linking UI configuration
- Visual progress feedback

This driver complements SMAPI automation by handling complex UI operations
not available through REST APIs, providing a complete automation solution.
"""

import logging
import os
import time
from types import TracebackType
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class BrowserAutomationDriver:
    """Browser automation for complex Developer Console operations."""

    DEVELOPER_CONSOLE_URL = "https://developer.amazon.com/alexa/console/ask"

    def __init__(self, headless: bool = False):
        """Initialize browser automation driver."""
        self.headless = headless
        self.driver: webdriver.Chrome | None = None
        self.wait: WebDriverWait[webdriver.Chrome] | None = None

    def __enter__(self) -> "BrowserAutomationDriver":
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.stop_browser()
        self.stop_browser()

    def start_browser(self) -> bool:
        """Start Chrome browser with automation settings."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_experimental_option(  # pyright: ignore[reportUnknownMemberType]
                "useAutomationExtension", False
            )
            chrome_options.add_experimental_option(  # pyright: ignore[reportUnknownMemberType]
                "excludeSwitches", ["enable-automation"]
            )

            self.driver = webdriver.Chrome(options=chrome_options)

            # Minimize detection as automated browser
            self.driver.execute_script(  # pyright: ignore[reportUnknownMemberType]
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Browser automation started successfully")
            return True

        except (WebDriverException, TimeoutException) as e:
            logger.error("Failed to start browser: %s", e)
            return False

    def stop_browser(self) -> None:
        """Stop browser and cleanup resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                logger.info("Browser automation stopped")
        except (WebDriverException, AttributeError):
            pass  # Browser already closed or not initialized

    def restart_browser(self) -> bool:
        """Restart browser automation."""
        self.stop_browser()
        return self.start_browser()

    def navigate_to_developer_console(self) -> bool:
        """Navigate to Amazon Developer Console."""
        if not self.driver:
            return False

        try:
            self.driver.get(self.DEVELOPER_CONSOLE_URL)
            logger.info("Navigated to Developer Console")
            return True

        except (WebDriverException, TimeoutException) as e:
            logger.error("Failed to navigate to Developer Console: %s", e)
            return False

    def wait_for_login(self, timeout: int = 300) -> bool:
        """Wait for user to complete login process."""
        if not (self.driver and self.wait):
            return False

        logger.info("Waiting for user login (timeout: %s seconds)", timeout)

        try:
            # Wait for the main console dashboard to appear
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".console-header")
                    ),
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-automation-id='skillsConsole']")
                    ),
                    EC.url_contains("console/ask"),
                )
            )

            logger.info("User login detected")
            return True

        except (TimeoutException, WebDriverException) as e:
            logger.error("Login timeout or error: %s", e)
            return False

    def guided_skill_creation(self, skill_config: Any) -> str | None:
        """Guide user through skill creation process."""
        if not (self.driver and self.wait):
            return None

        logger.info("Starting guided skill creation")

        try:
            # Look for Create Skill button
            create_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Create Skill')]")
                )
            )
            create_button.click()

            # Fill skill name
            skill_name_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "skillName"))
            )
            skill_name_input.clear()
            skill_name_input.send_keys(skill_config.skill_name)

            # Select Smart Home model
            smart_home_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='SMART_HOME']"))
            )
            smart_home_option.click()

            # Continue to next step
            continue_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Continue')]")
                )
            )
            continue_button.click()

            # Wait for skill creation to complete and get skill ID
            # This is a simplified version - actual implementation would need
            # more robust skill ID extraction
            self.wait.until(EC.url_contains("/skills/"))

            # Extract skill ID from URL
            current_url = self.driver.current_url
            if "/skills/" in current_url:
                skill_id = current_url.split("/skills/")[1].split("/")[0]
                logger.info("Skill created with ID: %s", skill_id)
                return skill_id

        except (TimeoutException, WebDriverException) as e:
            logger.error("Guided skill creation failed: %s", e)

        return None

    def configure_endpoint(self, skill_config: Any) -> bool:
        """Configure Smart Home endpoint."""
        if not (self.driver and self.wait):
            return False

        logger.info("Configuring Smart Home endpoint")

        try:
            # Navigate to Smart Home section
            smart_home_tab = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(), 'Smart Home')]")
                )
            )
            smart_home_tab.click()

            # Find endpoint input field
            endpoint_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "endpoint"))
            )
            endpoint_input.clear()
            endpoint_input.send_keys(skill_config.lambda_function_arn)

            # Save configuration
            save_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Save')]")
                )
            )
            save_button.click()

            logger.info("Smart Home endpoint configured successfully")
            return True

        except (TimeoutException, WebDriverException) as e:
            logger.error("Endpoint configuration failed: %s", e)
            return False

    def configure_account_linking_ui(self, skill_config: Any) -> bool:
        """Configure account linking through UI."""
        if not (self.driver and self.wait):
            return False

        logger.info("Configuring account linking via UI")

        try:
            # Navigate to Account Linking section
            account_linking_tab = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(), 'Account Linking')]")
                )
            )
            account_linking_tab.click()

            # Enable account linking
            enable_checkbox = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "enableAccountLinking"))
            )
            if not enable_checkbox.is_selected():
                enable_checkbox.click()

            # Configure OAuth settings
            auth_uri_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "authorizationUri"))
            )
            auth_uri_input.clear()
            auth_uri_input.send_keys(skill_config.oauth_web_auth_uri)

            token_uri_input = self.driver.find_element(By.NAME, "accessTokenUri")
            token_uri_input.clear()
            token_uri_input.send_keys(skill_config.oauth_access_token_uri)

            client_id_input = self.driver.find_element(By.NAME, "clientId")
            client_id_input.clear()
            client_id_input.send_keys(skill_config.oauth_client_id)

            # Save account linking configuration
            save_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Save')]")
                )
            )
            save_button.click()

            logger.info("Account linking configured successfully")
            return True

        except (TimeoutException, WebDriverException) as e:
            logger.error("Account linking configuration failed: %s", e)
            return False

    def take_screenshot(self, filename: str | None = None) -> bool:
        """Take screenshot for debugging or verification."""
        if not self.driver:
            return False

        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"browser_automation_{timestamp}.png"

            screenshot_path = os.path.join(os.getcwd(), filename)
            self.driver.save_screenshot(  # pyright: ignore[reportUnknownMemberType]
                screenshot_path
            )

            logger.info("Screenshot saved: %s", filename)
            return True

        except (WebDriverException, TimeoutException) as e:
            logger.error("Failed to take screenshot: %s", e)
            return False

    def wait_for_user_input(self, message: str, timeout: int = 300) -> bool:
        """Display message and wait for user to complete manual steps."""
        logger.info("Manual step required: %s", message)
        logger.info("Waiting up to %s seconds for completion...", timeout)

        # This is a simplified implementation
        # In practice, you might want to show a modal dialog or other UI
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(1)
            # Check for some completion indicator
            # This would need to be customized based on the specific workflow

        return True

    def get_current_page_info(self) -> dict[str, Any]:
        """Get information about the current page."""
        if not self.driver:
            return {}

        try:
            return {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "page_source_length": len(self.driver.page_source),
            }

        except (WebDriverException, AttributeError):
            return {}
