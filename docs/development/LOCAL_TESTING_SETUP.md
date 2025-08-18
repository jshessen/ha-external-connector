# Local Testing Setup for Browser Mod Integration

## 🚀 Development Environment Options

Based on the Home Assistant development documentation, we have multiple approaches for local testing of our Browser Mod integration:

### Option 1: VSCode Devcontainer (Recommended)

**Advantages:**

- Pre-configured Home Assistant development environment
- Automatic dependency management
- Integrated debugging with F5 launch
- Browser Mod can be installed directly

**Setup:**

```bash
# Clone HA core repository alongside our project
cd ~/Development/GitHub
git clone https://github.com/home-assistant/core.git ha-core

# Open in VSCode with devcontainer
code ha-core
# VSCode will prompt to reopen in container
```

**Browser Mod Installation in Devcontainer:**

```bash
# Inside devcontainer
cd config/custom_components
git clone https://github.com/thomasloven/hass-browser_mod.git browser_mod
```

### Option 2: Manual Local Setup (Alternative)

**Prerequisites:**

- Python 3.13+ (✅ Already have 3.13.6)
- Home Assistant Core
- Browser Mod custom component

**Setup:**

```bash
# Create separate HA development instance
mkdir ~/Development/ha-dev-instance
cd ~/Development/ha-dev-instance

# Create virtual environment for HA
python -m venv ha-venv
source ha-venv/bin/activate

# Install Home Assistant
pip install homeassistant

# Initialize HA configuration
hass --config . --script ensure_config
```

## 🧪 Browser Mod Testing Strategy

### Phase 1: Basic Browser Mod Validation

#### 1. Install Browser Mod in Test Environment

```bash
# In HA config directory
mkdir -p custom_components
cd custom_components
git clone https://github.com/thomasloven/hass-browser_mod.git browser_mod
```

#### 2. Test Basic Browser Mod Services

Create test script for our project:

```python
# scripts/test_browser_mod_local.py
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

async def test_browser_mod_services():
    """Test Browser Mod services in local HA instance."""
    hass = HomeAssistant()

    # Setup Browser Mod component
    await async_setup_component(hass, "browser_mod", {})

    # Test service calls
    services = [
        "browser_mod.popup",
        "browser_mod.navigate",
        "browser_mod.notification",
        "browser_mod.javascript"
    ]

    for service in services:
        print(f"✅ Testing {service}")
        # Test service availability
        assert hass.services.has_service("browser_mod", service.split(".")[1])
```

### Phase 2: Integration Testing

#### 1. Create Test Configuration

```yaml
# config/configuration.yaml
browser_mod:
  devices:
    test_browser:
      name: "Test Browser"

automation:
  - alias: "Test LWA Browser Mod"
    trigger:
      platform: event
      event_type: test_lwa_automation
    action:
      - service: browser_mod.popup
        data:
          title: "LWA Setup"
          content: |
            <ha-card>
              <div class="card-content">
                <h3>Amazon LWA Security Profile Setup</h3>
                <p>This will guide you through creating your LWA Security Profile.</p>
              </div>
            </ha-card>
```

#### 2. Test Our Browser Mod Integration

```bash
# Copy our Browser Mod files to HA custom components
cp src/ha_connector/integrations/alexa/browser_mod_lwa_*.py ~/Development/ha-dev-instance/custom_components/ha_connector/

# Start HA with our integration
cd ~/Development/ha-dev-instance
source ha-venv/bin/activate
hass --config . --verbose
```

### Phase 3: Development Workflow

#### 1. Live Development Setup

```bash
# Create symlink for live editing
cd ~/Development/ha-dev-instance/custom_components
ln -sf ~/Development/GitHub/ha-external-connector/src/ha_connector ha_connector

# Now edits in our main project reflect immediately in HA
```

#### 2. Debugging Browser Mod Integration

```python
# Add to our Browser Mod assistant for local testing
class BrowserModLWAAssistant:
    def __init__(self, hass: HomeAssistant, debug_mode: bool = False):
        self.hass = hass
        self.debug_mode = debug_mode
        self.logger = HAConnectorLogger(__name__)

    async def debug_service_availability(self):
        """Debug Browser Mod service availability."""
        if self.debug_mode:
            services = self.hass.services.async_services()
            browser_mod_services = services.get("browser_mod", {})
            self.logger.info(f"Available Browser Mod services: {list(browser_mod_services.keys())}")
```

## 🔄 Testing Workflows

### Workflow 1: Rapid Iteration Testing

```bash
# Terminal 1: Run HA with live reload
cd ~/Development/ha-dev-instance
source ha-venv/bin/activate
hass --config . --verbose

# Terminal 2: Edit and test our integration
cd ~/Development/GitHub/ha-external-connector
source .venv/bin/activate

# Edit Browser Mod files
code src/ha_connector/integrations/alexa/browser_mod_lwa_assistant.py

# Test changes (HA picks up changes via symlink)
# Use HA Developer Tools -> Services to test browser_mod calls
```

### Workflow 2: Automated Testing

```bash
# Create test suite for Browser Mod integration
# tests/integration/test_browser_mod_integration.py

import pytest
from homeassistant.core import HomeAssistant
from custom_components.ha_connector.integrations.alexa.browser_mod_lwa_assistant import BrowserModLWAAssistant

@pytest.mark.asyncio
async def test_browser_mod_services(hass: HomeAssistant):
    """Test Browser Mod services are available."""
    assistant = BrowserModLWAAssistant(hass)

    # Test service availability
    available = await assistant.check_browser_mod_availability()
    assert available is True

    # Test popup service
    result = await assistant.show_setup_popup()
    assert result is True
```

### Workflow 3: Browser Testing

**Frontend Testing:**

1. Open HA web interface: `http://localhost:8123`
2. Navigate to Developer Tools -> Services
3. Test Browser Mod services manually:
   - `browser_mod.popup` with our LWA content
   - `browser_mod.navigate` to Amazon LWA pages
   - `browser_mod.javascript` for form automation

**User Experience Testing:**

1. Trigger our LWA automation from HA
2. Verify popup appears correctly
3. Test navigation to Amazon LWA
4. Validate form interactions
5. Confirm credential collection

## 🎯 Success Criteria

### Phase 1 Complete

- [ ] Browser Mod services available in local HA
- [ ] Basic popup/navigate/notification working
- [ ] No dependency conflicts with our project

### Phase 2 Complete

- [ ] Our Browser Mod assistant integrates cleanly
- [ ] LWA popup workflow functional
- [ ] Navigation to Amazon LWA working
- [ ] Form automation successful

### Phase 3 Complete

- [ ] Complete LWA workflow tested end-to-end
- [ ] No external dependencies required
- [ ] Ready for HACS packaging
- [ ] User experience validated

## 🔧 Development Velocity Optimization

**Quick Testing Loop:**

1. Edit Browser Mod integration files
2. Reload HA configuration (or use symlink for instant changes)
3. Test via HA Developer Tools
4. Validate in browser
5. Iterate rapidly

**Debugging Tools:**

- HA logs: `config/home-assistant.log`
- Browser console for frontend issues
- Our logger with debug mode enabled
- VSCode debugging with F5 launch (devcontainer)

**Performance Testing:**

- Monitor HA startup time with our integration
- Test Browser Mod service response times
- Validate memory usage
- Ensure no blocking operations

This setup gives us the flexibility to rapidly develop and test our Browser Mod integration while maintaining development velocity!

## 📦 Next Steps: HACS Publishing

Once local testing is successful, review the [HACS Publishing Requirements](../deployment/HACS_PUBLISHING_REQUIREMENTS.md) for:

- Repository structure requirements
- Manifest file creation
- Home Assistant Brands registration
- HACS submission process
- Container compatibility validation

The Browser Mod approach eliminates external dependencies and provides a clean path to HACS publication!
