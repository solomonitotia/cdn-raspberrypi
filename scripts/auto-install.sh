#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║     CDN Portal — Fully Automated Installer (No Interaction Required)    ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Usage with environment variables:
#   sudo CDN_NODE_NAME="My Network" CDN_ADMIN_PASSWORD="SecurePass123" bash auto-install.sh
#
# Or with curl (one-liner):
#   curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh | \
#     sudo CDN_NODE_NAME="My Network" CDN_ADMIN_PASSWORD="SecurePass123" bash
#
# Environment variables (all optional, have defaults):
#   CDN_NODE_NAME         - Network name (default: "Community CDN Node")
#   CDN_NODE_TAGLINE      - Tagline (default: "by Community Networks")
#   CDN_ADMIN_PASSWORD    - Admin password (default: "admin123")
#   CDN_PORT              - Port number (default: 8282)
#   CDN_MEDIA_ROOT        - Media storage path (default: /var/cdn-media)
#   CDN_PLATFORM_URL      - Platform URL (optional)
#   CDN_API_KEY           - Platform API key (optional)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()   { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
info()  { echo -e "${CYAN}ℹ${NC} $1"; }

clear
echo -e "${CYAN}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     🌐  CDN Portal - Automated Installer              ║
  ║                                                        ║
  ║     Fully automated setup (no interaction needed)     ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check root
[ "$EUID" -ne 0 ] && error "Run as root: sudo bash $0"

# Ensure we have a valid working directory (can fail when piped via curl)
cd /root 2>/dev/null || cd /tmp

# ═══════════════════════════════════════════════════════════════════════════
# Configuration (from environment or defaults)
# ═══════════════════════════════════════════════════════════════════════════

NODE_NAME="${CDN_NODE_NAME:-Community CDN Node}"
TAGLINE="${CDN_NODE_TAGLINE:-by Community Networks}"
PORT="${CDN_PORT:-8282}"
MEDIA_ROOT="${CDN_MEDIA_ROOT:-/var/cdn-media}"
PLATFORM_URL="${CDN_PLATFORM_URL:-}"
API_KEY="${CDN_API_KEY:-}"

INSTALL_DIR="/opt/cdn-portal"
SERVICE_USER="cdnportal"

# Password: use provided value, or auto-generate a secure one
PASSWORD_GENERATED=false
if [ -z "$CDN_ADMIN_PASSWORD" ] || [ ${#CDN_ADMIN_PASSWORD} -lt 8 ]; then
    ADMIN_PASSWORD=$(python3 -c 'import secrets, string; print("".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20)))')
    PASSWORD_GENERATED=true
else
    ADMIN_PASSWORD="$CDN_ADMIN_PASSWORD"
fi

# Show configuration
echo -e "${CYAN}${BOLD}Configuration:${NC}"
echo -e "  Node Name:      ${BOLD}$NODE_NAME${NC}"
echo -e "  Tagline:        $TAGLINE"
if [ "$PASSWORD_GENERATED" = true ]; then
    echo -e "  Admin Password: ${YELLOW}(auto-generated — shown at end of install)${NC}"
else
    echo -e "  Admin Password: ${BOLD}********${NC} (${#ADMIN_PASSWORD} characters)"
fi
echo -e "  Port:           $PORT"
echo -e "  Media Storage:  $MEDIA_ROOT"
echo -e "  Platform URL:   ${PLATFORM_URL:-Not configured}"
echo ""

sleep 2

# ═══════════════════════════════════════════════════════════════════════════
# Installation Steps
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Installing System Dependencies${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

info "Updating package list..."
apt-get update -qq

info "Installing Python and dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv git curl libffi-dev libjpeg-dev zlib1g-dev

log "Dependencies installed"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Downloading Portal Code${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

mkdir -p "$INSTALL_DIR"

if [ -f "$(dirname "$0")/../manage.py" ]; then
    info "Copying from local repository..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
else
    info "Cloning from GitHub..."
    git clone https://github.com/solomonitotia/cdn-raspberrypi.git "$INSTALL_DIR" 2>&1 | grep -v "^Cloning"
fi

[ -f "$INSTALL_DIR/manage.py" ] || error "Code download failed — $INSTALL_DIR/manage.py not found. Check your internet connection and try again."

log "Portal code downloaded"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Creating System User${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash -d "$INSTALL_DIR" "$SERVICE_USER"
    log "User '$SERVICE_USER' created"
else
    info "User '$SERVICE_USER' already exists"
fi

# ── Detect external drive and redirect media storage ────────────────────────
SERVICE_UID=$(id -u "$SERVICE_USER")
SERVICE_GID=$(id -g "$SERVICE_USER")
ROOT_DEV=$(stat -c %d / 2>/dev/null)
EXT_DRIVE=""
EXT_DRIVE_DEV=""
EXT_DRIVE_FS=""

for base in /mnt /media; do
    [ -d "$base" ] || continue
    for dir in "$base"/*/; do
        [ -d "$dir" ] || continue
        dir="${dir%/}"
        dir_dev=$(stat -c %d "$dir" 2>/dev/null)
        # Skip if same device as root filesystem
        [ "$dir_dev" = "$ROOT_DEV" ] && continue
        EXT_DRIVE="$dir"
        EXT_DRIVE_DEV=$(findmnt -n -o SOURCE "$dir" 2>/dev/null || echo "")
        EXT_DRIVE_FS=$(findmnt -n -o FSTYPE  "$dir" 2>/dev/null || echo "")
        break 2
    done
done

if [ -n "$EXT_DRIVE" ]; then
    info "External drive detected: $EXT_DRIVE (${EXT_DRIVE_FS:-unknown fs})"

    # Update /etc/fstab to mount with cdnportal's uid/gid so it can write files
    if [ -n "$EXT_DRIVE_DEV" ] && grep -q "$EXT_DRIVE" /etc/fstab 2>/dev/null; then
        # Replace existing uid/gid in the fstab entry
        sed -i "/$EXT_DRIVE/s/uid=[0-9]*/uid=$SERVICE_UID/g;/$EXT_DRIVE/s/gid=[0-9]*/gid=$SERVICE_GID/g" /etc/fstab
        log "Updated fstab mount options for $EXT_DRIVE"
    elif [ -n "$EXT_DRIVE_DEV" ]; then
        # Add a new fstab entry
        if echo "$EXT_DRIVE_FS" | grep -qE "^ntfs|^fuseblk"; then
            echo "$EXT_DRIVE_DEV $EXT_DRIVE ntfs-3g uid=$SERVICE_UID,gid=$SERVICE_GID,umask=0022,nofail,defaults 0 0" >> /etc/fstab
        else
            echo "$EXT_DRIVE_DEV $EXT_DRIVE $EXT_DRIVE_FS uid=$SERVICE_UID,gid=$SERVICE_GID,nofail,defaults 0 0" >> /etc/fstab
        fi
        log "Added fstab entry for $EXT_DRIVE"
    fi

    # Remount to apply new uid/gid
    umount "$EXT_DRIVE" 2>/dev/null || true
    mount "$EXT_DRIVE" 2>/dev/null || true

    # Use the external drive for media storage
    MEDIA_ROOT="$EXT_DRIVE/cdn-media"
    mkdir -p "$MEDIA_ROOT"
    chown "$SERVICE_USER:$SERVICE_USER" "$MEDIA_ROOT"
    chmod 755 "$MEDIA_ROOT"
    log "Media storage → $MEDIA_ROOT  ($(df -h --output=avail "$EXT_DRIVE" 2>/dev/null | tail -1 | tr -d ' ') free)"
fi

mkdir -p "$MEDIA_ROOT" /var/log/cdn-portal
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$MEDIA_ROOT" /var/log/cdn-portal
chmod 755 "$MEDIA_ROOT"

log "Permissions configured"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Installing Python Packages${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

info "Installing packages (this may take 2-3 minutes)..."
pip install --upgrade pip -q 2>&1 | grep -v "^Requirement" || true
pip install -r requirements.txt -q 2>&1 | grep -v "^Requirement" || true

log "Python packages installed"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Configuring Portal${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(40))')

if [ -f /sys/class/net/eth0/address ]; then
    NODE_ID="pi-$(cat /sys/class/net/eth0/address | tr -d ':')"
elif [ -f /sys/class/net/wlan0/address ]; then
    NODE_ID="pi-$(cat /sys/class/net/wlan0/address | tr -d ':')"
else
    NODE_ID="pi-$(hostname)"
fi

cat > "$INSTALL_DIR/.env" <<EOF
SECRET_KEY="$SECRET_KEY"
DEBUG=False
ALLOWED_HOSTS=*
CDN_NODE_NAME="$NODE_NAME"
CDN_NODE_TAGLINE="$TAGLINE"
CDN_NODE_IDENTIFIER="$NODE_ID"
MEDIA_ROOT="$MEDIA_ROOT"
CDN_PLATFORM_URL="${PLATFORM_URL:-}"
CDN_API_KEY="${API_KEY:-}"
EOF

chmod 600 "$INSTALL_DIR/.env"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"

log "Configuration saved"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Setting Up Database${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cd "$INSTALL_DIR"
source venv/bin/activate
set -a; source .env; set +a

info "Running migrations..."
python manage.py migrate --no-input 2>&1 | grep -E "Applying|OK|Running" || true

info "Collecting static files..."
python manage.py collectstatic --no-input -v 0 2>&1 > /dev/null

info "Creating admin user..."
DJANGO_ADMIN_PASSWORD="$ADMIN_PASSWORD" python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
password = os.environ['DJANGO_ADMIN_PASSWORD']
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', password)
    print('Admin user created')
else:
    u = User.objects.get(username='admin')
    u.set_password(password)
    u.save()
    print('Admin password updated')
" 2>&1 | tail -1

# Mark that the admin must change password on first login
touch "$INSTALL_DIR/.password_change_required"

# Save credentials to a file (readable only by root and the service user)
cat > "$INSTALL_DIR/.admin-credentials" <<CREDEOF
CDN Portal Admin Credentials
=============================
Username : admin
Password : $ADMIN_PASSWORD
Portal   : http://$(hostname -I | awk '{print $1}'):$PORT
Admin    : http://$(hostname -I | awk '{print $1}'):$PORT/admin

To view again: sudo cat $INSTALL_DIR/.admin-credentials
CREDEOF
chmod 640 "$INSTALL_DIR/.admin-credentials"

log "Database ready"

# Fix ownership — migrations run as root create db.sqlite3 owned by root,
# but the service runs as $SERVICE_USER and needs write access.
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Installing System Service${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cat > /etc/systemd/system/cdn-portal.service <<EOF
[Unit]
Description=Community CDN Portal
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn \\
    --workers 2 \\
    --bind 0.0.0.0:$PORT \\
    --timeout 120 \\
    --access-logfile /var/log/cdn-portal/access.log \\
    --error-logfile /var/log/cdn-portal/error.log \\
    cdnnode.wsgi:application
Restart=always
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${EXT_DRIVE:+$EXT_DRIVE }$MEDIA_ROOT /var/log/cdn-portal $INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cdn-portal.service 2>&1 > /dev/null
systemctl restart cdn-portal.service

sleep 3

if systemctl is-active --quiet cdn-portal.service; then
    log "Service started successfully"
else
    warn "Service may have issues. Check logs: sudo journalctl -u cdn-portal -n 50"
fi

echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Configuring Firewall${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if command -v ufw &>/dev/null; then
    ufw allow "$PORT/tcp" comment "CDN Portal" 2>/dev/null
    ufw reload 2>/dev/null
    log "Firewall: port $PORT allowed"
else
    warn "ufw not found — make sure port $PORT is open on your firewall manually"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Success Message
# ═══════════════════════════════════════════════════════════════════════════

LOCAL_IP=$(hostname -I | awk '{print $1}')

clear
echo -e "${GREEN}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     ✅  Installation Complete! 🎉                     ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
echo -e "${CYAN}${BOLD}📱 Access Your Portal:${NC}"
echo -e "   ${BOLD}Portal:${NC}          http://$LOCAL_IP:$PORT"
echo -e "   ${BOLD}Admin Panel:${NC}     http://$LOCAL_IP:$PORT/admin"
echo ""
echo -e "${CYAN}${BOLD}🔑 Admin Credentials:${NC}"
echo -e "   ${BOLD}Username:${NC}        admin"
echo -e "   ${BOLD}Password:${NC}        ${GREEN}${BOLD}$ADMIN_PASSWORD${NC}"
echo ""

if [ "$PASSWORD_GENERATED" = true ]; then
    echo -e "${YELLOW}${BOLD}⚠️  This password was auto-generated. Save it now!${NC}"
    echo -e "   Change it at: http://$LOCAL_IP:$PORT/admin/password_change/"
    echo ""
fi

if [ "$PASSWORD_GENERATED" = true ]; then
    echo -e "${CYAN}${BOLD}💾 Credentials saved to:${NC}  ${BOLD}$INSTALL_DIR/.admin-credentials${NC}"
    echo -e "   View any time:   ${BOLD}sudo cat $INSTALL_DIR/.admin-credentials${NC}"
    echo ""
fi

echo -e "${CYAN}${BOLD}🛠️ Useful Commands:${NC}"
echo -e "   Check status:    ${BOLD}sudo systemctl status cdn-portal${NC}"
echo -e "   View logs:       ${BOLD}sudo journalctl -u cdn-portal -f${NC}"
echo -e "   Restart:         ${BOLD}sudo systemctl restart cdn-portal${NC}"
echo ""

if [ -z "$PLATFORM_URL" ]; then
    echo -e "${YELLOW}${BOLD}⚠️  Platform not connected${NC}"
    echo -e "   This node is not linked to a CN Platform yet."
    echo -e "   To connect it:"
    echo -e "   1. Register this node on your CN Platform → CDN Nodes page"
    echo -e "   2. Copy the API key shown after registration"
    echo -e "   3. Run:"
    echo -e "      ${BOLD}sudo sed -i 's|CDN_PLATFORM_URL=.*|CDN_PLATFORM_URL=\"<platform-url>\"|' $INSTALL_DIR/.env${NC}"
    echo -e "      ${BOLD}sudo sed -i 's|CDN_API_KEY=.*|CDN_API_KEY=\"<api-key>\"|' $INSTALL_DIR/.env${NC}"
    echo -e "      ${BOLD}sudo systemctl restart cdn-portal${NC}"
    echo ""
fi

echo -e "${GREEN}Setup complete! Your portal is ready to use. 🌐${NC}"
echo ""
