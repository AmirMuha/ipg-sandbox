"""Declarative base for all engine tables (SQLAlchemy 2.0 style)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single metadata root — Alembic's `target_metadata` and `create_all` both use it."""
