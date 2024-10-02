"""
WSGI config for niyam_saha_ai project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niyam_saha_ai.settings')

# Wrap the WSGI application with the static files handler
if settings.DEBUG:
    application = StaticFilesHandler(get_wsgi_application())
else:
    application = get_wsgi_application()

