# Configuration Management System

## Overview

The HA External Connector supports three configuration generations with indefinite
backward compatibility, providing users complete choice in their configuration
approach while offering optional migration to advanced features.

## Configuration Generations

### Generation 1 - Environment Variables (Official HA)

**Status**: ✅ Supported indefinitely

Uses environment variables directly in Lambda functions:

- `BASE_URL` - Home Assistant base URL
- `LONG_LIVED_ACCESS_TOKEN` - HA authentication token
- `NOT_VERIFY_SSL` - SSL verification flag
- `DEBUG` - Debug logging level

**Benefits**: Simple setup, matches official Home Assistant patterns
**Use Case**: Users who prefer minimal configuration complexity

### Generation 2 - CloudFlare + SSM (Current Default)

**Status**: ✅ Supported indefinitely

Uses SSM Parameter Store with JSON configuration at `/ha-alexa/appConfig`:

```json
{
  "base_url": "https://jarvis.hessenflow.net",
  "long_lived_access_token": "<HA_TOKEN>",
  "client_id": "<CLOUDFLARE_CLIENT_ID>",
  "client_secret": "<CLOUDFLARE_CLIENT_SECRET>",
  "proxy_url": "https://jarvis.hessenflow.net"
}
```

**Benefits**: Enhanced security with encrypted parameters, CloudFlare integration
**Use Case**: Current production deployments with CloudFlare OAuth

### Generation 3 - Standardized SSM Paths (Optional Advanced)

**Status**: 🚀 Available for optional migration

Uses structured SSM parameters under `/home-assistant/alexa/*`:

#### SSM Parameter Structure

**Core Configuration:**

```bash
/home-assistant/alexa/core/base_url
/home-assistant/alexa/core/long_lived_access_token
/home-assistant/alexa/core/timeout
/home-assistant/alexa/core/verify_ssl
```

**CloudFlare Configuration:**

```bash
/home-assistant/alexa/cloudflare/client_id
/home-assistant/alexa/cloudflare/client_secret
/home-assistant/alexa/cloudflare/redirect_uri
/home-assistant/alexa/cloudflare/scope
/home-assistant/alexa/cloudflare/proxy_url
```

**Lambda Function ARNs:**

```bash
/home-assistant/alexa/lambda/configuration_manager_arn
/home-assistant/alexa/lambda/cloudflare_security_gateway_arn
/home-assistant/alexa/lambda/smart_home_bridge_arn
```

**Cache Configuration:**

```bash
/home-assistant/alexa/lambda/cache/shared_cache_table
/home-assistant/alexa/lambda/cache/oauth_token_cache_table
/home-assistant/alexa/lambda/cache/ttl_seconds
```

**Security Configuration:**

```bash
/home-assistant/alexa/lambda/security/alexa_secret
/home-assistant/alexa/lambda/security/wrapper_secret
/home-assistant/alexa/lambda/security/api_key
/home-assistant/alexa/lambda/security/max_request_size
```

#### Generation 3 Benefits

- **Granular Control**: Individual parameter management and monitoring
- **Enhanced Security**: Separate encryption and access control per parameter
- **Standardized Paths**: Consistent structure across all Lambda functions
- **Advanced Monitoring**: Parameter-level CloudWatch integration
- **Cross-Lambda Communication**: Structured ARN and configuration sharing

#### Optional Migration Process

Generation 3 migration is completely optional and user-driven:

**Step 1: Assess Current Configuration**

```bash
# The Configuration Manager automatically detects your current generation
# No action required - assessment is automatic
```

**Step 2: Create Gen 3 Parameters (If Desired)**

```bash
# Core configuration
aws ssm put-parameter --name "/home-assistant/alexa/core/base_url" \
  --value "https://jarvis.hessenflow.net" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/core/long_lived_access_token" \
  --value "<YOUR_HA_TOKEN>" \
  --type "SecureString"

# Lambda ARNs
aws ssm put-parameter --name "/home-assistant/alexa/lambda/cloudflare_security_gateway_arn" \
  --value "arn:aws:lambda:us-east-1:719118582283:function:CloudFlare-Security-Gateway" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/lambda/smart_home_bridge_arn" \
  --value "arn:aws:lambda:us-east-1:719118582283:function:HomeAssistant" \
  --type "String"

# Cache configuration
aws ssm put-parameter --name "/home-assistant/alexa/lambda/cache/shared_cache_table" \
  --value "ha-external-connector-config-cache" \
  --type "String"
```

**Step 3: Update Lambda Environment (Optional)**

```bash
# Update Lambda functions to use Gen 3 base path
aws lambda update-function-configuration \
  --function-name CloudFlare-Security-Gateway \
  --environment Variables='{APP_CONFIG_PATH="/home-assistant/alexa/"}'

aws lambda update-function-configuration \
  --function-name HomeAssistant \
  --environment Variables='{APP_CONFIG_PATH="/home-assistant/alexa/"}'
```

## Configuration Setup Wizard

### Automated Setup Tool

The Configuration Setup Wizard provides user-friendly tools for all generations:

**Features:**

- **Generation Detection**: Automatically identifies current configuration
- **Health Validation**: Verifies configuration completeness and access
- **IAM Policy Setup**: Creates required permissions automatically
- **Optional Migration**: Offers Gen 3 upgrade without pressure
- **Rollback Support**: Safe migration with rollback capabilities

### Wizard Implementation

```python
class ConfigurationWizard:
    """User-friendly configuration management."""
    
    def detect_generation(self) -> str:
        """Detect current configuration generation."""
        if self._check_gen3_parameters():
            return "gen3"
        elif self._check_gen2_parameter():
            return "gen2"
        else:
            return "gen1"
    
    def validate_health(self, generation: str) -> bool:
        """Validate configuration health for detected generation."""
        if generation == "gen3":
            return self._validate_gen3_parameters()
        elif generation == "gen2":
            return self._validate_gen2_configuration()
        else:
            return self._validate_gen1_environment()
    
    def offer_migration(self, current_gen: str) -> None:
        """Offer optional migration to Gen 3."""
        if current_gen == "gen3":
            print("🎉 You're already using the latest Gen 3 configuration!")
            return
        
        print(f"\n🚀 Optional Migration to Gen 3 Available")
        print("Benefits of Gen 3:")
        print("  ✅ Enhanced security with granular parameter control")
        print("  ✅ Advanced monitoring and alerting capabilities")
        print("  ✅ Standardized paths across all Lambda functions")
        print("  ✅ Cross-Lambda communication optimization")
        print("  ⚠️  Your current setup will continue working indefinitely")
        
        migrate = input(f"\nWould you like to migrate from {current_gen.upper()} to Gen 3? (y/n): ")
        
        if migrate.lower() == 'y':
            self._perform_migration(current_gen)
        else:
            print(f"✅ Staying with {current_gen.upper()} - your choice is respected!")
```

### IAM Policy Requirements

**Comprehensive Cross-Lambda Policy:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:PutParameter"
            ],
            "Resource": [
                "arn:aws:ssm:*:*:parameter/ha-alexa/*",
                "arn:aws:ssm:*:*:parameter/home-assistant/alexa/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:ConfigurationManager",
                "arn:aws:lambda:*:*:function:CloudFlare-Security-Gateway",
                "arn:aws:lambda:*:*:function:HomeAssistant"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/ha-external-connector-config-cache",
                "arn:aws:dynamodb:*:*:table/ha-external-connector-oauth-cache"
            ]
        }
    ]
}
```

## Configuration Philosophy

### User Choice and Respect

- **Indefinite Support**: All generations (Gen 1/2/3) supported forever
- **User-Driven Migration**: Migration to Gen 3 is optional, never required
- **Setup Assistance**: Wizard helps with initial setup and IAM policies
- **No Pressure**: Users can stay with current generation indefinitely

### Benefits by Generation

**Gen 1 Users**: Can stay with environment variables forever
**Gen 2 Users**: Can keep CloudFlare + SSM setup indefinitely  
**Gen 3 Users**: Get advanced features and standardized paths
**All Users**: Benefit from improved setup and management tools

### Implementation Status

✅ **Enhanced Configuration Manager validation** - Content-aware error detection  
✅ **Comprehensive cross-Lambda permissions** - Full IAM policy for ecosystem
operations  
✅ **Configuration path analysis complete** - All three generations documented  
✅ **Setup wizard specification** - User-friendly tools for configuration management  
📋 **Ready for implementation** - Detailed plan for indefinite backward compatibility  

### Next Steps

1. **Implement robust backward compatibility** in Configuration Manager for all generations
2. **Create setup wizard** with automatic IAM policy setup and validation  
3. **Build optional migration tools** for users who want Gen 3 features
4. **Deploy configuration management front-end** (CLI and web interface)
5. **Provide ongoing support** for all generations indefinitely

The focus is on **user empowerment** and **choice preservation** while providing
optional paths to enhanced functionality without forced migrations or deprecation.