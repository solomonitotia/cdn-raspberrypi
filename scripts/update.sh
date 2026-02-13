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
# Step 2: Install / update Python packages
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Installing Python Packages${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

info "Installing/upgrading packages from requirements.txt..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install \
    -r "$INSTALL_DIR/requirements.txt" -q 2>&1 | grep -v "^Requirement already" || true
log "Packages up to date"

# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Apply database migrations
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Applying Migrations${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

info "Running migrations..."
# Run as cdnportal with the .env loaded so Django has the correct MEDIA_ROOT etc.
sudo -u "$SERVICE_USER" bash -c "
    set -a
    source '$INSTALL_DIR/.env'
    set +a
    '$INSTALL_DIR/venv/bin/python' '$INSTALL_DIR/manage.py' migrate --no-input
" 2>&1

# Fix ownership in case new files were created during migration
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Fix media file permissions — directories must be executable, files readable
MEDIA_ROOT_PATH=$(grep -oP '(?<=^MEDIA_ROOT=)["\x27]?\K[^"'\'']+' "$INSTALL_DIR/.env" 2>/dev/null || echo "/var/cdn-media")
if [ -d "$MEDIA_ROOT_PATH" ]; then
    chown -R "$SERVICE_USER:$SERVICE_USER" "$MEDIA_ROOT_PATH"
    find "$MEDIA_ROOT_PATH" -type d -exec chmod 755 {} +
    find "$MEDIA_ROOT_PATH" -type f -exec chmod 644 {} +
fi

log "Database up to date"

# ═══════════════════════════════════════════════════════════════════════════
# Step 4: Collect static files
# ═══════════════════════════════════════════════════════════════════════════

echo ""
info "Collecting static files..."
sudo -u "$SERVICE_USER" bash -c "
    set -a
    source '$INSTALL_DIR/.env'
    set +a
    '$INSTALL_DIR/venv/bin/python' '$INSTALL_DIR/manage.py' collectstatic --no-input -v 0
" 2>&1 > /dev/null
log "Static files updated"

# ═══════════════════════════════════════════════════════════════════════════
# Step 5: Restart service
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
    warn "Service may have issues — showing recent error log:"
    echo ""
    tail -n 30 /var/log/cdn-portal/error.log 2>/dev/null || journalctl -u cdn-portal -n 30 --no-pager
fi

LOCAL_IP=$(hostname -I | awk '{print $1}')
PORT=$(grep -oP '(?<=--bind 0.0.0.0:)\d+' /etc/systemd/system/cdn-portal.service 2>/dev/null || echo "8282")

echo ""
echo -e "${GREEN}${BOLD}Update complete! Portal is running at http://$LOCAL_IP:$PORT${NC}"
echo ""
echo -e "${CYAN}If you're still seeing errors in the admin, check the error log:${NC}"
echo -e "  sudo tail -n 30 /var/log/cdn-portal/error.log"
echo ""
