"""
Rentora Django Settings
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-me')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver,.onrender.com').split(',') if h.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')
if DEBUG:
    ALLOWED_HOSTS.extend(['*', '192.168.29.117'])
render_external_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)

# Sentry SDK Integration (Production Monitoring)
if os.getenv('SENTRY_DSN') and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

# Production Security Hardening
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# CSRF Trusted Origins for Production
CSRF_TRUSTED_ORIGINS = [
    f"https://{h.strip()}" for h in ALLOWED_HOSTS if h.strip() and not h.startswith('.') and h not in ('localhost', '127.0.0.1', 'testserver')
]
CSRF_TRUSTED_ORIGINS.extend(['https://*.onrender.com', 'https://*.supabase.co'])
if os.getenv('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS').split(',') if o.strip()])
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))  # Remove duplicates

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party
    'storages',
    'crispy_forms',
    'crispy_tailwind',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Local apps
    'core',
    'accounts',
    'admin_panel',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.ProfilePrefetchMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rentora_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.shared_layout_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'rentora_project.wsgi.application'

# Database Configuration — Production-Grade PostgreSQL
import dj_database_url

db_url = os.getenv('DATABASE_URL')
db_host = os.getenv('DB_HOST', '127.0.0.1')
is_local_host = db_host in ('localhost', '127.0.0.1')

if db_url:
    # Neon Best Practice: Direct unpooled connection for DDL migrations, pooled for web traffic
    is_migration = any(cmd in sys.argv for cmd in ('migrate', 'makemigrations', 'inspectdb'))
    unpooled_url = os.getenv('DATABASE_URL_UNPOOLED')
    active_db_url = unpooled_url if (is_migration and unpooled_url) else db_url
    
    db_config = dj_database_url.config(
        default=active_db_url,
        conn_max_age=0 if '-pooler' in active_db_url else 600,
        ssl_require=not any(h in active_db_url for h in ('localhost', '127.0.0.1'))
    )
    # DNS fallback for Windows local environments when ISP DNS blocks *.neon.tech
    if 'neon.tech' in db_config.get('HOST', ''):
        try:
            import socket
            socket.gethostbyname(db_config['HOST'])
        except Exception:
            db_config.setdefault('OPTIONS', {})['hostaddr'] = '52.220.170.93'

    DATABASES = {
        'default': db_config
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'rentora_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': db_host,
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'sslmode': 'disable' if is_local_host else os.getenv('DB_SSLMODE', 'require'),
            },
        }
    }

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.test.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Production Static & Media Storage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
WHITENOISE_MANIFEST_STRICT = False

# Media Storage Configuration (Cloudinary / Supabase S3 / Local fallback)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'ap-south-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_VERIFY = True

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
    import cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    if 'cloudinary_storage' not in INSTALLED_APPS:
        INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    }
    MEDIA_URL = '/media/'
elif not DEBUG and AWS_ACCESS_KEY_ID:
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.storage.supabase.co/storage/v1/s3/'
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
    }
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Auth
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Stripe Configuration
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_CURRENCY = os.getenv('STRIPE_CURRENCY', 'inr')

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# Domain Configuration
DOMAIN_URL = os.getenv('DOMAIN_URL', 'http://127.0.0.1:8000')

# Email Configuration — Resend (Professional Transactional Email)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

if RESEND_API_KEY:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.resend.com'
    EMAIL_PORT = 465
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
    EMAIL_HOST_USER = 'resend'
    EMAIL_HOST_PASSWORD = RESEND_API_KEY
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Rentora <noreply@rentora.com>')

# Allauth / Social Auth
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.MySocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('SOCIAL_AUTH_GOOGLE_CLIENT_ID'),
            'secret': os.getenv('SOCIAL_AUTH_GOOGLE_SECRET'),
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# VAPID Keys for Push Notifications
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
VAPID_ADMIN_EMAIL = os.getenv('VAPID_ADMIN_EMAIL', 'admin@rentora.com')

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Admin Notification Settings
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', DEFAULT_FROM_EMAIL)
ADMIN_PHONE = os.getenv('ADMIN_PHONE')

# Twilio Settings
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

# ===================== LOGGING =====================
# This ensures Django tracebacks appear in Render/Gunicorn logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
