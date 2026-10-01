import os
import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
import httpx
from fastapi import FastAPI, Request, HTTPException, Response, Cookie
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="IPG Sandbox Demo Proxy")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/ipg_sandbox")

# T072: a SQLite URL lets the demo run under test. Postgres is the production path (the raw
# SQL below uses JSONB casts), so this is opt-in and only used where DATABASE_URL says so.
_SQLITE = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _SQLITE else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _now_sql() -> str:
    """`now()` on Postgres, a literal CURRENT_TIMESTAMP elsewhere (T072)."""
    return "now()" if not _SQLITE else "CURRENT_TIMESTAMP"


def _jsonb_sql(param: str = ":creds") -> str:
    """`CAST(x AS JSONB)` on Postgres; SQLite stores JSONB columns as TEXT (T072)."""
    return f"CAST({param} AS JSONB)" if not _SQLITE else param


def _utcnow_sql() -> str:
    """A UTC timestamp string in a format that sorts correctly on every backend.

    Written as a bound parameter rather than a SQL literal so it is compared against a value of
    exactly the same shape. Under SQLite, `CURRENT_TIMESTAMP` renders as
    `'2026-10-01 10:50:26'` while a Python `isoformat()` is `'2026-10-01T09:50:26.014631+00:00'`;
    comparing those as strings made an already-expired token look valid (T071/T072).
    """
    if _SQLITE:
        return f"'{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}'"
    return "now()"

# In-memory rate limits
signup_limits = {}

class SignupRequest(BaseModel):
    email: str

class VerifyRequest(BaseModel):
    token: str

# --- Magic-link delivery (T069) -------------------------------------------------------
# T053 specifies "dev transport logs link, prod SMTP via env". Only the dev branch existed, so
# the token came back in the response body and the email gate was bypassable without ever
# reading an email. SMTP_* being set is the switch: no SMTP configured -> dev transport, and
# the token is only echoed then.
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@ipg-sandbox.local")
MAGIC_LINK_BASE_URL = os.environ.get("MAGIC_LINK_BASE_URL", "")
# T071: links are single-use *and* expiring.
MAGIC_LINK_TTL_MINUTES = int(os.environ.get("MAGIC_LINK_TTL_MINUTES", "30"))


def deliver_magic_link(email: str, token: str) -> None:
    """Send the magic link over SMTP, or log it when SMTP is not configured.

    Raises `RuntimeError` on a configured-but-failing SMTP transport, so a real deployment
    surfaces a broken mail path instead of silently dropping the email.
    """
    link = f"{MAGIC_LINK_BASE_URL}/demo/verify?token={token}" if MAGIC_LINK_BASE_URL else (
        f"/demo/verify?token={token}"
    )
    if not SMTP_HOST:
        print(f"DEV MAGIC LINK for {email}: {link}")
        return

    import smtplib
    from email.message import EmailMessage

    message = EmailMessage()
    message["Subject"] = "Your IPG Sandbox demo sign-in link"
    message["From"] = SMTP_FROM
    message["To"] = email
    message.set_content(
        f"Use this link to sign in to the IPG Sandbox demo:\n\n{link}\n\n"
        f"It expires in {MAGIC_LINK_TTL_MINUTES} minutes and can be used once."
    )
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)


# --- Rate limiting (T070) ---------------------------------------------------------------
SIGNUP_LIMIT_MAX = int(os.environ.get("SIGNUP_LIMIT_MAX", "3"))
SIGNUP_LIMIT_WINDOW_MINUTES = int(os.environ.get("SIGNUP_LIMIT_WINDOW_MINUTES", "10"))


def _check_signup_limit(key: str, now: datetime) -> None:
    """Rate-limit `key`, resetting once its window has passed.

    T070: this was keyed on the submitted email, which is attacker-chosen and unverified —
    varying the address defeated it entirely. The key must be something the caller cannot
    forge, so signup keys on the client IP. The email is still limited, so one address cannot
    be hammered from many IPs.
    """
    limits = signup_limits.setdefault(
        key, {"count": 0, "reset_at": now + timedelta(minutes=SIGNUP_LIMIT_WINDOW_MINUTES)}
    )
    if now > limits["reset_at"]:
        limits["count"] = 0
        limits["reset_at"] = now + timedelta(minutes=SIGNUP_LIMIT_WINDOW_MINUTES)

    if limits["count"] >= SIGNUP_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="rate_limited")

    limits["count"] += 1


@app.post("/demo/signup")
async def signup(req: SignupRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)

    # Both keys: the IP is the trust boundary, the email stops one address being sprayed
    # across many IPs.
    _check_signup_limit(f"ip:{ip}", now)
    _check_signup_limit(f"email:{req.email.lower()}", now)

    token = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    # Bound as a string in the same shape `_utcnow_sql` produces, so the expiry comparison is
    # a like-for-like string compare on SQLite and a real timestamp compare on Postgres.
    expires_at = (now + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    
    with SessionLocal() as db:
        # Create project if not exists
        project_id = str(uuid.uuid4())
        db.execute(text(f"""
            INSERT INTO projects (id, name, kind, default_scenario, history_cap, webhook_retry_max, pending_settle_delay_s, timeout_delay_s, created_at)
            VALUES (:id, :name, 'demo', 'approve', 1000, 3, 5, 30, {_now_sql()})
        """), {"id": project_id, "name": f"demo-{req.email}"})

        # Seed the three sandbox adapters for this visitor's project. Without them every
        # initiate answers `404 adapter zarinpal not found` and the demo flow cannot run a
        # payment at all. Mirrors `_seed_adapters` in the engine's api/app.py.
        for provider, prefix, unit, creds in (
            ("zarinpal", "/zarinpal", "rial", {"merchant_id": "sandbox-merchant"}),
            ("idpay", "/idpay", "toman", {"api_key": "sandbox-key"}),
            (
                "behpardakht",
                "/behpardakht",
                "rial",
                {"terminal_id": 123456, "username": "sandbox", "password": "sandbox"},
            ),
        ):
            db.execute(text(f"""
                INSERT INTO adapter_configs (id, project_id, provider, endpoint_path_prefix, api_unit, credentials)
                VALUES (:id, :project_id, :provider, :prefix, :unit, {_jsonb_sql()})
            """), {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "provider": provider,
                "prefix": prefix,
                "unit": unit,
                "creds": json.dumps(creds),
            })

        # Insert visitor session
        session_id = str(uuid.uuid4())
        db.execute(text(f"""
            INSERT INTO visitor_sessions (id, project_id, email, magic_link_token_hash, expires_at, created_at)
            VALUES (:id, :project_id, :email, :token_hash, :expires_at, {_now_sql()})
        """), {
            "id": session_id,
            "project_id": project_id,
            "email": req.email,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })
        db.commit()

    deliver_magic_link(req.email, token)
    # T069: only echo the token when there is no SMTP transport, so a real deployment cannot
    # have its email gate bypassed by reading the response body.
    if SMTP_HOST:
        return {"status": "magic_link_sent"}
    return {"status": "magic_link_sent", "dev_token": token}

@app.post("/demo/verify")
async def verify(req: VerifyRequest, response: Response):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()

    with SessionLocal() as db:
        # T071: `expires_at IS NULL OR expires_at > now()` — the NULL branch keeps tokens issued
        # before migration 0005 usable rather than locking those visitors out.
        res = db.execute(text(f"""
            SELECT id, project_id FROM visitor_sessions
            WHERE magic_link_token_hash = :hash
              AND verified_at IS NULL
              AND (expires_at IS NULL OR expires_at > {_utcnow_sql()})
        """), {"hash": token_hash}).fetchone()

        if not res:
            raise HTTPException(status_code=400, detail="invalid_token")

        session_id, project_id = res
        db.execute(text(f"""
            UPDATE visitor_sessions SET verified_at = {_now_sql()} WHERE id = :id
        """), {"id": session_id})
        db.commit()
    
    response.set_cookie(
        key="demo_session", 
        value=session_id,
        httponly=True,
        max_age=86400 * 7,
        path="/"
    )
    return {"status": "verified"}

@app.post("/demo/logout")
async def logout(response: Response):
    response.delete_cookie("demo_session", path="/")
    return {"status": "logged_out"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    engine_url = os.environ.get("ENGINE_URL", "http://engine:8080")
    dashboard_url = os.environ.get("DASHBOARD_URL", "http://dashboard:3000")
    
    if path.startswith("api/v1") or path.startswith("zarinpal") or path.startswith("idpay") or path.startswith("behpardakht"):
        target_base = engine_url
    else:
        target_base = dashboard_url
        
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    
    async with httpx.AsyncClient() as client:
        proxy_req = client.build_request(
            request.method,
            f"{target_base}{url}",
            headers=request.headers.raw,
            content=await request.body()
        )
        try:
            proxy_resp = await client.send(proxy_req, stream=True)
            return StreamingResponse(
                proxy_resp.aiter_raw(),
                status_code=proxy_resp.status_code,
                headers=proxy_resp.headers
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Bad Gateway")
