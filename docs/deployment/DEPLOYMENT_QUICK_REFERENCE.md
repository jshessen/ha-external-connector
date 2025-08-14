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
