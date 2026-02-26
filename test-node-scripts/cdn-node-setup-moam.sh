#!/bin/bash
# CDN Node Setup Script
# Generated for: Moam
# Platform: http://192.168.88.241:5000
# DO NOT SHARE - Contains API Key

# Self-elevate to root if not already running as root
if [ "$(id -u)" -ne 0 ]; then
  exec sudo --preserve-env=CDN_NODE_NAME,CDN_API_KEY,CDN_PLATFORM_URL,CDN_NODE_IDENTIFIER "$0" "$@"
fi

set -e

echo "=========================================="
echo "   CDN Portal Setup"
echo "   Node: Moam"
echo "=========================================="
echo ""
echo "Downloading and running automated installer..."
echo ""

CDN_NODE_NAME="Moam" \
  CDN_API_KEY="cdn_e0c0c71e242a52ad0bb8360c2236192d01c9bd7a4736b511eaa94ef75fc73cbf" \
  CDN_PLATFORM_URL="http://192.168.88.241:5000" \
  CDN_NODE_IDENTIFIER="D8:3A:DD:95:CA:56" \
  bash <(curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh)
