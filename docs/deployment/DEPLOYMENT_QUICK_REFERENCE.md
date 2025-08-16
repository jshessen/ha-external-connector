# Lambda Deployment Quick Reference

## 🚀 Simplified Deployment Commands

The deployment shell scripts have been removed as they were redundant technical debt. Use the deployment manager directly for all operations:

### **Individual Function Deployment**

```bash
# Deploy CloudFlare Security Gateway
python scripts/lambda_deployment/deployment_manager.py --deploy --function cloudflare_security_gateway

# Deploy Smart Home Bridge
python scripts/lambda_deployment/deployment_manager.py --deploy --function smart_home_bridge

# Deploy all functions at once
python scripts/lambda_deployment/deployment_manager.py --deploy --function all
```

### **Dry-Run Testing**

```bash
# Test deployments without making changes
python scripts/lambda_deployment/deployment_manager.py --deploy --function cloudflare_security_gateway --dry-run
python scripts/lambda_deployment/deployment_manager.py --deploy --function all --dry-run
```

### **Step-by-Step Operations**

```bash
# Build deployment files
python scripts/lambda_deployment/deployment_manager.py --build

# Package specific function
python scripts/lambda_deployment/deployment_manager.py --package --function smart_home_bridge

# Test deployed function
python scripts/lambda_deployment/deployment_manager.py --test --function smart_home_bridge

# Validate deployment files
python scripts/lambda_deployment/deployment_manager.py --validate

# Clean up deployment files
python scripts/lambda_deployment/deployment_manager.py --clean
```

### **What Was Removed**

- ❌ `deploy_enhanced_smart_home_bridge.sh` (116 lines of wrapper code)
- ❌ `deploy_cloudflare_security_gateway.sh` (97 lines of wrapper code)

### **Why Removed**

1. **100% Redundant** - All functionality moved to deployment_manager.py
2. **Better Error Handling** - Python provides superior error handling vs bash
3. **More Flexible** - Individual function deployment, dry-run support, testing
4. **Single Source of Truth** - One tool to maintain instead of three
5. **Reduced Technical Debt** - Eliminates duplicate validation and deployment logic

### **Migration Examples**

| Old Command | New Command |
|-------------|-------------|
| `bash deploy_cloudflare_security_gateway.sh --dry-run` | `python scripts/lambda_deployment/deployment_manager.py --deploy --function cloudflare_security_gateway --dry-run` |
| `bash deploy_enhanced_smart_home_bridge.sh` | `python scripts/lambda_deployment/deployment_manager.py --deploy --function smart_home_bridge` |
| Deploy both functions | `python scripts/lambda_deployment/deployment_manager.py --deploy --function all` |

The deployment manager provides all the same functionality with better validation, error handling, and flexibility.

## 🧪 Deployment Validation and Testing

### Comprehensive Testing After Deployment

**Alexa Smart Home Testing Suite**:

```bash
# Full testing suite after deployment
python tests/validation/tools/alexa_smart_home_testing_suite.py

# Discovery testing only
python tests/validation/tools/alexa_smart_home_testing_suite.py --discovery

# Test specific endpoints
python tests/validation/tools/alexa_smart_home_testing_suite.py --test <endpoint_id>

# Save test artifacts for analysis
python tests/validation/tools/alexa_smart_home_testing_suite.py --save-files
```

**Security Validation**:

```bash
# 12-point security framework validation
python scripts/demo_security.py

# Security demonstration and testing
python tests/validation/tools/cloudflare_security_gateway_testing_suite.py
```

### Performance Benchmarking

**Response Time Validation** (Target: Sub-500ms):

```bash
# Check deployment performance metrics  
python scripts/lambda_deployment/deployment_manager.py metrics

# SMAPI integration performance testing
python scripts/demo_smapi_integration.py

# Voice command response time testing
python tests/validation/tools/alexa_smart_home_testing_suite.py --performance
```

**Cache Performance Monitoring**:

- **Container Cache**: 0-1ms access (warm Lambda containers)
- **Shared Cache**: 20-50ms cross-function sharing (DynamoDB)
- **SSM Fallback**: 100-200ms authoritative source

## 🔄 Transfer Block Synchronization

### Lambda Function Code Synchronization

The deployment system manages **Transfer Blocks** - synchronized code sections between Lambda functions:

**Primary Transfer Block Locations**:
- **Source**: `src/ha_connector/integrations/alexa/lambda_functions/cloudflare_security_gateway.py` (line ~3149)
- **Target**: `src/ha_connector/integrations/alexa/lambda_functions/smart_home_bridge.py` (line ~255)

**Transfer Block Workflow**:

1. **Edit Primary Source**: Update the CloudFlare Security Gateway transfer block
2. **Copy Content**: Transfer block content between START/END markers
3. **Update Target**: Apply to Smart Home Bridge with service customizations
4. **Validate**: Test both functions independently

**Service Customizations**:
- Cache prefixes: `oauth_config_` → `bridge_config_`
- Function names: `"cloudflare_security_gateway"` → `"smart_home_bridge"`
- Service-specific constants and identifiers

## 📊 Deployment Monitoring

### Key Metrics to Monitor

**Performance Targets**:
- **Voice Command Response**: <500ms end-to-end
- **Lambda Cold Start**: <2 seconds
- **Security Validation**: <50ms OAuth validation
- **Cache Hit Rate**: >95% container, >80% shared

**Health Checks**:

```bash
# Overall system health
python scripts/agent_helper.py all

# SMAPI token health
python src/ha_connector/integrations/alexa/smapi_token_helper.py status

# Deployment validation
python scripts/lambda_deployment/deployment_manager.py validate
```
