import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings


def _get_media_root():
    """Read the configured media root from SiteSettings, falling back to settings.MEDIA_ROOT."""
    try:
        from portal.models import SiteSettings
        row = SiteSettings.objects.filter(pk=1).values_list('media_root', flat=True).first()
        if row and row.strip():
            return row.strip()
    except Exception:
        pass
    return str(settings.MEDIA_ROOT)


class DynamicMediaStorage(FileSystemStorage):
    """
    Storage backend that resolves the upload path from SiteSettings at runtime.
    Allows admins to redirect uploads to an external USB drive via the admin panel
    without restarting the service.
    """

    def __init__(self):
        # Initialised with the settings default; actual path resolved per-operation
        super().__init__(location=str(settings.MEDIA_ROOT), base_url=settings.MEDIA_URL)

    def deconstruct(self):
        # Tell Django migrations: just call DynamicMediaStorage() — no args needed
        return ('portal.storage.DynamicMediaStorage', [], {})

    def _storage(self):
        return FileSystemStorage(location=_get_media_root(), base_url=settings.MEDIA_URL)

    def _open(self, name, mode='rb'):
        return self._storage()._open(name, mode)

    def _save(self, name, content):
        return self._storage()._save(name, content)

    def path(self, name):
        return self._storage().path(name)

    def exists(self, name):
        return self._storage().exists(name)

    def url(self, name):
        return self._storage().url(name)

    def size(self, name):
        return self._storage().size(name)

    def listdir(self, path):
        return self._storage().listdir(path)

    def delete(self, name):
        return self._storage().delete(name)
