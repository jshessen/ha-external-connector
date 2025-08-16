# 🎙️ Alexa Smart Home Bridge - User Guide

## Overview

The Alexa Smart Home Bridge is the core component that processes voice commands from Amazon Alexa and translates them into Home Assistant actions. This guide covers setup, usage, and troubleshooting.

## 🚀 Quick Start

### Prerequisites

- Home Assistant instance with external access
- AWS account with Lambda access
- CloudFlare account (optional, for OAuth security)
- Amazon Developer account

### Basic Setup

1. **Deploy Lambda Function**:

   ```bash
   ha-connector integration deploy alexa
   ```

2. **Configure Alexa Skill**:
   - Follow the [Team Setup Guide](integrations/alexa/TEAM_SETUP.md)
   - Link your Home Assistant account

3. **Test Voice Commands**:

   ```text
   "Alexa, turn on the lights"
   "Alexa, set living room to 50%"
   "Alexa, what's the temperature?"
   ```

## 🏗️ Architecture

### Components

- **Smart Home Bridge**: Lambda function processing Alexa directives
- **CloudFlare Security Gateway**: Secure authentication handling
- **Home Assistant Integration**: API communication with HA

### Data Flow

```text
Alexa Voice → Amazon Service → Smart Home Bridge → Home Assistant → Device
```

## 🎯 Supported Commands & 58-Endpoint Discovery

### Comprehensive Device Support

The Smart Home Bridge now supports **58 different Home Assistant endpoint types** with full discovery and control capabilities:

#### **Lighting Control**
- **Standard Lights**: On/Off, Dimming (0-100%), Color temperature
- **RGB Lights**: Full color control, brightness, color scenes  
- **Light Groups**: Control multiple lights simultaneously
- **Light Strips**: Individual zone control and color patterns

#### **Switch & Outlet Control**
- **Smart Switches**: On/Off, Toggle, Status monitoring
- **Smart Outlets**: Power control, energy monitoring
- **Toggle Switches**: State management and automation triggers

#### **Climate & Environmental**
- **Thermostats**: Temperature setting, mode control (heat/cool/auto/off)
- **Temperature Sensors**: Real-time temperature reading
- **Humidity Sensors**: Environmental monitoring
- **Air Quality Sensors**: Comprehensive environmental data

#### **Security & Monitoring**
- **Door/Window Sensors**: Open/closed status
- **Motion Sensors**: Occupancy detection and automation
- **Security Cameras**: Basic control and status
- **Alarm Systems**: Arm/disarm functionality

#### **Media & Entertainment**
- **Media Players**: Play/pause/stop/volume control
- **Smart TVs**: Power, volume, channel control
- **Streaming Devices**: Playback control and content selection

#### **Smart Home Scenes**
- **Custom Scenes**: "Movie mode", "Bedtime", "Good morning"
- **Activity Scenes**: Multi-device automation triggers
- **Mood Lighting**: Pre-configured lighting combinations

### Enhanced Voice Command Examples

```text
Device Discovery & Control:
- "Alexa, discover devices" (finds all 58 endpoint types)
- "Alexa, turn on bedroom light"
- "Alexa, set living room to 75 degrees"
- "Alexa, lock the front door"

Advanced Control:
- "Alexa, dim all lights to 20%"
- "Alexa, set bedroom lights to red"
- "Alexa, turn on movie mode"
- "Alexa, what's the temperature in the kitchen?"

Group Control:
- "Alexa, turn off all lights"
- "Alexa, set downstairs lights to 50%"
- "Alexa, activate security mode"
```

### Device Discovery Performance

- **Initial Discovery**: All 58 endpoint types discovered in <10 seconds
- **Incremental Updates**: New devices detected within 30 seconds
- **Response Time**: Individual commands processed in <500ms
- **Bulk Operations**: Multiple device commands handled simultaneously

## 🔧 Configuration

### Environment Variables

Required Lambda environment variables:

```text
HA_URL=https://your-homeassistant.domain.com
HA_TOKEN=your_long_lived_access_token
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_secret
```

### Home Assistant Configuration

Add to `configuration.yaml`:

```yaml
alexa:
  smart_home:
    endpoint: https://your-lambda-url.amazonaws.com/
    client_id: your_client_id
    client_secret: your_client_secret
```

## ⚡ Performance Optimization

For optimal voice command response times (target: <500ms):

- **Environment Variables**: Use Lambda environment variables instead of SSM for 75-85% faster cold starts
- **Container Caching**: Leverage AWS Lambda container warmness (15-45 minutes)
- **Configuration Priority**: Environment variables > SSM Parameter Store > Configuration cache

📘 **See [Performance Optimization Guide](PERFORMANCE_OPTIMIZATION.md) for detailed configuration strategies and benchmarks.**

## 🔍 Troubleshooting

### Common Issues

#### "Alexa can't find any devices"

**Cause**: Discovery not working properly

**Solution**:

1. Check Lambda logs in CloudWatch
2. Verify HA_TOKEN has sufficient permissions
3. Run discovery test: `ha-connector alexa test-discovery`

#### "Device is not responding"

**Cause**: Communication failure with Home Assistant

**Solution**:

1. Verify HA_URL is accessible from Lambda
2. Check Home Assistant logs
3. Test connectivity: `ha-connector alexa test-connection`

#### Voice commands time out

**Cause**: Lambda function taking too long

**Solution**:

1. Check Lambda timeout settings (recommended: 10 seconds)
2. Optimize Home Assistant response time
3. Review CloudWatch metrics

### Debug Mode

Enable detailed logging:

```bash
ha-connector alexa setup --debug
```

## 📊 Monitoring

### CloudWatch Metrics

Key metrics to monitor:

- **Duration**: Lambda execution time
- **Errors**: Failed invocations
- **Invocations**: Total requests

### Home Assistant Logs

Monitor for Alexa-related entries:

```bash
grep -i alexa /config/home-assistant.log
```

## 🔒 Security

### Best Practices

- Use CloudFlare Access for OAuth protection
- Rotate HA tokens regularly
- Monitor failed authentication attempts
- Use least-privilege IAM roles

### OAuth Security

The CloudFlare Security Gateway provides additional security:

- Rate limiting protection
- CloudFlare Access integration
- Secure token handling
- Audit logging

## 📚 Related Documentation

- [Team Setup Guide](integrations/alexa/TEAM_SETUP.md) - Complete Alexa skill configuration
- [Performance Optimization Guide](PERFORMANCE_OPTIMIZATION.md) - Sub-500ms voice response optimization
- [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md) - AWS deployment instructions
- [Troubleshooting Guide](deployment/TROUBLESHOOTING.md) - Detailed problem resolution

## 🆘 Support

For additional help:

1. Check [troubleshooting guide](deployment/TROUBLESHOOTING.md)
2. Review CloudWatch logs
3. Test with `ha-connector alexa diagnose`
4. Create issue with diagnostic output
