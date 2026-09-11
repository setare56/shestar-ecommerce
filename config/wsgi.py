"""WSGI entry point - used by traditional servers (e.g. gunicorn) to run the app."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
