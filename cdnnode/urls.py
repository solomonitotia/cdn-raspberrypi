from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve


def _serve_media(request, path):
    """Serve media files from the dynamically configured media root."""
    from portal.storage import _get_media_root
    return static_serve(request, path, document_root=_get_media_root())


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('portal.urls', namespace='portal')),
    re_path(r'^media/(?P<path>.+)$', _serve_media),
]
