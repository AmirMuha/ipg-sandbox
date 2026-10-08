import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode
from src.config import Settings
from src.core.security import hash_api_key
from src.models import Project, User, UserSession, utcnow
from src.models.api_key import ApiKey
from src.models.visitor import VisitorSession
from src.services.auth import hash_session_token


async def get_current_user(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> User | None:
    """Resolve authenticated user from ipg_session cookie or Bearer header, or API key."""
    token = request.cookies.get("ipg_session")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    if token.startswith("ipg_key_"):
        key_hash = hash_api_key(token)
        stmt = select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.revoked_at.is_(None)
        )
        api_key = await db.scalar(stmt)
        if not api_key:
            return None
            
        api_key.last_used_at = utcnow()
        await db.commit()
        return await db.get(User, api_key.user_id)

    token_hash = hash_session_token(token)
    stmt = select(UserSession).where(
        UserSession.token_hash == token_hash,
        UserSession.expires_at > utcnow(),
    )
    user_session = await db.scalar(stmt)
    if not user_session:
        return None

    return await db.get(User, user_session.user_id)


async def get_current_project(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> Project:
    """Resolve current project from authenticated user session, demo session, or local default."""
    user = await get_current_user(request, db)
    if user:
        stmt = (
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.created_at.asc())
            .limit(1)
        )
        project = await db.scalar(stmt)
        if project:
            return project

    profile = os.environ.get("ENGINE_PROFILE", "local")

    if profile == "demo":
        session_id = request.cookies.get("demo_session")
        if not session_id:
            raise ApiError(ErrorCode.session_required, "Session cookie missing", status=401)

        stmt = select(VisitorSession).where(
            VisitorSession.id == session_id, VisitorSession.verified_at.is_not(None)
        )
        visitor = await db.scalar(stmt)
        if not visitor:
            raise ApiError(ErrorCode.session_required, "Invalid or unverified session", status=401)

        project = await db.scalar(select(Project).where(Project.id == visitor.project_id))
        if not project:
            raise ApiError(ErrorCode.session_required, "Project not found", status=401)
        return project

    # Local mode default project fallback
    project = await db.scalar(select(Project).order_by(Project.created_at.asc()).limit(1))
    if not project:
        raise HTTPException(status_code=500, detail="Default project not found")
    return project


async def require_admin(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """The signed-in administrator, or raise. FR-001/002/003.

    Reuses `get_current_user` rather than re-reading the session, so token expiry and the
    Bearer-header fallback are handled once. The allowlist is read per request rather than
    cached, so it is never stale relative to a restarted process.

    `forbidden` (403) and `session_required` (401) are deliberately different: a merchant who is
    correctly signed in should be told they lack the privilege, not bounced to the login page.
    """
    user = await get_current_user(request, db)
    if user is None:
        raise ApiError(ErrorCode.session_required, "Authentication required", status=401)

    allowlist = Settings.from_env().admin_emails
    if not allowlist:
        raise ApiError(
            ErrorCode.forbidden,
            "No administrator is configured; set ADMIN_EMAILS to grant this access",
            status=403,
        )
    if user.email.lower() not in allowlist:
        raise ApiError(ErrorCode.forbidden, "Administrator privileges required", status=403)
    return user
