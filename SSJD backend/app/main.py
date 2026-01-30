from fastapi import FastAPI
from app.core.logging import setup_logging
from .api import auth, society, test

setup_logging()

app = FastAPI(title="Cooperative Society Core API")

app.include_router(auth.router)
app.include_router(society.router)
app.include_router(test.router)

@app.get("/health")
def health():
    return {"status": "ok"}
