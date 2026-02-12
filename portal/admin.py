from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Category, ContentItem, SiteSettings, Announcement, ICON_CHOICES


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


class SiteSettingsForm(forms.ModelForm):
    primary_color = forms.CharField(widget=ColorPickerWidget(), label="Primary Color", help_text="Main brand color — buttons, links, active states")
    accent_color  = forms.CharField(widget=ColorPickerWidget(), label="Accent / Hover Color", help_text="Darker variant on hover/pressed states")
    sidebar_color = forms.CharField(widget=ColorPickerWidget(), label="Sidebar Background", help_text="Background color of the left sidebar")

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
    ]
    readonly_fields = ["logo_preview"]

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
