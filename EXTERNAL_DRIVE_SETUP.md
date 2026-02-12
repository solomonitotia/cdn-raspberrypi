# External Drive Setup for CDN Node

This guide explains how to configure the CDN node to store all content (videos, images, documents, announcements) on an external USB drive attached to your Raspberry Pi.

---

## 📦 Why External Drive?

- **Limited SD Card Space** — Raspberry Pi SD cards are small (typically 32GB)
- **Offline Content Sharing** — Store hundreds of GBs of movies, music, documents
- **Easy Expansion** — Use 500GB, 1TB, or larger USB drives
- **Reliability** — External drives are more reliable for heavy read/write

---

## 🔧 Setup Steps

### **1. Attach USB Drive to Raspberry Pi**

1. Insert your USB drive into the Raspberry Pi's USB port
2. The drive will auto-mount (usually to `/media/pi/YourDriveName` or `/mnt/usb`)

### **2. Find the Mount Point**

```bash
# List all mounted drives
lsblk

# Example output:
# NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
# sda           8:0    0 931.5G  0 disk
# └─sda1        8:1    0 931.5G  0 part /media/pi/USB_DRIVE
```

Note the mount point (e.g., `/media/pi/USB_DRIVE`)

### **3. Create Media Directory**

```bash
# Create a dedicated folder for CDN content
sudo mkdir -p /media/pi/USB_DRIVE/cdn-media

# Set ownership to your user
sudo chown -R $USER:$USER /media/pi/USB_DRIVE/cdn-media

# Set permissions
chmod -R 755 /media/pi/USB_DRIVE/cdn-media
```

### **4. Configure Django to Use External Drive**

When running the Django server or systemd service, set the `MEDIA_ROOT` environment variable:

**Option A: Manual Run**
```bash
cd ~/cdn-raspberrypi-django
export MEDIA_ROOT=/media/pi/USB_DRIVE/cdn-media
venv/bin/python manage.py runserver 0.0.0.0:8282
```

**Option B: Using .env File** (Recommended)
```bash
# Create .env file in project root
echo "MEDIA_ROOT=/media/pi/USB_DRIVE/cdn-media" >> .env
echo "CDN_NODE_NAME=Athi Community Network" >> .env
echo "CDN_NODE_TAGLINE=Free offline content for everyone" >> .env
```

Then update `settings.py` to load from .env:
```python
# Install python-dotenv: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

**Option C: Systemd Service** (Production)

Edit the systemd service file:
```bash
sudo nano /etc/systemd/system/cdn-node.service
```

Add the environment variable:
```ini
[Service]
Environment="MEDIA_ROOT=/media/pi/USB_DRIVE/cdn-media"
Environment="CDN_NODE_NAME=Athi Community Network"
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart cdn-node
```

### **5. Migrate Existing Content (if any)**

If you already uploaded content to the default location, migrate it:

```bash
# Default location is ~/cdn-raspberrypi-django/media
cp -r ~/cdn-raspberrypi-django/media/* /media/pi/USB_DRIVE/cdn-media/
```

---

## 📁 Directory Structure on External Drive

```
/media/pi/USB_DRIVE/cdn-media/
├── branding/              # Logo uploads from Site Settings
│   └── logo.png
├── covers/                # Category cover images
│   ├── movies_cover.jpg
│   └── music_cover.jpg
├── announcements/         # Announcement media (images, posters)
│   ├── event_poster.png
│   └── ad_banner.jpg
├── networking/            # Files in "Networking" category
│   └── cisco_tutorial.pdf
├── movies/                # Files in "Movies" category
│   ├── action_movie.mp4
│   └── comedy_film.mkv
└── music/                 # Files in "Music" category
    └── song.mp3
```

---

## ✅ Verification

### **Check Media Root**

1. Go to Django admin → **Site Settings**
2. Upload a logo image
3. SSH to Pi and verify:
   ```bash
   ls -lh /media/pi/USB_DRIVE/cdn-media/branding/
   ```

### **Upload Test Content**

1. Admin → **Categories** → Add category "Test"
2. Admin → **Content Items** → Add new item with a video file
3. Verify the file appears in:
   ```bash
   ls -lh /media/pi/USB_DRIVE/cdn-media/test/
   ```

### **Test In-Browser Viewing**

1. Visit the portal homepage
2. Click on a video → Should play directly in browser (no download)
3. Click on a PDF → Should open in browser viewer
4. Click on an image → Should display inline

---

## 🎬 In-Browser Viewing (No Download Required)

### **Supported File Types:**

| Type | Viewing Method | Download Optional? |
|------|----------------|-------------------|
| **Video** (.mp4, .mkv, .webm) | Built-in HTML5 video player | ✅ Yes |
| **Audio** (.mp3, .wav, .ogg) | Built-in HTML5 audio player | ✅ Yes |
| **PDF** (.pdf) | Inline iframe PDF viewer | ✅ Yes |
| **Images** (.jpg, .png, .gif) | Full-screen image viewer | ✅ Yes |
| **Documents** (.doc, .docx, .txt) | Download to view | ✅ Yes |
| **Software** (.exe, .apk, .zip) | Download only | Required |

### **Download Button**

- Every file has an **optional** "⬇ Download" button
- Users can choose to download if they want offline access
- Otherwise, they **view/watch directly in the browser**

---

## 🔄 Auto-Mount on Boot

To ensure the USB drive auto-mounts on Raspberry Pi boot:

### **1. Find Drive UUID**
```bash
sudo blkid
# Example output:
# /dev/sda1: UUID="1234-5678" TYPE="exfat" PARTUUID="abcd-01"
```

### **2. Edit fstab**
```bash
sudo nano /etc/fstab
```

Add this line (replace UUID with yours):
```
UUID=1234-5678  /mnt/usb  exfat  defaults,auto,users,rw,nofail  0  0
```

### **3. Create mount point and test**
```bash
sudo mkdir -p /mnt/usb
sudo mount -a
ls /mnt/usb
```

### **4. Update MEDIA_ROOT**

Update your environment variable or .env file to use `/mnt/usb/cdn-media` instead of `/media/pi/...`

---

## 🚨 Troubleshooting

### **Drive Not Mounting**
```bash
# Check if drive is detected
lsblk

# Manually mount
sudo mount /dev/sda1 /mnt/usb

# Check drive filesystem
sudo blkid /dev/sda1
```

### **Permission Denied When Uploading**
```bash
# Fix ownership
sudo chown -R www-data:www-data /mnt/usb/cdn-media  # For systemd service
# OR
sudo chown -R $USER:$USER /mnt/usb/cdn-media  # For manual run
```

### **Files Not Showing in Browser**
- Check MEDIA_ROOT environment variable is set correctly
- Restart Django server
- Check file permissions (should be readable)

### **Video Won't Play**
- Ensure `.mp4` codec is H.264 (most compatible)
- Convert with: `ffmpeg -i input.mkv -codec copy output.mp4`
- Check browser console for errors

---

## 💡 Best Practices

1. **Use exFAT or ext4 filesystem** — Better for large files
2. **Regular backups** — External drives can fail
3. **Label your drive** — Helps identify if multiple drives
4. **Use quality USB drives** — SanDisk, Samsung, WD recommended
5. **Power supply** — Some drives need powered USB hub

---

## 📊 Disk Space Monitoring

Check available space:
```bash
df -h /mnt/usb
```

The portal **automatically shows storage usage** in the sidebar!

---

## ✨ Summary

✅ **All content stored on external drive**
✅ **In-browser viewing for videos, audio, PDFs, images**
✅ **Download is optional, not required**
✅ **Announcement media also stored on external drive**
✅ **Easy to expand — just use a bigger USB drive**

Your Raspberry Pi CDN is now ready to serve **hundreds of GBs** of offline content to your community! 🎉
