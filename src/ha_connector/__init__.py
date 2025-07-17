"""Home Assistant External Connector Package."""

__version__ = "0.1.0"
__author__ = "Home Assistant External Connector Team"
__description__ = "Secure integration between Home Assistant and external services"

from .config import Settings
from .models import InstallationScenario

__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "Settings",
    "InstallationScenario",
]
