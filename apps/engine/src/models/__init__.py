"""ORM models and enums for the IPG Sandbox engine (T008).

Importing this package registers every table on `Base.metadata`, which is what Alembic's
`target_metadata` and autogenerate rely on.
"""

from .base import Base
from .enums import (
    ApiUnit,
    ProjectKind,
    Provider,
    ScenarioOutcome,
    TransactionStatus,
)
from .models import (
    ALLOWED_TRANSITIONS,
    AdapterConfig,
    IllegalTransitionError,
    Project,
    Transaction,
    UsageMeter,
    utcnow,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "AdapterConfig",
    "ApiUnit",
    "Base",
    "IllegalTransitionError",
    "Project",
    "ProjectKind",
    "Provider",
    "ScenarioOutcome",
    "Transaction",
    "TransactionStatus",
    "UsageMeter",
    "utcnow",
]
