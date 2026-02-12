# 🚀 Easy Installation Guide

## Method 1: Fully Automated (Zero Interaction)

Run this **single command** with your settings:

```bash
curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh | \
  sudo CDN_NODE_NAME="My Network" CDN_ADMIN_PASSWORD="YourSecurePass123" bash
```

Or with all options:

```bash
curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/auto-install.sh | \
  sudo CDN_NODE_NAME="Athi Community Network" \
       CDN_NODE_TAGLINE="Free offline content" \
       CDN_ADMIN_PASSWORD="SecurePass123" \
       CDN_PORT="8282" \
       CDN_MEDIA_ROOT="/mnt/usb/cdn-media" \
  bash
```

✅ **No questions asked** - fully automatic!
✅ **Time required:** 5-10 minutes

---

## Method 2: Interactive Installer

Download the script first, then run it (allows interactive prompts):

```bash
# Download the script
wget https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/easy-install.sh

# Make it executable
chmod +x easy-install.sh

# Run it
sudo ./easy-install.sh
```

The installer will:
- ✅ Ask you simple questions (node name, password, etc.)
- ✅ Install everything automatically
- ✅ Set up the portal to start on boot
- ✅ Give you the URL to access your portal

**Time required:** 5-10 minutes (mostly automatic)

---

## What You'll Be Asked

The installer will ask you:

1. **Node Name** - What to call your community network (e.g., "Athi Community Network")
2. **Tagline** - A short description (e.g., "Free offline content")
3. **Port** - Which port to run on (default: 8282)
4. **Admin Password** - Password for the admin panel (minimum 8 characters)
5. **External Drive** - Whether to use a USB drive for storage (optional)
6. **Platform Integration** - Central platform URL and API key (optional)

---

## After Installation

Once complete, you'll see:

```
✅ Installation Complete! 🎉

📱 Access Your Portal:
   Portal URL:      http://192.168.1.100:8282
   Admin Panel:     http://192.168.1.100:8282/admin

🔑 Admin Login:
   Username:        admin
   Password:        (the one you set)
```

### Next Steps:

1. **Open the admin panel** in your browser
2. **Upload your logo** (Admin → Site Settings)
3. **Create categories** (Movies, Music, Documents, etc.)
4. **Upload content** (Videos, songs, PDFs, etc.)
5. **Share the portal URL** with your community!

---

## Advanced Installation (For Technical Users)

If you're comfortable with Linux and want more control:

```bash
# Clone the repository
git clone https://github.com/solomonitotia/cdn-raspberrypi.git
cd cdn-raspberrypi

# Set environment variables
export CDN_NODE_NAME="Your Network Name"
export CDN_API_KEY="your-api-key"
export CDN_PLATFORM_URL="https://platform.example.com"
export MEDIA_ROOT="/mnt/usb/cdn-media"  # Optional: external drive

# Run deployment script
sudo bash scripts/deploy-pi.sh
```

See [README.md](README.md) for full documentation.

---

## Troubleshooting

### Installation fails with "permission denied"
Make sure you're running with `sudo`:
```bash
curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/easy-install.sh | sudo bash
```

### Can't access the portal after installation
1. Check the service status:
   ```bash
   sudo systemctl status cdn-portal
   ```

2. View logs:
   ```bash
   sudo journalctl -u cdn-portal -f
   ```

3. Make sure you're using the correct IP address (shown at the end of installation)

### Portal runs but can't upload files
Check media folder permissions:
```bash
sudo chown -R cdnportal:cdnportal /var/cdn-media
```

### Want to use an external USB drive
The installer will ask you during setup. Make sure your USB drive is plugged in and mounted before running the installer.

---

## Uninstall

To remove the portal:

```bash
# Stop and disable the service
sudo systemctl stop cdn-portal
sudo systemctl disable cdn-portal
sudo rm /etc/systemd/system/cdn-portal.service

# Remove files
sudo rm -rf /opt/cdn-portal
sudo rm -rf /var/cdn-media  # Only if you want to delete uploaded content
sudo rm -rf /var/log/cdn-portal

# Remove user
sudo userdel cdnportal

# Reload systemd
sudo systemctl daemon-reload
```

---

## Support

- **Documentation:** See [README.md](README.md) and [EXTERNAL_DRIVE_SETUP.md](EXTERNAL_DRIVE_SETUP.md)
- **Issues:** https://github.com/solomonitotia/cdn-raspberrypi/issues
- **Community:** Join our community network forum

---

**Built with ❤️ for Community Networks**
