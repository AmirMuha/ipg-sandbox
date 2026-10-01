import os
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
import httpx
from fastapi import FastAPI, Request, HTTPException, Response, Cookie
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="IPG Sandbox Demo Proxy")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ipg_sandbox")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# In-memory rate limits
signup_limits = {}

class SignupRequest(BaseModel):
    email: str

class VerifyRequest(BaseModel):
    token: str

@app.post("/demo/signup")
async def signup(req: SignupRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    
    limits = signup_limits.setdefault(req.email, {"count": 0, "reset_at": now + timedelta(minutes=10)})
    if now > limits["reset_at"]:
        limits["count"] = 0
        limits["reset_at"] = now + timedelta(minutes=10)
    
    if limits["count"] >= 3:
        raise HTTPException(status_code=429, detail="rate_limited")
    
    limits["count"] += 1
    
    token = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    with SessionLocal() as db:
        # Create project if not exists
        project_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO projects (id, name, kind, default_scenario, history_cap, webhook_retry_max, pending_settle_delay_s, timeout_delay_s, created_at)
            VALUES (:id, :name, 'demo', 'approve', 1000, 3, 5, 30, now())
        """), {"id": project_id, "name": f"demo-{req.email}"})
        
        # Insert visitor session
        session_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO visitor_sessions (id, project_id, email, magic_link_token_hash, created_at)
            VALUES (:id, :project_id, :email, :token_hash, now())
        """), {"id": session_id, "project_id": project_id, "email": req.email, "token_hash": token_hash})
        db.commit()
    
    print(f"DEV MAGIC LINK: /demo/verify?token={token}")
    return {"status": "magic_link_sent", "dev_token": token}

@app.post("/demo/verify")
async def verify(req: VerifyRequest, response: Response):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    
    with SessionLocal() as db:
        res = db.execute(text("""
            SELECT id, project_id FROM visitor_sessions 
            WHERE magic_link_token_hash = :hash AND verified_at IS NULL
        """), {"hash": token_hash}).fetchone()
        
        if not res:
            raise HTTPException(status_code=400, detail="invalid_token")
            
        session_id, project_id = res
        db.execute(text("""
            UPDATE visitor_sessions SET verified_at = now() WHERE id = :id
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
