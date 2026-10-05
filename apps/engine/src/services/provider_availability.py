"""Platform-wide gateway availability (006-admin-ipg-visibility, research.md D1).

One read path, two consumers: the public providers page and the payment-initiation gate. Both
must agree on what "offered" means, and a second hand-kept rule is exactly the duplication
`adapters/registry.py` warns about.

Global state is *not* a new table. It is the existing `AdapterConfig.enabled` column on the
platform project — the one row with `user_id IS NULL`, created by `_seed_default_project` in
`api/app.py`. Every registered user gets a project with `user_id` set, so `user_id IS NULL`
selects exactly one row on both fresh and existing databases.

`user_id IS NULL` is the discriminator, NOT `kind` and NOT "oldest by created_at": the platform
project is created with the `local` default so `kind` does not identify it, and on a database
where a user registered before the platform project existed, "oldest" would be a *merchant's*
project — a silent, platform-wide misread of the availability flag.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AdapterConfig, Project, Provider


async def platform_project(session: AsyncSession) -> Project | None:
    """The project holding platform-wide availability, or `None` if there isn't one.

    `None` is a real state, not an error: a database where every project belongs to a user has no
    platform row, and callers decide how to degrade (FR-023 — render empty, never raise).
    """
    return await session.scalar(select(Project).where(Project.user_id.is_(None)).limit(1))


async def get_offered_providers(session: AsyncSession) -> set[Provider]:
    """Providers enabled on the platform project. Empty set when there is no platform project."""
    project = await platform_project(session)
    if project is None:
        return set()
    stmt = select(AdapterConfig.provider).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.enabled.is_(True),
    )
    return set(await session.scalars(stmt))


async def is_offered(session: AsyncSession, provider: Provider) -> bool:
    """Whether `provider` is offered to every merchant right now."""
    project = await platform_project(session)
    if project is None:
        return False
    stmt = select(AdapterConfig.id).where(
        AdapterConfig.project_id == project.id,
        AdapterConfig.provider == provider,
        AdapterConfig.enabled.is_(True),
    )
    return (await session.scalar(stmt)) is not None


async def platform_adapter(session: AsyncSession, provider: Provider) -> AdapterConfig | None:
    """The platform project's row for `provider`, enabled or not — the admin write target."""
    project = await platform_project(session)
    if project is None:
        return None
    return await session.scalar(
        select(AdapterConfig).where(
            AdapterConfig.project_id == project.id,
            AdapterConfig.provider == provider,
        )
    )
