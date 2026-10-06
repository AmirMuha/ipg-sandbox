"""Unit and contract tests for Zarinpal billing service (004-launch-readiness-flows)."""

import uuid
from datetime import timedelta
from unittest.mock import patch

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.errors import ApiError
from src.config import Settings
from src.models import (
    Base,
    Project,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    User,
    utcnow,
)
from src.services.billing import (
    deactivate_subscription,
    expire_due_subscriptions,
    initiate_plan_upgrade,
    verify_plan_upgrade,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


async def _paid_setup(session, *, expires_in_days: int = 30, status="active"):
    """A team-tier project plus one subscription row; returns (project, subscription)."""
    user = User(email=f"paid-{uuid.uuid4().hex[:8]}@merchant.ir", auth_provider="local")
    session.add(user)
    await session.flush()
    project = Project(
        name="Paid Proj",
        user_id=user.id,
        tier=SubscriptionTier.team.value,
        daily_requests_cap=0,
        max_active_adapters=0,
        history_cap=1000,
        webhook_retry_max=3,
        pending_settle_delay_s=5,
        timeout_delay_s=30,
    )
    session.add(project)
    await session.flush()
    sub = Subscription(
        project_id=project.id,
        user_id=user.id,
        tier=SubscriptionTier.team.value,
        status=status,
        amount_rial=1_990_000,
        zarinpal_authority=f"A{uuid.uuid4().hex[:20]}",
        started_at=utcnow(),
        expires_at=utcnow() + timedelta(days=expires_in_days),
    )
    session.add(sub)
    await session.commit()
    return project, sub


@pytest.fixture
def db_session_factory(tmp_path):
    url = f"sqlite:///{tmp_path / 'billing_test.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    async_url = f"sqlite+aiosqlite:///{tmp_path / 'billing_test.db'}"
    async_engine = create_async_engine(async_url)
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    return factory


@pytest.mark.asyncio
async def test_billing_initiate_and_verify_flow(db_session_factory):
    settings = Settings.from_env()

    request_response = httpx.Response(
        200,
        json={
            "data": {"code": 100, "message": "Success", "authority": "A0000000000012345678"},
            "errors": [],
        },
    )
    verify_response = httpx.Response(
        200,
        json={
            "data": {"code": 100, "message": "Paid", "ref_id": 987654321},
            "errors": [],
        },
    )

    with patch.object(httpx.AsyncClient, "post", side_effect=[request_response, verify_response]):
        async with db_session_factory() as session:
            user = User(email="test@merchant.ir", auth_provider="local")
            session.add(user)
            await session.flush()

            project = Project(
                name="Test Proj",
                user_id=user.id,
                tier=SubscriptionTier.developer.value,
                daily_requests_cap=100,
                max_active_adapters=2,
                history_cap=1000,
                webhook_retry_max=3,
                pending_settle_delay_s=5,
                timeout_delay_s=30,
            )
            session.add(project)
            await session.commit()

            # 1. Initiate upgrade
            sub, pay_url = await initiate_plan_upgrade(
                project=project,
                user=user,
                tier=SubscriptionTier.team.value,
                callback_url="http://localhost:8080/api/v1/billing/callback",
                db=session,
                settings=settings,
            )
            assert sub.status == SubscriptionStatus.pending.value
            assert sub.zarinpal_authority == "A0000000000012345678"
            assert f"StartPay/{sub.zarinpal_authority}" in pay_url

            # 2. Verify upgrade
            verified_sub = await verify_plan_upgrade(
                authority="A0000000000012345678",
                status_param="OK",
                db=session,
                settings=settings,
            )
            assert verified_sub.status == SubscriptionStatus.active.value
            assert verified_sub.zarinpal_ref_id == 987654321

            # Check project was upgraded
            updated_proj = await session.get(Project, project.id)
            assert updated_proj.tier == SubscriptionTier.team.value
            assert updated_proj.daily_requests_cap == 0
            assert updated_proj.max_active_adapters == 0


@pytest.mark.asyncio
async def test_initiate_rejects_project_with_active_subscription(db_session_factory):
    """No double-charge and no re-buy while the paid plan is running (409)."""
    settings = Settings.from_env()
    async with db_session_factory() as session:
        project, _sub = await _paid_setup(session)

        with pytest.raises(ApiError) as excinfo:
            await initiate_plan_upgrade(
                project=project,
                user=None,
                tier=SubscriptionTier.team.value,
                callback_url="http://localhost:8080/api/v1/billing/callback",
                db=session,
                settings=settings,
            )
        assert excinfo.value.status == 409
        assert excinfo.value.code.value == "unsupported_operation"


@pytest.mark.asyncio
async def test_expire_due_subscriptions_lapses_and_reverts(db_session_factory):
    """The expiry sweep is the only thing that ends entitlements (they used to last forever)."""
    async with db_session_factory() as session:
        overdue_project, overdue_sub = await _paid_setup(session, expires_in_days=-1)
        fresh_project, fresh_sub = await _paid_setup(session, expires_in_days=30)

        expired = await expire_due_subscriptions(session)
        assert expired == 1

        assert (await session.get(Subscription, overdue_sub.id)).status == (
            SubscriptionStatus.expired.value
        )
        overdue = await session.get(Project, overdue_project.id)
        assert overdue.tier == SubscriptionTier.developer.value
        assert overdue.daily_requests_cap == 100
        assert overdue.max_active_adapters == 2

        assert (await session.get(Subscription, fresh_sub.id)).status == (
            SubscriptionStatus.active.value
        )
        assert (await session.get(Project, fresh_project.id)).tier == (SubscriptionTier.team.value)


@pytest.mark.asyncio
async def test_deactivate_active_subscription_reverts_immediately(db_session_factory):
    """Admin deactivation: cancelled now, free tier now — not at expires_at."""
    async with db_session_factory() as session:
        project, sub = await _paid_setup(session)

        await deactivate_subscription(session, sub)

        assert (await session.get(Subscription, sub.id)).status == (
            SubscriptionStatus.cancelled.value
        )
        reverted = await session.get(Project, project.id)
        assert reverted.tier == SubscriptionTier.developer.value
        assert reverted.daily_requests_cap == 100
        assert reverted.max_active_adapters == 2


@pytest.mark.asyncio
async def test_deactivate_non_active_subscription_is_rejected(db_session_factory):
    async with db_session_factory() as session:
        _project, sub = await _paid_setup(session, status="pending")

        with pytest.raises(ApiError) as excinfo:
            await deactivate_subscription(session, sub)
        assert excinfo.value.status == 409
        assert (await session.get(Subscription, sub.id)).status == (
            SubscriptionStatus.pending.value
        )
