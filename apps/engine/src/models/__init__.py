"""ORM models and enums for the IPG Sandbox engine (T008).

Importing this package registers every table on `Base.metadata`, which is what Alembic's
`target_metadata` and autogenerate rely on.
"""

from .auth import EmailVerification, User, UserSession
from .base import Base
from .billing import Subscription, SubscriptionStatus, SubscriptionTier
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
from .visitor import VisitorSession
from .webhook import DeliveryResult, WebhookDelivery

__all__ = [
    "ALLOWED_TRANSITIONS",
    "AdapterConfig",
    "ApiUnit",
    "Base",
    "DeliveryResult",
    "EmailVerification",
    "IllegalTransitionError",
    "Project",
    "ProjectKind",
    "Provider",
    "ScenarioOutcome",
    "Subscription",
    "SubscriptionStatus",
    "SubscriptionTier",
    "Transaction",
    "TransactionStatus",
    "UsageMeter",
    "User",
    "UserSession",
    "VisitorSession",
    "WebhookDelivery",
    "utcnow",
]
