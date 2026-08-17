"""Pytest fixtures. Uses an in-memory SQLite DB so tests need no Postgres.

Environment is set BEFORE importing app modules, because app.core.database
reads DATABASE_URL / JWT_SECRET_KEY at import time.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importing app.models registers every model on Base.metadata.
import app.models  # noqa: F401
from app.core.database import Base


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
