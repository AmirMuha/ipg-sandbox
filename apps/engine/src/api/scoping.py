import os
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.project import Project, ProjectKind
from src.models.visitor import VisitorSession
from src.api.errors import ApiError, ErrorCode

async def get_current_project(request: Request, db: AsyncSession) -> Project:
    profile = os.environ.get("ENGINE_PROFILE", "local")
    
    if profile == "demo":
        session_id = request.cookies.get("demo_session")
        if not session_id:
            raise ApiError(ErrorCode.session_required, "Session cookie missing")
            
        # Lookup session
        stmt = select(VisitorSession).where(
            VisitorSession.id == session_id,
            VisitorSession.verified_at.is_not(None)
        )
        res = await db.execute(stmt)
        visitor = res.scalar_one_or_none()
        
        if not visitor:
            raise ApiError(ErrorCode.session_required, "Invalid or unverified session")
            
        stmt_proj = select(Project).where(Project.id == visitor.project_id)
        res_proj = await db.execute(stmt_proj)
        project = res_proj.scalar_one_or_none()
        if not project:
            raise ApiError(ErrorCode.session_required, "Project not found")
        return project
    else:
        # Local mode: return the default project
        stmt = select(Project).order_by(Project.created_at.asc()).limit(1)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=500, detail="Default project not found")
        return project
