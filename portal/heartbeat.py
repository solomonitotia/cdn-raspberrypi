"""
Heartbeat service — runs in a background thread, sends status to CN Platform.
Started from apps.py when Django is ready.
"""
import threading
import time
import logging
import requests
import platform
from django.conf import settings

logger = logging.getLogger(__name__)

_thread = None
_stop_event = threading.Event()


def _get_storage_info():
    try:
        import shutil
        from portal.storage import _get_media_root
        disk = shutil.disk_usage(_get_media_root())
        return {
            'total': disk.total,
            'used': disk.used,
            'available': disk.free,
        }
    except Exception:
        return {'total': 0, 'used': 0, 'available': 0}


def _get_system_info():
    info = {
        'platform': platform.system(),
        'python': platform.python_version(),
    }
    try:
        import psutil
        info['cpu_percent'] = psutil.cpu_percent(interval=1)
        info['memory_percent'] = psutil.virtual_memory().percent
    except ImportError:
        pass
    # Raspberry Pi CPU temperature
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            info['temperature'] = int(f.read().strip()) / 1000
    except Exception:
        pass
    return info


def _send_heartbeat():
    platform_url = settings.CDN_PLATFORM_URL
    api_key = settings.CDN_API_KEY
    if not platform_url or not api_key:
        return  # Not configured — silently skip

    # Lazy import to avoid Django startup issues
    from portal.models import ContentItem, Category
    from django.db import connection

    try:
        total_items = ContentItem.objects.filter(is_active=True).count()
        storage = _get_storage_info()
        system = _get_system_info()

        payload = {
            'identifier': settings.CDN_NODE_IDENTIFIER,
            'name': settings.CDN_NODE_NAME,
            'status': 'online',
            'storage': storage,
            'content': {'totalItems': total_items},
            'deviceInfo': system,
        }

        response = requests.post(
            f"{platform_url.rstrip('/')}/api/cdn/node/heartbeat",
            json=payload,
            headers={'X-CDN-API-Key': api_key},
            timeout=10,
        )
        logger.info('Heartbeat sent: %s', response.status_code)
    except requests.exceptions.ConnectionError:
        logger.error('Heartbeat: cannot reach platform at %s', platform_url)
    except Exception as e:
        logger.error('Heartbeat error: %s', e)


def _heartbeat_loop():
    interval = settings.CDN_HEARTBEAT_INTERVAL
    logger.info('Heartbeat service started (interval: %ss)', interval)
    while not _stop_event.is_set():
        _send_heartbeat()
        _stop_event.wait(interval)
    logger.info('Heartbeat service stopped')


def start():
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_heartbeat_loop, daemon=True, name='heartbeat')
    _thread.start()


def stop():
    _stop_event.set()
