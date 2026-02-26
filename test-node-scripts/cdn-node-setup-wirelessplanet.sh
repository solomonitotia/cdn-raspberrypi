#!/bin/bash
# CDN Node Setup Script
# Generated for: Wirelessplanet
# Platform: http://192.168.88.241:5000
# DO NOT SHARE - Contains API Key

# Self-elevate to root if not already running as root
if [ "$(id -u)" -ne 0 ]; then
  exec sudo bash "$0" "$@"
fi

set -e

echo "=========================================="
echo "   CDN Portal Setup"
echo "   Node: Wirelessplanet"
echo "=========================================="
echo ""
echo "Downloading and running automated installer..."
echo ""

CDN_NODE_NAME="Wirelessplanet" \
  CDN_API_KEY="cdn_d19b77d6ec4065b5949df2f3299e02186194f41d20a67799f613c2b91a5a1833" \
  CDN_PLATFORM_URL="http://192.168.88.241:5000" \
  CDN_NODE_IDENTIFIER="D8:3A:DD:95:CA:56" \
  bash <(curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh)
