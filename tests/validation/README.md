# AWS Lambda Function Validation Suite

This directory contains comprehensive validation and testing tools for the
Home Assistant External Connector AWS Lambda functions.

## 📁 Directory Structure

### 🛠️ Active Testing Tools (`tools/`)

- **`alexa_smart_home_testing_suite.py`** - Comprehensive Alexa Smart Home testing
  with discovery, power control, and artifact management

### 📚 Legacy Validation Scripts (`legacy/`)

Historical validation scripts from development phases:

- **`test_authentication_fix.py`** - Authentication fix validation
- **`test_deployed_cloudflare_security_gateway.py`** - Deployed CloudFlare Security
  Gateway testing
- **`test_cloudflare_security_gateway_validation.py`** - CloudFlare Security Gateway
  validation suite
- **`test_smart_home_bridge_validation.py`** - Smart Home Bridge validation

### 📋 Documentation

- **`GUEST_FAN_TEST_RESULTS.md`** - Comprehensive guest fan test results and analysis
- **`README.md`** - This file

## 🚀 Quick Start

### Alexa Smart Home Testing

```bash
# Run full test suite
python tools/alexa_smart_home_testing_suite.py

# Discovery only
python tools/alexa_smart_home_testing_suite.py --discovery

# Test specific endpoint
python tools/alexa_smart_home_testing_suite.py --test fan#guest_outlet_2

# Save files permanently for debugging
python tools/alexa_smart_home_testing_suite.py --discovery --save-files

# Clean up test artifacts
python tools/alexa_smart_home_testing_suite.py --cleanup
```

## 🎯 Key Testing Capabilities

### Discovery Testing

- Find all available Alexa endpoints in Home Assistant
- Validate endpoint IDs and friendly names
- Test authentication and connectivity

### Power Control Testing

- Turn devices on/off through Alexa interface
- Test both hash (#) and dot (.) endpoint formats
- Validate proper state changes and responses

### Artifact Management

- Automatic cleanup of temporary test files
- Optional permanent file saving for debugging
- Manual cleanup commands for maintenance

## 📊 Test Results

See `GUEST_FAN_TEST_RESULTS.md` for detailed test outcomes including:

- Working endpoint IDs (e.g., `fan#guest_outlet_2`)
- Authentication validation results
- Power control success/failure analysis

## 🔧 Development History

Legacy validation scripts in `legacy/` directory contain historical development
artifacts from various testing phases. These are preserved for reference but
superseded by the current testing suite.

## 💡 Usage Tips

1. **Start with discovery**: Always run `--discovery` first to find available endpoints
2. **Use save-files for debugging**: Add `--save-files` to preserve test payloads
3. **Regular cleanup**: Use `--cleanup` to maintain clean project state
4. **Test specific endpoints**: Use `--test <endpoint_id>` for focused testing

### Run Guest Fan Tests

```bash
cd tests/validation
python test_guest_fan_comprehensive.py
```

### Test Individual Lambda Functions

```bash
# Test Smart Home Bridge
python test_smart_home_bridge_validation.py

# Test CloudFlare Security Gateway
python test_cloudflare_security_gateway_validation.py
```

### Manual Lambda Testing

```bash
# Use generated payloads for direct testing
aws lambda invoke --function-name HomeAssistant --payload file://guest_fan_on_1.json response.json
```

## ✅ Validation Checklist

- [ ] Guest fan control working (`fan#guest_outlet_2`)
- [ ] Authentication (no 401 errors)
- [ ] Discovery responses complete
- [ ] Smart Home Bridge functionality
- [ ] CloudFlare Security Gateway token exchange
- [ ] CloudWatch logs clean
- [ ] Home Assistant device state changes

## 🎯 Working Endpoints

**Guest Fan**: `fan#guest_outlet_2` ✅

Use the comprehensive test suite to validate all functionality after code changes or deployments.
