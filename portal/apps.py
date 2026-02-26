from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'

    def ready(self):
        import os
        # Skip during management commands (migrate, collectstatic, shell, etc.)
        # RUN_MAIN=true is set by Django's dev reloader in the child process — allow it.
        # Skip only when there's no settings module (direct import without Django context).
        import sys
        if any(cmd in sys.argv for cmd in ('migrate', 'collectstatic', 'shell', 'makemigrations', 'createsuperuser')):
            return
        from . import heartbeat
        heartbeat.start()
