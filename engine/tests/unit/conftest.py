"""Fixtures for the data-layer unit tests (T008/T009).

Lives here rather than in `tests/conftest.py` so it stays file-disjoint from the
contract-test dispatch running in the same worktree.

The models target Postgres, but four of their types have no SQLite equivalent.
The shims below map them onto SQLite so the *constraint* rules — which are plain
CHECK constraints — can be executed for real instead of merely inspected.
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from src.models import Base


@compiles(JSONB, "sqlite")
def _jsonb_as_json(element, compiler, **kw) -> str:
    return "JSON"


@compiles(UUID, "sqlite")
def _uuid_as_blob(element, compiler, **kw) -> str:
    return "BLOB"


@compiles(ARRAY, "sqlite")
def _array_as_json_text(element, compiler, **kw) -> str:
    """DDL half of the ARRAY shim — store the schedule as JSON text."""
    return "JSON"


def _array_bind_processor(self, dialect):
    """Bind half: sqlite3 refuses a Python list, so serialize it. Postgres stays native."""
    if dialect.name != "sqlite":
        return None
    return lambda value: None if value is None else json.dumps(value)


ARRAY.bind_processor = _array_bind_processor


@pytest.fixture
def session():
    """In-memory SQLite session with the real schema created from the models."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
