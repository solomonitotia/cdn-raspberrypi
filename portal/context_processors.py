from .models import SiteSettings, Category


def site_settings(request):
    """Inject SiteSettings and all_categories into every template context."""
    return {
        'site_settings': SiteSettings.get(),
        'all_categories': Category.objects.all(),
    }
