# Lambda Functions Patterns

## Overview

This instruction file documents the specialized patterns and standards for Lambda function
development in the `src/ha_connector/integrations/alexa/lambda_functions/` directory.
These patterns ensure optimal performance, deployment independence, and maintainable code
architecture.

## Standardized Deployment Markers System

### Visual Bracket Markers

All Lambda functions use a standardized visual marker system for automated deployment:

```python
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
import configparser
import json
import logging
# ... other imports

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import (
    AlexaValidator,
    RateLimiter,
    SecurityValidator,
    # ... other shared imports
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯

# ╭─────────────────── FUNCTION_BLOCK_START ───────────────────╮

# === LOGGING CONFIGURATION ===

def _initialize_logging() -> logging.Logger:
    """🔧 LOGGING INITIALIZER: Setup Smart Logging System"""
    # Function implementation
    pass

# ... all function implementations

# ╰─────────────────── FUNCTION_BLOCK_END ───────────────────╯
```

### Required Marker Elements

**✅ MANDATORY COMPONENTS:**

1. **Visual Brackets**: Use Unicode box-drawing characters `╭`, `╮`, `╰`, `╯`
2. **Block Identifiers**: `IMPORT_BLOCK_START/END` and `FUNCTION_BLOCK_START/END`
3. **Shared Import Identification**: `# === SHARED CONFIGURATION IMPORTS ===`
4. **Development Comment**:
   `# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment`

**🔧 VALIDATION INTEGRATION:**

The marker system is validated by `scripts/validate_lambda_markers.py`:

```bash
python scripts/validate_lambda_markers.py
# ✅ Validates all 4 Lambda functions
# ✅ Checks marker presence and formatting
# ✅ Demonstrates content extraction capabilities
```

## Dual Mode Architecture

### Development Mode vs Deployment Mode

**🔧 DEVELOPMENT MODE** (src/ha_connector/integrations/alexa/lambda_functions/):

- Import shared code from `shared_configuration.py`
- Fast iteration and testing
- Single source of truth for shared implementations
- Easy debugging with proper stack traces

**🚀 DEPLOYMENT MODE** (infrastructure/deployment/):

- Standalone Lambda function files
- Shared code embedded directly into each function
- No external dependencies in production
- Optimal AWS Lambda performance

### Deployment Script Integration

The `scripts/deploy_shared_config.py` handles the transformation:

```python
# Automatically extracts content between markers
# Replaces shared imports with embedded implementations
# Generates standalone deployment files
# Maintains identical functionality across modes
```

**Usage Examples:**

```bash
# Development/testing mode
python scripts/deploy_shared_config.py --mode development

# Production deployment mode
python scripts/deploy_shared_config.py --mode deployment

# Validation of synchronization
python scripts/deploy_shared_config.py --validate
```

## Transfer Block System for Strategic Code Duplication

### Performance-Critical Code Duplication

**🔄 INTENTIONAL DUPLICATION STRATEGY:**

Lambda functions maintain strategic duplicate code using transfer blocks for optimal performance
and deployment independence.

### Transfer Block Markers

```python
# ╭─────────────────── TRANSFER BLOCK START ───────────────────╮
# ║                    🚀 TRANSFER-READY CODE 🚀                ║
# ║ 📋 PURPOSE: Speed-optimized configuration for <500ms response ║
# ║ 🔄 STATUS: Ready for duplication across Lambda functions     ║
# ║ ⚡ PERFORMANCE: Container 0-1ms | Shared 20-50ms | SSM 100-200ms ║
# ║                                                              ║
# ║ 🎯 USAGE PATTERN:                                            ║
# ║   1. Copy entire block between START and END markers        ║
# ║   2. Update function prefixes (e.g., _oauth_ → _bridge_)     ║
# ║   3. Adjust cache keys and service identifiers              ║
# ║   4. Maintain identical core functionality                  ║
# ╚═════════════════════════════════════════════════════════════╝

def load_standardized_configuration(...):
    """Speed-optimized configuration loading with 3-tier caching."""
    # Core performance-critical implementation
    pass

# ╭─────────────────── TRANSFER BLOCK END ───────────────────╮
```

### Transfer Block Synchronization Workflow

**🔧 SYNCHRONIZATION PROCESS:**

1. **Edit Primary Source** (typically `cloudflare_security_gateway.py`)
2. **Copy Transfer Block Content** (between START/END markers)
3. **Update Target Location** (e.g., `smart_home_bridge.py`)
4. **Apply Service Customizations**:
   - Cache prefixes: `oauth_config_` → `bridge_config_`
   - Function names: `"cloudflare_security_gateway"` → `"smart_home_bridge"`
   - Service-specific constants and identifiers
5. **Test Both Functions** independently after synchronization

### When to Use Transfer Blocks vs Shared Imports

**✅ USE TRANSFER BLOCKS FOR:**

- Performance-critical configuration loading
- Voice command processing (<500ms requirement)
- Container-level caching optimizations
- Service-specific authentication flows

**✅ USE SHARED IMPORTS FOR:**

- Utility functions and validators
- Common error handling patterns
- Logging and security components
- Non-performance-critical shared code

## Service Specialization Patterns

### CloudFlare Security Gateway (cloudflare_security_gateway.py)

**🔐 SECURITY-FIRST ARCHITECTURE:**

```python
"""
🌐 STREAMLINED CLOUDFLARE CLOUDFLARE SECURITY GATEWAY: Essential Security Bridge for Alexa 🔐

This is your "security checkpoint" that handles OAuth authentication with
CloudFlare protection for account linking workflows.
"""

# Specialized for:
# - OAuth token exchange and validation
# - CloudFlare security integration
# - High-security authentication workflows
# - Account linking and token refresh
```

**Key Patterns:**

- CloudFlare header management
- OAuth token caching with security
- Dual-mode operations (OAuth + Smart Home proxy)
- Comprehensive error handling with correlation tracking

### Smart Home Bridge (smart_home_bridge.py)

**⚡ SPEED-FIRST ARCHITECTURE:**

```python
"""
⚡ OPTIMIZED HOME ASSISTANT ↔ ALEXA VOICE COMMAND BRIDGE 🗣️

This is the "executive receptionist" optimized for <500ms voice command
processing with maximum efficiency.
"""

# Specialized for:
# - Sub-500ms voice command response times
# - Container-level configuration caching
# - Optimized request processing with connection reuse
# - Bearer token validation for daily operations
```

**Key Patterns:**

- Multi-layer caching strategy (Environment → DynamoDB → Container → SSM)
- Connection reuse and optimization
- Streamlined error handling
- Performance-focused logging

### Configuration Manager (configuration_manager.py)

**🔧 OPTIMIZATION-FIRST ARCHITECTURE:**

```python
"""
Configuration management and cache warming for optimal Lambda performance.
"""

# Specialized for:
# - Background configuration optimization
# - Cache warming strategies
# - Configuration validation and testing
# - Cross-Lambda function cache coordination
```

### Shared Configuration (shared_configuration.py)

**📚 CENTRALIZED CODE MANAGEMENT:**

```python
"""
🔧 SHARED CONFIGURATION MODULE: Centralized Lambda Function Configuration

DUAL MODE ARCHITECTURE:
1. DEVELOPMENT MODE: Import from this module for testing
2. DEPLOYMENT MODE: Code embedded into standalone Lambda functions
"""

# Contains:
# - All shared functions and classes
# - Security infrastructure (RateLimiter, SecurityValidator)
# - Configuration loading and caching
# - Alexa protocol validation
```

## Code Quality Standards

### Required Pylint Disable Patterns

**✅ ARCHITECTURAL JUSTIFICATIONS:**

```python
# pylint: disable=too-many-lines  # Lambda functions must be standalone
# pylint: disable=duplicate-code  # Lambda functions must be standalone - no shared modules
```

**Key Principles:**

- Lambda functions inherently need to be self-contained
- Strategic code duplication is intentional for performance
- Use targeted disables with clear architectural justification

### Import Organization Within Marker Blocks

**✅ PROPER IMPORT STRUCTURE:**

```python
# ╭─────────────────── IMPORT_BLOCK_START ───────────────────╮
# Standard library imports first
import configparser
import json
import logging
import os

# Third-party imports second
import boto3
import urllib3
from botocore.exceptions import ClientError

# === SHARED CONFIGURATION IMPORTS ===
# SHARED_CONFIG_IMPORT: Development-only imports replaced in deployment
from .shared_configuration import (
    AlexaValidator,
    RateLimiter,
    # ... alphabetically organized shared imports
)

# ╰─────────────────── IMPORT_BLOCK_END ───────────────────╯
```

### Function Naming Conventions

**✅ NAMING PATTERNS:**

- **Transfer Block Functions**: `load_standardized_configuration`, `validate_alexa_request`
- **Service-Specific Functions**: `_oauth_validate_token`, `_bridge_process_command`
- **Internal Helpers**: `_initialize_logging`, `_create_response`
- **Lambda Handlers**: `lambda_handler` (entry point)

## Integration with ServiceInstaller

### ServiceType Enum Mapping

```python
# In integration_installer.py
class ServiceType(Enum):
    ALEXA_OAUTH = "alexa_oauth"           # → cloudflare_security_gateway.py
    ALEXA_SMART_HOME = "alexa_smart_home" # → smart_home_bridge.py
    ALEXA_CONFIG = "alexa_config"         # → configuration_manager.py
```

### Deployment Path Resolution

```python
def get_lambda_function_path(service_type: ServiceType) -> Path:
    """Resolve Lambda function file from ServiceType."""
    mapping = {
        ServiceType.ALEXA_OAUTH: "cloudflare_security_gateway.py",
        ServiceType.ALEXA_SMART_HOME: "smart_home_bridge.py",
        ServiceType.ALEXA_CONFIG: "configuration_manager.py",
    }
    return LAMBDA_FUNCTIONS_DIR / mapping[service_type]
```

## Performance Optimization Patterns

### 3-Tier Caching Strategy

**⚡ PERFORMANCE HIERARCHY:**

1. **Environment Variables** (0-1ms): Instant startup configuration
2. **Container Cache** (0-1ms): Warm Lambda container optimization
3. **DynamoDB Shared Cache** (20-50ms): Cross-Lambda function sharing
4. **SSM Parameter Store** (100-200ms): Authoritative configuration source

### Container Lifecycle Optimization

```python
# Global initialization (outside Lambda handler)
_logger = _initialize_logging()
_rate_limiter = RateLimiter()
_security_validator = SecurityValidator()

# Container-level caching
_container_config_cache: dict[str, Any] = {}
_container_cache_timestamp: float = 0.0

def lambda_handler(event: dict, context: Any) -> dict:
    """Optimized Lambda handler with container reuse."""
    # Leverage global components for warm starts
    # Implement smart caching strategies
    # Minimize cold start overhead
```

## Testing and Validation Standards

### Import Testing After Deployment

```python
# Validate imports work after deployment script runs
python -c "from cloudflare_security_gateway import lambda_handler; print('✅ CloudFlare Security Gateway imports')"
python -c "from smart_home_bridge import lambda_handler; print('✅ Smart Home Bridge imports')"
python -c "from configuration_manager import lambda_handler; print('✅ Config Manager imports')"
```

### Marker System Validation

```python
# Required validation after any marker changes
python scripts/validate_lambda_markers.py
# Must pass for all Lambda functions before deployment
```

### Transfer Block Synchronization Validation

```python
# After transfer block updates, validate both functions
def validate_transfer_block_sync():
    """Ensure transfer blocks are properly synchronized."""
    # Extract transfer blocks from both files
    # Compare core functionality (ignoring service-specific prefixes)
    # Validate both functions import successfully
    # Test both functions handle identical core scenarios
```

## AI Assistant Guidelines

### Critical Rules for AI Assistants

**🚨 NEVER "Clean Up" Duplicate Code:**

- The duplicate code between Lambda functions is INTENTIONAL
- Strategic duplication ensures deployment independence
- Performance optimization requires embedded implementations

**✅ PRESERVE SYSTEM INTEGRITY:**

1. **Maintain Marker System**: Always preserve deployment markers when editing
2. **Sync Transfer Blocks**: Copy changes between synchronized transfer blocks
3. **Service Customizations**: Maintain service-specific prefixes and identifiers
4. **Import Structure**: Keep shared imports within marker blocks
5. **Validation Requirements**: Run marker validation after structural changes

### Editing Workflow for AI Assistants

**🔧 RECOMMENDED PROCESS:**

1. **Identify Change Scope**: Determine if change affects shared code, transfer blocks,
   or service-specific code
2. **Preserve Markers**: Ensure all deployment markers remain intact
3. **Sync Changes**: If editing transfer blocks, synchronize across Lambda functions
4. **Validate Imports**: Test imports after structural changes
5. **Run Validation**: Execute `scripts/validate_lambda_markers.py`

### Common Pitfalls to Avoid

**❌ AVOID THESE PATTERNS:**

- Removing "duplicate" code between Lambda functions
- Breaking deployment marker formatting
- Moving shared imports outside marker blocks
- Consolidating Lambda functions into a single file
- Removing service-specific customizations in transfer blocks

**✅ FOLLOW THESE PATTERNS:**

- Preserve strategic code duplication for performance
- Maintain clear separation between development and deployment modes
- Keep transfer blocks synchronized with service customizations
- Validate marker system integrity after changes
- Document architectural constraints with targeted pylint disables

## Future Evolution Patterns

### Planned Enhancements

**🚀 ROADMAP INTEGRATION:**

- **Enhanced Transfer Blocks**: More sophisticated synchronization tools
- **Performance Monitoring**: Container cache hit rate tracking
- **Automated Validation**: CI/CD integration for marker system validation
- **Service Expansion**: Additional Lambda functions following established patterns

### Maintenance Considerations

**🔧 ONGOING REQUIREMENTS:**

- Regular validation of marker system integrity
- Transfer block synchronization monitoring
- Performance optimization validation
- Service specialization boundary maintenance

---

**Key Takeaway**: Lambda functions in this project use intentional architectural
patterns for optimal AWS performance. Preserve these patterns and use the
established systems for deployment, validation, and synchronization.
