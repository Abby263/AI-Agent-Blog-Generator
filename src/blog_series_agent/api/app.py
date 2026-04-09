"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Blog Series Agent API", version="0.1.0")
app.include_router(router)

