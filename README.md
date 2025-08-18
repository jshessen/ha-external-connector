# Home Assistant External Connector

[![hacs][hacs-badge]][hacs-url]
[![GitHub Release][releases-badge]][releases-url]
[![GitHub License][license-badge]][license-url]

A comprehensive Home Assistant custom integration for managing external Alexa connections and automation workflows.

## Features

- **Alexa Skills Management**: Direct integration with Amazon Alexa Skills Management API (SMAPI)
- **OAuth2 Authentication**: Secure authentication flow with AWS CloudFlare security gateway
- **Browser Mod Integration**: Automated LWA (Login with Amazon) profile management using Browser Mod
- **Smart Home Bridge**: AWS Lambda-based bridge for Alexa smart home commands
- **Configuration Manager**: Centralized configuration management across cloud infrastructure

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/jshessen/ha-external-connector` as an "Integration"
6. Search for "Home Assistant External Connector"
7. Click "Install"
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases-url]
2. Extract the contents to your `custom_components/ha_external_connector` directory
3. Restart Home Assistant

## Configuration

After installation, add the integration through the Home Assistant UI:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Home Assistant External Connector"
4. Follow the configuration wizard

### Prerequisites

- **Browser Mod**: This integration depends on [Browser Mod](https://github.com/thomasloven/hass-browser_mod) for automated browser interactions
- **AWS Account**: Required for cloud infrastructure components (optional for basic functionality)
- **Alexa Developer Account**: Required for SMAPI integration features

## Services

The integration provides several services for automation:

### `ha_external_connector.alexa_oauth_automation`

Automates the Alexa OAuth flow using Browser Mod for seamless authentication.

### `ha_external_connector.smapi_client_management`

Manages Alexa Skills through the SMAPI client for skill deployment and configuration.

## Documentation

- **User Guide**: [Alexa Integration Setup](docs/integrations/alexa/)
- **Developer Documentation**: [Development Setup](docs/development/)
- **Deployment Guide**: [Cloud Infrastructure](docs/deployment/)

## Support

- **Issues**: [GitHub Issues][issues-url]
- **Discussions**: [GitHub Discussions](https://github.com/jshessen/ha-external-connector/discussions)

## Contributing

We welcome contributions! Please see our [Development Workflow Guide](docs/development/DEVELOPMENT_WORKFLOW_GUIDE.md) for details on:

- Development environment setup
- Code quality standards
- Testing requirements
- Contribution guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Quality

This integration maintains high quality standards:

- **Code Quality**: Perfect 10.00/10 Pylint scores
- **Testing**: Comprehensive test suite with >95% coverage
- **Standards Compliance**: Follows Home Assistant development best practices

---

**Maintainer**: [@jshessen](https://github.com/jshessen)

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/custom-components/hacs
[releases-badge]: https://img.shields.io/github/release/jshessen/ha-external-connector.svg
[releases-url]: https://github.com/jshessen/ha-external-connector/releases
[license-badge]: https://img.shields.io/github/license/jshessen/ha-external-connector.svg
[license-url]: https://github.com/jshessen/ha-external-connector/blob/main/LICENSE
[issues-url]: https://github.com/jshessen/ha-external-connector/issues
