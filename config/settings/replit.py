from .base import *
import os
from decouple import config

# Replit-specific settings
DEBUG = False

# Get Replit domain
REPLIT_DOMAIN = os.getenv('REPLIT_OWNER', 'replit') + '.repl.co'
ALLOWED_HOSTS = [
    REPLIT_DOMAIN,
    'appbackend-2--afzalrehan779.replit.app',
    'localhost',
    '127.0.0.1',
]

# Database - Use SQLite on Replit (simpler, no external DB needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Security Settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}

# CORS Settings - Update for Replit and frontend
CORS_ALLOWED_ORIGINS = [
    f"https://{REPLIT_DOMAIN}",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:51463",
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For testing on Replit

# Disable Celery on Replit (no Redis available on free tier)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# JWT Settings (keep from base)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'PAGE_SIZE': 20,
}
