"""
app/main.py
-----------
FastAPI application entry-point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.scheduler import start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / shutdown lifecycle."""
    start_scheduler()
    yield
    stop_scheduler()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Expense Splitter API",
        description=(
            "REST API for tracking and splitting shared expenses among groups. "
            "Built with FastAPI · SQLAlchemy 2.0 · PostgreSQL."
        ),
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS — origins controlled entirely via .env / Settings
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_origin_regex=r"https://.*\.onrender\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------
    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_application()
