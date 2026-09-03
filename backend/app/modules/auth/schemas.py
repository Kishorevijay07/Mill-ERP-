"""Pydantic schemas for the auth API boundary."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    # Accepts either an email address or a username.
    identifier: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool


class MeResponse(BaseModel):
    user: UserOut
    roles: list[str]
    permissions: list[str]


class MessageResponse(BaseModel):
    message: str
