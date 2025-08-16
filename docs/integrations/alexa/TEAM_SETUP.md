# 🏢 ALEXA SKILL TEAM CONFIGURATION GUIDE

## 👮💼 Security Guard & Executive Receptionist Setup

This guide shows you how to configure your Alexa Smart Home Skill to work with
both team members: the **Security Guard** (CloudFlare Security Gateway) and the
**Executive Receptionist** (Voice Command Bridge).

---

## 🎯 **THE COMPLETE TEAM OVERVIEW**

### 👮 **SECURITY GUARD** (`cloudflare_cloudflare_security_gateway.py`)

- **Role**: Handles OAuth authentication and CloudFlare protection
- **When Active**: During account linking and token refresh
- **Specializes In**: High-security authentication tasks
- **Lambda URL**: `https://your-cloudflare-security-gateway-lambda-url.us-east-1.on.aws/`

### 💼 **EXECUTIVE RECEPTIONIST** (`voice_command_bridge.py`)

- **Role**: Processes daily voice commands efficiently
- **When Active**: Every time you give Alexa a smart home command
- **Specializes In**: Fast, efficient daily operations
- **Lambda URL**: `[Your Voice Command Bridge Lambda URL]`

---

## ⚙️ **ALEXA SKILL CONFIGURATION**

### 🔗 **Account Linking Settings**

Navigate to: **Amazon Developer Console** → **Your Smart Home Skill** → **Account Linking**

#### **OAuth Configuration**

```check-list
☑️ Do you allow users to create an account or link to an existing account with you?
   YES - Enable this option

☑️ Allow users to link their account to your skill from within your application or website
   YES - Enable this option (optional but recommended)

☑️ Allow users to authenticate using your mobile application
   NO - Leave this disabled unless you have a mobile app
```

#### **Security Provider Information**

```plaintext
Authorization Grant Type: Auth Code Grant

Web Authorization URI:
   https://your-homeassistant.domain.com/auth/authorize
   👮 → This goes to your SECURITY GUARD for initial credential checking

Access Token URI:
   https://your-cloudflare-security-gateway-lambda-url.us-east-1.on.aws/
   👮 → This goes to your SECURITY GUARD for token exchange and refresh

Client ID:
   https://pitangui.amazon.com
   (or your custom client ID)

Authorization Scheme:
   HTTP Basic (Recommended)

Scope:
   smart_home
   (or your custom scope)

Domain List:
   your-homeassistant.domain.com
   (your Home Assistant domain)
```

### 🏠 **Smart Home Settings**

Navigate to: **Amazon Developer Console** → **Your Smart Home Skill** → **Smart Home**

```plaintext
Default Endpoint:
   [Your Voice Command Bridge Lambda URL]
   💼 → This goes to your EXECUTIVE RECEPTIONIST for daily operations

Account Linking Required: YES
```

---

## 🔄 **HOW THE TEAM WORKS TOGETHER**

### **PHASE 1: INITIAL SETUP** (One-time account linking)

```list
1. 👤 User opens Alexa app
2. 📱 User clicks "Link Account"
3. 🌐 Alexa → Web Authorization URI → 👮 SECURITY GUARD
4. 🔐 Security Guard handles OAuth with Home Assistant
5. 🎫 Security Guard issues access token
6. 📋 Security Guard → Access Token URI → back to Alexa
7. ✅ "Account successfully linked!"
```

### **PHASE 2: DAILY OPERATIONS** (Every voice command)

```list
1. 🗣️ "Alexa, turn on the lights"
2. 🌐 Alexa → Default Endpoint → 💼 EXECUTIVE RECEPTIONIST
3. 🔍 Receptionist validates token (from Security Guard's work)
4. 📞 Receptionist translates to Home Assistant
5. 💡 Lights turn on
6. 🗣️ "OK"
```

---

## 🛠️ **DEPLOYMENT CHECKLIST**

### ✅ **Security Guard Setup**

- [ ] Deploy `cloudflare_cloudflare_security_gateway.py` to AWS Lambda
- [ ] Configure AWS Parameter Store with OAuth credentials
- [ ] Set up CloudFlare Access headers
- [ ] Test OAuth flow in Alexa app
- [ ] Verify token exchange works

### ✅ **Executive Receptionist Setup**

- [ ] Deploy `voice_command_bridge.py` to AWS Lambda
- [ ] Configure AWS Parameter Store with HA credentials
- [ ] Test voice commands work
- [ ] Verify fast response times
- [ ] Check CloudWatch logs

### ✅ **Alexa Skill Configuration**

- [ ] Set Web Authorization URI to Security Guard
- [ ] Set Access Token URI to Security Guard
- [ ] Set Default Endpoint to Executive Receptionist
- [ ] Enable Account Linking
- [ ] Test complete flow end-to-end

---

## 🔍 **TROUBLESHOOTING THE TEAM**

### 👮 **Security Guard Issues**

- **Problem**: "Account linking fails"
- **Check**: CloudWatch logs for OAuth gateway
- **Fix**: Verify Parameter Store credentials

### 💼 **Executive Receptionist Issues**

- **Problem**: "Voice commands don't work"
- **Check**: CloudWatch logs for voice command bridge
- **Fix**: Verify token validation and HA connection

### 🤝 **Team Coordination Issues**

- **Problem**: "Linking works but commands fail"
- **Check**: Token format and expiration
- **Fix**: Ensure both Lambda functions use same token format

---

## 📊 **PERFORMANCE EXPECTATIONS**

### 👮 **Security Guard Performance**

- **OAuth Flow**: 2-5 seconds (acceptable for one-time setup)
- **Token Refresh**: 1-2 seconds (rare operation)
- **CloudFlare Bypass**: Additional 500ms (security overhead)

### 💼 **Executive Receptionist Performance**

- **Voice Commands**: 500ms-2 seconds (optimal for daily use)
- **Token Validation**: <100ms (cached validation)
- **HA Communication**: 200-800ms (depends on HA response)

---

## 🎯 **SUCCESS METRICS**

### **Account Linking Success**

- Users can link accounts in Alexa app
- OAuth flow completes without errors
- Tokens are properly exchanged and stored

### **Voice Command Success**

- Commands execute within 2 seconds
- High success rate (>95%)
- Proper error handling and user feedback

### **Security Compliance**

- All authentication goes through Security Guard
- Sensitive data is properly masked in logs
- Rate limiting prevents abuse

---

## 📚 **ADDITIONAL RESOURCES**

- **Security Guard Documentation**: See `cloudflare_cloudflare_security_gateway.py` header
- **Executive Receptionist Documentation**: See `voice_command_bridge.py` header
- **AWS Lambda Setup**: See project deployment guides
- **Home Assistant Integration**: See HA configuration documentation

---

*This professional team approach ensures your Alexa Smart Home Skill is both secure and efficient, with each component specialized for its specific role in the system.*
