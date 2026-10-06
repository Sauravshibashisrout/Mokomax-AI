import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.routes import ingest, query, admin, auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

cfg = get_settings()

app = FastAPI(title="MokoMax AI", version="1.0.0")

app.add_middleware(SessionMiddleware, secret_key=cfg.secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(admin.router)
app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok", "model": cfg.groq_model, "embedding": cfg.embedding_model}
