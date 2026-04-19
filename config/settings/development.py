from .base import *
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,10.0.2.2').split(',')

# Database for development
# Use SQLite by default if no PostgreSQL is available
use_sqlite = os.getenv('USE_SQLITE', 'True') == 'True'

if use_sqlite:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':  os.getenv('DB_NAME', 'neat_now_db'),
            'USER': os. getenv('DB_USER', 'postgres'),
            'PASSWORD':  os.getenv('DB_PASSWORD', 'admin'),
            'HOST': os. getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# Email backend for development
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Media files (uploads) - BASE_DIR is already defined in base.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
WEBSITE_URL = 'http://localhost:51463'
FRONTEND_URL = 'http://localhost:51463'

# For production, use: 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'afzalrehan779@gmail.com'
EMAIL_HOST_PASSWORD = 'iiqyvwwutxxjuhjg'  # Use Gmail App Password
DEFAULT_FROM_EMAIL = 'Admin System <afzalrehan779@gmail.com>'


# ==================== CORS CONFIGURATION (FIXED) ====================

# ✅ Allow Flutter Web (running on different port)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:56901',  # ✅ Add Flutter web port
    'http://127.0.0.1:56901',
    'http://10.0.2.2:8000',
]

# ✅ For development - allow all origins
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# ✅ Add preflight caching
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',  # ✅ Add custom headers
]

# ✅ Expose custom headers
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-session-id',
]

# ==================== CSRF SETTINGS (FIXED) ====================

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:56901',  # ✅ Add Flutter web port
    'http://127.0.0.1:56901',
    'http://10.0.2.2:8000',
]
from datetime import timedelta
APPEND_SLASH = True  # Default behavior
# Your existing SIMPLE_JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'account_id',  # ← Add this line
    'USER_ID_CLAIM': 'user_id',     # ← Add this line
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# ✅ Disable CSRF for API endpoints in development
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False