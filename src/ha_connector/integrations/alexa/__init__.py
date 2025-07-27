"""
Alexa Smart Home integration for Home Assistant External Connector.

This module provides complete automation for Alexa Smart Home Skill setup,
including Lambda function deployment, skill configuration, and OAuth gateway.
"""

from .skill_automation_manager import SmartHomeSkillAutomator

# Lambda functions are imported on-demand to avoid environment validation issues
# from .lambda_functions.smart_home_bridge import handle_smart_home_directive
# from .lambda_functions.oauth_gateway import lambda_handler as oauth_handler

__all__ = [
    "SmartHomeSkillAutomator",
]
