#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║     CDN Portal — Easy Installer for Raspberry Pi                        ║
# ║     One-command setup for non-technical users                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Usage: Just run this command on your Raspberry Pi:
#   curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/easy-install.sh | sudo bash
#
# Or if you already cloned the repo:
#   sudo bash scripts/easy-install.sh

set -e

# Colors for pretty output
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
ask()   { echo -e "${BLUE}?${NC} $1"; }

clear
echo -e "${CYAN}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     🌐  CDN Portal - Easy Installer                   ║
  ║                                                        ║
  ║     Setting up your offline content sharing portal    ║
  ║     on Raspberry Pi in just a few minutes!            ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   error "Please run with sudo: sudo bash $0"
fi

info "This installer will:"
echo "  • Install all required software"
echo "  • Download the CDN portal code from GitHub"
echo "  • Set up the database"
echo "  • Create an admin account"
echo "  • Start the portal automatically"
echo ""

read -p "$(echo -e ${BLUE}Press ENTER to continue or CTRL+C to cancel...${NC})"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Gather Settings (Interactive)
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 1: Configure Your Portal${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

# Node name
ask "What should we call your community network?"
read -p "   Name (e.g. 'Athi Community Network'): " NODE_NAME
NODE_NAME=${NODE_NAME:-"Community CDN Node"}

# Tagline
ask "Add a tagline/description:"
read -p "   Tagline (e.g. 'Free offline content'): " TAGLINE
TAGLINE=${TAGLINE:-"by Community Networks"}

# Port
ask "Which port should the portal run on?"
read -p "   Port [8282]: " PORT
PORT=${PORT:-8282}

# Admin password
ask "Set admin panel password:"
while true; do
    read -s -p "   Password (min 8 characters): " ADMIN_PASSWORD
    echo
    if [ ${#ADMIN_PASSWORD} -ge 8 ]; then
        read -s -p "   Confirm password: " ADMIN_PASSWORD2
        echo
        if [ "$ADMIN_PASSWORD" = "$ADMIN_PASSWORD2" ]; then
            break
        else
            warn "Passwords don't match. Try again."
        fi
    else
        warn "Password too short. Use at least 8 characters."
    fi
done

# External drive setup
echo ""
ask "Do you want to use an external USB drive for storing content?"
info "   (Recommended if you have a large USB drive attached)"
read -p "   Use external drive? [y/N]: " USE_EXTERNAL
USE_EXTERNAL=${USE_EXTERNAL:-n}

if [[ "$USE_EXTERNAL" =~ ^[Yy]$ ]]; then
    # Auto-detect USB drives
    echo ""
    info "Detecting USB drives..."
    DETECTED_DRIVES=$(lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E "sd[a-z]1.*part" || true)

    if [ -z "$DETECTED_DRIVES" ]; then
        warn "No USB drives detected. Make sure your USB drive is plugged in."
        MEDIA_ROOT="/var/cdn-media"
    else
        echo ""
        echo "Detected drives:"
        lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,LABEL | grep -E "sd[a-z]|NAME"
        echo ""
        ask "Enter the mount point of your USB drive:"
        info "   (e.g., /media/pi/USB_DRIVE or /mnt/usb)"
        read -p "   Path: " MEDIA_ROOT
        MEDIA_ROOT=${MEDIA_ROOT:-/var/cdn-media}

        # Create media folder if doesn't exist
        if [ -d "$MEDIA_ROOT" ]; then
            log "Drive found at $MEDIA_ROOT"
        else
            warn "Path doesn't exist yet. Will create it."
            mkdir -p "$MEDIA_ROOT"
        fi
    fi
else
    MEDIA_ROOT="/var/cdn-media"
    info "Using internal storage: $MEDIA_ROOT"
fi

# Platform integration (optional)
echo ""
ask "Do you have a central platform URL and API key? (Optional)"
info "   (Only needed if connecting to a central management platform)"
read -p "   Configure platform integration? [y/N]: " USE_PLATFORM
USE_PLATFORM=${USE_PLATFORM:-n}

if [[ "$USE_PLATFORM" =~ ^[Yy]$ ]]; then
    read -p "   Platform URL: " PLATFORM_URL
    read -p "   API Key: " API_KEY
else
    PLATFORM_URL=""
    API_KEY=""
fi

# Show summary
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Configuration Summary${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "  Node Name:      ${BOLD}$NODE_NAME${NC}"
echo -e "  Tagline:        $TAGLINE"
echo -e "  Port:           $PORT"
echo -e "  Media Storage:  $MEDIA_ROOT"
echo -e "  Platform:       ${PLATFORM_URL:-Not configured}"
echo ""
read -p "$(echo -e ${BLUE}Press ENTER to start installation...${NC})"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Install Dependencies
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 2: Installing Software (1-2 minutes)${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

info "Updating package list..."
apt-get update -qq

info "Installing Python and dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv git curl libffi-dev libjpeg-dev zlib1g-dev

log "Dependencies installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Download Portal Code
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 3: Downloading Portal Code${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

INSTALL_DIR="/opt/cdn-portal"
SERVICE_USER="cdnportal"

info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Check if we're running from the repo or need to clone
if [ -f "$(dirname "$0")/../manage.py" ]; then
    info "Copying from local repository..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
else
    info "Cloning from GitHub..."
    git clone https://github.com/solomonitotia/cdn-raspberrypi.git "$INSTALL_DIR" || \
        error "Failed to clone repository. Check your internet connection."
fi

log "Portal code downloaded"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Create User & Set Permissions
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 4: Setting Up System User${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash -d "$INSTALL_DIR" "$SERVICE_USER"
    log "User '$SERVICE_USER' created"
else
    info "User '$SERVICE_USER' already exists"
fi

mkdir -p "$MEDIA_ROOT" /var/log/cdn-portal
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$MEDIA_ROOT" /var/log/cdn-portal
chmod 755 "$MEDIA_ROOT"

log "Permissions configured"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Install Python Packages
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 5: Installing Python Packages (2-3 minutes)${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cd "$INSTALL_DIR"

info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

info "Installing Django and other packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

log "Python packages installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Configure Django
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 6: Configuring Portal${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

# Generate secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(40))')

# Auto-detect node identifier
if [ -f /sys/class/net/eth0/address ]; then
    NODE_ID="pi-$(cat /sys/class/net/eth0/address | tr -d ':')"
elif [ -f /sys/class/net/wlan0/address ]; then
    NODE_ID="pi-$(cat /sys/class/net/wlan0/address | tr -d ':')"
else
    NODE_ID="pi-$(hostname)"
fi

# Create environment file
cat > "$INSTALL_DIR/.env" <<EOF
# Django Settings
SECRET_KEY="$SECRET_KEY"
DEBUG=False
ALLOWED_HOSTS=*

# Portal Settings
CDN_NODE_NAME="$NODE_NAME"
CDN_NODE_TAGLINE="$TAGLINE"
CDN_NODE_IDENTIFIER="$NODE_ID"

# Storage
MEDIA_ROOT="$MEDIA_ROOT"

# Platform Integration (optional)
CDN_PLATFORM_URL=${PLATFORM_URL:-}
CDN_API_KEY=${API_KEY:-}
EOF

chmod 600 "$INSTALL_DIR/.env"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"

log "Configuration saved"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Setup Database
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 7: Setting Up Database${NC}"
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo ""

cd "$INSTALL_DIR"
source venv/bin/activate
set -a; source .env; set +a

info "Running database migrations..."
python manage.py migrate --no-input

info "Collecting static files..."
python manage.py collectstatic --no-input -v 0

info "Creating admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', '$ADMIN_PASSWORD')
    print('Admin user created')
else:
    print('Admin user already exists')
"

log "Database ready"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 8: Create System Service
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────${NC}"
echo -e "${CYAN}${BOLD} Step 8: Installing Auto-Start Service${NC}"
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
ReadWritePaths=$MEDIA_ROOT /var/log/cdn-portal $INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cdn-portal.service
systemctl start cdn-portal.service

sleep 3

if systemctl is-active --quiet cdn-portal.service; then
    log "Portal service started"
else
    error "Service failed to start. Check logs: sudo journalctl -u cdn-portal -n 50"
fi

# ═══════════════════════════════════════════════════════════════════════════
# DONE! Show Success Message
# ═══════════════════════════════════════════════════════════════════════════
LOCAL_IP=$(hostname -I | awk '{print $1}')

clear
echo -e "${GREEN}${BOLD}"
cat << "EOF"
  ╔════════════════════════════════════════════════════════╗
  ║                                                        ║
  ║     ✅  Installation Complete! 🎉                     ║
  ║                                                        ║
  ║     Your CDN Portal is now running!                   ║
  ║                                                        ║
  ╚════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""
echo -e "${CYAN}${BOLD}📱 Access Your Portal:${NC}"
echo -e "   ${BOLD}Portal URL:${NC}      http://$LOCAL_IP:$PORT"
echo -e "   ${BOLD}Admin Panel:${NC}     http://$LOCAL_IP:$PORT/admin"
echo ""
echo -e "${CYAN}${BOLD}🔑 Admin Login:${NC}"
echo -e "   ${BOLD}Username:${NC}        admin"
echo -e "   ${BOLD}Password:${NC}        (the one you just set)"
echo ""
echo -e "${CYAN}${BOLD}📂 Media Storage:${NC}"
echo -e "   ${BOLD}Location:${NC}        $MEDIA_ROOT"
echo ""
echo -e "${CYAN}${BOLD}🛠️ Useful Commands:${NC}"
echo -e "   ${BOLD}Check status:${NC}    sudo systemctl status cdn-portal"
echo -e "   ${BOLD}View logs:${NC}       sudo journalctl -u cdn-portal -f"
echo -e "   ${BOLD}Restart:${NC}         sudo systemctl restart cdn-portal"
echo -e "   ${BOLD}Stop:${NC}            sudo systemctl stop cdn-portal"
echo ""
echo -e "${YELLOW}${BOLD}📝 Next Steps:${NC}"
echo "   1. Open the admin panel at http://$LOCAL_IP:$PORT/admin"
echo "   2. Upload your logo and customize colors"
echo "   3. Create categories (Movies, Music, etc.)"
echo "   4. Start uploading content!"
echo ""
echo -e "${GREEN}Thank you for using Community CDN Portal! 🌐${NC}"
echo ""
