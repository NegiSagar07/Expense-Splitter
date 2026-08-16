"""
app/api/v1/endpoints/health.py
-------------------------------
Health-check endpoint — used for Render keep-alive pings (Phase 6).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check", tags=["meta"])
async def health() -> dict:
    """Returns 200 OK. Used by UptimeRobot to prevent Render sleep."""
    return {"status": "ok"}
