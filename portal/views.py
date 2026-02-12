from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.utils import timezone
from .models import Category, ContentItem, Announcement
import os


def _node_context():
    """Common context injected into all portal pages."""
    return {
        'node_name': settings.CDN_NODE_NAME,
        'node_tagline': settings.CDN_NODE_TAGLINE,
    }


def home(request):
    """Main portal page — shows all categories."""
    categories = Category.objects.prefetch_related('items').all()

    # Get active, non-expired announcements
    now = timezone.now()
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )[:3]  # Limit to 3 most recent

    context = {
        **_node_context(),
        'categories': categories,
        'announcements': announcements,
    }
    return render(request, 'portal/home.html', context)


def category_detail(request, slug):
    """Browse all content in a category."""
    category = get_object_or_404(Category, slug=slug)
    items = category.items.filter(is_active=True)

    # Filter by type
    file_type = request.GET.get('type')
    if file_type:
        items = items.filter(file_type=file_type)

    # Search within category
    q = request.GET.get('q', '').strip()
    if q:
        items = items.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))

    context = {
        **_node_context(),
        'category': category,
        'items': items,
        'all_categories': Category.objects.all(),
        'search_query': q,
        'active_type': file_type,
    }
    return render(request, 'portal/category.html', context)


def item_detail(request, pk):
    """View/play a single content item."""
    item = get_object_or_404(ContentItem, pk=pk, is_active=True)
    # Increment download/view counter
    ContentItem.objects.filter(pk=pk).update(downloads=item.downloads + 1)

    related = ContentItem.objects.filter(
        category=item.category, is_active=True
    ).exclude(pk=pk)[:8]

    context = {
        **_node_context(),
        'item': item,
        'related': related,
        'all_categories': Category.objects.all(),
    }
    return render(request, 'portal/item_detail.html', context)


def search(request):
    """Search across all content."""
    q = request.GET.get('q', '').strip()
    items = ContentItem.objects.none()
    if q:
        items = ContentItem.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q),
            is_active=True
        ).select_related('category')

    context = {
        **_node_context(),
        'items': items,
        'search_query': q,
        'all_categories': Category.objects.all(),
    }
    return render(request, 'portal/search.html', context)


def recent(request):
    """Recently added content."""
    items = ContentItem.objects.filter(is_active=True).select_related('category')[:50]
    context = {
        **_node_context(),
        'items': items,
        'all_categories': Category.objects.all(),
        'page_title': 'Recently Added',
    }
    return render(request, 'portal/listing.html', context)


# ── API endpoints (JSON) ───────────────────────────────────────────────────────

@require_GET
def api_stats(request):
    categories = Category.objects.prefetch_related('items').all()
    total_size = sum(c.total_size for c in categories)
    max_size = settings.MEDIA_ROOT
    try:
        import shutil
        disk = shutil.disk_usage(str(settings.MEDIA_ROOT))
        disk_total = disk.total
        disk_used = disk.used
    except Exception:
        disk_total = 0
        disk_used = total_size

    return JsonResponse({
        'node_name': settings.CDN_NODE_NAME,
        'categories': [
            {
                'name': c.name,
                'slug': c.slug,
                'icon': c.icon,
                'count': c.item_count,
                'total_size': c.total_size,
                'cover': c.cover_image.url if c.cover_image else None,
            }
            for c in categories
        ],
        'total_files': ContentItem.objects.filter(is_active=True).count(),
        'total_size': total_size,
        'disk_used': disk_used,
        'disk_total': disk_total,
    })


@require_GET
def api_files(request):
    items = ContentItem.objects.filter(is_active=True).select_related('category')
    category_slug = request.GET.get('category')
    q = request.GET.get('q', '').strip()
    if category_slug:
        items = items.filter(category__slug=category_slug)
    if q:
        items = items.filter(Q(title__icontains=q) | Q(tags__icontains=q))
    return JsonResponse({'items': [
        {
            'id': item.pk,
            'title': item.title,
            'category': item.category.name,
            'file_type': item.file_type,
            'file_url': item.file.url,
            'thumbnail': item.thumbnail.url if item.thumbnail else None,
            'size': item.file_size,
            'year': item.year,
        }
        for item in items[:200]
    ]})
