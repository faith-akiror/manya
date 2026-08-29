"""Django settings for the MANYA platform.

All secrets come from environment variables (or a local `.env` file).
Never commit `.env` to version control.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env (dev convenience). Production should export real env vars.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


# --- Core ---
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-9kz0c-manya-dev-only-do-not-use-in-production-7xy",
)
DEBUG = env_bool("DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="*") or ["*"]

# --- Applications ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # MANYA
    "apps.languages",
    "apps.legal",
    "apps.referrals",
    "apps.policies",
    "apps.ussd",
    "apps.messaging",
    "apps.voice",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---
_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            _database_url, conn_max_age=300, conn_health_checks=True
        )
    }
else:
    # Local development default: SQLite at the project root.
    DATABASES = {
        "default": dj_database_url.parse(
            "sqlite:///" + str(BASE_DIR / "db.sqlite3").replace("\\", "/"),
            conn_max_age=300,
            conn_health_checks=True,
        )
    }

# --- Authentication / validation ---
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Sunbird AI translation ---
# SUNBIRD_ENABLED turns the automatic translation layer on. When enabled, a
# missing translation is fetched from Sunbird, cached in the database and
# reused — Sunbird is never called on every request. Secrets stay in
# environment variables and are never logged.
SUNBIRD_ENABLED = env_bool("SUNBIRD_ENABLED", default=False)
SUNBIRD_BASE_URL = os.getenv("SUNBIRD_BASE_URL", "https://api.sunbird.ai")
SUNBIRD_API_TOKEN = os.getenv("SUNBIRD_API_TOKEN", "")
SUNBIRD_TIMEOUT = int(os.getenv("SUNBIRD_TIMEOUT", "10"))

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Kampala"
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Security ---
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=True)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# --- CORS ---
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", default="")

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/hour",
        "sms": "20/hour",
        "voice": "200/hour",
        "ussd": "1500/hour",
    },
}

# --- drf-spectacular (OpenAPI) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "MANYA API",
    "DESCRIPTION": (
        "MANYA — Know your rights. Know your next step.\n\n"
        "MANYA makes verified Ugandan legal and policy information easier to "
        "access through the web, USSD, SMS and Voice, in the languages people "
        "use. Every public legal item is backed by a verified source."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
