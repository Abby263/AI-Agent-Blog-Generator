"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import get_settings
from .routes import router

app = FastAPI(title="Blog Series Agent API", version="0.1.0")
settings = get_settings()
cors_origins = [
    origin.strip()
    for origin in settings.blog_series_cors_origins.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
