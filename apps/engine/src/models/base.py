"""Declarative base for all engine tables (SQLAlchemy 2.0 style)."""

import json

from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single metadata root — Alembic's `target_metadata` and `create_all` both use it."""


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
