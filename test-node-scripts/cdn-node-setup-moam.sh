#!/bin/bash
# CDN Node Setup Script
# Generated for: Moam
# Platform: http://192.168.88.241:5000
# DO NOT SHARE - Contains API Key

# Self-elevate to root if not already running as root
if [ "$(id -u)" -ne 0 ]; then
  exec sudo bash "$0" "$@"
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
  CDN_API_KEY="cdn_9b354465518c15e21617160c7814e03c4e48c0625c0068c0256e31f168249218" \
  CDN_PLATFORM_URL="http://192.168.88.241:5000" \
  CDN_NODE_IDENTIFIER="D8:3A:DD:95:CA:56" \
  bash <(curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh)
