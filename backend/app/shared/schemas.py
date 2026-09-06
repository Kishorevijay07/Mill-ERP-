"""Shared API schema helpers (pagination)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """A page of results for list endpoints."""

    items: list[T]
    total: int
    page: int
    page_size: int
