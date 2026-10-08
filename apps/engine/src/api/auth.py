"""Authentication API routes: registration, login, session inspection, and OAuth (004-launch-readiness-flows)."""

import logging
import re
import secrets
from datetime import timedelta
from typing import Annotated, Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import seed_configs
from src.api.db import get_session
from src.api.errors import ApiError, ErrorCode
from src.api.scoping import get_current_user
from src.config import Settings, dashboard_base_url
from src.core.security import generate_api_key, hash_api_key
from src.models import (
    AdapterConfig,
    EmailVerification,
    Project,
    UsageMeter,
    User,
    UserSession,
    utcnow,
)
from src.models.api_key import ApiKey
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


logger = logging.getLogger(__name__)


@router.post("/otp/send")
async def send_otp(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise ApiError(ErrorCode.validation_error, "Invalid JSON body", status=422)

    raw_email = body.get("email")
    if not isinstance(raw_email, str):
        raise ApiError(ErrorCode.validation_error, "ایمیل الزامی است", status=422)

    email = raw_email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(ErrorCode.validation_error, "قالب ایمیل معتبر نیست", status=422)

    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(ErrorCode.validation_error, "این ایمیل قبلاً ثبت‌نام کرده است", status=400)

    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = utcnow() + timedelta(minutes=5)

    verification = EmailVerification(
        email=email,
        code=code,
        expires_at=expires_at,
    )
    db.add(verification)
    await db.commit()

    from src.services.email import send_otp_email

    send_otp_email(email, code)

    return {
        "status": "sent",
        "resend_in_seconds": 60,
    }


@router.post("/otp/verify")
async def verify_otp(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise ApiError(ErrorCode.validation_error, "Invalid JSON body", status=422)

    raw_email = body.get("email")
    raw_code = body.get("code")
    if not isinstance(raw_email, str) or not isinstance(raw_code, str):
        raise ApiError(ErrorCode.validation_error, "ایمیل و کد تأیید الزامی است", status=422)

    email = raw_email.strip().lower()
    code = raw_code.strip()

    stmt = (
        select(EmailVerification)
        .where(
            EmailVerification.email == email,
            EmailVerification.code == code,
            EmailVerification.expires_at > utcnow(),
        )
        .order_by(EmailVerification.created_at.desc())
        .limit(1)
    )
    verification = await db.scalar(stmt)
    if not verification:
        raise ApiError(ErrorCode.validation_error, "کد تأیید نامعتبر یا منقضی شده است", status=400)

    verification_token = secrets.token_hex(32)
    verification.verified_at = utcnow()
    verification.verification_token = verification_token
    await db.commit()

    return {
        "verified": True,
        "verification_token": verification_token,
    }


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
    raw_confirm = body.get("password_confirmation")
    full_name = body.get("full_name")
    raw_token = body.get("verification_token")

    if not isinstance(raw_email, str) or not isinstance(raw_password, str):
        raise ApiError(ErrorCode.validation_error, "ایمیل و رمز عبور الزامی است", status=422)

    if raw_confirm is not None and raw_password != raw_confirm:
        raise ApiError(ErrorCode.validation_error, "رمز عبور با تکرار آن یکسان نیست", status=422)

    email = raw_email.strip().lower()
    if not EMAIL_RE.match(email):
        raise ApiError(ErrorCode.validation_error, "قالب ایمیل معتبر نیست", status=422)

    if len(raw_password) < 8:
        raise ApiError(ErrorCode.validation_error, "رمز عبور باید حداقل ۸ نویسه باشد", status=422)

    if raw_token:
        v_stmt = select(EmailVerification).where(
            EmailVerification.email == email,
            EmailVerification.verification_token == raw_token,
            EmailVerification.verified_at.is_not(None),
        )
        v = await db.scalar(v_stmt)
        if not v:
            raise ApiError(ErrorCode.validation_error, "اعتبار تأییدیه ایمیل یافت نشد", status=400)

    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(ErrorCode.validation_error, "این ایمیل قبلاً ثبت نام کرده است", status=400)

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
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.asc())
        .limit(1)
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": user.auth_provider,
            "is_admin": user.email.lower() in Settings.from_env().admin_emails,
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
    user: Annotated[User | None, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    if not user:
        raise ApiError(ErrorCode.session_required, "Authentication required", status=401)
    project = await db.scalar(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.asc())
        .limit(1)
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": user.auth_provider,
            "is_admin": user.email.lower() in Settings.from_env().admin_emails,
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


@router.post("/api-keys", status_code=201)
async def create_api_key(
    request: Request,
    user_and_session: Annotated[tuple[User, UserSession], Depends(get_current_user_and_session)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    user, _ = user_and_session
    try:
        body = await request.json()
    except Exception:
        raise ApiError(ErrorCode.validation_error, "Invalid JSON body", status=422)

    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiError(ErrorCode.validation_error, "Name is required", status=422)

    # Check limit (max 10)
    count_stmt = select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.revoked_at.is_(None))
    active_keys = await db.scalars(count_stmt)
    if len(active_keys.all()) >= 10:
        raise ApiError(ErrorCode.validation_error, "API key limit reached (10)", status=400)

    token = generate_api_key()
    api_key = ApiKey(
        user_id=user.id,
        name=name.strip(),
        key_hash=hash_api_key(token),
        last_four=token[-4:]
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "data": {
            "id": str(api_key.id),
            "name": api_key.name,
            "token": token,
            "last_four": api_key.last_four,
            "created_at": api_key.created_at.isoformat(),
        }
    }

@router.get("/api-keys")
async def list_api_keys(
    user_and_session: Annotated[tuple[User, UserSession], Depends(get_current_user_and_session)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    user, _ = user_and_session
    stmt = select(ApiKey).where(
        ApiKey.user_id == user.id,
        ApiKey.revoked_at.is_(None)
    ).order_by(ApiKey.created_at.desc())
    keys = await db.scalars(stmt)

    return {
        "data": [
            {
                "id": str(k.id),
                "name": k.name,
                "last_four": k.last_four,
                "created_at": k.created_at.isoformat(),
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            }
            for k in keys
        ]
    }

@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: UUID,
    user_and_session: Annotated[tuple[User, UserSession], Depends(get_current_user_and_session)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    user, _ = user_and_session
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    api_key = await db.scalar(stmt)
    
    if not api_key or api_key.revoked_at is not None:
        raise ApiError(ErrorCode.not_found, "API key not found", status=404)
        
    api_key.revoked_at = utcnow()
    await db.commit()
