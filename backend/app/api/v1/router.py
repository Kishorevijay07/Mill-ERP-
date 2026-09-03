"""Aggregate router for API v1.

Business module routers (auth, government, receiving, milling, rice, delivery,
billing, inventory, documents, reports, audit) are included here as they are
implemented from Stage 1 onward. Keep this file a thin wiring layer.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)

# Further business routers are registered here as later stages land.
