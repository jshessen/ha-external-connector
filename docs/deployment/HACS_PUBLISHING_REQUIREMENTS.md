# HACS Publishing Requirements

## 🚀 Complete Guide to Publishing Home Assistant Integration via HACS

### Overview

This document provides comprehensive requirements for publishing the **HA External Connector** integration to HACS (Home Assistant Community Store), ensuring proper container compatibility and professional deployment.

## 📋 Repository Structure Requirements

### ✅ MANDATORY Structure

```text
ROOT_OF_REPO/
├── custom_components/
│   └── ha_external_connector/           # MUST be single integration
│       ├── __init__.py                  # Integration entry point
│       ├── manifest.json                # MANDATORY manifest
│       ├── config_flow.py               # Configuration flow
│       ├── const.py                     # Constants
│       ├── browser_mod_lwa_assistant.py # Browser Mod LWA assistant
│       └── ...                          # Other integration files
├── README.md                            # MANDATORY repository documentation
├── hacs.json                            # MANDATORY HACS manifest
└── ...                                  # Other project files
```

### ❌ INVALID Structures

```text
# WRONG: No custom_components wrapper
ha_external_connector/
├── __init__.py
├── manifest.json
└── ...

# WRONG: Multiple integrations
custom_components/
├── integration_one/
└── integration_two/
```

### 🔧 Key Rules

- **Single Integration**: Only ONE subdirectory allowed in `custom_components/`
- **All Files Inside**: ALL integration files must be in `custom_components/INTEGRATION_NAME/`
- **No Root Content**: Unless `content_in_root: true` in `hacs.json`

## 📄 Required Files

### 1. `manifest.json` (MANDATORY)

Location: `custom_components/ha_external_connector/manifest.json`

```json
{
  "domain": "ha_external_connector",
  "name": "Home Assistant External Connector",
  "version": "1.0.0",
  "documentation": "https://github.com/jshessen/ha-external-connector",
  "issue_tracker": "https://github.com/jshessen/ha-external-connector/issues",
  "codeowners": ["@jshessen"],
  "dependencies": [],
  "requirements": [],
  "config_flow": true,
  "iot_class": "cloud_polling"
}
```

**Required Keys:**

- `domain` - Integration domain name
- `name` - Display name
- `version` - Current version
- `documentation` - Documentation URL
- `issue_tracker` - Issues URL
- `codeowners` - GitHub usernames with @

### 2. `hacs.json` (MANDATORY)

Location: `ROOT_OF_REPO/hacs.json`

```json
{
  "name": "Home Assistant External Connector",
  "homeassistant": "2024.1.0",
  "hacs": "1.30.0"
}
```

**Optional Keys:**

- `content_in_root` - Set to `true` if content is in repository root
- `zip_release` - For zipped releases (integrations only)
- `filename` - Specific file name for single items
- `hide_default_branch` - Hide default branch download option
- `country` - ISO 3166-1 alpha-2 country codes
- `persistent_directory` - Safe directory during upgrades

### 3. `README.md` (MANDATORY)

Must include:

- Clear description of integration purpose
- Installation instructions
- Configuration guide
- Usage examples
- Browser Mod dependency requirements

## 🏷️ GitHub Repository Requirements

### Repository Settings

1. **Description**: Clear, concise repository description
2. **Topics**: GitHub topics for searchability
3. **Public Repository**: Must be public (private repos not supported)
4. **Releases**: Optional but recommended for versioning

### Example Topics

```text
home-assistant
hacs
integration
alexa
browser-mod
automation
```

## 🔧 Browser Mod Integration Considerations

### Dependencies Declaration

In `manifest.json`, declare Browser Mod dependency:

```json
{
  "dependencies": ["browser_mod"],
  "requirements": []
}
```

### Documentation Requirements

Must document Browser Mod requirement:

```markdown
## Prerequisites

This integration requires:
- Home Assistant 2024.1.0+
- Browser Mod integration installed via HACS
- Web browser with Home Assistant frontend access
```

## 🎯 Home Assistant Brands Registration

### MANDATORY Step

Must add integration to [home-assistant/brands](https://github.com/home-assistant/brands) repository:

1. Fork `home-assistant/brands`
2. Add integration icon and metadata
3. Submit pull request
4. Wait for approval before HACS submission

### Brand Structure

```text
custom_integrations/ha_external_connector/
├── icon.png          # 256x256 PNG icon
└── icon@2x.png       # 512x512 PNG icon (optional)
```

## 📦 Version Management

### GitHub Releases (Recommended)

- Create GitHub releases for version tracking
- HACS presents 5 latest releases + default branch
- Use semantic versioning (e.g., `v1.0.0`)

### Without Releases

- HACS uses 7-character commit SHA
- Less user-friendly version display

## 🚀 Container Compatibility

### Browser Mod Benefits

✅ **HACS-Compatible Architecture:**

- No external dependencies (Chrome driver, Selenium)
- Pure Home Assistant integration
- Native browser control via Browser Mod services
- Container-friendly deployment

❌ **Avoided Selenium Issues:**

- External Chrome driver installation
- System-level dependencies
- Container permission complexities
- Port exposure requirements

## 📝 Submission Process

### 1. Pre-Submission Checklist

- [ ] Repository structure follows HACS requirements
- [ ] `manifest.json` includes all required keys
- [ ] `hacs.json` created with proper configuration
- [ ] README.md comprehensive and clear
- [ ] GitHub repository has description and topics
- [ ] Integration added to Home Assistant Brands
- [ ] Browser Mod dependency documented
- [ ] Local testing completed

### 2. HACS Submission

1. **Add as Custom Repository**: Test installation first
2. **Submit to Default Store**: Follow HACS submission process
3. **Wait for Review**: HACS team reviews submission
4. **Address Feedback**: Make requested changes
5. **Publication**: Integration appears in HACS store

### 3. Post-Publication

- Monitor issues and user feedback
- Maintain compatibility with HA updates
- Update Browser Mod integration as needed
- Keep documentation current

## 🔍 Quality Standards

### Code Quality

- All Python code must pass Ruff, Pylint, MyPy checks
- Comprehensive test coverage
- Error handling and logging
- Type annotations

### Documentation Quality

- Clear installation instructions
- Configuration examples
- Troubleshooting guide
- Browser Mod setup requirements

### User Experience

- Intuitive configuration flow
- Clear error messages
- Helpful logging
- Browser Mod service examples

## 🎯 Success Metrics

### Technical Validation

- [ ] HACS installation successful
- [ ] Integration loads without errors
- [ ] Browser Mod services work correctly
- [ ] Configuration flow completes
- [ ] No Home Assistant log errors

### User Experience Validation

- [ ] Clear setup instructions
- [ ] Intuitive configuration
- [ ] Reliable Browser Mod integration
- [ ] Helpful error messages
- [ ] Good documentation

## 📚 Reference Resources

### Official Documentation

- [HACS Integration Publishing](https://hacs.xyz/docs/publish/integration/)
- [HACS General Requirements](https://hacs.xyz/docs/publish/start/)
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Home Assistant Brands](https://github.com/home-assistant/brands)

### Templates and Examples

- [Blueprint Integration Template](https://github.com/custom-components/blueprint)
- [Cookiecutter HA Custom Component](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component)
- [Browser Mod Integration](https://github.com/thomasloven/hass-browser_mod)

### Community Support

- [HACS Discord Server](https://discord.gg/apgchf8)
- [Home Assistant Community](https://community.home-assistant.io/)
- [HACS GitHub Issues](https://github.com/hacs/integration/issues)

---

## 🎉 Deployment Roadmap

1. **Phase 1**: Restructure repository for HACS compatibility
2. **Phase 2**: Create required HACS manifest files
3. **Phase 3**: Submit to Home Assistant Brands
4. **Phase 4**: Local testing with Browser Mod integration
5. **Phase 5**: Submit to HACS as custom repository
6. **Phase 6**: Submit for inclusion in default HACS store
7. **Phase 7**: Community adoption and feedback integration

This comprehensive approach ensures successful HACS publication while leveraging Browser Mod's native Home Assistant integration capabilities for optimal container compatibility.
