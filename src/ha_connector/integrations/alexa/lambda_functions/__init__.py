"""
🏢 Home Assistant Alexa Integration Lambda Functions

Professional office-style Lambda functions for Alexa Smart Home integration
with optional CloudFlare security and performance enhancements.

AVAILABLE COMPONENTS (for user selection):

🎯 CORE COMPONENTS (Required):
- smart_home_bridge: Executive Receptionist for voice command processing
- shared_configuration: Back-Office Support Services (embedded in all functions)

⚡ OPTIONAL ENHANCEMENTS:
- cloudflare_security_gateway: Security Guard for enhanced OAuth + CloudFlare proxy
- configuration_manager: Operations Manager for performance optimization

INTEGRATION ARCHITECTURE:
- Each component operates independently
- Optional components provide enhancements without dependencies
- Professional deployment with enterprise security standards
"""

from typing import NotRequired, TypedDict


class ComponentDict(TypedDict, total=False):
    name: str
    role: str
    description: str
    required: bool
    dependencies: list[str]
    deployment_size: str
    performance_impact: str
    benefits: NotRequired[list[str]]


AVAILABLE_COMPONENTS: dict[str, dict[str, ComponentDict]] = {
    "core": {
        "smart_home_bridge": {
            "name": "Smart Home Bridge",
            "role": "Executive Receptionist",
            "description": (
                "Processes Alexa voice commands and communicates with Home Assistant"
            ),
            "required": True,
            "dependencies": ["shared_configuration"],
            "deployment_size": "Medium",
            "performance_impact": "High (sub-500ms responses)",
        }
    },
    "optional": {
        "cloudflare_security_gateway": {
            "name": "CloudFlare Security Gateway",
            "role": "Security Guard",
            "description": (
                "OAuth authentication with optional CloudFlare proxy protection"
            ),
            "required": False,
            "dependencies": ["shared_configuration"],
            "deployment_size": "Small",
            "performance_impact": "Low (authentication only)",
            "benefits": [
                "Enhanced security",
                "CloudFlare DDoS protection",
                "Enterprise OAuth",
            ],
        },
        "configuration_manager": {
            "name": "Configuration Manager",
            "role": "Operations Manager",
            "description": (
                "Background service for performance optimization and config caching"
            ),
            "required": False,
            "dependencies": ["shared_configuration"],
            "deployment_size": "Small",
            "performance_impact": "High (75% faster cold starts)",
            "benefits": [
                "Faster Lambda responses",
                "Config caching",
                "Performance monitoring",
            ],
        },
    },
    "embedded": {
        "shared_configuration": {
            "name": "Shared Configuration",
            "role": "Back-Office Support Services",
            "description": "Common administrative functions embedded in all components",
            "required": True,
            "dependencies": [],
            "deployment_size": "Embedded",
            "performance_impact": "Essential (core services)",
        }
    },
}

# Export for CLI/UI integration
__all__ = ["AVAILABLE_COMPONENTS"]
