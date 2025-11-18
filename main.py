"""FastAPI entry point for the AI Agent Blog Series Generator."""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router as api_router

load_dotenv()

app = FastAPI(
    title="AI Agent Blog Series Generator",
    version="1.0.0",
    description="REST API for orchestrating the LangGraph-based blog workflow",
)

# Basic CORS setup for upcoming frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Expose generated assets for the frontend
for directory in ("output", "images"):
    Path(directory).mkdir(parents=True, exist_ok=True)

app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/images", StaticFiles(directory="images"), name="images")


@app.on_event("startup")
async def validate_startup_environment() -> None:
    """Ensure required environment variables are configured."""
    validate_environment()


def validate_environment() -> None:
    """Validate core environment variables and raise if missing."""
    required_env = {
        "OPENAI_API_KEY": "OpenAI API key for LLM",
        "TAVILY_API_KEY": "Tavily API key for web search",
    }
    missing: List[str] = []
    for key, desc in required_env.items():
        if not os.getenv(key):
            missing.append(f"{key}: {desc}")
    if missing:
        message = "Missing required environment variables:\n" + "\n".join(missing)
        raise RuntimeError(message)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Simple root endpoint."""
    return {"message": "AI Agent Blog Series Generator API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
