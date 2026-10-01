import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode
from src.models import Project
from src.models.visitor import VisitorSession


async def get_current_project(
    request: Request, db: Annotated[AsyncSession, Depends(get_session)]
) -> Project:
    profile = os.environ.get("ENGINE_PROFILE", "local")

    if profile == "demo":
        session_id = request.cookies.get("demo_session")
        if not session_id:
            # status=401 explicitly: ApiError defaults to 400, which reported a missing
            # session as a *validation* fault and collided with `invalid_credentials` (also
            # 401) in the contract's status->code map. A demo client distinguishes the two by
            # status alone.
            raise ApiError(ErrorCode.session_required, "Session cookie missing", status=401)

        # Lookup session
        stmt = select(VisitorSession).where(
            VisitorSession.id == session_id, VisitorSession.verified_at.is_not(None)
        )
        res = await db.execute(stmt)
        visitor = res.scalar_one_or_none()

        if not visitor:
            raise ApiError(ErrorCode.session_required, "Invalid or unverified session", status=401)

        stmt_proj = select(Project).where(Project.id == visitor.project_id)
        res_proj = await db.execute(stmt_proj)
        project = res_proj.scalar_one_or_none()
        if not project:
            raise ApiError(ErrorCode.session_required, "Project not found", status=401)
        return project
    else:
        # Local mode: return the default project
        stmt = select(Project).order_by(Project.created_at.asc()).limit(1)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=500, detail="Default project not found")
        return project
