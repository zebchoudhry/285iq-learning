import os
import logging
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

_IS_VERCEL = bool(os.environ.get('VERCEL'))


def _env(name, default=''):
    """Prefer real environment variables (Vercel) over .env files."""
    return os.environ.get(name) or config(name, default=default)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False if _IS_VERCEL else True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,.vercel.app,285iq.com,www.285iq.com',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)

# Vercel sets VERCEL_URL to the deployment hostname (e.g. my-app-xxx.vercel.app)
_vercel_url = os.environ.get('VERCEL_URL', '').strip()
if _vercel_url and _vercel_url not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_vercel_url)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)
if _vercel_url:
    _origin = f'https://{_vercel_url}'
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'users',
    'learning',
    'gamification', 
    'content',
    'dashboard',
    'decision_engine',
    'teachers',
]

# WhiteNoise is for local/Docker only; Vercel serves static files from the CDN.
_use_whitenoise = (not _IS_VERCEL) and config('USE_WHITENOISE', default=False, cast=bool)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]
if _use_whitenoise:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'studymate285.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studymate285.wsgi.application'

# Database: DATABASE_URL (Vercel/Neon) > DB_ENGINE PostgreSQL > SQLite.
# USE_SQLITE=True forces SQLite locally even when .env sets PostgreSQL.
# Prefer non-pooling URL for serverless (Vercel Postgres provides both).
_database_url = (
    _env('POSTGRES_URL_NON_POOLING')
    or _env('DATABASE_URL')
    or _env('POSTGRES_URL')
    or _env('POSTGRES_PRISMA_URL')
)
_db_engine = config('DB_ENGINE', default='')
_use_sqlite = config('USE_SQLITE', default=False, cast=bool)

if _database_url:
    import dj_database_url

    _db_ssl = _IS_VERCEL or not DEBUG
    if 'sslmode=disable' in _database_url.lower():
        _db_ssl = False

    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=0 if _IS_VERCEL else 600,
            ssl_require=_db_ssl,
        )
    }
elif _IS_VERCEL:
    # Ephemeral fallback so the process can start; use DATABASE_URL in production.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/285iq.sqlite3',
        }
    }
elif _use_sqlite:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif _db_engine == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='285iq_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'users.Student'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / "static",
] if (BASE_DIR / "static").exists() else []

if _use_whitenoise:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

if _IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    MIDDLEWARE.insert(
        len(MIDDLEWARE) - 1,
        'learning.middleware.VercelDiagnosticMiddleware',
    )

    if _env('VERCEL_DIAGNOSTIC', '0') in ('1', 'true', 'True'):
        DEBUG = True
        ALLOWED_HOSTS = ['*']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '300/hour',
        'practice': '120/hour',
        'tutor': '60/hour',
        'parent': '30/hour',
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
if _vercel_url:
    _vercel_origin = f"https://{_vercel_url}"
    if _vercel_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(_vercel_origin)

# Email (for password reset). In development, use console backend.
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@285iq.com')

# LLM configuration (Phase 4)
# LLM_BACKEND: disabled | mock | openai_compatible | huggingface
LLM_BACKEND = config('LLM_BACKEND', default='disabled')
LLM_MODEL = config('LLM_MODEL', default='gpt-4o-mini')
LLM_BASE_URL = config('LLM_BASE_URL', default='')
LLM_API_KEY = config('LLM_API_KEY', default='')
LLM_USE_FOR_QUIZ = config('LLM_USE_FOR_QUIZ', default=False, cast=bool)
LLM_USE_TUTOR = config('LLM_USE_TUTOR', default=True, cast=bool)

# Hugging Face (LLM_BACKEND=huggingface, or HF Inference Endpoint via openai_compatible)
HF_TOKEN = config('HF_TOKEN', default='')
HF_MODEL = config('HF_MODEL', default='')
HF_PROVIDER = config('HF_PROVIDER', default='')  # e.g. together, fireworks-ai; empty = auto route

# Semantic dedupe for questions (requires sentence-transformers)
HF_EMBEDDINGS_ENABLED = config('HF_EMBEDDINGS_ENABLED', default=False, cast=bool)
HF_EMBEDDING_MODEL = config(
    'HF_EMBEDDING_MODEL',
    default='sentence-transformers/all-MiniLM-L6-v2',
)

# Stripe subscription billing
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_MONTHLY_PRICE_ID = config('STRIPE_MONTHLY_PRICE_ID', default='')
STRIPE_ANNUAL_PRICE_ID = config('STRIPE_ANNUAL_PRICE_ID', default='')

ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

# Twilio (WhatsApp + SMS parent notifications — optional)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM', default='')  # e.g. +14155238886
TWILIO_SMS_FROM = config('TWILIO_SMS_FROM', default='')             # e.g. +14155238886

# Parent notifications — comma-separated parent email list (production)
PARENT_NOTIFICATION_EMAILS_RAW = config('PARENT_NOTIFICATION_EMAILS', default='')
PARENT_NOTIFICATION_EMAILS = [
    e.strip() for e in PARENT_NOTIFICATION_EMAILS_RAW.split(',') if e.strip()
] or None

# Sentry error tracking (optional — set SENTRY_DSN in env to enable)
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
        )
    except ImportError:
        pass

# Structured logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='WARNING'),
            'propagate': False,
        },
        'learning': {
            'handlers': ['console'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['console'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'decision_engine': {
            'handlers': ['console'],
            'level': config('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# Dashboard snapshot cache TTL in seconds (1 hour default)
PARENT_DASHBOARD_CACHE_TTL = int(config('PARENT_DASHBOARD_CACHE_TTL', default=3600))