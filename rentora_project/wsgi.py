"""
WSGI config for rentora_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import threading
import time
import urllib.request
import logging

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

application = get_wsgi_application()

logger = logging.getLogger(__name__)

def _start_keep_alive_ping():
    """
    Self-ping keep-alive background worker for Render free tier.
    Render free instances spin down after 15 minutes of inactivity.
    This background daemon pings /health/ every 9 minutes to keep the instance warm.
    """
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    keep_alive_enabled = os.environ.get('RENDER_KEEP_ALIVE', 'true').lower() in ('true', '1', 'yes')

    if not render_host or not keep_alive_enabled:
        return

    def ping_loop():
        # Allow the web server 30 seconds to start listening on its assigned port
        time.sleep(30)
        target_url = f"https://{render_host}/health/"
        logger.info(f"[Render Keep-Alive] Started daemon pinging {target_url} every 9 minutes.")
        while True:
            try:
                req = urllib.request.Request(
                    target_url,
                    headers={'User-Agent': 'RentoraKeepAlive/1.0'}
                )
                with urllib.request.urlopen(req, timeout=15) as res:
                    logger.debug(f"[Render Keep-Alive] Ping {target_url} -> {res.status}")
            except Exception as e:
                logger.debug(f"[Render Keep-Alive] Ping notice: {e}")
            time.sleep(540)  # 9 minutes (well before the 15-minute idle cutoff)

    t = threading.Thread(target=ping_loop, daemon=True, name="RenderKeepAliveWorker")
    t.start()

_start_keep_alive_ping()
