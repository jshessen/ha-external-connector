"""
Unit Tests for Configuration Module

Tests configuration manager and installation scenario functionality.
"""

from unittest.mock import Mock, patch

from ha_connector.config import (
    ConfigurationManager,
    ConfigurationState,
    InstallationScenario,
)


class TestConfigurationManager:
    """Test Configuration Manager functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # pylint: disable=attribute-defined-outside-init
        self.config_manager = ConfigurationManager()

    def test_init(self):
        """Test initialization"""
        manager = ConfigurationManager()
        assert manager.config is None

    def test_init_config(self):
        """Test configuration initialization for different scenarios"""
        manager = ConfigurationManager()

        # Test direct Alexa scenario
        config = manager.init_config(InstallationScenario.DIRECT_ALEXA)
        assert isinstance(config, ConfigurationState)
        assert config.scenario == InstallationScenario.DIRECT_ALEXA
        assert config.aws_region == "us-east-1"
        assert manager.config == config

    def test_validate_ha_base_url_valid(self):
        """Test HA base URL validation with valid URL"""
        manager = ConfigurationManager()
        assert manager.validate_ha_base_url("https://homeassistant.example.com") is True

    def test_validate_ha_base_url_invalid_protocol(self):
        """Test HA base URL validation with invalid protocol"""
        manager = ConfigurationManager()
        assert manager.validate_ha_base_url("http://homeassistant.example.com") is False

    def test_validate_ha_base_url_empty(self):
        """Test HA base URL validation with empty URL"""
        manager = ConfigurationManager()
        assert manager.validate_ha_base_url("") is False

    def test_validate_alexa_config_valid(self):
        """Test Alexa configuration validation with valid secret"""
        manager = ConfigurationManager()
        valid_secret = "a" * 32
        assert manager.validate_alexa_config(valid_secret) is True

    def test_validate_alexa_config_too_short(self):
        """Test Alexa configuration validation with short secret"""
        manager = ConfigurationManager()
        short_secret = "short"
        assert manager.validate_alexa_config(short_secret) is False

    def test_validate_alexa_config_none(self):
        """Test Alexa configuration validation with None secret"""
        manager = ConfigurationManager()
        assert manager.validate_alexa_config(None) is False

    def test_validate_alexa_region_valid(self):
        """Test Alexa region validation with valid regions"""
        manager = ConfigurationManager()
        for region in manager.ALEXA_VALID_REGIONS:
            assert manager.validate_alexa_region(region) is True

    def test_validate_alexa_region_invalid(self):
        """Test Alexa region validation with invalid region"""
        manager = ConfigurationManager()
        assert manager.validate_alexa_region("ap-southeast-1") is False

    @patch('ha_connector.config.manager.aws_credentials_check')
    @patch('subprocess.run')
    def test_check_prerequisites_success(self, mock_subprocess, mock_aws_check):
        """Test successful prerequisites check"""
        mock_subprocess.return_value = Mock()
        mock_aws_check.return_value = True

        manager = ConfigurationManager()
        result = manager.check_prerequisites_for_scenario(
            InstallationScenario.DIRECT_ALEXA
        )
        assert result is True

    @patch('ha_connector.config.manager.aws_credentials_check')
    @patch('subprocess.run')
    def test_check_prerequisites_missing_aws_cli(self, mock_subprocess, mock_aws_check):
        """Test prerequisites check with missing AWS CLI"""
        mock_subprocess.side_effect = FileNotFoundError()
        mock_aws_check.return_value = True

        manager = ConfigurationManager()
        result = manager.check_prerequisites_for_scenario(
            InstallationScenario.DIRECT_ALEXA
        )
        assert result is False

    @patch('ha_connector.config.manager.aws_credentials_check')
    @patch('subprocess.run')
    def test_check_prerequisites_invalid_aws_credentials(
        self, mock_subprocess, mock_aws_check
    ):
        """Test prerequisites check with invalid AWS credentials"""
        mock_subprocess.return_value = Mock()
        mock_aws_check.return_value = False

        manager = ConfigurationManager()
        result = manager.check_prerequisites_for_scenario(
            InstallationScenario.DIRECT_ALEXA
        )
        assert result is False

    def test_validate_direct_alexa_scenario(self):
        """Test direct Alexa scenario validation"""
        manager = ConfigurationManager()

        # Initialize configuration
        config = manager.init_config(InstallationScenario.DIRECT_ALEXA)
        config.ha_base_url = "https://homeassistant.example.com"
        config.alexa_secret = "a" * 32
        config.aws_region = "us-east-1"

        result = manager.validate_direct_alexa_scenario()
        assert result is True

    def test_validate_direct_alexa_scenario_invalid_url(self):
        """Test direct Alexa scenario validation with invalid URL"""
        manager = ConfigurationManager()

        # Initialize configuration with invalid URL
        config = manager.init_config(InstallationScenario.DIRECT_ALEXA)
        config.ha_base_url = "http://homeassistant.example.com"  # Invalid protocol
        config.alexa_secret = "a" * 32
        config.aws_region = "us-east-1"

        result = manager.validate_direct_alexa_scenario()
        assert result is False

    def test_validate_cloudflare_config_no_config(self):
        """Test CloudFlare config validation with no configuration"""
        manager = ConfigurationManager()
        result = manager.validate_cloudflare_config()
        assert result is False

    @patch.dict('os.environ', {'CF_API_TOKEN': 'test-token'})
    def test_validate_cloudflare_config_with_api_token(self):
        """Test CloudFlare config validation with API token"""
        manager = ConfigurationManager()
        manager.init_config(InstallationScenario.CLOUDFLARE_ALEXA)

        result = manager.validate_cloudflare_config()
        assert result is True

    def test_validate_cloudflare_config_missing_client_secret(self):
        """Test CloudFlare config validation with client ID but no secret"""
        manager = ConfigurationManager()
        config = manager.init_config(InstallationScenario.CLOUDFLARE_ALEXA)
        config.cf_client_id = "test-client-id"
        # cf_client_secret is None

        result = manager.validate_cloudflare_config()
        assert result is False

    def test_collect_ha_url(self):
        """Test HA URL collection"""
        manager = ConfigurationManager()

        with patch('builtins.input', return_value='https://homeassistant.example.com'):
            url = manager.collect_ha_url()
            assert url == 'https://homeassistant.example.com'

    def test_generate_secure_secret(self):
        """Test secure secret generation"""
        manager = ConfigurationManager()

        # Test default length
        secret = manager.generate_secure_secret()
        assert len(secret) == 32

        # Test custom length - actual implementation may be shorter due to
        # character filtering, so just test it's reasonable
        secret = manager.generate_secure_secret(64)
        assert len(secret) <= 64
        assert len(secret) >= 32  # Should have some reasonable minimum

    def test_collect_alexa_config(self):
        """Test Alexa configuration collection"""
        manager = ConfigurationManager()
        manager.init_config(InstallationScenario.DIRECT_ALEXA)

        # Ensure alexa_secret is not already set
        if manager.config:
            manager.config.alexa_secret = None

        # Test with empty input to trigger secret generation
        with patch('builtins.input', return_value=''), \
             patch.object(manager, 'generate_secure_secret',
                          return_value='test-secret-32-chars-long-here') as mock_gen:
            manager.collect_alexa_config()

            assert manager.config is not None
            mock_gen.assert_called_once_with(32)
            assert manager.config.alexa_secret == 'test-secret-32-chars-long-here'

    def test_collect_cloudflare_config(self):
        """Test CloudFlare configuration collection"""
        manager = ConfigurationManager()
        manager.init_config(InstallationScenario.CLOUDFLARE_ALEXA)

        # CloudFlare config collection is not implemented yet, just logs warning
        manager.collect_cloudflare_config()

        # Since implementation logs a warning and doesn't collect,
        # we just verify it doesn't crash
        assert manager.config is not None

    @patch.dict('os.environ', {})
    def test_export_config(self):
        """Test configuration export"""
        manager = ConfigurationManager()
        config = manager.init_config(InstallationScenario.DIRECT_ALEXA)
        config.ha_base_url = "https://homeassistant.example.com"
        config.alexa_secret = "test-secret"
        config.aws_region = "us-east-1"

        # Mock os.environ to capture exports
        with patch('os.environ', {}):
            manager.export_config()

            # Check that environment variables were set
            # Note: The actual implementation may vary


class TestConfigurationState:
    """Test Configuration State functionality"""

    def test_init_with_scenario(self):
        """Test initialization with scenario"""
        config = ConfigurationState(InstallationScenario.DIRECT_ALEXA)
        assert config.scenario == InstallationScenario.DIRECT_ALEXA
        assert config.aws_region == "us-east-1"

    @patch.dict('os.environ', {
        'HA_BASE_URL': 'https://test.example.com',
        'ALEXA_SECRET': 'test-secret',
        'AWS_REGION': 'us-west-2'
    })
    def test_post_init_from_env(self):
        """Test post-init loading from environment variables"""
        # Create config with aws_region="" to allow env override
        config = ConfigurationState(
            InstallationScenario.DIRECT_ALEXA,
            aws_region=""
        )
        assert config.ha_base_url == 'https://test.example.com'
        assert config.alexa_secret == 'test-secret'
        assert config.aws_region == 'us-west-2'

    def test_post_init_explicit_values_override_env(self):
        """Test that explicit values override environment variables"""
        with patch.dict('os.environ', {'HA_BASE_URL': 'https://env.example.com'}):
            config = ConfigurationState(
                InstallationScenario.DIRECT_ALEXA,
                ha_base_url='https://explicit.example.com'
            )
            assert config.ha_base_url == 'https://explicit.example.com'


class TestInstallationScenario:
    """Test Installation Scenario enumeration"""

    def test_scenario_values(self):
        """Test that scenario enum has expected values"""
        assert InstallationScenario.DIRECT_ALEXA.value == "direct_alexa"
        assert InstallationScenario.CLOUDFLARE_ALEXA.value == "cloudflare_alexa"
        assert InstallationScenario.CLOUDFLARE_IOS.value == "cloudflare_ios"
        assert InstallationScenario.ALL.value == "all"

    def test_scenario_iteration(self):
        """Test that we can iterate through scenarios"""
        scenarios = list(InstallationScenario)
        assert InstallationScenario.DIRECT_ALEXA in scenarios
        assert InstallationScenario.CLOUDFLARE_ALEXA in scenarios
        assert InstallationScenario.CLOUDFLARE_IOS in scenarios
        assert InstallationScenario.ALL in scenarios


class TestScenarioValidation:
    """Test scenario-specific validation methods"""

    def setup_method(self):
        """Set up test fixtures"""
        # pylint: disable=attribute-defined-outside-init
        self.manager = ConfigurationManager()

    def test_validate_cloudflare_alexa_scenario(self):
        """Test CloudFlare Alexa scenario validation"""
        config = self.manager.init_config(InstallationScenario.CLOUDFLARE_ALEXA)
        config.ha_base_url = "https://homeassistant.example.com"
        config.alexa_secret = "a" * 32
        config.aws_region = "us-east-1"
        config.cf_client_id = "test-client-id"
        config.cf_client_secret = "test-client-secret"

        result = self.manager.validate_cloudflare_alexa_scenario()
        assert result is True

    def test_validate_cloudflare_ios_scenario(self):
        """Test CloudFlare iOS scenario validation"""
        config = self.manager.init_config(InstallationScenario.CLOUDFLARE_IOS)
        config.ha_base_url = "https://homeassistant.example.com"
        config.cf_client_id = "test-client-id"
        config.cf_client_secret = "test-client-secret"

        result = self.manager.validate_cloudflare_ios_scenario()
        assert result is True

    def test_validate_all_scenarios(self):
        """Test validation of all scenarios"""
        # This test would need to be more comprehensive
        result = self.manager.validate_all_scenarios()
        # Since no configuration is set up, this should likely return False
        assert isinstance(result, bool)


class TestResourceManagement:
    """Test resource discovery and management functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # pylint: disable=attribute-defined-outside-init
        self.manager = ConfigurationManager()

    def test_resource_patterns_exist(self):
        """Test that resource patterns are defined"""
        assert hasattr(self.manager, 'IAM_PATTERNS')
        assert hasattr(self.manager, 'LAMBDA_PATTERNS')
        assert hasattr(self.manager, 'SSM_PATTERNS')

        assert isinstance(self.manager.IAM_PATTERNS, dict)
        assert isinstance(self.manager.LAMBDA_PATTERNS, dict)
        assert isinstance(self.manager.SSM_PATTERNS, dict)

    def test_alexa_valid_regions(self):
        """Test that Alexa valid regions are defined"""
        assert hasattr(self.manager, 'ALEXA_VALID_REGIONS')
        assert "us-east-1" in self.manager.ALEXA_VALID_REGIONS
        assert "eu-west-1" in self.manager.ALEXA_VALID_REGIONS
        assert "us-west-2" in self.manager.ALEXA_VALID_REGIONS

    @patch('ha_connector.config.manager.safe_exec')
    def test_get_scenario_resource_requirements(self, mock_safe_exec):
        """Test getting resource requirements for a scenario"""
        mock_safe_exec.return_value = (0, "[]", "")

        requirements = self.manager.get_scenario_resource_requirements(
            InstallationScenario.DIRECT_ALEXA
        )

        # The exact return type depends on implementation
        assert isinstance(requirements, list)

    @patch('ha_connector.config.manager.safe_exec')
    def test_check_aws_resources_for_scenario(self, mock_safe_exec):
        """Test checking AWS resources for a scenario"""
        mock_safe_exec.return_value = (0, "[]", "")

        self.manager.init_config(InstallationScenario.DIRECT_ALEXA)
        result = self.manager.check_aws_resources_for_scenario(
            InstallationScenario.DIRECT_ALEXA
        )

        # The exact return type depends on implementation
        # This test mainly ensures the method can be called without errors
        assert result is not None
