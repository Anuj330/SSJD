"""Production settings — hardened security."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

# Refuse to boot in production with an unsafe / unset secret key.
if not SECRET_KEY or SECRET_KEY in ("insecure-dev-key-change-me",  # noqa: F405
                                    "change-me-run-python-c-import-secrets-print-secrets-token-urlsafe-50"):
    raise ImproperlyConfigured("SECRET_KEY must be set to a strong, unique value in production.")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]:  # noqa: F405
    raise ImproperlyConfigured("ALLOWED_HOSTS must be explicitly set in production.")

# HTTPS / cookies / headers
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")  # noqa: F405

# Real broker required in prod.
CELERY_TASK_ALWAYS_EAGER = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
