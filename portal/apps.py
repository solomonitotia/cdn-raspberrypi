from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'

    def ready(self):
        import sys
        # Skip during management commands (migrate, collectstatic, shell, etc.)
        if any(cmd in sys.argv for cmd in ('migrate', 'collectstatic', 'shell', 'makemigrations', 'createsuperuser')):
            return
        from . import heartbeat
        heartbeat.start()
        _auto_configure_storage()


def _auto_configure_storage():
    """
    Detect mounted external drives on startup and auto-configure media storage.

    Only activates when SiteSettings.media_root is not already set.
    Scans /mnt and /media for filesystems that differ from root (i.e. external drives).
    Uses the first writable external drive found, creating a cdn-media subdirectory.

    On NTFS drives the mount must use uid=<cdnportal> — the installer configures
    /etc/fstab for this automatically.  If the drive is not writable we log a hint
    and fall back to the default MEDIA_ROOT.
    """
    import os
    import shutil
    import concurrent.futures
    import logging

    logger = logging.getLogger('portal.heartbeat')

    def _usage_safe(path, timeout=2):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(shutil.disk_usage, path).result(timeout=timeout)
        except Exception:
            return None

    try:
        from portal.models import SiteSettings
        site = SiteSettings.get()

        # Don't override an already-configured path
        if site.media_root and site.media_root.strip():
            return

        root_usage = _usage_safe('/')

        for base in ('/mnt', '/media'):
            if not os.path.isdir(base):
                continue
            try:
                for entry in os.scandir(base):
                    if not entry.is_dir():
                        continue
                    usage = _usage_safe(entry.path)
                    if not usage:
                        continue
                    # Skip if same filesystem as root (i.e. not an external drive)
                    if root_usage and usage.total == root_usage.total:
                        continue

                    # Found a candidate external drive — try to use it
                    media_path = os.path.join(entry.path, 'cdn-media')
                    try:
                        os.makedirs(media_path, exist_ok=True)
                        test_file = os.path.join(media_path, '.write_test')
                        with open(test_file, 'w') as f:
                            f.write('ok')
                        os.remove(test_file)
                    except OSError:
                        logger.error(
                            'External drive at %s is not writable by this process. '
                            'Fix mount permissions (fstab uid=<cdnportal uid>) or '
                            'run: sudo chown -R cdnportal:cdnportal %s',
                            entry.path, media_path,
                        )
                        continue

                    # Writable — save to DB and stop scanning
                    site.media_root = media_path
                    site.save(update_fields=['media_root'])
                    logger.error(
                        'Auto-configured media storage → %s  (%.1f GB free, %.1f GB total)',
                        media_path,
                        usage.free / 1024 ** 3,
                        usage.total / 1024 ** 3,
                    )
                    return

            except Exception as e:
                logger.error('Storage auto-detection error scanning %s: %s', base, e)

    except Exception:
        pass  # Never crash startup
