"""API package for FastAPI routes."""

from fastapi import APIRouter
from api.routes import router as api_router

__all__ = ["api_router", "APIRouter"]
