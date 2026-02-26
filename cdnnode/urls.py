from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve


def _serve_media(request, path):
    """
    Serve media files from the dynamically configured media root.
    Falls back to settings.MEDIA_ROOT so files uploaded before a storage
    path change (e.g. before an external drive was configured) are still served.
    """
    import os
    from portal.storage import _get_media_root
    primary = _get_media_root()
    if os.path.exists(os.path.join(primary, path)):
        return static_serve(request, path, document_root=primary)
    fallback = str(settings.MEDIA_ROOT)
    if fallback != primary and os.path.exists(os.path.join(fallback, path)):
        return static_serve(request, path, document_root=fallback)
    # Default — will return 404 with the correct media path in the error
    return static_serve(request, path, document_root=primary)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('portal.urls', namespace='portal')),
    re_path(r'^media/(?P<path>.+)$', _serve_media),
]
