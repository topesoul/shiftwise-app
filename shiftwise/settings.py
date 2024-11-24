# settings.py

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

# Load environment variables from env.py if it exists
if os.path.exists("env.py"):
    import env  # noqa

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Security Settings
# -----------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure-'):
    raise ImproperlyConfigured(
        "SECRET_KEY must be set in environment variables with at least 50 characters and not start with 'django-insecure-'."
    )

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in environment variables.")

FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY must be set in environment variables."
    )

# -----------------------------------------------------------------------------
# Application Definition
# -----------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    # Default Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",

    # Third-party apps
    "storages",
    "crispy_forms",
    "crispy_bootstrap4",
    "django_extensions",
    "django_filters",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.mfa",
    "allauth.usersessions",

    # Your apps
    "accounts.apps.AccountsConfig",
    "core",
    "subscriptions",
    "shifts",
    "home",
    "contact",
    "notifications",
    # Uncomment the line below if using Django Debug Toolbar
    # 'debug_toolbar',
]

CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Uncomment the line below if using Django Debug Toolbar
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    "allauth.usersessions.middleware.UserSessionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "shiftwise.urls"

SITE_URL = os.getenv("SITE_URL")

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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
                "shiftwise.context_processors.google_places_api_key",
            ],
            "builtins": [
                "django.templatetags.static",
            ],
        },
    },
]

WSGI_APPLICATION = "shiftwise.wsgi.application"

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL must be set in environment variables.")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

# Configure SSL for PostgreSQL database
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# -----------------------------------------------------------------------------
# Password Validation
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Allauth Configuration
# -----------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)
SITE_ID = 1
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
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
MFA_TOTP_PERIOD = 30
MFA_TOTP_DIGITS = 6
MFA_TOTP_ISSUER = "ShiftWise"

# User Sessions Configuration
USERSESSIONS_ADAPTER = "allauth.usersessions.adapter.DefaultUserSessionsAdapter"
USERSESSIONS_TRACK_ACTIVITY = True
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Allauth email settings
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# -----------------------------------------------------------------------------
# Email Configuration
# -----------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

ADMINS = [
    (os.getenv("ADMIN_NAME", "Admin Name"), os.getenv("ADMIN_EMAIL", "admin@example.com")),
]

# -----------------------------------------------------------------------------
# Stripe Configuration
# -----------------------------------------------------------------------------

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Plan configuration
STRIPE_PRICE_IDS = {
    "Basic": os.getenv("STRIPE_PRICE_BASIC"),
    "Pro": os.getenv("STRIPE_PRICE_PRO"),
    "Enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE"),
}

# -----------------------------------------------------------------------------
# CSRF Trusted Origins
# -----------------------------------------------------------------------------

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in CSRF_TRUSTED_ORIGINS if origin.strip()
]

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------

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
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        "accounts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "subscriptions": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shifts": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Add logging for storages and boto3
        "storages": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "boto3": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "botocore": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# -----------------------------------------------------------------------------
# Static and Media Files Configuration
# -----------------------------------------------------------------------------

USE_AWS = os.getenv('USE_AWS', 'False') == 'True'

# Always define STATICFILES_DIRS
STATICFILES_DIRS = [BASE_DIR / "static"]

# Always define STATICFILES_FINDERS
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

if USE_AWS:
    # AWS S3 settings
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # 1 day
    }

    # AWS Credentials
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not all([AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise ImproperlyConfigured("AWS credentials and bucket configuration must be set in environment variables.")

    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

    # Disable default ACLs
    AWS_DEFAULT_ACL = None

    # Static and Media settings
    STATICFILES_LOCATION = 'static'
    MEDIAFILES_LOCATION = 'media'

    # **New STORAGES setting**
    STORAGES = {
        "default": {
            "BACKEND": "custom_storages.MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "custom_storages.StaticStorage",
        },
    }

    # Static and media URLs
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'

    # Define STATIC_ROOT to prevent collectstatic errors
    STATIC_ROOT = BASE_DIR / 'staticfiles'  # Unused but required by Django
else:
    # Local static and media files settings
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# Security Settings for Production
# -----------------------------------------------------------------------------

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # One year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

# -----------------------------------------------------------------------------
# Debugging and Verification
# -----------------------------------------------------------------------------

print(f"USE_AWS: {USE_AWS}")
print(f"STATICFILES_STORAGE: {locals().get('STATICFILES_STORAGE')}")
print(f"DEFAULT_FILE_STORAGE: {locals().get('DEFAULT_FILE_STORAGE')}")
print(f"STATIC_ROOT: {STATIC_ROOT}")
print(f"STATICFILES_DIRS: {STATICFILES_DIRS}")
