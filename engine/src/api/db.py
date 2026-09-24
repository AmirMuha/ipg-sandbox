"""Engine session dependency (T011) — one async engine for the process, one session per request.

`app.state.engine` is set at startup (or injected by tests), which keeps the module importable
without a database: importing the app must not open a connection.
"""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Per-request session. Read-only handlers never commit, so no auto-commit here."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session
