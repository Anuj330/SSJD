from fastapi import FastAPI

# ✅ ABSOLUTE imports only
from app.api.urls import router as api_router
from app.api import auth, society

app = FastAPI(title="SSJD Backend")

app.include_router(api_router)
app.include_router(auth.router)
app.include_router(society.router)
