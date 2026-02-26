from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Category, ContentItem, SiteSettings, Announcement, ICON_CHOICES
import os
import shutil
import concurrent.futures


def _disk_usage_safe(path, timeout=2):
    """
    Return shutil.disk_usage(path) or None.
    Uses a thread with a hard timeout so a stuck NFS/USB mount can never
    block the web request indefinitely.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(shutil.disk_usage, path)
            return future.result(timeout=timeout)
    except Exception:
        return None


class ColorPickerWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            "type": "color",
            "style": "width:56px;height:38px;padding:2px 3px;cursor:pointer;border-radius:6px;border:1px solid #ccc;vertical-align:middle",
        })


class IconPickerWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        current = value or "📁"
        uid = (attrs or {}).get("id", f"id_{name}")
        buttons = []
        for emoji, label in ICON_CHOICES:
            sel = " ipk-selected" if emoji == current else ""
            buttons.append(
                f'<button type="button" title="{label}" class="ipk-btn{sel}" '
                f'onclick="ipkSelect(\'{uid}\',this)">{emoji}</button>'
            )
        return mark_safe(
            '<div class="ipk-wrap">'
            f'<input type="hidden" name="{name}" id="{uid}" value="{current}">'
            '<div class="ipk-grid">' + "".join(buttons) + "</div>"
            '<p class="help" style="margin-top:6px;color:#666">Click an icon to select it.</p>'
            "</div>"
            "<style>"
            ".ipk-grid{display:flex;flex-wrap:wrap;gap:5px;max-width:480px;margin-top:8px}"
            ".ipk-btn{font-size:22px;background:#f8fafc;border:2px solid #e2e8f0;border-radius:8px;"
            "width:44px;height:44px;cursor:pointer;transition:all .12s;"
            "display:flex;align-items:center;justify-content:center;padding:0}"
            ".ipk-btn:hover{background:#eff6ff;border-color:#93c5fd;transform:scale(1.1)}"
            ".ipk-btn.ipk-selected{background:#dbeafe;border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.25)}"
            "</style>"
            "<script>"
            'function ipkSelect(uid,btn){var val=btn.textContent.trim();document.getElementById(uid).value=val;btn.closest(".ipk-grid").querySelectorAll(".ipk-btn").forEach(function(b){b.classList.remove("ipk-selected")});btn.classList.add("ipk-selected")}'
            "</script>"
        )


class CategoryAdminForm(forms.ModelForm):
    icon = forms.CharField(widget=IconPickerWidget(), required=False, initial="📁", label="Icon")

    class Meta:
        model = Category
        fields = "__all__"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ["cover_preview", "name", "icon_display", "item_count_display", "size_display", "order"]
    list_display_links = ["name"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    ordering = ["order", "name"]

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="width:60px;height:40px;object-fit:cover;border-radius:6px">', obj.cover_image.url)
        return format_html('<div style="width:60px;height:40px;background:#e2e8f0;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:22px">{}</div>', obj.icon)
    cover_preview.short_description = "Cover"

    def icon_display(self, obj):
        return format_html('<span style="font-size:22px">{}</span>', obj.icon)
    icon_display.short_description = "Icon"

    def item_count_display(self, obj):
        return format_html("<strong>{}</strong> items", obj.items.filter(is_active=True).count())
    item_count_display.short_description = "Items"

    def size_display(self, obj):
        return obj.formatted_total_size()
    size_display.short_description = "Total Size"


class ContentItemInline(admin.TabularInline):
    model = ContentItem
    extra = 0
    fields = ["title", "file", "file_type", "is_active"]


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ["thumbnail_preview", "title", "category", "file_type_badge", "formatted_size", "year", "downloads", "is_active", "uploaded_at"]
    list_display_links = ["title"]
    list_filter = ["category", "file_type", "is_active", "uploaded_at"]
    search_fields = ["title", "description", "tags"]
    list_editable = ["is_active"]
    readonly_fields = ["file_size", "downloads", "uploaded_at", "updated_at"]
    fieldsets = [
        ("Content", {"fields": ["title", "description", "category", "file", "thumbnail"]}),
        ("Details", {"fields": ["file_type", "year", "duration", "tags"]}),
        ("Status",  {"fields": ["is_active", "file_size", "downloads", "uploaded_at", "updated_at"]}),
    ]
    actions = ["make_active", "make_inactive"]

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width:60px;height:40px;object-fit:cover;border-radius:6px">', obj.thumbnail.url)
        icons = {"video": "🎬", "audio": "🎵", "document": "📄", "image": "🖼️", "software": "💾", "other": "📁"}
        return format_html('<div style="width:60px;height:40px;background:#e2e8f0;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:20px">{}</div>', icons.get(obj.file_type, "📁"))
    thumbnail_preview.short_description = "Preview"

    def file_type_badge(self, obj):
        colors = {"video": "#3b82f6", "audio": "#8b5cf6", "document": "#f59e0b", "image": "#10b981", "software": "#6b7280", "other": "#94a3b8"}
        return format_html('<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600">{}</span>', colors.get(obj.file_type, "#94a3b8"), obj.get_file_type_display())
    file_type_badge.short_description = "Type"

    @admin.action(description="Mark selected as active")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected as inactive")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


class DrivePickerWidget(forms.TextInput):
    """Text input with a list of detected mounted drives shown as clickable buttons."""

    def _fmt(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _detect_drives(self):
        drives = []
        for base in ['/mnt', '/media']:
            if not os.path.exists(base):
                continue
            try:
                for entry in os.scandir(base):
                    if not entry.is_dir():
                        continue
                    try:
                        usage = _disk_usage_safe(entry.path)
                        if usage is None:
                            continue  # mount timed out or errored — skip it
                        # Only list if it's a separate mount from root
                        root_usage = _disk_usage_safe('/')
                        if root_usage and usage.total != root_usage.total:
                            drives.append({'path': entry.path, 'free': usage.free, 'total': usage.total})
                    except Exception:
                        pass
            except Exception:
                pass
        # Always include the default system path
        from django.conf import settings
        default = str(settings.MEDIA_ROOT)
        if not any(d['path'] == default for d in drives):
            usage = _disk_usage_safe(default)
            if usage:
                drives.insert(0, {'path': default, 'free': usage.free, 'total': usage.total, 'default': True})
        return drives

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs, renderer)
        drives = self._detect_drives()
        uid = (attrs or {}).get('id', f'id_{name}')
        picker_id = f'{uid}_picker'
        prefix_id = f'{uid}_prefix'
        sub_id    = f'{uid}_sub'
        preview_id = f'{uid}_preview'

        if not drives:
            drive_html = '<p style="color:#666;font-size:13px;margin:8px 0">No drives detected. Enter a path manually above.</p>'
        else:
            btns = []
            for d in drives:
                free_pct = (d['free'] / d['total'] * 100) if d['total'] else 0
                color = '#16a34a' if free_pct > 30 else '#d97706' if free_pct > 10 else '#dc2626'
                label = d['path']
                if d.get('default'):
                    label += ' (system default)'
                # On click: highlight button, show subfolder picker, set prefix
                btns.append(
                    f'<button type="button" '
                    f'onclick="'
                    f'this.closest(\'div\').querySelectorAll(\'button.dpk-btn\').forEach(b=>b.style.borderColor=\'#e2e8f0\');'
                    f'this.style.borderColor=\'#2563eb\';'
                    f'var pk=document.getElementById(\'{picker_id}\');'
                    f'var pr=document.getElementById(\'{prefix_id}\');'
                    f'var sb=document.getElementById(\'{sub_id}\');'
                    f'pr.textContent=\'{d["path"]}/\';'
                    f'pk.style.display=\'block\';'
                    f'sb.focus();'
                    f'var fv=document.getElementById(\'{uid}\');'
                    f'fv.value=\'{d["path"]}/\'+sb.value;" '
                    f'class="dpk-btn" '
                    f'style="display:block;width:100%;text-align:left;padding:8px 12px;margin:4px 0;'
                    f'border:2px solid #e2e8f0;border-radius:8px;background:#f8fafc;cursor:pointer;font-size:13px;">'
                    f'💾 <strong>{label}</strong> &nbsp;'
                    f'<span style="color:{color}">{self._fmt(d["free"])} free</span>'
                    f' / {self._fmt(d["total"])} total'
                    f'</button>'
                )
            drive_html = ''.join(btns)

        # Subfolder picker panel (hidden until a drive is clicked)
        folder_picker = (
            f'<div id="{picker_id}" style="display:none;margin-top:10px;padding:12px;'
            f'background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px">'
            f'<p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#166534">'
            f'📁 Choose a folder name on this drive:</p>'
            f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">'
            f'<code id="{prefix_id}" style="font-size:13px;color:#374151;background:#e5e7eb;'
            f'padding:4px 8px;border-radius:4px">/media/</code>'
            f'<input id="{sub_id}" type="text" value="cdn-media" placeholder="folder-name" '
            f'oninput="'
            f'var p=document.getElementById(\'{prefix_id}\').textContent;'
            f'var full=p+this.value;'
            f'document.getElementById(\'{uid}\').value=full;'
            f'document.getElementById(\'{preview_id}\').textContent=full;" '
            f'style="border:1px solid #6ee7b7;border-radius:6px;padding:4px 10px;'
            f'font-family:monospace;font-size:13px;width:160px;background:#fff" />'
            f'<button type="button" '
            f'onclick="document.getElementById(\'{picker_id}\').style.display=\'none\';" '
            f'style="padding:4px 14px;background:#16a34a;color:#fff;border:none;'
            f'border-radius:6px;cursor:pointer;font-size:13px">✓ Apply</button>'
            f'</div>'
            f'<p style="margin:6px 0 0;font-size:12px;color:#15803d">'
            f'Full path: <code id="{preview_id}" style="background:#dcfce7;padding:2px 6px;border-radius:4px"></code>'
            f'&nbsp;— This folder will be <strong>created automatically</strong> when you save.</p>'
            f'</div>'
        )

        return mark_safe(
            text_html +
            folder_picker +
            '<div style="margin-top:10px">'
            '<p style="font-weight:600;font-size:13px;margin:0 0 4px;color:#374151">🔍 Detected drives — click to select:</p>'
            + drive_html +
            '</div>'
        )


class SiteSettingsForm(forms.ModelForm):
    primary_color = forms.CharField(widget=ColorPickerWidget(), label="Primary Color", help_text="Main brand color — buttons, links, active states")
    accent_color  = forms.CharField(widget=ColorPickerWidget(), label="Accent / Hover Color", help_text="Darker variant on hover/pressed states")
    sidebar_color = forms.CharField(widget=ColorPickerWidget(), label="Sidebar Background", help_text="Background color of the left sidebar")
    media_root    = forms.CharField(widget=DrivePickerWidget(), required=False, label="Media Storage Path",
                                    help_text="Full path where uploads are stored (e.g. /mnt/usb1). "
                                              "Leave empty for system default. "
                                              "⚠️ Changing this does NOT move existing files.")

    class Meta:
        model = SiteSettings
        fields = "__all__"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm
    fieldsets = [
        ("Identity", {
            "description": "Customize this node's name, tagline, and logo shown on the public portal.",
            "fields": ["node_name", "tagline", "logo", "logo_preview"],
        }),
        ("Theme Colors", {
            "description": "✨ Enable auto-extract to automatically set colors from your logo, or pick colors manually using the swatches below.",
            "fields": ["auto_extract_colors", "primary_color", "accent_color", "sidebar_color"],
        }),
        ("Media Storage", {
            "description": "Configure where uploaded content files (videos, audio, documents) are stored. "
                           "Point this to an external USB drive to handle large libraries. "
                           "⚠️ Changing this path only affects NEW uploads — existing files are not moved.",
            "fields": ["media_root", "storage_usage"],
        }),
    ]
    readonly_fields = ["logo_preview", "storage_usage"]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.get()
        return HttpResponseRedirect(reverse("admin:portal_sitesettings_change", args=[obj.pk]))

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:80px;border-radius:8px;margin-top:4px">', obj.logo.url)
        return mark_safe('<span style="color:#999">No logo uploaded — the emoji icon (📡) is shown.</span>')
    logo_preview.short_description = "Current Logo Preview"

    def storage_usage(self, obj):
        from portal.storage import _get_media_root
        import os as _os
        path = _get_media_root()

        # Count existing files in the current path (to warn if changing)
        file_count = 0
        total_size = 0
        if _os.path.exists(path):
            try:
                for dirpath, _dirs, files in _os.walk(path):
                    for f in files:
                        if f.startswith('.'):
                            continue
                        try:
                            fsize = _os.path.getsize(_os.path.join(dirpath, f))
                            total_size += fsize
                            file_count += 1
                        except OSError:
                            pass
            except Exception:
                pass

        if not _os.path.exists(path):
            return format_html(
                '<span style="color:#d97706">⚠️ Path does not exist yet: <strong>{}</strong> — '
                'it will be created automatically when you save.</span>', path)
        usage = _disk_usage_safe(path)
        if usage is None:
            return format_html('<span style="color:#999">Path not accessible (or timed out): {}</span>', path)
        used_pct = (usage.used / usage.total * 100) if usage.total else 0
        bar_color = '#16a34a' if used_pct < 70 else '#d97706' if used_pct < 90 else '#dc2626'
        fmt = lambda s: f"{s/1024**3:.1f} GB" if s >= 1024**3 else f"{s/1024**2:.0f} MB"

        # Build existing-files warning if there are files here
        files_warning = ''
        if file_count > 0:
            files_warning = format_html(
                '<div style="margin-top:10px;padding:10px 12px;background:#fef9c3;'
                'border:1px solid #fde047;border-radius:8px">'
                '<p style="margin:0;font-size:13px;color:#854d0e">'
                '⚠️ <strong>{} file{}</strong> ({}) exist at this path. '
                'If you select a <em>different</em> folder above and save, '
                'those files will <strong>stay here</strong> and their download URLs '
                'will return 404. <br>'
                'To safely move: use <code>rsync -a {}/ &lt;new-path&gt;/</code> '
                'via SSH <em>before</em> changing this setting.</p>'
                '</div>',
                file_count,
                's' if file_count != 1 else '',
                fmt(total_size),
                path,
            )

        return format_html(
            '<div style="max-width:500px">'
            '<p style="margin:0 0 4px;font-size:13px">📂 Path: <strong>{}</strong></p>'
            '<div style="background:#e5e7eb;border-radius:6px;height:16px;overflow:hidden">'
            '<div style="background:{};height:100%;width:{:.1f}%"></div></div>'
            '<p style="margin:4px 0 0;font-size:12px;color:#6b7280">'
            '{} used &nbsp;·&nbsp; {} free &nbsp;·&nbsp; {} total</p>'
            '{}'
            '</div>',
            path, bar_color, used_pct,
            fmt(usage.used), fmt(usage.free), fmt(usage.total),
            files_warning,
        )
    storage_usage.short_description = "Current Storage Usage"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['type_badge', 'media_preview', 'title', 'is_active', 'created_at', 'expires_at']
    list_display_links = ['title']
    list_filter = ['announcement_type', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'media_preview_large']
    fieldsets = [
        ('Announcement', {
            'fields': ['title', 'content', 'announcement_type', 'icon'],
        }),
        ('Media (Optional)', {
            'fields': ['media_image', 'video_url', 'media_preview_large'],
            'description': 'Upload an image/poster OR add a video URL. Media will be displayed prominently in the announcement.',
        }),
        ('Link (Optional)', {
            'fields': ['link', 'link_text'],
            'description': 'Add a call-to-action link (e.g., "Read More", "Download Now")',
        }),
        ('Visibility', {
            'fields': ['is_active', 'expires_at', 'created_at'],
        }),
    ]

    def media_preview(self, obj):
        if obj.media_image:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px">', obj.media_image.url)
        if obj.video_url:
            return format_html('<span style="font-size:20px">🎬</span>')
        return '—'
    media_preview.short_description = 'Media'

    def media_preview_large(self, obj):
        if obj.media_image:
            return format_html('<img src="{}" style="max-width:400px;max-height:300px;border-radius:8px;margin-top:8px">', obj.media_image.url)
        if obj.video_url:
            return format_html('<p>Video URL: <a href="{}" target="_blank">{}</a></p>', obj.video_url, obj.video_url)
        return mark_safe('<span style="color:#999">No media attached</span>')
    media_preview_large.short_description = 'Media Preview'

    def type_badge(self, obj):
        colors = {
            'info': '#3b82f6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'promo': '#8b5cf6',
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:600;text-transform:uppercase">{}</span>',
            colors.get(obj.announcement_type, '#94a3b8'),
            obj.get_announcement_type_display()
        )
    type_badge.short_description = 'Type'

    @admin.action(description='Mark selected as active')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Mark selected as inactive')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    actions = ['make_active', 'make_inactive']


# ── Admin site branding ────────────────────────────────────────────────────────
admin.site.site_header = "CDN Node Administration"
admin.site.site_title  = "CDN Node Admin"
admin.site.index_title = "Content Management"
