"""Central import point that registers every ORM model with ``Base.metadata``.

Alembic's migration environment and any code needing the full schema import this
module so that all mapped classes are loaded. Add new model modules here as each
feature module is implemented.
"""

from __future__ import annotations

from app.modules.auth import models as auth_models

__all__ = ["auth_models"]
