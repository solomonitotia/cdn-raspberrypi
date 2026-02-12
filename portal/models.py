from django.db import models
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from PIL import Image
import io
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC


# ── Color extraction utility ──────────────────────────────────────────────────
def extract_colors_from_image(image_file):
    """
    Extract dominant colors from an uploaded image.
    Returns a dict with 'primary', 'accent', and 'sidebar' hex colors.
    """
    try:
        # Open image
        img = Image.open(image_file)

        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize for faster processing
        img.thumbnail((150, 150))

        # Get color palette (quantize to 5 colors)
        img = img.quantize(colors=5)
        palette = img.getpalette()

        # Extract RGB triplets
        colors = []
        for i in range(5):
            r, g, b = palette[i*3:(i+1)*3]
            # Skip very dark (almost black) or very light (almost white) colors
            brightness = (r + g + b) / 3
            if 30 < brightness < 230:
                colors.append((r, g, b))

        if not colors:
            # Fallback: use any color if all are filtered out
            r, g, b = palette[0:3]
            colors = [(r, g, b)]

        # Sort by saturation (more vibrant colors first)
        def saturation(rgb):
            r, g, b = rgb
            return max(r, g, b) - min(r, g, b)

        colors.sort(key=saturation, reverse=True)

        # Primary: most vibrant color
        primary_rgb = colors[0]

        # Accent: darker version of primary (80% brightness)
        accent_rgb = tuple(int(c * 0.7) for c in primary_rgb)

        # Sidebar: very dark, slightly tinted with primary
        sidebar_rgb = (
            int(primary_rgb[0] * 0.08 + 12),
            int(primary_rgb[1] * 0.08 + 17),
            int(primary_rgb[2] * 0.08 + 29)
        )

        # Convert to hex
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        return {
            'primary_color': rgb_to_hex(primary_rgb),
            'accent_color': rgb_to_hex(accent_rgb),
            'sidebar_color': rgb_to_hex(sidebar_rgb),
        }

    except Exception as e:
        # If extraction fails, return default colors
        return {
            'primary_color': '#2563eb',
            'accent_color': '#1d4ed8',
            'sidebar_color': '#0c111d',
        }


# ── Thumbnail generation utilities ────────────────────────────────────────────
def extract_audio_thumbnail(audio_file):
    """
    Extract album art from audio files (MP3, M4A, FLAC, etc.).
    Returns a ContentFile with the image data, or None if no album art found.
    """
    try:
        # Read the audio file using mutagen
        audio = MutagenFile(audio_file.path)

        if audio is None:
            return None

        # Extract album art based on file type
        image_data = None

        # MP3 files (ID3 tags)
        if isinstance(audio, MP3):
            for tag in audio.tags.values():
                if hasattr(tag, 'mime') and tag.mime.startswith('image/'):
                    image_data = tag.data
                    break

        # M4A/MP4 files
        elif isinstance(audio, MP4):
            if 'covr' in audio.tags:
                image_data = audio.tags['covr'][0]

        # FLAC files
        elif isinstance(audio, FLAC):
            if audio.pictures:
                image_data = audio.pictures[0].data

        # Other formats with generic picture support
        elif hasattr(audio, 'pictures') and audio.pictures:
            image_data = audio.pictures[0].data

        if image_data:
            # Create thumbnail from the extracted image
            img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Create square thumbnail (300x300)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)

            # Save to BytesIO
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)

            return ContentFile(output.read(), name='thumb.jpg')

        return None

    except Exception as e:
        return None


def extract_image_thumbnail(image_file):
    """
    Create a thumbnail from an image file.
    Returns a ContentFile with the thumbnail data.
    """
    try:
        img = Image.open(image_file)

        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Create square thumbnail (300x300)
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)

        # Save to BytesIO
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

        return ContentFile(output.read(), name='thumb.jpg')

    except Exception as e:
        return None


# ── Icon choices ───────────────────────────────────────────────────────────────
ICON_CHOICES = [
    ('📁', '📁 Folder'),
    ('📂', '📂 Open Folder'),
    ('🎬', '🎬 Movies / Video'),
    ('📺', '📺 TV Series'),
    ('🎵', '🎵 Music'),
    ('🎶', '🎶 Audio'),
    ('🎤', '🎤 Podcast'),
    ('📄', '📄 Documents'),
    ('📚', '📚 Books / Library'),
    ('📰', '📰 News'),
    ('🖼️', '🖼️ Images / Photos'),
    ('📷', '📷 Photography'),
    ('💾', '💾 Software'),
    ('🎮', '🎮 Games'),
    ('💻', '💻 Computer / Tech'),
    ('📱', '📱 Mobile Apps'),
    ('🌐', '🌐 Web / Internet'),
    ('📡', '📡 Network / CDN'),
    ('🔧', '🔧 Tools'),
    ('⚙️', '⚙️ Technical'),
    ('🎓', '🎓 Education'),
    ('🔬', '🔬 Science'),
    ('🏥', '🏥 Health'),
    ('🌍', '🌍 Geography'),
    ('✈️', '✈️ Travel'),
    ('🏠', '🏠 Home'),
    ('🍎', '🍎 Food'),
    ('🎨', '🎨 Art / Design'),
    ('🎭', '🎭 Drama / Theater'),
    ('🎯', '🎯 Sports'),
]


class SiteSettings(models.Model):
    """Singleton — one row stores portal branding & theme for this CDN node."""
    node_name      = models.CharField(max_length=100, default='Community CDN Node')
    tagline        = models.CharField(max_length=200, default='by Community Networks')
    logo           = models.ImageField(upload_to='branding/', blank=True, null=True,
                                       help_text='Replaces the emoji icon in the sidebar')
    auto_extract_colors = models.BooleanField(default=True,
                                              help_text='Automatically extract theme colors from the uploaded logo')
    primary_color  = models.CharField(max_length=7, default='#2563eb',
                                      help_text='Main brand color (buttons, links, active states)')
    accent_color   = models.CharField(max_length=7, default='#1d4ed8',
                                      help_text='Darker accent / hover color')
    sidebar_color  = models.CharField(max_length=7, default='#0c111d',
                                      help_text='Sidebar background color')

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1

        # Auto-extract colors from logo if enabled and logo is new/changed
        if self.auto_extract_colors and self.logo:
            try:
                # Check if logo has changed
                if self.pk:
                    try:
                        old_instance = SiteSettings.objects.get(pk=self.pk)
                        logo_changed = old_instance.logo != self.logo
                    except SiteSettings.DoesNotExist:
                        logo_changed = True
                else:
                    logo_changed = True

                # Extract colors if logo changed
                if logo_changed:
                    colors = extract_colors_from_image(self.logo)
                    self.primary_color = colors['primary_color']
                    self.accent_color = colors['accent_color']
                    self.sidebar_color = colors['sidebar_color']
            except Exception:
                pass  # Silently fail, keep existing colors

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Singleton cannot be deleted

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.node_name


class Category(models.Model):
    """A content category — admin creates these (Movies, TV Series, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    icon = models.CharField(max_length=10, default='📁', choices=ICON_CHOICES)
    order = models.PositiveIntegerField(default=0, help_text='Display order')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def item_count(self):
        return self.items.filter(is_active=True).count()

    @property
    def total_size(self):
        return sum(
            item.file_size for item in self.items.filter(is_active=True) if item.file_size
        )

    def formatted_total_size(self):
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def content_upload_path(instance, filename):
    """Store files under media/<category-slug>/<filename>"""
    return f"{instance.category.slug}/{filename}"


class ContentItem(models.Model):
    """A single piece of content (video, document, song, etc.)"""
    FILE_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('image', 'Image'),
        ('software', 'Software'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    file = models.FileField(upload_to=content_upload_path)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField(default=0, editable=False)
    duration = models.CharField(max_length=20, blank=True, help_text='e.g. 1h 23m')
    year = models.PositiveIntegerField(blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    is_active = models.BooleanField(default=True)
    downloads = models.PositiveIntegerField(default=0, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = not self.pk

        # Auto-detect file type from extension
        if self.file and is_new:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = self._detect_type(ext)

        super().save(*args, **kwargs)

        # Store file size after save (file is committed at this point)
        if self.file:
            try:
                self.file_size = self.file.size
                ContentItem.objects.filter(pk=self.pk).update(file_size=self.file_size)
            except Exception:
                pass

        # Auto-generate thumbnail if not provided
        if is_new and self.file and not self.thumbnail:
            thumbnail_file = None

            try:
                # Extract thumbnail based on file type
                if self.file_type == 'audio':
                    thumbnail_file = extract_audio_thumbnail(self.file)
                elif self.file_type == 'image':
                    thumbnail_file = extract_image_thumbnail(self.file)
                # Add video thumbnail extraction here in the future

                # Save thumbnail if generated
                if thumbnail_file:
                    self.thumbnail.save(
                        f'{self.pk}_thumb.jpg',
                        thumbnail_file,
                        save=False
                    )
                    ContentItem.objects.filter(pk=self.pk).update(thumbnail=self.thumbnail)

            except Exception as e:
                # Silently fail - thumbnail generation is optional
                pass

    @staticmethod
    def _detect_type(ext):
        if ext in {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.wmv', '.flv'}:
            return 'video'
        if ext in {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}:
            return 'audio'
        if ext in {'.pdf', '.doc', '.docx', '.epub', '.txt', '.odt', '.ppt', '.pptx', '.xls', '.xlsx'}:
            return 'document'
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}:
            return 'image'
        if ext in {'.exe', '.deb', '.apk', '.dmg', '.zip', '.tar', '.gz', '.rar'}:
            return 'software'
        return 'other'

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower() if self.file else ''

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def formatted_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class Announcement(models.Model):
    """Admin-created announcements, news, or ads shown on the portal homepage."""
    ANNOUNCEMENT_TYPES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('promo', 'Promo / Ad'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField(help_text='Announcement message or description')
    announcement_type = models.CharField(max_length=10, choices=ANNOUNCEMENT_TYPES, default='info')
    icon = models.CharField(max_length=10, default='📢', help_text='Emoji icon')

    # Media attachments
    media_image = models.ImageField(upload_to='announcements/', blank=True, null=True,
                                     help_text='Upload an image/poster for this announcement')
    video_url = models.URLField(blank=True, help_text='Optional video URL (YouTube, Vimeo, or direct MP4 link)')

    link = models.URLField(blank=True, help_text='Optional link (e.g., to a file, external page)')
    link_text = models.CharField(max_length=50, blank=True, default='Learn More')
    is_active = models.BooleanField(default=True, help_text='Show this announcement on the homepage')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text='Optional expiration date/time')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def has_media(self):
        return bool(self.media_image or self.video_url)

    @property
    def media_type(self):
        if self.video_url:
            return 'video'
        if self.media_image:
            return 'image'
        return None
