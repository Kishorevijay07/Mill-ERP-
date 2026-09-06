"""Domain error types, decoupled from HTTP.

Services raise these; a single handler in ``app.main`` maps them to the safe
error contract ({error: {code, message}}). This keeps business logic free of
FastAPI/HTTP concerns (docs/DEVELOPMENT-RULES.md).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, client-facing business errors."""

    code: str = "domain_error"
    status_code: int = 400

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class InvalidStateError(DomainError):
    """A business state transition or precondition was violated."""

    code = "invalid_state"
    status_code = 409
