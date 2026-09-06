"""Shared HTTP helpers for routers (pagination query params)."""

from __future__ import annotations

from fastapi import Query


class Pagination:
    """Common list pagination query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ) -> None:
        self.page = page
        self.page_size = page_size
