"""
Django settings for budgetportal project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# THINK VERY CAREFULY before using the TEST variable.
# Tests should aim to be as production-like as possible.
import sys

import boto3

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
import dj_database_url
import environ
import sentry_sdk
from ckanapi import RemoteCKAN
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "true") == "true"


if "test" in sys.argv or "test_coverage" in sys.argv:
    TEST = True
else:
    TEST = False


ROOT_DIR = environ.Path(__file__) - 2
PROJ_DIR = ROOT_DIR.path("budgetportal")

# SECURITY WARNING: keep the secret key used in production secret!
if DEBUG:
    SECRET_KEY = "-r&cjf5&l80y&(q_fiidd$-u7&o$=gv)s84=2^a2$o^&9aco0o"
else:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG_TOOLBAR = os.environ.get("DJANGO_DEBUG_TOOLBAR", "false").lower() == "true"
print("Django Debug Toolbar %s." % "enabled" if DEBUG_TOOLBAR else "disabled")
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "budgetportal.debug_toolbar_config.show_toolbar_check"
}

GOOGLE_ANALYTICS_ID = "UA-93649482-8"

ALLOWED_HOSTS = ["*"]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition

INSTALLED_APPS = [
    "budgetportal.apps.BudgetPortalConfig",
    "budgetportal.webflow",
    "allauth_facebook",
    # before auth for LiveServerTestCase https://code.djangoproject.com/ticket/10827
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "django.contrib.admin.apps.SimpleAdminConfig",
    "adminplus",
    "adminsortable",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pipeline",
    "django_extensions",
    "django_q",
    "captcha",
    "rest_framework",
    "django_filters",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "import_export",
    "markdownify",
    "ckeditor",
    "haystack",
]

if DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
]

if DEBUG_TOOLBAR:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

SITE_ID = int(os.environ.get("DJANGO_SITE_ID", 1))

ROOT_URLCONF = "budgetportal.urls"

WSGI_APPLICATION = "budgetportal.wsgi.application"

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"


db_config = dj_database_url.config()
db_config["ATOMIC_REQUESTS"] = True

DATABASES = {"default": db_config}

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
AWS_DEFAULT_ACL = "private"
AWS_BUCKET_ACL = "private"
AWS_AUTO_CREATE_BUCKET = True
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", None)
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", None)

SOLR_URL = os.environ["SOLR_URL"]

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": SOLR_URL,
        "ADMIN_URL": "",
    }
}


# Caches
if DEBUG:
    if os.environ.get("DEBUG_CACHE", "false").lower() == "true":
        print("\nDEBUG_CACHE=True: Django cache enabled.\n")
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake",
            }
        }
    else:
        CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": "/var/tmp/django_cache",
        }
    }
CACHE_MIDDLEWARE_SECONDS = 600


CKAN_URL = os.environ.get("CKAN_URL", "https://treasurydata.openup.org.za")
CKAN_API_KEY = os.environ.get("CKAN_API_KEY", None)
CKAN = RemoteCKAN(CKAN_URL, apikey=CKAN_API_KEY)

DISCOURSE_SSO_URLS = {
    "discourse": os.environ.get(
        "DISCOURSE_SSO_URL", "https://discussions.vulekamali.gov.za/session/sso_login"
    ),
    "ckan": os.environ.get("CKAN_SSO_URL", "https://data.vulekamali.gov.za/user/login"),
}
DISCOURSE_SSO_SECRET = os.environ.get("DISCOURSE_SSO_SECRET", None)
COMMENTS_ENABLED = os.environ.get("COMMENTS_ENABLED", "false").lower() == "true"

BUST_OPENSPENDING_CACHE = (
    os.environ.get("BUST_OPENSPENDING_CACHE", "false").lower() == "true"
)
OPENSPENDING_HOST = os.environ.get("OPENSPENDING_HOST", "https://openspending.org")

# http://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "budgetportal.allauthadapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "budgetportal.allauthadapters.SocialAccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.environ.get("HTTP_PROTOCOL", "https")
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_FORM_CLASS = "budgetportal.forms.AllauthSignupForm"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = os.environ.get(
    "ACCOUNT_LOGOUT_REDIRECT_URL", "https://vulekamali.gov.za"
)
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "apikey")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", None)
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", True)

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "info@vulekamali.gov.za")

RECAPTCHA_PUBLIC_KEY = os.environ.get(
    "RECAPTCHA_PUBLIC_KEY", "6LfV_1EUAAAAAAZtrLkMOG6Fyyepj-Mgs1cVH5_c"
)
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY")
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(ROOT_DIR.path("assets/js"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "budgetportal.context_processors.google_analytics",
                "budgetportal.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
            ]
        },
    }
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATICFILES_DIRS = [
    str(ROOT_DIR.path("assets")),
    str(ROOT_DIR.path("packages/webapp/build/static")),
]

ASSETS_DEBUG = DEBUG
ASSETS_URL_EXPIRE = False

# assets must be placed in the 'static' dir of your Django app

# where the compiled assets go
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# the URL for assets
STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)

PYSCSS_LOAD_PATHS = [
    os.path.join(BASE_DIR, "budgetportal", "static"),
    os.path.join(BASE_DIR, "budgetportal", "static", "bower_components"),
]

PIPELINE = {
    "STYLESHEETS": {
        "css": {
            "source_filenames": ("stylesheets/app.scss",),
            "output_filename": "app.css",
        },
        "vulekamali-webflow-css": {
            "source_filenames": ("scss/vulekamali-webflow.scss",),
            "output_filename": "vulekamali-webflow.css",
        },
        "admin": {
            "source_filenames": ("stylesheets/admin.scss",),
            "output_filename": "admin.css",
        },
    },
    "JAVASCRIPT": {
        "js": {"source_filenames": ("javascript/app.js",), "output_filename": "app.js"}
    },
    "CSS_COMPRESSOR": None,
    "JS_COMPRESSOR": None,
    "COMPILERS": ("budgetportal.pipeline.PyScssCompiler",),
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
if not TEST:
    STATICFILES_STORAGE = "budgetportal.pipeline.GzipManifestPipelineStorage"

ROBOTS_DENY_ALL = os.environ.get("ROBOTS_DENY_ALL", "false").lower() == "true"

# Logging


SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()])

boto3.set_stream_logger("boto3.resources", logging.INFO)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO"},
    "loggers": {
        "budgetportal": {"level": "DEBUG" if DEBUG else "INFO"},
        "django": {"level": "DEBUG" if DEBUG else "INFO"},
    },
}

DJANGO_Q_SYNC = os.environ.get("DJANGO_Q_SYNC", "false").lower() == "true"

Q_CLUSTER = {
    "name": "Something",
    "workers": 1,
    "timeout": 30 * 60,  # Timeout a task after this many seconds
    "retry": 5,
    "queue_limit": 1,
    "bulk": 1,
    "orm": "default",  # Use Django ORM as storage backend
    "poll": 10,  # Check for queued tasks this frequently (seconds)
    "save_limit": 0,
    "ack_failures": True,  # Dequeue failed tasks
    "sync": DJANGO_Q_SYNC,
}

MARKDOWNIFY_WHITELIST_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "em",
    "i",
    "li",
    "ol",
    "p",
    "strong",
    "ul",
    "h1",
    "h2",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}
