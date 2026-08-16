"""
app/api/v1/router.py
---------------------
Top-level API v1 router — registers all sub-routers with their prefixes.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, expenses, groups, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(groups.router, prefix="/groups", tags=["Groups"])
api_router.include_router(expenses.router, prefix="", tags=["Expenses & Balances"])
