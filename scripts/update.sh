#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║     CDN Portal — Update Script                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Updates the portal to the latest version from GitHub.
#
# Usage:
#   sudo bash /opt/cdn-portal/scripts/update.sh
#
# Or fetch and run directly:
#   curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/update.sh | sudo bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()   { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
info()  { echo -e "${CYAN}ℹ${NC} $1"; }

[ "$EUID" -ne 0 ] && error "Run as root: sudo bash $0"

INSTALL_DIR="/opt/cdn-portal"
SERVICE_USER="cdnportal"

[ -d "$INSTALL_DIR" ] || error "Portal not found at $INSTALL_DIR. Run auto-install.sh first."

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     🔄  CDN Portal - Updater                          ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ═══════════════════════════════════════════════════════════════════════════
# Step 1: Pull latest code
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Pulling Latest Code${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cd "$INSTALL_DIR"

CURRENT=$(sudo -u "$SERVICE_USER" git rev-parse --short HEAD 2>/dev/null || echo "unknown")
info "Current version: $CURRENT"

sudo -u "$SERVICE_USER" git pull origin main 2>&1 | grep -v "^From\|^  "

NEW=$(sudo -u "$SERVICE_USER" git rev-parse --short HEAD 2>/dev/null || echo "unknown")

if [ "$CURRENT" = "$NEW" ]; then
    warn "Already up to date (${NEW}). No changes pulled."
else
    log "Updated: $CURRENT → $NEW"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Step 2: Apply database migrations
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Applying Migrations${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

info "Running migrations..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" manage.py migrate --no-input \
    2>&1 | grep -E "Applying|OK|No migrations" || true

# Fix ownership in case new files were created
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

log "Database up to date"

# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Collect static files
# ═══════════════════════════════════════════════════════════════════════════

echo ""
info "Collecting static files..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" manage.py collectstatic \
    --no-input -v 0 2>&1 > /dev/null
log "Static files updated"

# ═══════════════════════════════════════════════════════════════════════════
# Step 4: Restart service
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Restarting Service${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

systemctl restart cdn-portal.service
sleep 3

if systemctl is-active --quiet cdn-portal.service; then
    log "Service restarted successfully"
else
    warn "Service may have issues. Check logs: sudo journalctl -u cdn-portal -n 50"
fi

LOCAL_IP=$(hostname -I | awk '{print $1}')
PORT=$(grep -oP '(?<=--bind 0.0.0.0:)\d+' /etc/systemd/system/cdn-portal.service 2>/dev/null || echo "8282")

echo ""
echo -e "${GREEN}${BOLD}Update complete! Portal is running at http://$LOCAL_IP:$PORT${NC}"
echo ""
