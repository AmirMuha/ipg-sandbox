"""Root fixtures for engine test suite (T017–T020).

Uses file-backed SQLite with PostgreSQL dialect compilation shims so real FastAPI
TestClient can run without requiring an external PostgreSQL instance.
"""

import asyncio
import json
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from src.api.app import create_app
from src.models import (
    AdapterConfig,
    ApiUnit,
    Base,
    Project,
    Provider,
)


@compiles(JSONB, "sqlite")
def _jsonb_as_json(element, compiler, **kw) -> str:
    return "JSON"


@compiles(UUID, "sqlite")
def _uuid_as_blob(element, compiler, **kw) -> str:
    return "BLOB"


@compiles(ARRAY, "sqlite")
def _array_as_json_text(element, compiler, **kw) -> str:
    return "JSON"


def _array_bind_processor(self, dialect):
    if dialect.name != "sqlite":
        return None
    return lambda value: None if value is None else json.dumps(value)


def _array_result_processor(self, dialect, coltype):
    if dialect.name != "sqlite":
        return None
    return lambda value: None if value is None else json.loads(value)


ARRAY.bind_processor = _array_bind_processor
ARRAY.result_processor = _array_result_processor


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    """TestClient backed by a real SQLite database with default seeded project & adapters."""
    db_file = tmp_path / "engine_test.db"
    sync_url = f"sqlite:///{db_file}"
    sync_engine = create_engine(sync_url)
    Base.metadata.create_all(sync_engine)

    with Session(sync_engine) as session:
        project = Project(
            id=uuid.uuid4(),
            name="default",
            history_cap=1000,
            webhook_retry_max=3,
            pending_settle_delay_s=5,
            timeout_delay_s=30,
        )
        session.add(project)
        session.add_all(
            [
                AdapterConfig(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    provider=Provider.zarinpal,
                    endpoint_path_prefix="/zarinpal",
                    api_unit=ApiUnit.rial,
                    credentials={"merchant_id": "test-merchant"},
                ),
                AdapterConfig(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    provider=Provider.idpay,
                    endpoint_path_prefix="/idpay",
                    api_unit=ApiUnit.toman,
                    credentials={"api_key": "test-idpay-key"},
                ),
                AdapterConfig(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    provider=Provider.behpardakht,
                    endpoint_path_prefix="/behpardakht",
                    api_unit=ApiUnit.rial,
                    credentials={
                        "terminal_id": 123456,
                        "username": "sandbox",
                        "password": "sandbox",
                    },
                ),
            ]
        )
        session.commit()
    sync_engine.dispose()

    async_url = f"sqlite+aiosqlite:///{db_file}"
    async_engine = create_async_engine(async_url)
    factory = async_sessionmaker(async_engine, expire_on_commit=False)

    app = create_app()
    app.state.session_factory = factory

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(async_engine.dispose())
