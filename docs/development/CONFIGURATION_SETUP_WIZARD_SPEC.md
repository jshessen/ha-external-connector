# Configuration Setup Wizard Specification

## Overview

This document specifies the design and implementation of the Configuration Setup Wizard - a user-friendly front-end tool that helps users set up the necessary minimum configuration (IAM policies and SSM definitions) for the Configuration Manager and offers optional migration to Gen 3.

## Core Principles

1. **Indefinite Backward Compatibility**: Support Gen 1/2 indefinitely
2. **User Choice**: Migration to Gen 3 is optional, not required
3. **Minimum Viable Setup**: Focus on getting users operational quickly
4. **Guided Experience**: Step-by-step wizard for complex AWS setup
5. **Safety First**: Backup and rollback capabilities for all operations

## Tool Components

### 1. Configuration Detection Engine

```python
class ConfigurationDetector:
    """Detects current configuration state and validates setup."""

    def detect_current_setup(self):
        """Detect existing configuration across all generations."""
        return {
            'version': self._detect_version(),
            'lambda_functions': self._detect_lambda_functions(),
            'iam_policies': self._validate_iam_policies(),
            'ssm_parameters': self._validate_ssm_parameters(),
            'health_status': self._check_health()
        }

    def _detect_version(self):
        """Determine which generation is currently in use."""
        if self._has_gen3_parameters():
            return "gen3"
        elif self._has_gen2_parameters():
            return "gen2"
        elif self._has_gen1_environment():
            return "gen1"
        else:
            return "none"

    def validate_minimum_requirements(self, version):
        """Ensure minimum IAM policies and SSM access exist."""
        requirements = {
            'gen1': ['lambda:InvokeFunction', 'logs:CreateLogGroup'],
            'gen2': ['lambda:InvokeFunction', 'ssm:GetParameter', 'ssm:GetParametersByPath'],
            'gen3': ['lambda:InvokeFunction', 'ssm:GetParameter', 'ssm:GetParametersByPath', 'dynamodb:GetItem']
        }

        return self._validate_policies(requirements.get(version, []))
```

### 2. Setup Wizard Interface

#### CLI Version

```python
class ConfigurationSetupWizard:
    """Interactive CLI wizard for configuration setup."""

    def run(self):
        """Main wizard flow."""
        print("🏠 Home Assistant Alexa Configuration Setup Wizard")
        print("=" * 50)

        # Detect current state
        current_state = self.detector.detect_current_setup()

        if current_state['version'] != 'none':
            self._handle_existing_configuration(current_state)
        else:
            self._handle_new_setup()

    def _handle_existing_configuration(self, state):
        """Handle cases where configuration already exists."""
        print(f"✅ Detected existing {state['version'].upper()} configuration")

        if state['health_status']['healthy']:
            print("✅ Configuration is healthy and operational")
            self._offer_optional_migration(state['version'])
        else:
            print("⚠️  Configuration issues detected:")
            for issue in state['health_status']['issues']:
                print(f"   - {issue}")
            self._offer_repair_options(state)

    def _handle_new_setup(self):
        """Guide user through initial setup."""
        print("🆕 No existing configuration detected. Let's set one up!")

        setup_type = self._prompt_setup_type()
        aws_region = self._prompt_aws_region()
        ha_details = self._prompt_home_assistant_details()

        if setup_type in ['gen2', 'gen3']:
            cloudflare_details = self._prompt_cloudflare_details()

        # Execute setup
        self._execute_setup(setup_type, aws_region, ha_details, cloudflare_details)

    def _offer_optional_migration(self, current_version):
        """Offer optional migration to Gen 3."""
        if current_version == 'gen3':
            print("🎉 You're already using the latest Gen 3 configuration!")
            return

        print(f"\n🚀 Optional Migration to Gen 3 Available")
        print("Benefits of Gen 3:")
        print("  • Standardized paths (/home-assistant/alexa/*)")
        print("  • Granular parameter control")
        print("  • Enhanced monitoring and auditability")
        print("  • Better cross-Lambda coordination")
        print("  • Advanced caching and performance features")

        migrate = input(f"\nWould you like to migrate from {current_version.upper()} to Gen 3? (y/n): ")

        if migrate.lower() == 'y':
            self._execute_migration_to_gen3(current_version)
        else:
            print(f"✅ Keeping your current {current_version.upper()} configuration")
            print("   (You can migrate later by running this wizard again)")
```

#### Web Interface Specification

```typescript
interface ConfigurationWizardState {
  currentStep: 'detection' | 'setup-type' | 'aws-config' | 'ha-config' | 'cloudflare-config' | 'review' | 'execute';
  detectedConfig?: ConfigurationState;
  setupChoices: {
    generation: 'gen1' | 'gen2' | 'gen3';
    awsRegion: string;
    homeAssistant: {
      baseUrl: string;
      token: string;
      sslVerify: boolean;
    };
    cloudflare?: {
      clientId: string;
      clientSecret: string;
      wrapperSecret: string;
    };
  };
  migrationOffered: boolean;
  setupProgress: SetupProgress;
}

interface SetupProgress {
  steps: Array<{
    name: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    details?: string;
  }>;
  currentStep: number;
  canRollback: boolean;
}
```

### 3. IAM Policy Management

```python
class IAMPolicyManager:
    """Manages IAM policies for Configuration Manager."""

    def ensure_minimum_policies(self, generation: str):
        """Ensure minimum required IAM policies exist."""
        policy_templates = {
            'gen1': self._get_gen1_policy_template(),
            'gen2': self._get_gen2_policy_template(),
            'gen3': self._get_gen3_policy_template()
        }

        required_policy = policy_templates[generation]
        existing_policies = self._get_existing_policies()

        missing_permissions = self._compare_policies(required_policy, existing_policies)

        if missing_permissions:
            self._create_or_update_policies(missing_permissions)

        return self._validate_policy_attachment()

    def _get_gen1_policy_template(self):
        """Minimum policy for Gen 1 (environment variable) setup."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:lambda:*:*:function:HomeAssistant",
                        "arn:aws:lambda:*:*:function:ConfigurationManager",
                        "arn:aws:logs:*:*:*"
                    ]
                }
            ]
        }

    def _get_gen2_policy_template(self):
        """Enhanced policy for Gen 2 (SSM + CloudFlare) setup."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction",
                        "ssm:GetParameter",
                        "ssm:GetParametersByPath",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:lambda:*:*:function:HomeAssistant",
                        "arn:aws:lambda:*:*:function:CloudFlare-Security-Gateway",
                        "arn:aws:lambda:*:*:function:ConfigurationManager",
                        "arn:aws:ssm:*:*:parameter/ha-alexa/*",
                        "arn:aws:logs:*:*:*"
                    ]
                }
            ]
        }

    def _get_gen3_policy_template(self):
        """Comprehensive policy for Gen 3 (full feature) setup."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction",
                        "ssm:GetParameter",
                        "ssm:GetParametersByPath",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "cloudwatch:PutMetricData"
                    ],
                    "Resource": [
                        "arn:aws:lambda:*:*:function:HomeAssistant",
                        "arn:aws:lambda:*:*:function:CloudFlare-Security-Gateway",
                        "arn:aws:lambda:*:*:function:ConfigurationManager",
                        "arn:aws:ssm:*:*:parameter/home-assistant/alexa/*",
                        "arn:aws:dynamodb:*:*:table/ha-external-connector-*",
                        "arn:aws:logs:*:*:*"
                    ]
                }
            ]
        }
```

### 4. Migration Assistant

```python
class MigrationAssistant:
    """Handles optional migration between configuration generations."""

    def offer_migration(self, current_version: str):
        """Present migration options to user."""
        if current_version == 'gen3':
            return None  # Already on latest

        benefits = self._get_migration_benefits(current_version)
        risks = self._get_migration_risks(current_version)

        return {
            'from_version': current_version,
            'to_version': 'gen3',
            'benefits': benefits,
            'risks': risks,
            'estimated_time': self._estimate_migration_time(current_version),
            'backup_required': True,
            'rollback_supported': True
        }

    def execute_migration(self, from_version: str, options: dict):
        """Execute migration with full backup and rollback support."""
        try:
            # Step 1: Create comprehensive backup
            backup_id = self._create_backup(from_version)

            # Step 2: Validate current configuration
            if not self._validate_current_config(from_version):
                raise MigrationError("Current configuration is invalid")

            # Step 3: Create Gen 3 parameters
            if from_version == 'gen1':
                self._migrate_gen1_to_gen3()
            elif from_version == 'gen2':
                self._migrate_gen2_to_gen3()

            # Step 4: Validate Gen 3 configuration
            if not self._validate_gen3_config():
                self._rollback_migration(backup_id)
                raise MigrationError("Gen 3 configuration validation failed")

            # Step 5: Test Lambda functions with new config
            if not self._test_lambda_functions():
                self._rollback_migration(backup_id)
                raise MigrationError("Lambda function testing failed")

            # Step 6: Offer to cleanup old configuration
            if options.get('cleanup_old', False):
                self._cleanup_old_config(from_version)

            return {
                'success': True,
                'backup_id': backup_id,
                'new_version': 'gen3',
                'rollback_available': True
            }

        except Exception as e:
            # Auto-rollback on any failure
            if 'backup_id' in locals():
                self._rollback_migration(backup_id)
            raise MigrationError(f"Migration failed: {str(e)}")
```

### 5. Health Check and Validation

```python
class ConfigurationHealthCheck:
    """Ongoing health monitoring for all configuration generations."""

    def run_comprehensive_check(self):
        """Run full health check across all components."""
        results = {
            'overall_health': 'unknown',
            'configuration': self._check_configuration_health(),
            'lambda_functions': self._check_lambda_health(),
            'iam_policies': self._check_iam_health(),
            'connectivity': self._check_connectivity_health(),
            'performance': self._check_performance_health()
        }

        results['overall_health'] = self._calculate_overall_health(results)
        return results

    def _check_configuration_health(self):
        """Validate configuration parameters are accessible and valid."""
        version = self.detector.detect_current_setup()['version']

        if version == 'gen1':
            return self._check_gen1_config()
        elif version == 'gen2':
            return self._check_gen2_config()
        elif version == 'gen3':
            return self._check_gen3_config()
        else:
            return {'status': 'error', 'message': 'No configuration detected'}

    def _check_lambda_health(self):
        """Test Lambda function invocation and response."""
        functions_to_test = ['ConfigurationManager', 'HomeAssistant']
        results = {}

        for function_name in functions_to_test:
            try:
                response = self._invoke_lambda_test(function_name)
                results[function_name] = {
                    'status': 'healthy',
                    'response_time': response['response_time'],
                    'memory_used': response.get('memory_used', 'unknown')
                }
            except Exception as e:
                results[function_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return results
```

## User Experience Flow

### First-Time Setup

1. **Welcome & Detection**
   - Welcome message and purpose explanation
   - Automatic detection of existing configuration
   - AWS credentials and region verification

2. **Setup Type Selection** (if no existing config)
   - Gen 1: "Quick Start" (environment variables)
   - Gen 2: "Enhanced Security" (SSM + CloudFlare)
   - Gen 3: "Full Features" (standardized paths)

3. **Configuration Gathering**
   - Home Assistant URL and token
   - CloudFlare details (if Gen 2/3)
   - AWS region and account confirmation

4. **IAM Policy Setup**
   - Automatic detection of existing policies
   - Creation of missing policies
   - Attachment to appropriate roles

5. **Parameter Creation**
   - SSM parameter creation (if Gen 2/3)
   - Environment variable guidance (if Gen 1)
   - Encryption and security validation

6. **Testing & Validation**
   - Lambda function connectivity test
   - Home Assistant API connectivity test
   - End-to-end Alexa flow test (optional)

### Migration Flow

1. **Current State Analysis**
   - Detailed analysis of existing configuration
   - Identification of migration paths

2. **Migration Benefits Presentation**
   - Clear explanation of Gen 3 benefits
   - Honest assessment of migration complexity

3. **User Decision Point**
   - No pressure to migrate
   - Clear option to keep current setup
   - "Remind me later" option

4. **Migration Execution** (if chosen)
   - Comprehensive backup creation
   - Step-by-step migration with progress
   - Automatic rollback on any failure

5. **Post-Migration Validation**
   - Full functionality testing
   - Performance comparison
   - Optional cleanup of old configuration

## Implementation Phases

### Phase 1: Core Detection and Health Check (Month 1)

- Configuration detection engine
- Basic health check functionality
- IAM policy validation

### Phase 2: Setup Wizard CLI (Month 2)

- Interactive CLI wizard
- IAM policy auto-setup
- Basic migration tools

### Phase 3: Web Interface (Month 3)

- Web-based setup wizard
- Enhanced user experience
- Advanced migration features

### Phase 4: Production Ready (Month 4)

- Comprehensive testing
- Error handling and recovery
- User documentation

## Success Criteria

1. **Setup Success Rate**: >95% successful first-time setups
2. **User Satisfaction**: Positive feedback on ease of use
3. **Migration Adoption**: User-driven migration without pressure
4. **Support Reduction**: Fewer configuration-related support requests
5. **Backward Compatibility**: 100% support for existing Gen 1/2 deployments

This specification ensures that users can easily set up and manage their Home Assistant Alexa integration while maintaining full backward compatibility and providing optional migration paths to enhanced features.
