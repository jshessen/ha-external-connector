# 🔍 Deployment Troubleshooting Guide

## Overview

This guide covers common deployment issues and their solutions for the HA External Connector Lambda functions.

## 🚨 Common Deployment Issues

### Lambda Function Deployment Failures

#### Issue: Function Package Too Large
```bash
Error: Deployment package size (>50MB) exceeds Lambda limit
```

**Solution:**
```bash
# Clean and rebuild with optimized packaging
python scripts/lambda_deployment/deployment_manager.py --clean
python scripts/lambda_deployment/deployment_manager.py --build --optimize

# Verify package size
python scripts/lambda_deployment/deployment_manager.py --validate --size-check
```

#### Issue: Transfer Block Synchronization Failure
```bash
Error: Transfer block content mismatch between functions
```

**Solution:**
```bash
# Force synchronization of transfer blocks
python scripts/lambda_deployment/deployment_manager.py --sync-blocks --force

# Validate synchronization
python scripts/lambda_deployment/deployment_manager.py --validate --transfer-blocks
```

#### Issue: Import Validation Failure
```bash
Error: Lambda function imports fail after deployment
```

**Solution:**
```bash
# Test imports locally before deployment
python -c "from src.ha_connector.integrations.alexa.lambda_functions.smart_home_bridge import lambda_handler"
python -c "from src.ha_connector.integrations.alexa.lambda_functions.cloudflare_security_gateway import lambda_handler"

# Deploy with import validation
python scripts/lambda_deployment/deployment_manager.py --deploy --function all --validate-imports
```

### OAuth and Authentication Issues

#### Issue: OAuth Flow Validation Failure
```bash
Error: OAuth callback timeout or invalid state parameter
```

**Solutions:**

1. **Check Security Profile Configuration:**
```bash
# Validate LWA security profile
python src/ha_connector/integrations/alexa/smapi_token_helper.py --validate-profile

# Test OAuth flow in development mode
python src/ha_connector/integrations/alexa/smapi_token_helper.py --test-oauth --debug
```

2. **Verify Redirect URIs:**
```bash
# Ensure redirect URIs are properly configured
python -c "
from smapi_token_helper import SMAPITokenHelper
helper = SMAPITokenHelper()
print('Required redirect URIs:', helper.REQUIRED_REDIRECT_URIS)
"
```

#### Issue: Token Refresh Failure
```bash
Error: Unable to refresh SMAPI tokens
```

**Solution:**
```bash
# Test token refresh manually
python src/ha_connector/integrations/alexa/smapi_automation_enhancer.py --refresh-tokens --debug

# Validate environment variables
echo "SMAPI_CLIENT_ID: ${SMAPI_CLIENT_ID:+SET}"
echo "SMAPI_CLIENT_SECRET: ${SMAPI_CLIENT_SECRET:+SET}"
```

### Performance and Caching Issues

#### Issue: Cache Performance Degradation
```bash
Warning: Cache response times exceeding targets
```

**Diagnostic Commands:**
```bash
# Test caching layers
python scripts/lambda_deployment/deployment_manager.py --test --function all --cache-benchmark

# Validate DynamoDB table configuration
aws dynamodb describe-table --table-name ha-connector-shared-cache --no-cli-pager

# Test SSM parameter access
aws ssm get-parameters --names "/ha-connector/oauth/config" --no-cli-pager
```

**Performance Targets:**
- Container Cache: < 1ms
- Shared Cache: < 50ms  
- SSM Fallback: < 200ms
- Total Voice Response: < 500ms

#### Issue: Cold Start Performance
```bash
Warning: Lambda cold start time exceeding 3 seconds
```

**Optimization Steps:**
```bash
# Deploy with performance optimization
python scripts/lambda_deployment/deployment_manager.py --deploy --function all --optimize-cold-start

# Test cold start performance
python scripts/lambda_deployment/deployment_manager.py --test --function smart_home_bridge --cold-start-test
```

## 🔧 Diagnostic Commands

### Environment Validation
```bash
# Complete environment check
python scripts/agent_helper.py env

# AWS credentials validation
aws sts get-caller-identity --no-cli-pager

# Lambda function status
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `ha-connector`)].{Name:FunctionName,Status:State}' --no-cli-pager
```

### Code Quality Validation
```bash
# Run complete quality suite
source .venv/bin/activate
ruff check src/
pylint src/ha_connector/
mypy src/ha_connector/

# Validate Lambda function independence
python -c "
import sys
sys.path.insert(0, 'src')
from ha_connector.integrations.alexa.lambda_functions.smart_home_bridge import lambda_handler
from ha_connector.integrations.alexa.lambda_functions.cloudflare_security_gateway import lambda_handler as csg_handler
print('✅ All imports successful')
"
```

### Deployment State Validation
```bash
# Check deployment readiness
python scripts/lambda_deployment/deployment_manager.py --validate --comprehensive

# Verify function configuration
aws lambda get-function-configuration --function-name ha-connector-smart-home-bridge --no-cli-pager
aws lambda get-function-configuration --function-name ha-connector-cloudflare-security-gateway --no-cli-pager
```

## 🎯 Performance Benchmarking

### Voice Command Response Time Testing
```bash
# Test complete voice command flow
python scripts/lambda_deployment/deployment_manager.py --test --function smart_home_bridge --voice-command-test

# Benchmark all performance metrics
python scripts/lambda_deployment/deployment_manager.py --benchmark --comprehensive
```

### Alexa Smart Home Endpoint Testing
```bash
# Test all 58 Home Assistant endpoints
python scripts/lambda_deployment/deployment_manager.py --test --function smart_home_bridge --endpoint-discovery

# Validate device control capabilities
python scripts/lambda_deployment/deployment_manager.py --test --function smart_home_bridge --device-control
```

## 🔒 Security Validation

### OAuth Security Testing
```bash
# Complete OAuth flow validation
python src/ha_connector/integrations/alexa/smapi_token_helper.py --security-test

# Test security validation API
curl -X POST https://your-domain.com/api/security/validate \
  -H "Content-Type: application/json" \
  -d '{"access_token": "your-token", "test_mode": true}'
```

### Rate Limiting Validation
```bash
# Test rate limiting functionality
python scripts/lambda_deployment/deployment_manager.py --test --function cloudflare_security_gateway --rate-limit-test

# Validate IP-based throttling
python scripts/lambda_deployment/deployment_manager.py --test --function all --security-validation
```

## 📊 Monitoring and Logging

### CloudWatch Logs Analysis
```bash
# Get recent Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ha-connector" --no-cli-pager

# Stream real-time logs
aws logs tail /aws/lambda/ha-connector-smart-home-bridge --follow --no-cli-pager
```

### Performance Metrics
```bash
# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=ha-connector-smart-home-bridge \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --no-cli-pager
```

## 🆘 Emergency Recovery

### Function Rollback
```bash
# List function versions
aws lambda list-versions-by-function --function-name ha-connector-smart-home-bridge --no-cli-pager

# Rollback to previous version
aws lambda update-alias \
  --function-name ha-connector-smart-home-bridge \
  --name LIVE \
  --function-version $PREVIOUS_VERSION \
  --no-cli-pager
```

### Complete Redeployment
```bash
# Clean and redeploy everything
python scripts/lambda_deployment/deployment_manager.py --clean
python scripts/lambda_deployment/deployment_manager.py --deploy --function all --force

# Validate complete system
python scripts/lambda_deployment/deployment_manager.py --test --function all --comprehensive
```

## 📞 Support Resources

### Internal Resources
- **[Deployment Quick Reference](DEPLOYMENT_QUICK_REFERENCE.md)** - Basic deployment commands
- **[Security Validation Guide](security_validation_guide.md)** - Security configuration
- **[Lambda Deployment Markers](../development/LAMBDA_DEPLOYMENT_MARKERS.md)** - Technical details

### External Resources
- **[AWS Lambda Troubleshooting](https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html)** - AWS official guide
- **[Amazon SMAPI Troubleshooting](https://developer.amazon.com/en-US/docs/alexa/smapi/troubleshooting.html)** - Amazon developer docs
- **[CloudWatch Logs Guide](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)** - Log analysis

---

**Last Updated**: January 2025  
**Covers**: Lambda deployment, OAuth authentication, performance optimization, security validation