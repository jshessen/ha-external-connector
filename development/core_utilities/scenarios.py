"""Installation scenario models for Home Assistant External Connector."""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ScenarioType(str, Enum):
    """Supported installation scenarios."""

    DIRECT_ALEXA = "direct_alexa"
    CLOUDFLARE_ALEXA = "cloudflare_alexa"
    CLOUDFLARE_IOS = "cloudflare_ios"


class InstallationScenario(BaseModel):
    """Complete installation scenario configuration."""

    scenario_type: ScenarioType
    ha_base_url: str | None = None
    alexa_secret: str | None = None
    cf_client_id: str | None = None
    cf_client_secret: str | None = None
    aws_region: str = "us-east-1"
    additional_config: dict[str, Any] = {}

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
