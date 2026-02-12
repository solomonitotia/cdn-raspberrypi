# 🌐 Community CDN Node

A Django-powered offline content delivery network (CDN) for community networks. Share movies, music, documents, and educational content with your community — **no internet required!**

---

## ✨ Features

### **For Users:**
- 📺 **Watch videos directly** in browser (no download required)
- 🎵 **Stream audio** with built-in player
- 📄 **View PDFs** inline
- 🖼️ **Browse images** in full-screen viewer
- 🔍 **Search** across all content
- 📱 **Mobile-friendly** responsive design
- ⬇️ **Optional download** for offline access

### **For Admins:**
- 🎨 **Customizable branding** — Logo, name, colors
- 📢 **Announcements** — Post news with images/videos
- 📁 **Category management** — Organize content with emoji icons
- 💾 **External drive support** — Store TBs of content on USB drive
- 📊 **Storage monitoring** — Track disk usage
- 🎯 **Content metadata** — Year, tags, descriptions, thumbnails

---

## 🚀 Quick Start

### **Option 1: Easy Installation (Recommended for Non-Technical Users)**

Run this **single command** on your Raspberry Pi:

```bash
curl -sSL https://raw.githubusercontent.com/solomonitotia/cdn-raspberrypi/main/scripts/easy-install.sh | sudo bash
```

The installer will ask you simple questions and set everything up automatically in 5-10 minutes!

📖 **[Full Installation Guide →](INSTALL.md)**

---

### **Option 2: Manual Installation (For Advanced Users)**

```bash
# Clone the repository
git clone https://github.com/solomonitotia/cdn-raspberrypi.git ~/cdn-raspberrypi
cd ~/cdn-raspberrypi

# Set environment variables
export CDN_NODE_NAME="Athi Community Network"
export CDN_NODE_TAGLINE="Free offline content"
export MEDIA_ROOT="/mnt/usb/cdn-media"  # External USB drive
export CDN_PLATFORM_URL="https://platform.example.com"
export CDN_API_KEY="your-api-key"

# Run the deployment script
bash scripts/deploy-pi.sh
```

---

### **Access the Portal**

- **Public Portal:** `http://<raspberry-pi-ip>:8282`
- **Admin Panel:** `http://<raspberry-pi-ip>:8282/admin`
  - Username: `admin`
  - Password: `admin123` (⚠️ Change this!)

### **3. Customize Your Node**

1. Go to **Admin → Site Settings**
2. Upload your logo
3. Change node name and tagline
4. Pick your brand colors
5. Save!

---

## 📦 External Drive Setup

For storing large amounts of content (movies, music, etc.), use an external USB drive.

### **Quick Setup:**

```bash
# 1. Mount USB drive (auto-mounts to /media/pi/USB_DRIVE)

# 2. Create media folder
sudo mkdir -p /media/pi/USB_DRIVE/cdn-media
sudo chown -R $USER:$USER /media/pi/USB_DRIVE/cdn-media

# 3. Set environment variable
echo "MEDIA_ROOT=/media/pi/USB_DRIVE/cdn-media" >> ~/.bashrc
source ~/.bashrc

# 4. Restart Django
sudo systemctl restart cdn-node
```

📖 **[Full External Drive Setup Guide →](EXTERNAL_DRIVE_SETUP.md)**

---

## 📚 Adding Content

### **Create Categories**

1. Admin → **Categories** → **Add Category**
2. Name: "Movies"
3. Pick an icon: 🎬
4. Upload a cover image (optional)
5. Save

### **Upload Content**

1. Admin → **Content Items** → **Add Content Item**
2. Title: "Action Movie 2024"
3. Category: Movies
4. Upload file (.mp4, .mkv, etc.)
5. Add thumbnail, description, year, tags
6. Save

**Supported File Types:**
- Videos: `.mp4`, `.mkv`, `.avi`, `.webm`
- Audio: `.mp3`, `.wav`, `.ogg`, `.flac`
- Documents: `.pdf`, `.doc`, `.docx`, `.txt`
- Images: `.jpg`, `.png`, `.gif`, `.webp`
- Software: `.exe`, `.apk`, `.zip`, `.deb`

---

## 📢 Announcements

Post news, events, or ads with images/videos:

1. Admin → **Announcements** → **Add Announcement**
2. Title: "Movie Night This Friday!"
3. Content: "Join us for a community movie night..."
4. Type: **Promo** (purple border)
5. Upload image or video URL
6. Optional link: Link to a category or external page
7. Set expiration date (optional)
8. Save

**Announcement Types:**
- 📘 **Info** (blue) — General announcements
- ✅ **Success** (green) — Good news, achievements
- ⚠️ **Warning** (orange) — Important notices
- 🎁 **Promo** (purple) — Ads, events, promotions

---

## 🎬 In-Browser Viewing

**Users don't need to download!** Content plays directly in the browser:

| File Type | Viewing Experience |
|-----------|-------------------|
| 🎬 **Video** | HTML5 video player with controls |
| 🎵 **Audio** | HTML5 audio player with album art |
| 📄 **PDF** | Inline PDF viewer |
| 🖼️ **Image** | Full-screen image viewer |
| 📁 **Other** | Download button available |

**Download is always optional** — users can choose to download for offline access.

---

## ⚙️ Configuration

### **Site Settings**

Customize via **Admin → Site Settings**:
- Node name
- Tagline
- Logo (replaces 📡 emoji)
- Primary color (buttons, links)
- Accent color (hover states)
- Sidebar color

### **Environment Variables**

Located in `cdnnode/settings.py`:

```python
CDN_NODE_NAME = "Community CDN Node"           # Node display name
CDN_NODE_TAGLINE = "Free offline content"      # Subtitle
MEDIA_ROOT = "/mnt/usb/cdn-media"              # File storage location
CDN_PLATFORM_URL = "https://platform.url"      # Central platform API
CDN_API_KEY = "your-api-key"                   # Platform authentication
CDN_HEARTBEAT_INTERVAL = 60                    # Heartbeat interval (seconds)
```

Set via environment variables or `.env` file.

---

## 🔧 Development

### **Local Development (Windows/Mac)**

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Run development server
python manage.py runserver 8282
```

Visit `http://localhost:8282`

### **Project Structure**

```
cdn-raspberrypi-django/
├── cdnnode/              # Django project settings
│   ├── settings.py       # Main configuration
│   └── urls.py           # URL routing
├── portal/               # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View logic
│   ├── admin.py          # Admin customization
│   └── urls.py           # Portal URLs
├── templates/            # HTML templates
│   ├── base.html         # Base layout
│   └── portal/           # Portal templates
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript
├── media/                # Uploaded content (default)
├── scripts/              # Deployment scripts
│   └── deploy-pi.sh      # Auto-deploy to Pi
└── requirements.txt      # Python dependencies
```

---

## 🔐 Security

### **Change Default Password**

```bash
# SSH to Raspberry Pi
python manage.py changepassword admin
```

### **Production Settings**

For production, update `settings.py`:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-pi-ip', 'localhost']
SECRET_KEY = 'generate-new-secret-key'
```

---

## 📊 Monitoring

### **Check Service Status**

```bash
sudo systemctl status cdn-node
```

### **View Logs**

```bash
journalctl -u cdn-node -f
```

### **Storage Usage**

Visible in the portal sidebar!

---

## 🆘 Troubleshooting

### **Service Won't Start**
```bash
sudo journalctl -u cdn-node -n 50
```

### **Files Not Uploading**
Check MEDIA_ROOT permissions:
```bash
ls -la /mnt/usb/cdn-media
sudo chown -R www-data:www-data /mnt/usb/cdn-media
```

### **Video Won't Play**
- Use `.mp4` with H.264 codec
- Convert: `ffmpeg -i input.mkv -c:v libx264 output.mp4`

---

## 📦 Requirements

- **Raspberry Pi** 3B+ or newer (4GB RAM recommended)
- **External USB Drive** (500GB - 2TB recommended)
- **Python 3.9+**
- **Django 4.2+**

---

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

## 📄 License

[MIT License](LICENSE)

---

## 🎯 Use Cases

- **Community Centers** — Share educational videos, tutorials
- **Rural Areas** — Offline access to information
- **Schools** — Distribute learning materials
- **Events** — Share event videos and photos
- **Libraries** — Digital content distribution

---

**Built with ❤️ for Community Networks**
