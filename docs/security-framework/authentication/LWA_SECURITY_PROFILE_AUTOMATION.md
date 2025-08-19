# LWA Security Profile Browser Automation

## Overview

The LWA (Login with Amazon) Security Profile Browser Automation provides ethical browser
automation for creating and configuring Amazon Developer Console Security Profiles
required for SMAPI access. This component seamlessly integrates with the existing
SMAPITokenHelper to offer users a choice between manual setup and automated assistance.

## Architecture Integration

### Three-Layer Alexa Integration Structure

```text
📊 SMAPI API Layer
├── smapi_token_helper.py          # OAuth 2.0 flow management
├── smapi_client.py               # SMAPI REST API client
└── smapi_automation_enhancer.py  # Ethical hybrid automation

🎮 Skill Management Layer
├── skill_definition_manager.py   # Skill configuration management
├── skill_automation_manager.py   # Skill lifecycle automation
└── amazon_developer_console.py   # Console integration

⚡ Lambda Functions Layer
├── cloudflare_security_gateway.py  # OAuth + Authentication
├── smart_home_bridge.py            # Device control + Discovery
└── configuration_manager.py        # Shared configuration

🌐 Browser Automation Layer (NEW)
├── browser_automation.py              # Selenium WebDriver foundation
├── lwa_security_profile_automation.py # Security Profile automation
└── console_automation.py              # General console operations

```

### Integration Flow

1. **User starts SMAPI token setup**: `python -m ha_connector.integrations.alexa.smapi_token_helper`
2. **Automation choice offered**: User chooses between manual or automated
   Security Profile creation
3. **Browser automation activated**: Selenium WebDriver opens visible browser
4. **Ethical form automation**: Forms filled automatically, user stays in control
5. **User approval workflow**: User reviews and saves when ready
6. **Return to OAuth flow**: SMAPITokenHelper continues with standard OAuth process

## Ethical Automation Principles

### User Control First

- **Visible browser**: Never runs headless by default for user oversight

- **User approvals**: User clicks 'Save' buttons after reviewing automated forms

- #### Manual fallback: Always falls back to manual guidance if automation fails

- **Clear feedback**: Rich console output explaining each automation step

### Form Automation Balance

- **Automate tedious work**: Pre-fill lengthy forms with correct SMAPI-compatible values

- **Preserve decision making**: User reviews all settings before saving

- **Error recovery**: Graceful fallback to manual guidance on any automation failure

- #### Screenshot capture: Debugging and verification support

## Usage Patterns

### Integrated with SMAPITokenHelper (Recommended)

```python
# User experience with integrated automation
python -m ha_connector.integrations.alexa.smapi_token_helper

# Console output:
# 🤖 Would you like me to help automate the Security Profile creation process?
# (I'll open a browser and fill forms for you, but you stay in control)
# [Y/n]: y
#
# 🌐 Starting browser automation...
# 🔐 Please log in to your Amazon Developer account...
# ➕ Navigating to Security Profile creation...
# 📝 Filling Security Profile form...
# 👀 Please review the form and click 'Save' when ready...
# ⚙️ Configuring web settings...
# 📝 Filled redirect URIs:
#   • http://127.0.0.1:9090/cb
#   • https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html
# 👀 Please review the settings and click 'Save' when ready...
# ✅ Browser automation completed successfully!

```

### Direct Component Usage (Advanced)

```python
from ha_connector.integrations.alexa.lwa_security_profile_automation import (
    LWASecurityProfileAutomation,
    automate_security_profile_creation
)

# Method 1: Context manager approach (full automation)
with LWASecurityProfileAutomation(headless=False) as automation:
    result = automation.guide_security_profile_creation()

# Method 2: Integration function (used by SMAPITokenHelper)
result = automate_security_profile_creation(headless=False)

# Method 3: Step-by-step testing/demo (public API)
with LWASecurityProfileAutomation(headless=False) as automation:
    # Check browser status
    status = automation.get_browser_status()
    print(f"Browser status: {status['status']}")

    # Navigate to LWA Console
    if automation.navigate_to_lwa_console():
        print("Successfully navigated to LWA Console")

        # Take screenshot for verification
        automation.take_screenshot("lwa_console.png")

        # Get current page info
        status = automation.get_browser_status()
        print(f"Current URL: {status.get('current_url')}")
```

### Demo and Testing

```bash
# Demo the automation capabilities
python scripts/demo_lwa_automation.py

# Demo with headless mode (for CI/testing)
python scripts/demo_lwa_automation.py --headless
```

## Public API Methods

The `LWASecurityProfileAutomation` class provides the following public methods for
testing, debugging, and integration:

### Core Automation

- **`guide_security_profile_creation()`** - Complete automated workflow for
  Security Profile creation
- **`navigate_to_lwa_console()`** - Navigate to Amazon LWA Console (for testing/demo)

### Status and Debugging

- **`get_browser_status()`** - Get current browser status and page information
- **`take_screenshot(filename=None)`** - Capture screenshot for debugging/verification

### Context Manager Support

- **`__enter__()` / `__exit__()`** - Context manager for automatic resource cleanup

Example usage:

```python
with LWASecurityProfileAutomation() as automation:
    # Check if browser is ready
    status = automation.get_browser_status()
    if status['driver_available']:
        # Navigate and take screenshot
        automation.navigate_to_lwa_console()
        automation.take_screenshot("debug.png")
```

## Technical Implementation

### Selenium WebDriver Integration

The automation uses the established `BrowserAutomationDriver` patterns for consistency:

- **Chrome WebDriver**: Optimized configuration for Amazon Developer Console

- **Anti-detection**: Minimizes automated browser detection

- **Error handling**: Robust timeout and exception management

- **Screenshot support**: Debugging and verification capabilities

### Form Field Automation

The automation fills Security Profile forms with SMAPI-compatible values:

```python
# Default values optimized for Home Assistant integration
DEFAULT_PROFILE_NAME = "Home Assistant SMAPI Integration"
DEFAULT_PROFILE_DESCRIPTION = "SMAPI access for Home Assistant skill automation"
DEFAULT_PRIVACY_URL = "https://www.home-assistant.io/privacy/"

# Required redirect URIs for SMAPI compatibility
REQUIRED_REDIRECT_URIS = [
    "http://127.0.0.1:9090/cb",
    "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html",
]

```

### Error Recovery Strategy

- **Import failure**: Graceful fallback to manual guidance if Selenium not available

- **Navigation errors**: Retry mechanisms with user guidance

- **Form detection**: Multiple selector strategies for robust element finding

- **Timeout handling**: Clear user messages with manual continuation options

## Integration Benefits

### For Users

- **Reduced complexity**: Automated form-filling eliminates tedious manual work

- **Error prevention**: Correct SMAPI-compatible values pre-filled automatically

- **Maintained control**: User reviews and approves all automated actions

- **Faster setup**: Streamlined workflow from browser automation to OAuth completion

### For Developers

- **Consistent patterns**: Uses established Selenium WebDriver foundation

- **Ethical design**: Transparent automation with user oversight

- **Modular integration**: Clean separation between automation and core SMAPI logic

- **Extensible framework**: Foundation for additional Developer Console automations

### For System Architecture

- **Browser automation layer**: Complements existing SMAPI/Skill/Lambda structure

- **Ethical hybrid approach**: Balances efficiency with user agency

- **Four-path strategy**: Documentation → API → Browser → User choice

- **Future extensibility**: Framework for automating other Developer Console workflows

## Future Extensions

The browser automation foundation enables additional Developer Console automations:

- **Skill creation automation**: Extend to Smart Home skill setup

- **Endpoint configuration**: Automate Lambda function ARN configuration

- **Account linking setup**: Browser-based OAuth configuration

- **Testing workflow**: Automated skill testing and validation

## Configuration

### Browser Settings

```python
# Visible browser (default for user oversight)
automation = LWASecurityProfileAutomation(headless=False)

# Headless mode (for CI/testing environments)
automation = LWASecurityProfileAutomation(headless=True)

```

### Chrome Options

The automation uses optimized Chrome WebDriver settings:

```python
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

```

### Anti-Detection

Browser fingerprinting minimization:

```python
driver.execute_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)

```

## Security Considerations

### User Authentication

- **No credential storage**: Automation never stores Amazon account credentials

- **Browser session**: Uses normal browser login for authentic user session

- **Session scope**: Automation operates within user's existing Amazon session

### Form Data Handling

- **Standard values**: Only fills forms with documented, public configuration values

- **No sensitive data**: Never handles Client ID/Secret extraction automatically

- **User verification**: All form data visible to user for review before saving

### Network Security

- **HTTPS only**: All Amazon Developer Console interactions over encrypted connections

- **No proxy**: Direct browser connections without interception

- **Session integrity**: Maintains normal browser security features

## Troubleshooting

### Common Issues

#### ImportError: Selenium not available

```python
# Solution: Install selenium dependency
pip install selenium

```

#### WebDriverException: Chrome not found

```python
# Solution: Install ChromeDriver
# On Ubuntu: sudo apt-get install chromium-chromedriver
# On macOS: brew install chromedriver
# On Windows: Download from https://chromedriver.chromium.org/

```

#### TimeoutException: Login timeout

```python
# Solution: User needs to log in within 300 seconds
# Increase timeout if needed in _wait_for_user_login()

```

### Debugging Support

#### Screenshot capture for debugging

```python
automation.take_screenshot("debug_state.png")

```

#### Verbose logging

```python
import logging
logging.getLogger("ha_connector").setLevel(logging.DEBUG)

```

#### Manual fallback testing

```python
# Test manual guidance workflow
# Set automation choice to 'No' when prompted

```

## References

- [Amazon Login with Amazon Console](https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html)
- [SMAPI Authentication Documentation](https://developer.amazon.com/en-US/docs/alexa/smapi/skill-management-api-rest.html#authentication)
- [Selenium WebDriver Documentation](https://selenium-python.readthedocs.io/)
- [Home Assistant Privacy Policy](https://www.home-assistant.io/privacy/)

---

*This automation component follows the project's ethical automation principles: enhance user
efficiency while preserving user control and decision-making authority.*
