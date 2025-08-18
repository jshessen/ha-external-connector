#!/bin/bash

# Browser Mod Setup Script for HA Development Environment
# This script helps install Browser Mod in the HA core development environment

echo "🚀 Setting up Browser Mod for HA External Connector testing..."

HACORE_PATH="/mnt/development/GitHub/ha-core"
CONFIG_PATH="$HACORE_PATH/config"
CUSTOM_COMPONENTS_PATH="$CONFIG_PATH/custom_components"

echo "📂 Environment paths:"
echo "  HA Core: $HACORE_PATH"
echo "  Config: $CONFIG_PATH"
echo "  Custom Components: $CUSTOM_COMPONENTS_PATH"

# Verify our integration is properly linked
echo ""
echo "🔗 Checking HA External Connector integration..."
if [ -L "$CUSTOM_COMPONENTS_PATH/ha_external_connector" ]; then
    echo "✅ HA External Connector symbolic link exists"
    echo "   Target: $(readlink $CUSTOM_COMPONENTS_PATH/ha_external_connector)"

    if [ -f "$CUSTOM_COMPONENTS_PATH/ha_external_connector/manifest.json" ]; then
        echo "✅ Manifest file accessible"
        echo "   Domain: $(cat $CUSTOM_COMPONENTS_PATH/ha_external_connector/manifest.json | grep '"domain"' | cut -d'"' -f4)"
        echo "   Dependencies: $(cat $CUSTOM_COMPONENTS_PATH/ha_external_connector/manifest.json | grep '"dependencies"' | cut -d'[' -f2 | cut -d']' -f1)"
    else
        echo "❌ Manifest file not found"
        exit 1
    fi
else
    echo "❌ HA External Connector not linked properly"
    exit 1
fi

echo ""
echo "🌐 Browser Mod Installation Options:"
echo ""
echo "Option 1: Manual Browser Mod Installation"
echo "  cd $CUSTOM_COMPONENTS_PATH"
echo "  git clone https://github.com/thomasloven/hass-browser_mod.git browser_mod_temp"
echo "  mv browser_mod_temp/custom_components/browser_mod ."
echo "  rm -rf browser_mod_temp"
echo ""
echo "Option 2: HACS Installation (in devcontainer)"
echo "  1. Start HA devcontainer"
echo "  2. Install HACS via: wget -O - https://get.hacs.xyz | bash -"
echo "  3. Configure HACS in HA UI"
echo "  4. Search and install 'Browser Mod'"
echo ""
echo "Option 3: VSCode Devcontainer with Auto-Setup (recommended)"
echo "  1. Open /mnt/development/GitHub/ha-core in VSCode"
echo "  2. Accept 'Reopen in Container' prompt"
echo "  3. Wait for container build and setup"
echo "  4. Use integrated terminal to install Browser Mod"

echo ""
echo "🎯 Next Steps:"
echo "1. Choose Browser Mod installation method above"
echo "2. Open $HACORE_PATH in VSCode"
echo "3. Use devcontainer for development environment"
echo "4. Test HA External Connector services:"
echo "   - ha_external_connector.setup_lwa_profile"
echo "   - ha_external_connector.check_browser_mod"

echo ""
echo "🔧 Quick Browser Mod Manual Install:"
read -p "Install Browser Mod now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Installing Browser Mod..."
    cd "$CUSTOM_COMPONENTS_PATH"

    if [ ! -d "browser_mod" ]; then
        echo "  Cloning Browser Mod repository..."
        git clone https://github.com/thomasloven/hass-browser_mod.git browser_mod_temp

        if [ -d "browser_mod_temp/custom_components/browser_mod" ]; then
            echo "  Moving Browser Mod to custom_components..."
            mv browser_mod_temp/custom_components/browser_mod .
            rm -rf browser_mod_temp
            echo "✅ Browser Mod installed successfully"
        else
            echo "❌ Browser Mod repository structure unexpected"
            rm -rf browser_mod_temp
            exit 1
        fi
    else
        echo "✅ Browser Mod already exists"
    fi

    echo ""
    echo "🎉 Setup complete! Ready for devcontainer testing."
else
    echo "👍 Skipping Browser Mod installation - you can install it later."
fi

echo ""
echo "🚀 Final Setup:"
echo "1. cd /mnt/development/GitHub/ha-core"
echo "2. code .  # Open in VSCode"
echo "3. Accept devcontainer prompt"
echo "4. Wait for environment setup"
echo "5. Test integration in HA development environment"
