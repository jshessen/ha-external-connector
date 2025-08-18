"""
🎯 INTERACTIVE INTEGRATION SELECTION SYSTEM

Enhanced integration selection system that provides both web and CLI interfaces
for choosing and configuring Home Assistant external integrations.

Builds on the existing CLI wizard and web API patterns to provide:
1. Interactive integration selection with dependency management
2. Configuration validation and optimization recommendations
3. Step-by-step setup guidance for each integration
4. Integration compatibility and conflict detection
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ha_connector.utils import HAConnectorLogger

from ..config.manager import InstallationScenario

logger = HAConnectorLogger("integrations.selection")


class IntegrationType(str, Enum):
    """Types of integrations available for selection."""

    ALEXA_SMART_HOME = "alexa_smart_home"
    ALEXA_CLOUDFLARE = "alexa_cloudflare"
    IOS_COMPANION = "ios_companion"
    CLOUDFLARE_SECURITY = "cloudflare_security"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class IntegrationStatus(str, Enum):
    """Integration configuration and deployment status."""

    AVAILABLE = "available"
    SELECTED = "selected"
    CONFIGURED = "configured"
    DEPLOYED = "deployed"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"


class IntegrationRequirement(BaseModel):
    """Requirements for an integration."""

    aws_services: list[str] = Field(default_factory=list)
    home_assistant_version: str | None = None
    requires_domain: bool = False
    requires_oauth: bool = False
    estimated_setup_time: int = 30  # minutes
    complexity_level: str = "intermediate"  # beginner, intermediate, advanced


class IntegrationDefinition(BaseModel):
    """Complete definition of an available integration."""

    integration_type: IntegrationType
    name: str
    description: str
    long_description: str
    requirements: IntegrationRequirement
    dependencies: set[IntegrationType] = Field(default_factory=set)  # type: ignore[type-arg]
    conflicts: set[IntegrationType] = Field(default_factory=set)  # type: ignore[type-arg]
    optional_enhancements: set[IntegrationType] = Field(default_factory=set)  # type: ignore[type-arg]
    lambda_functions: list[str] = Field(default_factory=list)
    status: IntegrationStatus = IntegrationStatus.AVAILABLE
    configuration: dict[str, Any] = Field(default_factory=dict)


class IntegrationSelectionRequest(BaseModel):
    """Request model for integration selection."""

    selected_integrations: list[IntegrationType]
    auto_resolve_dependencies: bool = Field(
        default=True, description="Automatically include required dependencies"
    )
    skip_conflict_check: bool = Field(
        default=False, description="Skip compatibility conflict checking"
    )
    target_scenario: InstallationScenario | None = Field(
        default=None, description="Target installation scenario"
    )


class IntegrationSelectionResponse(BaseModel):
    """Response model for integration selection."""

    selected_integrations: list[IntegrationType]
    resolved_dependencies: list[IntegrationType]
    detected_conflicts: list[str]
    recommendations: list[str]
    estimated_total_time: int
    lambda_functions_required: list[str]
    aws_services_required: list[str]
    configuration_steps: list[dict[str, Any]]


class InteractiveIntegrationSelector:
    """
    Interactive system for selecting and configuring Home Assistant integrations.

    Provides intelligent dependency resolution, conflict detection, and
    configuration guidance for optimal integration setup.
    """

    def __init__(self):
        """Initialize the integration selector with available integrations."""
        self.available_integrations = self._initialize_integrations()
        self.selected_integrations: set[IntegrationType] = set()

    def _initialize_integrations(self) -> dict[IntegrationType, IntegrationDefinition]:
        """Initialize the catalog of available integrations."""

        integrations: dict[IntegrationType, IntegrationDefinition] = {}

        # Alexa Smart Home (Direct)
        integrations[IntegrationType.ALEXA_SMART_HOME] = IntegrationDefinition(
            integration_type=IntegrationType.ALEXA_SMART_HOME,
            name="Alexa Smart Home (Direct)",
            description="Direct Alexa Smart Home skill integration",
            long_description=(
                "Connect Alexa directly to Home Assistant via AWS Lambda for "
                "voice control of devices. Provides fast response times "
                "and simple setup."
            ),
            requirements=IntegrationRequirement(
                aws_services=["lambda", "iam"],
                requires_oauth=True,
                estimated_setup_time=45,
                complexity_level="intermediate",
            ),
            lambda_functions=["smart_home_bridge"],
            conflicts={IntegrationType.ALEXA_CLOUDFLARE},
        )

        # Alexa Smart Home (CloudFlare)
        integrations[IntegrationType.ALEXA_CLOUDFLARE] = IntegrationDefinition(
            integration_type=IntegrationType.ALEXA_CLOUDFLARE,
            name="Alexa Smart Home (CloudFlare)",
            description="Alexa Smart Home with CloudFlare Access security",
            long_description=(
                "Enhanced Alexa integration with CloudFlare Access providing "
                "additional security layers, DNS management, and access controls."
            ),
            requirements=IntegrationRequirement(
                aws_services=["lambda", "iam"],
                requires_domain=True,
                requires_oauth=True,
                estimated_setup_time=75,
                complexity_level="advanced",
            ),
            dependencies={IntegrationType.CLOUDFLARE_SECURITY},
            lambda_functions=["smart_home_bridge", "cloudflare_security_gateway"],
            conflicts={IntegrationType.ALEXA_SMART_HOME},
        )

        # iOS Companion
        integrations[IntegrationType.IOS_COMPANION] = IntegrationDefinition(
            integration_type=IntegrationType.IOS_COMPANION,
            name="iOS Companion",
            description="Home Assistant iOS app integration via CloudFlare",
            long_description=(
                "Secure external access for the Home Assistant iOS app using "
                "CloudFlare Access for authentication and secure tunneling."
            ),
            requirements=IntegrationRequirement(
                aws_services=["lambda", "iam"],
                requires_domain=True,
                requires_oauth=True,
                estimated_setup_time=60,
                complexity_level="advanced",
            ),
            dependencies={IntegrationType.CLOUDFLARE_SECURITY},
            lambda_functions=["ios_companion_wrapper"],
        )

        # CloudFlare Security Gateway
        integrations[IntegrationType.CLOUDFLARE_SECURITY] = IntegrationDefinition(
            integration_type=IntegrationType.CLOUDFLARE_SECURITY,
            name="CloudFlare Security Gateway",
            description="OAuth security layer via CloudFlare Access",
            long_description=(
                "Provides secure OAuth authentication and access control using "
                "CloudFlare Access. Required for CloudFlare-based integrations."
            ),
            requirements=IntegrationRequirement(
                aws_services=["lambda", "iam", "ssm"],
                requires_domain=True,
                requires_oauth=True,
                estimated_setup_time=30,
                complexity_level="advanced",
            ),
            lambda_functions=["cloudflare_security_gateway"],
        )

        # Performance Optimization
        integrations[IntegrationType.PERFORMANCE_OPTIMIZATION] = IntegrationDefinition(
            integration_type=IntegrationType.PERFORMANCE_OPTIMIZATION,
            name="Performance Optimization",
            description="Advanced caching and performance enhancements",
            long_description=(
                "Implements multi-tier caching, Lambda container warming, "
                "and performance optimizations for sub-500ms voice response times."
            ),
            requirements=IntegrationRequirement(
                aws_services=["lambda", "dynamodb", "ssm"],
                estimated_setup_time=20,
                complexity_level="intermediate",
            ),
            lambda_functions=["configuration_manager"],
            optional_enhancements={
                IntegrationType.ALEXA_SMART_HOME,
                IntegrationType.ALEXA_CLOUDFLARE,
            },
        )

        return integrations

    def select_integrations(
        self, request: IntegrationSelectionRequest
    ) -> IntegrationSelectionResponse:
        """
        Process integration selection with dependency resolution and conflict detection.

        Args:
            request: Integration selection parameters

        Returns:
            Resolved integration selection with recommendations
        """
        logger.info(
            f"🎯 Processing integration selection: {request.selected_integrations}"
        )

        selected: set[IntegrationType] = set(request.selected_integrations)
        resolved_dependencies: set[IntegrationType] = set()
        conflicts: list[str] = []
        recommendations: list[str] = []

        # Resolve dependencies
        if request.auto_resolve_dependencies:
            for integration_type in list(selected):
                dependencies = self.available_integrations[
                    integration_type
                ].dependencies
                resolved_dependencies.update(dependencies)

        # Check for conflicts
        if not request.skip_conflict_check:
            conflicts = self._detect_conflicts(selected | resolved_dependencies)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            selected, resolved_dependencies, request.target_scenario
        )

        # Calculate totals
        all_integrations = selected | resolved_dependencies
        total_time = sum(
            self.available_integrations[int_type].requirements.estimated_setup_time
            for int_type in all_integrations
        )

        lambda_functions: list[str] = list(
            set(
                func
                for int_type in all_integrations
                for func in self.available_integrations[int_type].lambda_functions
            )
        )

        aws_services: list[str] = (
            list(
                set(
                    aws_service
                    for int_type in all_integrations
                    for aws_service in self.available_integrations[
                        int_type
                    ].requirements.aws_services
                )
            )
            if all_integrations
            else []
        )

        # Generate configuration steps
        config_steps = self._generate_configuration_steps(all_integrations)

        return IntegrationSelectionResponse(
            selected_integrations=list(selected),
            resolved_dependencies=list(resolved_dependencies),
            detected_conflicts=conflicts,
            recommendations=recommendations,
            estimated_total_time=total_time,
            lambda_functions_required=lambda_functions,
            aws_services_required=aws_services,
            configuration_steps=config_steps,
        )

    def _detect_conflicts(self, integrations: set[IntegrationType]) -> list[str]:
        """Detect conflicts between selected integrations."""
        conflicts: list[str] = []

        for integration_type in integrations:
            integration = self.available_integrations[integration_type]
            conflicting = integration.conflicts & integrations

            if conflicting:
                for conflict in conflicting:
                    conflicts.append(
                        f"{integration.name} conflicts with "
                        f"{self.available_integrations[conflict].name}"
                    )

        return conflicts

    def _generate_recommendations(
        self,
        selected: set[IntegrationType],
        dependencies: set[IntegrationType],
        target_scenario: InstallationScenario | None,
    ) -> list[str]:
        """Generate setup recommendations based on selection."""
        recommendations: list[str] = []

        all_integrations = selected | dependencies

        # CloudFlare recommendations
        if any(
            self.available_integrations[t].requirements.requires_domain
            for t in all_integrations
        ):
            recommendations.append(
                "📋 You'll need a custom domain configured with CloudFlare"
            )
            recommendations.append(
                "🔒 Configure CloudFlare Access for OAuth authentication"
            )

        # Performance recommendations
        if (
            IntegrationType.ALEXA_SMART_HOME in all_integrations
            or IntegrationType.ALEXA_CLOUDFLARE in all_integrations
        ) and IntegrationType.PERFORMANCE_OPTIMIZATION not in all_integrations:
            recommendations.append(
                "⚡ Consider adding Performance Optimization for faster voice responses"
            )

        # Complexity warnings
        advanced_integrations = [
            t
            for t in all_integrations
            if self.available_integrations[t].requirements.complexity_level
            == "advanced"
        ]
        if len(advanced_integrations) >= 2:
            recommendations.append(
                "⚠️ Advanced setup complexity - consider phased deployment"
            )

        # Scenario-specific recommendations
        if (
            target_scenario == InstallationScenario.DIRECT_ALEXA
            and IntegrationType.CLOUDFLARE_SECURITY in all_integrations
        ):
            recommendations.append(
                "💡 Direct Alexa scenario doesn't require CloudFlare - "
                "consider simpler setup"
            )

        return recommendations

    def _generate_configuration_steps(
        self, integrations: set[IntegrationType]
    ) -> list[dict[str, Any]]:
        """Generate ordered configuration steps for selected integrations."""
        steps: list[dict[str, Any]] = []

        # Step 1: Prerequisites
        steps.append(
            {
                "step": 1,
                "title": "Prerequisites & Validation",
                "description": "Validate AWS access and Home Assistant connectivity",
                "integrations": list(integrations),
                "estimated_time": 10,
                "type": "validation",
            }
        )

        # Step 2: Lambda Deployment
        lambda_functions = list(
            {
                func
                for int_type in integrations
                for func in self.available_integrations[int_type].lambda_functions
            }
        )

        if lambda_functions:
            steps.append(
                {
                    "step": 2,
                    "title": "AWS Lambda Deployment",
                    "description": (
                        f"Deploy Lambda functions: {', '.join(lambda_functions)}"
                    ),
                    "lambda_functions": lambda_functions,
                    "estimated_time": 15,
                    "type": "deployment",
                }
            )

        # Step 3: Integration-specific configuration
        for i, integration_type in enumerate(sorted(integrations), start=3):
            integration = self.available_integrations[integration_type]
            steps.append(
                {
                    "step": i,
                    "title": f"Configure {integration.name}",
                    "description": integration.description,
                    "integration_type": integration_type,
                    "estimated_time": integration.requirements.estimated_setup_time,
                    "complexity": integration.requirements.complexity_level,
                    "type": "configuration",
                }
            )

        # Final step: Testing
        steps.append(
            {
                "step": len(steps) + 1,
                "title": "Testing & Validation",
                "description": "Validate all integrations are working correctly",
                "integrations": list(integrations),
                "estimated_time": 15,
                "type": "testing",
            }
        )

        return steps

    def get_integration_details(
        self, integration_type: IntegrationType
    ) -> IntegrationDefinition:
        """Get detailed information about a specific integration."""
        return self.available_integrations[integration_type]

    def get_available_integrations(self) -> list[IntegrationDefinition]:
        """Get list of all available integrations."""
        return list(self.available_integrations.values())

    def suggest_integration_combinations(
        self, primary_goal: str
    ) -> list[dict[str, Any]]:
        """Suggest optimal integration combinations based on user goals."""

        suggestions: list[dict[str, Any]] = []

        if "alexa" in primary_goal.lower():
            # Simple Alexa setup
            suggestions.append(
                {
                    "name": "Simple Alexa Voice Control",
                    "description": "Basic Alexa Smart Home skill for voice control",
                    "integrations": [IntegrationType.ALEXA_SMART_HOME],
                    "complexity": "intermediate",
                    "estimated_time": 45,
                    "pros": [
                        "Simple setup",
                        "Fast response times",
                        "No domain required",
                    ],
                    "cons": ["Limited security features", "Direct internet exposure"],
                }
            )

            # Secure Alexa setup
            suggestions.append(
                {
                    "name": "Secure Alexa with CloudFlare",
                    "description": "Alexa Smart Home with CloudFlare Access security",
                    "integrations": [
                        IntegrationType.ALEXA_CLOUDFLARE,
                        IntegrationType.CLOUDFLARE_SECURITY,
                    ],
                    "complexity": "advanced",
                    "estimated_time": 105,
                    "pros": [
                        "Enhanced security",
                        "Access control",
                        "Professional setup",
                    ],
                    "cons": ["Requires domain", "More complex", "Higher maintenance"],
                }
            )

            # Performance-optimized Alexa
            suggestions.append(
                {
                    "name": "High-Performance Alexa",
                    "description": (
                        "Alexa with performance optimizations for fastest responses"
                    ),
                    "integrations": [
                        IntegrationType.ALEXA_SMART_HOME,
                        IntegrationType.PERFORMANCE_OPTIMIZATION,
                    ],
                    "complexity": "intermediate",
                    "estimated_time": 65,
                    "pros": [
                        "Sub-500ms responses",
                        "Better user experience",
                        "Container warming",
                    ],
                    "cons": ["Additional AWS costs", "More complexity"],
                }
            )

        if "ios" in primary_goal.lower() or "mobile" in primary_goal.lower():
            suggestions.append(
                {
                    "name": "Secure iOS Companion",
                    "description": "Home Assistant iOS app with CloudFlare security",
                    "integrations": [
                        IntegrationType.IOS_COMPANION,
                        IntegrationType.CLOUDFLARE_SECURITY,
                    ],
                    "complexity": "advanced",
                    "estimated_time": 90,
                    "pros": [
                        "Secure external access",
                        "Professional setup",
                        "Access control",
                    ],
                    "cons": [
                        "Requires domain",
                        "Complex setup",
                        "CloudFlare dependency",
                    ],
                }
            )

        if "complete" in primary_goal.lower() or "everything" in primary_goal.lower():
            suggestions.append(
                {
                    "name": "Complete Integration Suite",
                    "description": "All integrations with full feature set",
                    "integrations": [
                        IntegrationType.ALEXA_CLOUDFLARE,
                        IntegrationType.IOS_COMPANION,
                        IntegrationType.CLOUDFLARE_SECURITY,
                        IntegrationType.PERFORMANCE_OPTIMIZATION,
                    ],
                    "complexity": "advanced",
                    "estimated_time": 165,
                    "pros": [
                        "Full feature set",
                        "Maximum security",
                        "Best performance",
                    ],
                    "cons": ["Complex setup", "Higher costs", "Requires domain"],
                }
            )

        return suggestions
