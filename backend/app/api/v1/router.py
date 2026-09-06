"""Aggregate router for API v1.

Business module routers (auth, government, receiving, milling, rice, delivery,
billing, inventory, documents, reports, audit) are included here as they are
implemented from Stage 1 onward. Keep this file a thin wiring layer.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.delivery.router import router as delivery_router
from app.modules.documents.router import router as documents_router
from app.modules.government.router import router as government_router
from app.modules.milling.router import router as milling_router
from app.modules.receiving.router import router as receiving_router
from app.modules.reports.router import router as reports_router
from app.modules.rice.router import router as rice_router
from app.modules.settings.router import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(government_router)
api_router.include_router(receiving_router)
api_router.include_router(milling_router)
api_router.include_router(rice_router)
api_router.include_router(delivery_router)
api_router.include_router(settings_router)
api_router.include_router(billing_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)

# Further business routers are registered here as later stages land.
