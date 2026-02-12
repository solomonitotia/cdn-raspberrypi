#!/bin/bash
# deploy-pi.sh — Automated Django CDN Node setup for Raspberry Pi
#
# Required env vars:
#   CDN_NODE_NAME        e.g. "Athi CN"
#   CDN_API_KEY          API key from platform
#   CDN_PLATFORM_URL     e.g. https://platform.example.com
#   CDN_NODE_IDENTIFIER  auto-detected from MAC if not set
#   MEDIA_ROOT           path to external drive e.g. /mnt/usb (default /var/cdn-media)
#   DJANGO_SECRET_KEY    random secret key
#
# Usage:
#   sudo CDN_NODE_NAME="Athi CN" CDN_API_KEY="..." CDN_PLATFORM_URL="..." bash deploy-pi.sh

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
hdr()   { echo -e "\n${BLUE}==> $1${NC}"; }

echo -e "${BLUE}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   CDN Node (Django) — Automated Setup    ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

[ "$EUID" -ne 0 ] && error "Run as root: sudo bash deploy-pi.sh"
[ -z "$CDN_NODE_NAME" ]  && error "CDN_NODE_NAME is required"
[ -z "$CDN_API_KEY" ]    && error "CDN_API_KEY is required"
[ -z "$CDN_PLATFORM_URL" ] && warn "CDN_PLATFORM_URL not set — heartbeat disabled"

# ── Config ─────────────────────────────────────────────────────────────────
INSTALL_DIR="/opt/cdn-node"
MEDIA_ROOT="${MEDIA_ROOT:-/var/cdn-media}"
LOG_DIR="/var/log/cdn-node"
CDN_PORT="${CDN_PORT:-8080}"
SERVICE_USER="cdn-node"
DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(40))')}"

if [ -z "$CDN_NODE_IDENTIFIER" ]; then
  if [ -f /sys/class/net/eth0/address ]; then
    CDN_NODE_IDENTIFIER="pi-$(cat /sys/class/net/eth0/address | tr -d ':')"
  elif [ -f /sys/class/net/wlan0/address ]; then
    CDN_NODE_IDENTIFIER="pi-$(cat /sys/class/net/wlan0/address | tr -d ':')"
  else
    CDN_NODE_IDENTIFIER="pi-$(hostname)"
  fi
fi

hdr "1/7 Installing system dependencies"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv libpq-dev curl
log "System dependencies installed"

hdr "2/7 Creating directories and user"
mkdir -p "$INSTALL_DIR" "$MEDIA_ROOT" "$LOG_DIR"

if ! id "$SERVICE_USER" &>/dev/null; then
  useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
  log "User '$SERVICE_USER' created"
fi

chown -R "$SERVICE_USER:$SERVICE_USER" "$MEDIA_ROOT" "$LOG_DIR" "$INSTALL_DIR"
log "Directories ready"

hdr "3/7 Installing application"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
log "Application installed"

hdr "4/7 Writing environment config"
cat > "$INSTALL_DIR/.env" <<EOF
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY"
DEBUG=false
CDN_NODE_NAME="$CDN_NODE_NAME"
CDN_NODE_IDENTIFIER="$CDN_NODE_IDENTIFIER"
CDN_PLATFORM_URL="${CDN_PLATFORM_URL:-}"
CDN_API_KEY="${CDN_API_KEY:-}"
MEDIA_ROOT="$MEDIA_ROOT"
EOF
chmod 600 "$INSTALL_DIR/.env"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
log "Environment written to $INSTALL_DIR/.env"

hdr "5/7 Running database migrations and collecting static files"
cd "$INSTALL_DIR"
source venv/bin/activate

# Source env
set -a; source .env; set +a

python manage.py migrate --no-input
python manage.py collectstatic --no-input -v 0

# Create superuser non-interactively if not exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser('admin', '', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"
log "Database ready"

hdr "6/7 Installing systemd service"
cat > /etc/systemd/system/cdn-node.service <<EOF
[Unit]
Description=CDN Node (Django) for Community Networks
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn \
    --workers 2 \
    --bind 0.0.0.0:$CDN_PORT \
    --timeout 120 \
    --access-logfile $LOG_DIR/access.log \
    --error-logfile $LOG_DIR/error.log \
    cdnnode.wsgi:application
Restart=always
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$MEDIA_ROOT $LOG_DIR $INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cdn-node.service
systemctl restart cdn-node.service
sleep 3

if systemctl is-active --quiet cdn-node.service; then
  log "Service started"
else
  echo -e "${RED}Service failed to start. Logs:${NC}"
  journalctl -u cdn-node -n 30 --no-pager
  exit 1
fi

hdr "7/7 Done!"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════╗"
echo -e "  ║          Setup Complete! 🎉               ║"
echo -e "  ╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Portal:${NC}       http://$LOCAL_IP:$CDN_PORT"
echo -e "  ${BLUE}Admin panel:${NC}  http://$LOCAL_IP:$CDN_PORT/admin"
echo -e "  ${BLUE}Admin login:${NC}  admin / admin123  ← CHANGE THIS!"
echo -e "  ${BLUE}Media drive:${NC}  $MEDIA_ROOT"
echo -e "  ${BLUE}Logs:${NC}         sudo journalctl -u cdn-node -f"
echo ""
echo "  ⚠  Change the admin password at http://$LOCAL_IP:$CDN_PORT/admin"
echo ""
