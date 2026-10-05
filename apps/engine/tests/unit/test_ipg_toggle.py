import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.adapters.registry import seed_configs
from src.api.app import create_app
from src.models import AdapterConfig, Base, Project, Provider


def test_seed_configs_defaults_only_zarinpal_enabled():
    project_id = uuid.uuid4()
    configs = seed_configs(project_id)
    assert len(configs) > 0

    zarinpal_found = False
    for row in configs:
        if row["provider"] == Provider.zarinpal:
            assert row["enabled"] is True
            zarinpal_found = True
        else:
            err = f"Provider {row['provider']} should be disabled by default"
            assert row["enabled"] is False, err

    assert zarinpal_found, "Zarinpal adapter was not found in seeded configs"


def test_patch_adapter_unauthorized_in_demo_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("ENGINE_PROFILE", "demo")

    url = f"sqlite:///{tmp_path / 'demo_test.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        project = Project(id=uuid.uuid4(), name="demo")
        session.add(project)
        adapter = AdapterConfig(
            id=uuid.uuid4(),
            project_id=project.id,
            provider=Provider.zarinpal,
            endpoint_path_prefix="/zarinpal",
        )
        session.add(adapter)
        session.commit()
        adapter_id = adapter.id
    sync_engine.dispose()

    app = create_app()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'demo_test.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as client:
        # Without session cookie in demo profile, requests to /adapters/{id} are rejected with 401
        res = client.patch(f"/api/v1/adapters/{adapter_id}", json={"enabled": True})
        assert res.status_code == 401
        assert res.json()["code"] == "session_required"

    asyncio.run(async_engine.dispose())


def test_patch_adapter_enabled_rejected_with_422(monkeypatch, tmp_path):
    """006-admin-ipg-visibility (FR-017): enabled is removed from merchant patchable fields."""
    monkeypatch.setenv("ENGINE_PROFILE", "local")

    url = f"sqlite:///{tmp_path / 'local_test.db'}"
    sync_engine = create_engine(url)
    Base.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        project = Project(id=uuid.uuid4(), name="default")
        session.add(project)
        adapter = AdapterConfig(
            id=uuid.uuid4(),
            project_id=project.id,
            provider=Provider.zarinpal,
            endpoint_path_prefix="/zarinpal",
        )
        session.add(adapter)
        session.commit()
        adapter_id = adapter.id
    sync_engine.dispose()

    app = create_app()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'local_test.db'}")
    app.state.session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    with TestClient(app) as client:
        res = client.patch(f"/api/v1/adapters/{adapter_id}", json={"enabled": True})
        assert res.status_code == 422
        body = res.json()
        assert body["code"] == "validation_error"
        assert body["details"]["allowed"] == ["credentials"]

    asyncio.run(async_engine.dispose())
