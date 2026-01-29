from fastapi import FastAPI
from .apis import auth, society

app = FastAPI(title="Cooperative Society Core API")

app.include_router(auth.router)
app.include_router(society.router)

@app.get("/health")
def health():
    return {"status": "ok"}
