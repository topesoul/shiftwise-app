# /workspace/shiftwise/shiftwise/settings.py

import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# Load environment variables from env.py if it exists
if os.path.exists("env.py"):
    import env

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"

# Encrypted Model Fields Configuration
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")

# Verify that FIELD_ENCRYPTION_KEY is set
if not FIELD_ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY must be set in the environment variables."
    )

# Hosts allowed to connect to the application
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

ALLOWED_HOSTS = ["*"]

# Application definition
AUTH_USER_MODEL = "accounts.User"  # Custom user model

# Installed Apps
INSTALLED_APPS = [
    # Third-party apps
    "crispy_forms",
    "crispy_bootstrap4",
    "django_extensions",
    "django_filters",
    "debug_toolbar",
    "channels",
    # django-allauth apps
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # MFA app
    "allauth.mfa",
    # User Sessions app
    "allauth.usersessions",
    # Your custom apps
    "core",
    "accounts.apps.AccountsConfig",
    "subscriptions",
    "shifts",
    "home",
    "contact",
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Additional apps
    "django.contrib.humanize",
]

ASGI_APPLICATION = "shiftwise.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Celery Configuration Options
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/London"

# Crispy Forms Configuration
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Middleware configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Debug Toolbar Middleware (must be first after session)
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # Allauth Account Middleware
    "allauth.account.middleware.AccountMiddleware",
    # Allauth User Sessions Middleware
    "allauth.usersessions.middleware.UserSessionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Internal IPs for Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

# Root URL configuration
ROOT_URLCONF = "shiftwise.urls"

# Google Location Services API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],  # Templates directory
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Default context processors
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # Required by allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Custom context processors
                "accounts.context_processors.user_roles_and_subscriptions",
                'shiftwise.context_processors.google_places_api_key',
            ],
            "builtins": [
                "django.templatetags.static",
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = "shiftwise.wsgi.application"

# Database configuration
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv(
            "DATABASE_URL", "postgres://user:password@localhost:5432/shiftwise_db"
        )
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization and time zone settings
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Allauth configuration for user management
SITE_ID = 1
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # Default
    "allauth.account.auth_backends.AuthenticationBackend",  # Allauth
)

LOGIN_REDIRECT_URL = "/"

# MFA Configuration
MFA_ADAPTER = "allauth.mfa.adapter.DefaultMFAAdapter"
MFA_FORMS = {
    "authenticate": "allauth.mfa.base.forms.AuthenticateForm",
    "reauthenticate": "allauth.mfa.base.forms.ReauthenticateForm",
    "activate_totp": "allauth.mfa.totp.forms.ActivateTOTPForm",
    "deactivate_totp": "allauth.mfa.totp.forms.DeactivateTOTPForm",
    "generate_recovery_codes": "allauth.mfa.recovery_codes.forms.GenerateRecoveryCodesForm",
}

# MFA-specific settings
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
MFA_TOTP_PERIOD = 30  # Seconds
MFA_TOTP_DIGITS = 6
MFA_TOTP_ISSUER = "ShiftWise"

# User Sessions Configuration
USERSESSIONS_ADAPTER = "allauth.usersessions.adapter.DefaultUserSessionsAdapter"
USERSESSIONS_TRACK_ACTIVITY = True  # Tracks IP, user agent, and last seen timestamp
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Allauth-specific settings for email-based authentication
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# Allauth Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # SendGrid requires 'apikey' as the user
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@shiftwise.com")

ADMINS = [
    ("Admin Name", "support@shiftwiseapp.com"),
]

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AWS Bucket Parameter Configuration
if "USE_AWS" in os.environ:
    # Cache Control
    AWS_S3_OBJECT_PARAMETERS = {
        "ExpiresAt": os.environ.get("CACHE_CONTROL_MAX_AGE", default=86400, type=int),
        "ContentType": "image/jpeg",
        "ContentDisposition": "inline",
        "CacheControl": "max-age=%d" % (AWS_S3_OBJECT_PARAMETERS["ExpiresAt"]),
    }

# AWS Cache Controller
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 60 * 60  # 1 hour
CACHE_MIDDLEWARE_KEY_PREFIX = "shiftwise"

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = "us-west-2"
AWS_STORAGE_BUCKET_NAME = "shiftwise-static-files"
AWS_DEFAULT_ACL = "public-read"
AWS_S3_FILE_OVERWRITE = False

# Stripe configuration
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Plan configuration
STRIPE_PRICE_IDS = {
    "Basic": os.getenv("STRIPE_PRICE_BASIC"),
    "Pro": os.getenv("STRIPE_PRICE_PRO"),
    "Enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE"),
}

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in CSRF_TRUSTED_ORIGINS
    if origin.strip() and origin.strip().startswith(("http://", "https://"))
]

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "shiftwise.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "subscriptions": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shifts": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
