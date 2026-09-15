"""Central import point that registers every ORM model with ``Base.metadata``.

Alembic's migration environment and any code needing the full schema import this
module so that all mapped classes are loaded. Add new model modules here as each
feature module is implemented.
"""

from __future__ import annotations

from app.modules.auth import models as auth_models
from app.modules.billing import models as billing_models
from app.modules.delivery import models as delivery_models
from app.modules.documents import models as documents_models
from app.modules.government import models as government_models
from app.modules.inventory import models as inventory_models
from app.modules.invoicing import models as invoicing_models
from app.modules.milling import models as milling_models
from app.modules.receiving import models as receiving_models
from app.modules.rice import models as rice_models
from app.modules.settings import models as settings_models
from app.shared import audit as audit_models
from app.shared import reference as reference_models

__all__ = [
    "audit_models",
    "auth_models",
    "billing_models",
    "delivery_models",
    "documents_models",
    "government_models",
    "inventory_models",
    "invoicing_models",
    "milling_models",
    "receiving_models",
    "reference_models",
    "rice_models",
    "settings_models",
]
