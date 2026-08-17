"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Browsable API is convenient in dev.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Run Celery tasks synchronously in dev unless a worker is running.
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_EAGER", True)  # noqa: F405
