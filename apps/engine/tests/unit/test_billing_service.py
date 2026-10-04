"""Unit and contract tests for Zarinpal billing service (004-launch-readiness-flows)."""

from unittest.mock import AsyncMock, patch
import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import Settings
from src.models import (
    Base,
    Project,
    SubscriptionStatus,
    SubscriptionTier,
    User,
)
from src.services.billing import initiate_plan_upgrade, verify_plan_upgrade

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


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
