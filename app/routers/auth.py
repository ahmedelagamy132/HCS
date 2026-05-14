from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import asyncpg
import hashlib
import uuid
import secrets
from app.database import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    user = await conn.fetchrow(
        """
        SELECT id, admin_code, full_name, email, role, is_active
        FROM admin_users
        WHERE email = $1 AND password_hash = crypt($2, password_hash)
        """,
        req.email, req.password
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account is disabled")

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    await conn.execute(
        """
        INSERT INTO admin_sessions (admin_id, token_hash, ip_address, user_agent, expires_at)
        VALUES ($1, $2, $3, $4, NOW() + INTERVAL '7 days')
        """,
        user["id"], token_hash, client_ip, user_agent
    )

    await conn.execute(
        "UPDATE admin_users SET last_login_at = NOW(), login_count = login_count + 1 WHERE id = $1",
        user["id"]
    )

    return {"access_token": raw_token, "token_type": "bearer", "role": user["role"]}

@router.get("/account")
@router.get("/me")
async def get_me(request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    raw_token = auth_header.split(" ")[1]
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    user = await conn.fetchrow(
        """
        SELECT u.id, u.admin_code, u.full_name, u.email, u.role, u.login_count, u.last_login_at, u.created_at
        FROM admin_sessions s
        JOIN admin_users u ON s.admin_id = u.id
        WHERE s.token_hash = $1 AND s.is_valid = TRUE AND s.expires_at > NOW()
        """,
        token_hash
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return dict(user)

@router.post("/logout")
async def logout(request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": True}
    
    raw_token = auth_header.split(" ")[1]
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    await conn.execute(
        "UPDATE admin_sessions SET is_valid = FALSE, revoked_at = NOW() WHERE token_hash = $1",
        token_hash
    )

    return {"success": True}

class ProfileUpdate(BaseModel):
    full_name: str
    email: str

class PasswordUpdate(BaseModel):
    password: str

@router.post("/me")
async def update_profile(data: ProfileUpdate, request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    user = await get_me(request, conn)
    await conn.execute("UPDATE admin_users SET full_name = $1, email = $2 WHERE id = $3", data.full_name, data.email, user['id'])
    return {"success": True}

@router.post("/password")
async def update_password(data: PasswordUpdate, request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    user = await get_me(request, conn)
    await conn.execute("UPDATE admin_users SET password_hash = crypt($1, gen_salt('bf',12)) WHERE id = $2", data.password, user['id'])
    return {"success": True}
