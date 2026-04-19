import os
from django.core.wsgi import get_wsgi_application

# Use replit settings if DJANGO_SETTINGS_MODULE not set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.replit')

application = get_wsgi_application()
