# Configuration Standardization Plan - Gen 3

## Generation 3 Configuration Architecture

### SSM Parameter Structure

**Core Configuration Paths (Your Definitions):**

```python
# Gen 3 Configuration Storage Paths (your defined structure)
SSM_CORE_CONFIG_PATH = "/home-assistant/alexa/core"
SSM_CLOUDFLARE_CONFIG_PATH = "/home-assistant/alexa/cloudflare"
SSM_LAMBDA_CONFIG_PATH = "/home-assistant/alexa/lambda"
SSM_CACHE_CONFIG_PATH = "/home-assistant/alexa/lambda/cache"
SSM_SECURITY_CONFIG_PATH = "/home-assistant/alexa/lambda/security"

# APP_CONFIG_PATH: Base reference point for finding SSM parameters
# Gen 3: /home-assistant/alexa/ (base for structured parameters)
APP_CONFIG_PATH_GEN3_DEFAULT = "/home-assistant/alexa/"
```

### Required SSM Parameters for Full Gen 3 Operation

**Core Configuration:**

```bash
# Home Assistant Core Settings
/home-assistant/alexa/core/base_url
/home-assistant/alexa/core/long_lived_access_token
/home-assistant/alexa/core/timeout
/home-assistant/alexa/core/verify_ssl
```

**CloudFlare Configuration:**

```bash
# CloudFlare OAuth and Proxy Settings
/home-assistant/alexa/cloudflare/client_id
/home-assistant/alexa/cloudflare/client_secret
/home-assistant/alexa/cloudflare/redirect_uri
/home-assistant/alexa/cloudflare/scope
/home-assistant/alexa/cloudflare/proxy_url
```

**Lambda Function ARNs:**

```bash
# Core Lambda ARNs (required for cross-Lambda communication)
/home-assistant/alexa/lambda/configuration_manager_arn
/home-assistant/alexa/lambda/oauth_gateway_arn
/home-assistant/alexa/lambda/smart_home_bridge_arn
```

**Cache Configuration:**

```bash
# DynamoDB Table Names and Cache Settings
/home-assistant/alexa/lambda/cache/shared_cache_table
/home-assistant/alexa/lambda/cache/oauth_token_cache_table
/home-assistant/alexa/lambda/cache/ttl_seconds
```

**Security Configuration:**

```bash
# Security Tokens and Validation Settings
/home-assistant/alexa/lambda/security/alexa_secret
/home-assistant/alexa/lambda/security/wrapper_secret
/home-assistant/alexa/lambda/security/api_key
/home-assistant/alexa/lambda/security/max_request_size
```

### Configuration Section Mapping

**Environment Variable to SSM Mapping:**

- `APP_CONFIG_PATH` → `/home-assistant/alexa/`
- Configuration sections map to subdirectories:
  - `ha_config` → `/home-assistant/alexa/core/`
  - `cloudflare_config` → `/home-assistant/alexa/cloudflare/`
  - `lambda_config` → `/home-assistant/alexa/lambda/`
  - `security_config` → `/home-assistant/alexa/lambda/security/`
  - Cache settings → `/home-assistant/alexa/lambda/cache/`

### Configuration Section Schemas

**ha_config (Core):**

```json
{
  "base_url": "https://jarvis.hessenflow.net",
  "long_lived_access_token": "<HA_TOKEN>",
  "timeout": "30",
  "verify_ssl": "true"
}
```

**cloudflare_config:**

```json
{
  "client_id": "<CLOUDFLARE_CLIENT_ID>",
  "client_secret": "<CLOUDFLARE_CLIENT_SECRET>",
  "redirect_uri": "https://pitangui.amazon.com/spa/skill/account-linking-status.html?vendorId=<VENDOR_ID>",
  "scope": "read:user",
  "proxy_url": "https://jarvis.hessenflow.net"
}
```

**lambda_config:**

```json
{
  "configuration_manager_arn": "arn:aws:lambda:us-east-1:719118582283:function:ConfigurationManager",
  "oauth_gateway_arn": "arn:aws:lambda:us-east-1:719118582283:function:CloudFlare-Wrapper",
  "smart_home_bridge_arn": "arn:aws:lambda:us-east-1:719118582283:function:HomeAssistant"
}
```

**security_config:**

```json
{
  "alexa_secret": "<ALEXA_SECRET>",
  "wrapper_secret": "<WRAPPER_SECRET>",
  "api_key": "<API_KEY>",
  "max_request_size": "1048576"
}
```

**cache_config:**

```json
{
  "shared_cache_table": "ha-external-connector-config-cache",
  "oauth_token_cache_table": "ha-external-connector-oauth-cache",
  "ttl_seconds": "300"
}
```

### Migration Strategy

**Step 1: Set Lambda ARNs**

```bash
aws ssm put-parameter --name "/home-assistant/alexa/lambda/oauth_gateway_arn" \
  --value "arn:aws:lambda:us-east-1:719118582283:function:CloudFlare-Wrapper" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/lambda/smart_home_bridge_arn" \
  --value "arn:aws:lambda:us-east-1:719118582283:function:HomeAssistant" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/lambda/configuration_manager_arn" \
  --value "arn:aws:lambda:us-east-1:719118582283:function:ConfigurationManager" \
  --type "String"
```

**Step 2: Set Cache Configuration**

```bash
aws ssm put-parameter --name "/home-assistant/alexa/lambda/cache/shared_cache_table" \
  --value "ha-external-connector-config-cache" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/lambda/cache/oauth_token_cache_table" \
  --value "ha-external-connector-oauth-cache" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/lambda/cache/ttl_seconds" \
  --value "300" \
  --type "String"
```

**Step 3: Set Core Configuration**

```bash
# Example: Set HA core configuration
aws ssm put-parameter --name "/home-assistant/alexa/core/base_url" \
  --value "https://jarvis.hessenflow.net" \
  --type "String"

aws ssm put-parameter --name "/home-assistant/alexa/core/long_lived_access_token" \
  --value "<YOUR_HA_TOKEN>" \
  --type "SecureString"
```

**Step 4: Update Lambda Environment Variables**

```bash
# Update all Lambda functions to use Gen 3 base path
aws lambda update-function-configuration \
  --function-name CloudFlare-Wrapper \
  --environment Variables='{APP_CONFIG_PATH="/home-assistant/alexa/"}'

aws lambda update-function-configuration \
  --function-name HomeAssistant \
  --environment Variables='{APP_CONFIG_PATH="/home-assistant/alexa/",BASE_URL="https://jarvis.hessenflow.net"}'

aws lambda update-function-configuration \
  --function-name ConfigurationManager \
  --environment Variables='{APP_CONFIG_PATH="/home-assistant/alexa/"}'
```

### Generation Detection Logic

The system automatically detects configuration generation:

1. **Gen 3 Detection**: Checks for structured SSM parameters under APP_CONFIG_PATH
2. **Gen 2 Fallback**: JSON dump approach under /ha-alexa/appConfig
3. **Gen 1 Fallback**: Pure environment variables

### Benefits of Gen 3

- **Hierarchical Organization**: Clear path structure with logical grouping
- **Enhanced Security**: SecureString parameter type for sensitive data
- **Cross-Lambda Coordination**: ARN-based service discovery
- **Performance Optimization**: Structured caching strategies
- **Operational Clarity**: Clear parameter organization and naming
- **Granular Access Control**: Individual parameter-level permissions

### Validation Commands

```bash
# Check Lambda ARN parameters
aws ssm get-parameters --names \
  "/home-assistant/alexa/lambda/oauth_gateway_arn" \
  "/home-assistant/alexa/lambda/smart_home_bridge_arn" \
  "/home-assistant/alexa/lambda/configuration_manager_arn"

# Check core configuration
aws ssm get-parameters --names \
  "/home-assistant/alexa/core/base_url" \
  "/home-assistant/alexa/core/long_lived_access_token"

# Check cache configuration
aws ssm get-parameters --names \
  "/home-assistant/alexa/lambda/cache/shared_cache_table" \
  "/home-assistant/alexa/lambda/cache/oauth_token_cache_table"

# Check security configuration
aws ssm get-parameters --names \
  "/home-assistant/alexa/lambda/security/alexa_secret" \
  "/home-assistant/alexa/lambda/security/wrapper_secret" \
  --with-decryption
```

This Gen 3 architecture provides the foundation for enterprise-grade configuration management with your defined hierarchical structure for enhanced security, performance, and maintainability.
