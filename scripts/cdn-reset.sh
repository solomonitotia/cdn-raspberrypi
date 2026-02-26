#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║        CDN Portal — Complete Reset / Uninstall Script                   ║
# ║                                                                          ║
# ║  Removes everything installed by auto-install.sh so you can retry       ║
# ║  a clean install. Media files are kept by default (pass --wipe-media    ║
# ║  to also delete them).                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   sudo bash cdn-reset.sh             # keeps media files
#   sudo bash cdn-reset.sh --wipe-media  # also deletes /var/cdn-media

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
info() { echo -e "${CYAN}ℹ${NC} $1"; }

WIPE_MEDIA=false
for arg in "$@"; do
  [ "$arg" = "--wipe-media" ] && WIPE_MEDIA=true
done

# ── Must run as root ────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
  exec sudo bash "$0" "$@"
fi

clear
echo -e "${RED}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     🗑️  CDN Portal — Reset / Uninstall                ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

INSTALL_DIR="/opt/cdn-portal"
SERVICE_USER="cdnportal"
SERVICE_FILE="/etc/systemd/system/cdn-portal.service"
LOG_DIR="/var/log/cdn-portal"

# Detect media root from .env if it exists
MEDIA_ROOT="/var/cdn-media"
if [ -f "$INSTALL_DIR/.env" ]; then
  _media=$(grep '^MEDIA_ROOT=' "$INSTALL_DIR/.env" | cut -d'"' -f2 | cut -d'=' -f2 | tr -d '"')
  [ -n "$_media" ] && MEDIA_ROOT="$_media"
fi

echo -e "${CYAN}${BOLD}Will remove:${NC}"
echo -e "   Service:       cdn-portal (systemd)"
echo -e "   Install dir:   $INSTALL_DIR"
echo -e "   Log dir:       $LOG_DIR"
echo -e "   System user:   $SERVICE_USER"
if $WIPE_MEDIA; then
  echo -e "   ${RED}Media files:   $MEDIA_ROOT  (--wipe-media)${NC}"
else
  echo -e "   ${YELLOW}Media files:   $MEDIA_ROOT  (KEPT — use --wipe-media to delete)${NC}"
fi
echo ""

# ── 1. Stop and disable service ─────────────────────────────────────────────
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Stopping Service${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if systemctl is-active --quiet cdn-portal 2>/dev/null; then
  systemctl stop cdn-portal
  log "Service stopped"
else
  info "Service was not running"
fi

if systemctl is-enabled --quiet cdn-portal 2>/dev/null; then
  systemctl disable cdn-portal 2>/dev/null
  log "Service disabled"
fi

if [ -f "$SERVICE_FILE" ]; then
  rm -f "$SERVICE_FILE"
  log "Service file removed: $SERVICE_FILE"
fi

systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true
log "Systemd reloaded"

# ── 2. Remove install directory ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Removing Files${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  log "Removed: $INSTALL_DIR"
else
  info "Not found: $INSTALL_DIR"
fi

if [ -d "$LOG_DIR" ]; then
  rm -rf "$LOG_DIR"
  log "Removed: $LOG_DIR"
else
  info "Not found: $LOG_DIR"
fi

# ── 3. Remove system user ────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Removing System User${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if id "$SERVICE_USER" &>/dev/null; then
  userdel -r "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER" 2>/dev/null || true
  log "User '$SERVICE_USER' removed"
else
  info "User '$SERVICE_USER' did not exist"
fi

# ── 4. Remove UFW rule ───────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw delete allow 8282/tcp 2>/dev/null || true
  log "Firewall rule removed (port 8282)"
fi

# ── 5. Optionally wipe media ─────────────────────────────────────────────────
echo ""
if $WIPE_MEDIA; then
  echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
  echo -e "${CYAN}${BOLD} Wiping Media Files${NC}"
  echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
  echo ""
  if [ -d "$MEDIA_ROOT" ]; then
    rm -rf "$MEDIA_ROOT"
    log "Removed media: $MEDIA_ROOT"
  else
    info "Not found: $MEDIA_ROOT"
  fi
else
  warn "Media files kept at: $MEDIA_ROOT"
  warn "Run with --wipe-media to also delete them"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD} Reset complete — ready for a fresh install${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Run the installer again:"
echo -e "  ${BOLD}bash <(curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh)${NC}"
echo ""
