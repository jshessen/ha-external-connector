# Home Assistant External Connector

[![hacs][hacs-badge]][hacs-url]
[![GitHub Release][releases-badge]][releases-url]
[![GitHub License][license-badge]][license-url]

Professional automation and integration system for Home Assistant with external services including Alexa, CloudFlare, and AWS infrastructure.

## 🚀 Quick Start

### For Users

- **[Alexa Integration Setup](docs/integrations/alexa/USER_GUIDE.md)** - Set up voice commands with Home Assistant
- **[SMAPI Configuration](docs/integrations/alexa/SMAPI_SETUP_GUIDE.md)** - Configure Alexa Smart Home API
- **[Performance Optimization](docs/integrations/alexa/PERFORMANCE_OPTIMIZATION.md)** - Optimize response times

### For Developers

- **[Development Setup](docs/development/AUTOMATION_SETUP.md)** - Environment and tooling setup
- **[Code Quality Standards](docs/development/CODE_QUALITY_SUITE.md)** - Linting and quality requirements
- **[Configuration Management](docs/development/CONFIGURATION_MANAGEMENT.md)** - System configuration patterns

### For Operations

- **[Deployment Guide](docs/deployment/DEPLOYMENT_QUICK_REFERENCE.md)** - Infrastructure deployment
- **[Security Validation](docs/deployment/security_validation_guide.md)** - Security compliance checks

## 🎯 Key Features

- **Voice Command Integration**: Seamless Alexa voice control for Home Assistant
- **Security-First Design**: Comprehensive validation and secure deployment patterns  
- **High Performance**: Sub-500ms response times with intelligent caching
- **Professional Tooling**: Full automation suite with quality gates
- **HACS Ready**: Prepared for Home Assistant Community Store publication

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

## 📚 Documentation

Complete documentation is organized by audience in the [`docs/`](docs/) directory:

- **[Integration Guides](docs/integrations/)** - User-focused setup and configuration
- **[Development Resources](docs/development/)** - Developer tools and standards
- **[Deployment Procedures](docs/deployment/)** - Operations and infrastructure
- **[Project History](docs/history/)** - Evolution and architectural decisions

## 🔧 Technology Stack

- **Python 3.11+** with modern async/await patterns
- **AWS Lambda** for serverless voice command processing
- **CloudFlare** for OAuth security gateway
- **Pydantic** for type-safe configuration management
- **Comprehensive Quality Suite** (Ruff, Pylint, MyPy, Bandit, Black)

## 🏆 Project Status

This project represents a complete evolution from CLI tool to professional Home Assistant integration, with full HACS readiness and community-focused development practices.

**Current Phase**: Professional integration with comprehensive documentation, security validation, and performance optimization.

**Next Phase**: HACS publication preparation and community release.

## 🤝 Contributing

We welcome contributions! Please see our [development documentation](docs/development/) for detailed setup instructions, coding standards, and contribution guidelines.

## Quality

This integration maintains high quality standards:

- **Code Quality**: Perfect 10.00/10 Pylint scores
- **Testing**: Comprehensive test suite with >95% coverage
- **Standards Compliance**: Follows Home Assistant development best practices

## Support

- **Issues**: [GitHub Issues][issues-url]
- **Discussions**: [GitHub Discussions](https://github.com/jshessen/ha-external-connector/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Maintainer**: [@jshessen](https://github.com/jshessen)

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/custom-components/hacs
[releases-badge]: https://img.shields.io/github/release/jshessen/ha-external-connector.svg
[releases-url]: https://github.com/jshessen/ha-external-connector/releases
[license-badge]: https://img.shields.io/github/license/jshessen/ha-external-connector.svg
[license-url]: https://github.com/jshessen/ha-external-connector/blob/main/LICENSE
[issues-url]: https://github.com/jshessen/ha-external-connector/issues
