"""
Home Assistant External Connector Automation Framework.

This module implements the 6-step automation workflow for deploying and
managing external service integrations with Home Assistant:

1. Discovery: Check what exists in the current environment
2. Matching: Identify exact matches between desired and current state
3. Compatibility: Find alternative matches and compatible options
4. Decision Engine: Determine reuse/update/add/remove actions
5. Execution: Deploy the determined changes
6. Validation: Test end-state success and compliance

The framework provides a consistent, reliable approach to automation
that minimizes manual intervention while ensuring system integrity.
"""

from .compatibility import CompatibilityAnalysis
from .decision_engine import AutomationDecisionEngine
from .discovery import EnvironmentDiscovery
from .execution import ChangeExecution
from .matching import StateMatching
from .validation import EndStateValidation

__all__ = [
    "EnvironmentDiscovery",
    "StateMatching",
    "CompatibilityAnalysis",
    "AutomationDecisionEngine",
    "ChangeExecution",
    "EndStateValidation",
]
