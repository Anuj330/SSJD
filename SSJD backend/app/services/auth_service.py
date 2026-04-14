# Re-export from the single JWT module to avoid duplication
from app.core.jwt import create_access_token  # noqa: F401
