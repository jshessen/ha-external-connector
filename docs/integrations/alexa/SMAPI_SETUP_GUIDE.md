# 🎯 SMAPI Setup Guide - HACS Pattern Implementation

## Overview

This guide demonstrates the **HACS-pattern guided setup** for Amazon's Skill
Management API (SMAPI) integration, following Login with Amazon OAuth 2.0
Authorization Code Grant flow.

## 🚀 What We've Built

### 1. Comprehensive SMAPI Setup Wizard (`smapi_setup_wizard.py`)

**Features:**

- **Rich CLI Interface**: Interactive terminal experience with progress indicators
- **Step-by-Step Guidance**: HACS-pattern user experience
- **OAuth 2.0 Flow**: Proper Authorization Code Grant implementation
- **Secure Token Management**: Automatic refresh capabilities
- **Error Handling**: Comprehensive validation and user feedback

**Key Components:**

```python
@dataclass
class LWASecurityProfile:
    """Login with Amazon Security Profile configuration"""
    client_id: str
    client_secret: str

@dataclass
class SMAPITokens:
    """SMAPI OAuth tokens with refresh capability"""
    access_token: str
    refresh_token: str
    expires_at: datetime
```

### 2. Enhanced Web Interface (`amazon_console.py`)

**HACS-Pattern Endpoints:**

- `/amazon-console/smapi/wizard/start` - Initialize guided setup
- `/amazon-console/smapi/wizard/security-profile` - Configure OAuth credentials
- `/amazon-console/smapi/wizard/authorize` - Handle OAuth authorization
- `/amazon-console/smapi/wizard/callback` - Process OAuth callback
- `/amazon-console/smapi/wizard/status` - Check setup progress

**User Experience:**

- Browser-based guided setup
- Real-time validation feedback
- Secure credential handling
- Progress tracking and status updates

## 🎯 HACS Pattern Implementation

### User-Friendly Guidance

Following Home Assistant Community Store patterns for intuitive setup:

1. **Clear Step Progression**: Users know exactly where they are in the process
2. **Visual Feedback**: Rich CLI with progress bars and status indicators
3. **Error Recovery**: Helpful error messages with suggested solutions
4. **Secure Defaults**: Safe credential handling and storage

### CLI Usage Example

```bash
# Interactive guided setup
python -m ha_connector.integrations.alexa.smapi_setup_wizard

# Quick status check
python scripts/agent_helper.py setup
```

### Web Interface Usage

```python
from ha_connector.web.amazon_console import amazon_console_bp
from flask import Flask

app = Flask(__name__)
app.register_blueprint(amazon_console_bp)
```

## 🔐 OAuth 2.0 Authorization Code Grant Flow

### Implementation Details

1. **Security Profile Setup**: User provides Client ID and Client Secret
2. **Authorization URL Generation**: CSRF-protected authorization request
3. **User Authorization**: Redirect to Amazon's OAuth endpoint
4. **Callback Handling**: Exchange authorization code for tokens
5. **Token Management**: Automatic refresh and secure storage

### Security Features

- **CSRF Protection**: State parameter validation
- **Secure Storage**: Environment variable management
- **Token Refresh**: Automatic token renewal
- **Input Validation**: Comprehensive credential validation

## 🏗️ Integration Architecture

### Hybrid Approach

The implementation provides both CLI and web interfaces for maximum flexibility:

**CLI Interface:**

- Perfect for developers and automation
- Rich terminal experience with colors and progress
- Direct integration with existing CLI commands

**Web Interface:**

- User-friendly browser experience
- RESTful API endpoints
- Integration with existing web infrastructure

### Code Organization

```tree
src/ha_connector/integrations/alexa/
├── smapi_setup_wizard.py          # CLI wizard implementation
└── lambda_functions/
    ├── cloudflare_security_gateway.py
    └── smart_home_bridge.py

src/ha_connector/web/
└── amazon_console.py               # Web interface endpoints
```

## 🎯 Next Steps

### Immediate Capabilities

✅ **Complete OAuth Setup**: Both CLI and web interfaces ready
✅ **Token Management**: Automatic refresh and secure storage
✅ **User Guidance**: HACS-pattern step-by-step experience
✅ **Integration Ready**: Works with existing Amazon Console automation

### Future Enhancements

- **Skill Templates**: Pre-configured skill templates for common use cases
- **Automated Testing**: Integration test suites for OAuth flow
- **Monitoring**: Setup progress tracking and health checks
- **Documentation**: Interactive tutorials and troubleshooting guides

## 🚀 Technical Achievements

This implementation successfully addresses the original request:

> "help guide a user to setup their ID, but also to enable the user to empower this automation to help build this on their behalf"

**Key Success Factors:**

1. **HACS Pattern Compliance**: Follows established Home Assistant patterns
2. **Hybrid Implementation**: Supports both CLI and web workflows
3. **Security Best Practices**: Proper OAuth 2.0 implementation
4. **User Experience**: Guided setup with clear feedback
5. **Integration Ready**: Works with existing automation infrastructure

The setup wizard empowers users to configure their Amazon Developer Console credentials while providing the automation framework to build skills on their behalf.
