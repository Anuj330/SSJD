import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends
from app.core.security import get_current_user

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ping")
def ping():
    logger.info("Ping test called")
    return {
        "status": "ok",
        "message": "API is running"
    }


@router.get("/db")
def db_test(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        logger.info("Database connectivity test successful")
        return {
            "status": "ok",
            "db_result": result
        }
    except Exception as e:
        logger.error("Database test failed", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/protected")
def protected_test(current_user: str = Depends(get_current_user)):
    return {
        "status": "ok",
        "message": f"Hello {current_user}, you are authenticated"
    }