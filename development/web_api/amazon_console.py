"""
🌐 AMAZON DEVELOPER CONSOLE WEB INTERFACE

Web-based guided interface for Amazon Developer Console integration.
Provides step-by-step guidance and SMAPI integration without requiring
browser automation dependencies.
"""

import secrets
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests

try:
    from flask import (
        Blueprint,
        Flask,
        Response,
        jsonify,
        redirect,
        render_template,
        request,
        session,
        url_for,
    )

    FLASK_AVAILABLE = True
except ImportError:
    # Flask is optional for development - web API functionality won't be available
    Flask = Blueprint = Response = request = session = None
    FLASK_AVAILABLE = False

    # Define stub functions when Flask is not available
    def jsonify(*_args, **_kwargs):
        """Stub function when Flask is not available."""
        return None

    def redirect(*_args, **_kwargs):
        """Stub function when Flask is not available."""
        return None

    def render_template(*_args, **_kwargs):
        """Stub function when Flask is not available."""
        return None

    def url_for(*_args, **_kwargs):
        """Stub function when Flask is not available."""
        return None


from development.alexa_automation_scripts.amazon_developer_console import (
    AmazonDeveloperConsoleIntegration,
    AutomationConfig,
    OAuthConfiguration,
    SkillConfiguration,
    SkillMetadata,
    SMAPICredentials,
)
from development.utils import HAConnectorLogger

# OAuth2 token endpoint for Amazon authentication (not a secret)
AMAZON_OAUTH_TOKEN_URL = "https://api.amazon.com/auth/o2/token"  # nosec: B105 - public OAuth endpoint, not a secret

logger = HAConnectorLogger("web.amazon_console")

if FLASK_AVAILABLE:
    # Flask is available - create the actual Blueprint
    amazon_console_bp = Blueprint(
        "amazon_console",
        __name__,
        template_folder="templates",
        static_folder="static",
        url_prefix="/amazon-console",
    )
else:
    # Flask is not available - create a mock Blueprint that doesn't error
    class MockBlueprint:
        """Mock Blueprint that provides no-op methods when Flask is unavailable."""

        def __init__(self, *_args, **_kwargs):
            pass

        def route(self, *_args, **_kwargs):
            """Mock route decorator."""

            def decorator(func):
                return func

            return decorator

        def __getattr__(self, name):
            """Return a no-op function for any other method calls."""

            def no_op(*_args, **_kwargs):
                return None

            return no_op

    amazon_console_bp = MockBlueprint()


@amazon_console_bp.route("/")
def dashboard():
    """Amazon Developer Console integration dashboard."""
    return render_template("amazon_console/dashboard.html")


@amazon_console_bp.route("/setup-credentials")
def setup_credentials():
    """Setup SMAPI credentials page with guided wizard."""
    return render_template("amazon_console/setup_credentials.html")


@amazon_console_bp.route("/smapi-wizard")
def smapi_wizard():
    """SMAPI setup wizard - HACS pattern guided experience."""
    return render_template("amazon_console/smapi_wizard.html")


@amazon_console_bp.route("/api/smapi-wizard/start", methods=["POST"])
def start_smapi_wizard():
    """Start the SMAPI setup wizard process."""
    try:
        # Initialize wizard session
        session["smapi_wizard"] = {
            "step": 1,
            "started_at": datetime.now().isoformat(),
            "state": secrets.token_urlsafe(32),
        }

        return jsonify(
            {
                "success": True,
                "message": "SMAPI wizard started",
                "step": 1,
                "instructions": {
                    "title": "Create Login with Amazon Security Profile",
                    "description": "Set up OAuth 2.0 credentials for SMAPI integration",
                    "steps": [
                        "Open the Login with Amazon Console",
                        "Create a new security profile",
                        "Configure redirect URLs",
                        "Get Client ID and Client Secret",
                    ],
                    "lwa_console_url": "https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html",
                    "required_redirect_urls": [
                        "http://127.0.0.1:9090/cb",
                        "https://ask-cli-static-content.s3-us-west-2.amazonaws.com/html/ask-cli-no-browser.html",
                        "http://localhost:3000/auth/callback",
                        "https://localhost:3000/auth/callback",
                    ],
                },
            }
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error starting SMAPI wizard: {e}")
        return (
            jsonify({"success": False, "message": f"Error starting wizard: {e}"}),
            500,
        )


@amazon_console_bp.route("/api/smapi-wizard/security-profile", methods=["POST"])
def configure_security_profile():
    """Configure security profile in wizard."""
    try:
        if "smapi_wizard" not in session:
            return jsonify({"success": False, "message": "Wizard not started"}), 400

        data = request.get_json()
        profile_name = data.get("profile_name", "").strip()
        client_id = data.get("client_id", "").strip()
        client_secret = data.get("client_secret", "").strip()

        if not all([profile_name, client_id, client_secret]):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": (
                            "Profile name, Client ID, and Client Secret are required"
                        ),
                    }
                ),
                400,
            )

        # Validate Client ID format
        valid_prefixes = ("amzn1.application-oa2-client", "amzn1.lwa.oa2-client")
        if not client_id.startswith(valid_prefixes):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": (
                            "Invalid Client ID format. Should start with "
                            "amzn1.application-oa2-client or amzn1.lwa.oa2-client"
                        ),
                    }
                ),
                400,
            )

        # Store in session
        session["smapi_wizard"].update(
            {
                "step": 2,
                "security_profile": {
                    "name": profile_name,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            }
        )

        # Generate authorization URL
        state = session["smapi_wizard"]["state"]
        scopes = [
            "alexa::ask:skills:readwrite",
            "alexa::ask:models:readwrite",
            "alexa::ask:skills:test",
        ]

        auth_params = {
            "client_id": client_id,
            "scope": " ".join(scopes),
            "response_type": "code",
            "state": state,
            "redirect_uri": "http://127.0.0.1:9090/cb",
        }

        auth_url = f"https://www.amazon.com/ap/oa?{urlencode(auth_params)}"

        return jsonify(
            {
                "success": True,
                "message": "Security profile configured",
                "step": 2,
                "auth_url": auth_url,
                "state": state,
                "instructions": {
                    "title": "Complete OAuth Authorization",
                    "description": "Authorize your application to access SMAPI",
                    "steps": [
                        "Click the authorization URL",
                        "Sign in with your Amazon Developer account",
                        "Accept the requested permissions",
                        "Copy the authorization code from the redirect URL",
                    ],
                },
            }
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error configuring security profile: {e}")
        return (
            jsonify({"success": False, "message": f"Error configuring profile: {e}"}),
            500,
        )


@amazon_console_bp.route("/api/smapi-wizard/oauth-complete", methods=["POST"])
def complete_oauth_authorization():
    """Complete OAuth authorization with authorization code."""
    try:
        # Validate wizard state
        validation_error = _validate_oauth_wizard_state()
        if validation_error:
            return validation_error

        # Get authorization code from request
        data = request.get_json()
        auth_code = data.get("auth_code", "").strip()
        if not auth_code:
            return (
                jsonify(
                    {"success": False, "message": "Authorization code is required"}
                ),
                400,
            )

        # Exchange code for tokens
        wizard_data = session["smapi_wizard"]
        token_response = _exchange_auth_code_for_tokens(wizard_data, auth_code)
        if isinstance(token_response, tuple):  # Error response
            return token_response

        # Get vendor information
        vendor_info = _get_vendor_info(token_response["access_token"])

        # Update session and return success
        _update_session_with_tokens(token_response, vendor_info)
        return _create_oauth_success_response(token_response, vendor_info)

    except (requests.RequestException, KeyError, ValueError) as e:
        logger.error(f"Error completing OAuth: {e}")
        return (
            jsonify({"success": False, "message": f"Error completing OAuth: {e}"}),
            500,
        )


def _validate_oauth_wizard_state() -> tuple[Response, int] | None:
    """Validate wizard state for OAuth completion."""
    if "smapi_wizard" not in session:
        return jsonify({"success": False, "message": "Wizard not started"}), 400

    wizard_data = session["smapi_wizard"]
    if "security_profile" not in wizard_data:
        return (
            jsonify({"success": False, "message": "Security profile not configured"}),
            400,
        )
    return None


def _exchange_auth_code_for_tokens(
    wizard_data: dict[str, Any], auth_code: str
) -> dict[str, Any] | tuple[Response, int]:
    """Exchange authorization code for access tokens."""
    profile = wizard_data["security_profile"]
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": "http://127.0.0.1:9090/cb",
        "client_id": profile["client_id"],
        "client_secret": profile["client_secret"],
    }

    response = requests.post(
        AMAZON_OAUTH_TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if response.status_code == 200:
        return response.json()

    # Return error response
    return (
        jsonify(
            {
                "success": False,
                "message": f"Token exchange failed: {response.status_code}",
                "error_detail": response.text,
            }
        ),
        400,
    )


def _get_vendor_info(access_token: str) -> dict[str, str]:
    """Get vendor information from SMAPI."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    vendor_response = requests.get(
        "https://api.amazonalexa.com/v1/vendors", headers=headers, timeout=10
    )

    vendor_id = ""
    vendor_name = "Unknown"

    if vendor_response.status_code == 200:
        vendor_data = vendor_response.json()
        if vendor_data.get("vendors"):
            vendor_info = vendor_data["vendors"][0]
            vendor_id = vendor_info.get("id", "")
            vendor_name = vendor_info.get("name", "Unknown")

    return {"id": vendor_id, "name": vendor_name}


def _update_session_with_tokens(
    token_response: dict[str, Any], vendor_info: dict[str, str]
) -> None:
    """Update session with token information."""
    session["smapi_wizard"].update(
        {
            "step": 3,
            "tokens": {
                "access_token": token_response["access_token"],
                "refresh_token": token_response["refresh_token"],
                "token_type": token_response.get("token_type", "Bearer"),
                "expires_in": token_response.get("expires_in", 3600),
                "vendor_id": vendor_info["id"],
                "vendor_name": vendor_info["name"],
            },
        }
    )


def _create_oauth_success_response(
    token_response: dict[str, Any], vendor_info: dict[str, str]
) -> Response:
    """Create success response for OAuth completion."""
    return jsonify(
        {
            "success": True,
            "message": "OAuth authorization completed successfully",
            "step": 3,
            "vendor_info": vendor_info,
            "token_info": {
                "expires_in": token_response.get("expires_in", 3600),
                "scope": token_response.get("scope", ""),
            },
        }
    )


@amazon_console_bp.route("/api/smapi-wizard/save-config", methods=["POST"])
def save_smapi_configuration():
    """Save SMAPI configuration to environment or file."""
    try:
        if "smapi_wizard" not in session:
            return jsonify({"success": False, "message": "Wizard not started"}), 400

        wizard_data = session["smapi_wizard"]
        if "tokens" not in wizard_data or "security_profile" not in wizard_data:
            return (
                jsonify({"success": False, "message": "Configuration incomplete"}),
                400,
            )

        data = request.get_json()
        save_method = data.get("save_method", "show")  # show, env_file

        profile = wizard_data["security_profile"]
        tokens = wizard_data["tokens"]

        env_vars = {
            "LWA_CLIENT_ID": profile["client_id"],
            "LWA_CLIENT_SECRET": profile["client_secret"],
            "LWA_ACCESS_TOKEN": tokens["access_token"],
            "LWA_REFRESH_TOKEN": tokens["refresh_token"],
            "AMAZON_VENDOR_ID": tokens["vendor_id"],
        }

        if save_method == "env_file":
            # Save to .env file
            env_file_path = ".env"
            try:
                with open(env_file_path, "a", encoding="utf-8") as f:
                    f.write("\n# SMAPI Configuration (Generated by Setup Wizard)\n")
                    for key, value in env_vars.items():
                        f.write(f"{key}={value}\n")

                return jsonify(
                    {
                        "success": True,
                        "message": f"Configuration saved to {env_file_path}",
                        "warning": "Add .env to .gitignore to protect secrets",
                    }
                )
            except OSError as e:
                return (
                    jsonify(
                        {"success": False, "message": f"Failed to write .env file: {e}"}
                    ),
                    500,
                )
        else:
            # Return configuration for manual setup
            masked_vars = {}
            for key, value in env_vars.items():
                sensitive_keys = [
                    "LWA_CLIENT_SECRET",
                    "LWA_ACCESS_TOKEN",
                    "LWA_REFRESH_TOKEN",
                ]
                if key in sensitive_keys:
                    masked_vars[key] = value[:8] + "..." if len(value) > 8 else value
                else:
                    masked_vars[key] = value

            return jsonify(
                {
                    "success": True,
                    "message": "Configuration ready for manual setup",
                    "env_vars": masked_vars,
                    "full_config": env_vars,  # For copy to clipboard
                }
            )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error saving SMAPI configuration: {e}")
        return (
            jsonify({"success": False, "message": f"Error saving configuration: {e}"}),
            500,
        )


@amazon_console_bp.route("/api/credentials", methods=["POST"])
def save_credentials():
    """Save SMAPI credentials."""
    try:
        data = request.get_json()
        client_id = data.get("client_id", "").strip()
        client_secret = data.get("client_secret", "").strip()

        if not client_id or not client_secret:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Client ID and Client Secret are required",
                    }
                ),
                400,
            )

        # Store in session for this flow
        session["smapi_credentials"] = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Generate authentication URL
        credentials = SMAPICredentials(client_id=client_id, client_secret=client_secret)

        console_integration = AmazonDeveloperConsoleIntegration(credentials)
        auth_url = console_integration.authenticate_smapi()

        return jsonify(
            {
                "success": True,
                "message": "Credentials saved successfully",
                "auth_url": auth_url,
                "redirect": url_for("amazon_console.authentication_flow"),
            }
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error saving credentials: {e}")
        return (
            jsonify({"success": False, "message": f"Error saving credentials: {e}"}),
            500,
        )


@amazon_console_bp.route("/authentication")
def authentication_flow():
    """Authentication flow page."""
    credentials = session.get("smapi_credentials")
    if not credentials:
        return redirect(url_for("amazon_console.setup_credentials"))

    # Generate auth URL
    smapi_credentials = SMAPICredentials(
        client_id=credentials["client_id"], client_secret=credentials["client_secret"]
    )

    console_integration = AmazonDeveloperConsoleIntegration(smapi_credentials)
    auth_url = console_integration.authenticate_smapi()

    return render_template("amazon_console/authentication.html", auth_url=auth_url)


@amazon_console_bp.route("/api/complete-auth", methods=["POST"])
def complete_authentication():
    """Complete SMAPI authentication."""
    try:
        data = request.get_json()
        auth_code = data.get("auth_code", "").strip()

        if not auth_code:
            return (
                jsonify(
                    {"success": False, "message": "Authorization code is required"}
                ),
                400,
            )

        credentials_data = session.get("smapi_credentials")
        if not credentials_data:
            return (
                jsonify(
                    {"success": False, "message": "No credentials found in session"}
                ),
                400,
            )

        credentials = SMAPICredentials(
            client_id=credentials_data["client_id"],
            client_secret=credentials_data["client_secret"],
        )

        console_integration = AmazonDeveloperConsoleIntegration(credentials)

        # Complete authentication
        success = console_integration.complete_smapi_authentication(
            auth_code, "http://localhost:3000/auth/callback"
        )

        if success:
            # Get vendor information
            vendor_id = None
            if console_integration.smapi_client is not None:
                vendor_id = console_integration.smapi_client.get_vendor_id()
                if vendor_id:
                    credentials.vendor_id = vendor_id
            else:
                logger.warning(
                    "SMAPI client is not initialized; cannot fetch vendor ID."
                )

            # Store authenticated credentials in session
            session["authenticated_credentials"] = {
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "vendor_id": credentials.vendor_id,
            }

            return jsonify(
                {
                    "success": True,
                    "message": "Authentication successful",
                    "vendor_id": vendor_id,
                    "redirect": url_for("amazon_console.skill_creation"),
                }
            )
        return jsonify({"success": False, "message": "Authentication failed"}), 400

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error completing authentication: {e}")
        return jsonify({"success": False, "message": f"Authentication error: {e}"}), 500


@amazon_console_bp.route("/skill-creation")
def skill_creation():
    """Skill creation page."""
    if "authenticated_credentials" not in session:
        return redirect(url_for("amazon_console.authentication_flow"))

    return render_template("amazon_console/skill_creation.html")


@amazon_console_bp.route("/api/create-skill", methods=["POST"])
def create_skill():
    """Create Alexa Smart Home skill."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "skill_name",
            "lambda_arn",
            "oauth_auth_uri",
            "oauth_token_uri",
        ]
        for field in required_fields:
            if not data.get(field, "").strip():
                return (
                    jsonify({"success": False, "message": f"{field} is required"}),
                    400,
                )

        # Get authenticated credentials
        credentials_data = session.get("authenticated_credentials")
        if not credentials_data:
            return (
                jsonify(
                    {"success": False, "message": "No authenticated credentials found"}
                ),
                401,
            )

        # Create credentials object
        credentials = SMAPICredentials(
            client_id=credentials_data["client_id"],
            client_secret=credentials_data["client_secret"],
            access_token=credentials_data["access_token"],
            refresh_token=credentials_data["refresh_token"],
            vendor_id=credentials_data["vendor_id"],
        )

        # Create skill configuration
        oauth_config = OAuthConfiguration(
            web_auth_uri=data["oauth_auth_uri"],
            access_token_uri=data["oauth_token_uri"],
            client_id=data.get("oauth_client_id", "https://pitangui.amazon.com"),
        )

        metadata = SkillMetadata(
            name=data["skill_name"],
            description=data.get("skill_description", ""),
        )

        skill_config = SkillConfiguration(
            lambda_function_arn=data["lambda_arn"],
            oauth_config=oauth_config,
            metadata=metadata,
        )

        # Create console integration
        automation_config = AutomationConfig(
            use_browser_fallback=False,  # Web interface doesn't use browser automation
            headless_browser=False,
        )
        console_integration = AmazonDeveloperConsoleIntegration(
            credentials=credentials,
            automation_config=automation_config,
        )

        # Create skill
        result = console_integration.create_skill_complete(skill_config)

        # Store result in session for manual steps if needed
        session["skill_creation_result"] = result

        return jsonify(
            {"success": True, "result": result, "message": "Skill creation completed"}
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error creating skill: {e}")
        return jsonify({"success": False, "message": f"Error creating skill: {e}"}), 500


@amazon_console_bp.route("/manual-steps")
def manual_steps():
    """Manual steps guidance page."""
    result = session.get("skill_creation_result")
    if not result:
        return redirect(url_for("amazon_console.skill_creation"))

    return render_template("amazon_console/manual_steps.html", result=result)


@amazon_console_bp.route("/api/list-skills")
def list_skills():
    """List all skills in the Amazon Developer account."""
    try:
        credentials_data = session.get("authenticated_credentials")
        if not credentials_data:
            return (
                jsonify(
                    {"success": False, "message": "No authenticated credentials found"}
                ),
                401,
            )

        credentials = SMAPICredentials(
            client_id=credentials_data["client_id"],
            client_secret=credentials_data["client_secret"],
            access_token=credentials_data["access_token"],
            refresh_token=credentials_data["refresh_token"],
            vendor_id=credentials_data["vendor_id"],
        )

        console_integration = AmazonDeveloperConsoleIntegration(credentials)
        if console_integration.smapi_client is not None:
            # Get vendor ID and list skills for that vendor
            vendor_id = (
                credentials.vendor_id
                or console_integration.smapi_client.get_vendor_id()
            )
            if vendor_id:
                skills = console_integration.smapi_client.list_skills_for_vendor(
                    vendor_id
                )
                return jsonify({"success": True, "skills": skills})
            logger.error("Vendor ID not found; cannot list skills.")
            return jsonify({"success": False, "error": "Vendor ID not found"})
        logger.error("SMAPI client is not initialized; cannot list skills.")
        return (
            jsonify(
                {
                    "success": False,
                    "message": ("SMAPI client is not initialized; cannot list skills."),
                }
            ),
            500,
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error listing skills: {e}")
        return jsonify({"success": False, "message": f"Error listing skills: {e}"}), 500


@amazon_console_bp.route("/api/generate-instructions", methods=["POST"])
def generate_instructions():
    """Generate setup instructions for manual configuration."""
    try:
        data = request.get_json()
        skill_id = data.get("skill_id")

        result = session.get("skill_creation_result")
        if not result:
            return (
                jsonify(
                    {"success": False, "message": "No skill creation result found"}
                ),
                400,
            )

        # Create skill configuration from result
        oauth_config = OAuthConfiguration(
            web_auth_uri=data["oauth_auth_uri"],
            access_token_uri=data["oauth_token_uri"],
        )

        metadata = SkillMetadata(
            name=data["skill_name"],
        )

        skill_config = SkillConfiguration(
            lambda_function_arn=data["lambda_arn"],
            oauth_config=oauth_config,
            metadata=metadata,
        )

        credentials_data = session.get("authenticated_credentials")
        credentials = SMAPICredentials(**credentials_data) if credentials_data else None

        console_integration = AmazonDeveloperConsoleIntegration(credentials)
        instructions = console_integration.generate_setup_instructions(
            skill_config, skill_id
        )

        return jsonify({"success": True, "instructions": instructions})

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error generating instructions: {e}")
        return (
            jsonify(
                {"success": False, "message": f"Error generating instructions: {e}"}
            ),
            500,
        )


# (import moved to top of file)


def register_amazon_console_routes(app: Flask) -> None:
    """Register Amazon Developer Console routes with the Flask app."""
    app.register_blueprint(amazon_console_bp)

    # Add template context processors
    @app.context_processor
    def _inject_amazon_console_context():
        return {
            "has_smapi_credentials": "authenticated_credentials" in session,
            "vendor_info": session.get("authenticated_credentials", {}).get(
                "vendor_info"
            ),
        }

    _unused_inject_amazon_console_context = _inject_amazon_console_context
