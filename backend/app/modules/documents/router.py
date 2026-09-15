"""Document download endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.documents import service

router = APIRouter(tags=["documents"])


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.BILLING_VIEW)),
) -> Response:
    document = service.get_document(db, document_id)
    data = service.read_document_bytes(document)
    return Response(
        content=data,
        media_type=document.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.filename}"',
        },
    )
