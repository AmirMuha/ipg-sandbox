"""Authentication API routes: registration, login, session inspection, and OAuth (004-launch-readiness-flows)."""

import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import seed_configs
from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode
from src.config import Settings, dashboard_base_url
from src.models import (
    AdapterConfig,
    Project,
    UsageMeter,
    User,
    UserSession,
    utcnow,
)
from src.services.auth import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from src.services.oauth import exchange_github_code, exchange_google_code

router = APIRouter(prefix="/api/v1/auth")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


def _set_session_cookie(response: Response, token: str, days: int) -> None:
    response.set_cookie(
        key="ipg_session",
        value=token,
        max_age=days * 24 * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )


async def get_current_user_and_session(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> tuple[User, UserSession]:
    token = request.cookies.get("ipg_session")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise ApiError(ErrorCode.session_required, "Authentication required", status=401)

    token_hash = hash_session_token(token)
    stmt = (
        select(UserSession)
        .where(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > utcnow(),
        )
    )
    user_session = await db.scalar(stmt)
    if not user_session:
        raise ApiError(ErrorCode.session_required, "Session expired or invalid", status=401)

    user = await db.get(User, user_session.user_id)
    if not user:
        raise ApiError(ErrorCode.session_required, "User not found", status=401)

    return user, user_session


@router.post("/register", status_code=201)
async def register(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise ApiError(ErrorCode.validation_error, "Invalid JSON body", status=422)

    raw_email = body.get("email")
    raw_password = body.get("password")
    full_name = body.get("full_name")

    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        raise ApiError(ErrorCode.validation_error, "Email and password are required", status=422)

    email = raw_email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(ErrorCode.validation_error, "Invalid email format", status=422)

    if len(raw_password) < 8:
        raise ApiError(ErrorCode.validation_error, "Password must be at least 8 characters", status=422)

    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(ErrorCode.validation_error, "Email is already registered", status=400)

    settings = Settings.from_env()
    user = User(
        email=email,
        password_hash=hash_password(raw_password),
        auth_provider="local",
        full_name=full_name.strip() if isinstance(full_name, str) and full_name.strip() else None,
    )
    db.add(user)
    await db.flush()

    project = Project(
        name=f"{user.full_name or user.email}'s workspace",
        user_id=user.id,
        tier="developer",
        daily_requests_cap=100,
        max_active_adapters=2,
        history_cap=settings.history_cap,
        webhook_retry_max=settings.webhook_retry_max,
        pending_settle_delay_s=settings.pending_settle_delay_s,
        timeout_delay_s=settings.timeout_delay_s,
    )
    db.add(project)
    await db.flush()

    configs = [AdapterConfig(**kw) for kw in seed_configs(project.id)]
    db.add_all(configs)

    meter = UsageMeter(
        project_id=project.id,
        requests_total=0,
        requests_today=0,
        transactions_total=0,
        history_retained=0,
    )
    db.add(meter)

    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=utcnow() + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    await db.commit()

    _set_session_cookie(response, token, settings.session_ttl_days)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": user.auth_provider,
            "created_at": user.created_at.isoformat(),
        },
        "project": {
            "id": str(project.id),
            "name": project.name,
            "tier": project.tier,
            "daily_requests_cap": project.daily_requests_cap,
            "max_active_adapters": project.max_active_adapters,
        },
        "token": token,
    }


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise ApiError(ErrorCode.validation_error, "Invalid JSON body", status=422)

    raw_email = body.get("email")
    raw_password = body.get("password")
    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        raise ApiError(ErrorCode.validation_error, "Email and password are required", status=422)

    email = raw_email.strip().lower()
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.password_hash or not verify_password(raw_password, user.password_hash):
        raise ApiError(ErrorCode.invalid_credentials, "Invalid email or password", status=401)

    settings = Settings.from_env()
    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=utcnow() + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    await db.commit()

    _set_session_cookie(response, token, settings.session_ttl_days)

    project = await db.scalar(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.asc()).limit(1)
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": user.auth_provider,
        },
        "project": {
            "id": str(project.id) if project else None,
            "name": project.name if project else None,
            "tier": project.tier if project else "developer",
        },
        "token": token,
    }


@router.get("/me")
async def me(
    user_and_session: Annotated[tuple[User, UserSession], Depends(get_current_user_and_session)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    user, _ = user_and_session
    project = await db.scalar(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.asc()).limit(1)
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": user.auth_provider,
        },
        "project": {
            "id": str(project.id) if project else None,
            "name": project.name if project else None,
            "tier": project.tier if project else "developer",
            "daily_requests_cap": project.daily_requests_cap if project else 100,
            "max_active_adapters": project.max_active_adapters if project else 2,
        },
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    token = request.cookies.get("ipg_session")
    if token:
        token_hash = hash_session_token(token)
        session = await db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))
        if session:
            await db.delete(session)
            await db.commit()

    response.delete_cookie(key="ipg_session", path="/")
    return {"status": "ok"}


@router.get("/oauth/{provider}")
async def oauth_redirect(provider: str) -> RedirectResponse:
    settings = Settings.from_env()
    state = generate_session_token()[:16]

    if provider == "github":
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        resp = RedirectResponse(url=url, status_code=302)
        resp.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax", path="/")
        return resp
    elif provider == "google":
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        resp = RedirectResponse(url=url, status_code=302)
        resp.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax", path="/")
        return resp
    else:
        raise ApiError(ErrorCode.validation_error, f"Unsupported OAuth provider: {provider}", status=400)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise ApiError(ErrorCode.invalid_credentials, "OAuth state mismatch or expired", status=401)

    settings = Settings.from_env()
    if provider == "github":
        profile = await exchange_github_code(code, settings)
    elif provider == "google":
        profile = await exchange_google_code(code, settings)
    else:
        raise ApiError(ErrorCode.validation_error, f"Unsupported OAuth provider: {provider}", status=400)

    oauth_id = profile["oauth_id"]
    email = profile["email"].lower()
    full_name = profile.get("full_name")

    user = await db.scalar(
        select(User).where(User.auth_provider == provider, User.oauth_id == oauth_id)
    )
    if not user:
        user = await db.scalar(select(User).where(User.email == email))

    if not user:
        user = User(
            email=email,
            auth_provider=provider,
            oauth_id=oauth_id,
            full_name=full_name,
        )
        db.add(user)
        await db.flush()

        project = Project(
            name=f"{user.full_name or user.email}'s workspace",
            user_id=user.id,
            tier="developer",
            daily_requests_cap=100,
            max_active_adapters=2,
            history_cap=settings.history_cap,
            webhook_retry_max=settings.webhook_retry_max,
            pending_settle_delay_s=settings.pending_settle_delay_s,
            timeout_delay_s=settings.timeout_delay_s,
        )
        db.add(project)
        await db.flush()

        configs = [AdapterConfig(**kw) for kw in seed_configs(project.id)]
        db.add_all(configs)
        meter = UsageMeter(project_id=project.id, requests_total=0, requests_today=0)
        db.add(meter)
    else:
        if not user.oauth_id:
            user.oauth_id = oauth_id
            user.auth_provider = provider

    token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=utcnow() + timedelta(days=settings.session_ttl_days),
    )
    db.add(session)
    await db.commit()

    dashboard_url = dashboard_base_url()
    resp = RedirectResponse(url=f"{dashboard_url}/fa/console", status_code=302)
    _set_session_cookie(resp, token, settings.session_ttl_days)
    resp.delete_cookie("oauth_state", path="/")
    return resp
