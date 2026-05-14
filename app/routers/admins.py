from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.database import get_db_connection
from app.schemas.admins import AdminCreate
import random
import string

router = APIRouter(prefix="/api/admins", tags=["admins"])

def generate_admin_code():
    return 'ADM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

from pydantic import BaseModel

class AdminLogin(BaseModel):
    email: str
    password: str
    rememberMe: bool = False

@router.post("/login")
async def login_admin(login_data: AdminLogin, conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        # Check if the password matches using pgcrypto's crypt() function
        query = "SELECT id, full_name, email, role, is_active FROM admin_users WHERE email = $1 AND password_hash = crypt($2, password_hash)"
        user = await conn.fetchrow(query, login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        if not user['is_active']:
            raise HTTPException(status_code=403, detail="Account is inactive")
            
        # Update last login time
        await conn.execute("UPDATE admin_users SET last_login_at = NOW(), login_count = login_count + 1 WHERE id = $1", user['id'])
        
        # Here we should ideally generate a JWT token. For simplicity given the scope, return a basic fake access token or simple string.
        import uuid
        access_token = str(uuid.uuid4())
        
        return {
            "access_token": access_token,
            "user": {
                "id": str(user['id']),
                "full_name": user['full_name'],
                "email": user['email'],
                "role": user['role']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"DB Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def get_admins(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        records = await conn.fetch("SELECT id, admin_code, full_name, email, role, is_active, created_at FROM admin_users ORDER BY created_at DESC")
        return [dict(record) for record in records]
    except Exception as e:
        print(f"DB Error fetching admins: {e}")
        return []

@router.post("/")
async def create_admin(admin: AdminCreate, conn: asyncpg.Connection = Depends(get_db_connection)):
    admin_code = generate_admin_code()
    
    db_role = 'view_only'
    if admin.role:
        rl = admin.role.lower()
        if 'super' in rl:
            db_role = 'super_admin'
        elif any(r in rl for r in ['staff', 'system', 'admin']):
            db_role = 'staff_admin'
            
    password = admin.password if admin.password else 'welcome123'
    
    try:
        await conn.execute(
            """INSERT INTO admin_users (admin_code, full_name, email, role, password_hash)
               VALUES ($1, $2, $3, $4, crypt($5, gen_salt('bf',12)))""",
            admin_code, admin.full_name, admin.email, db_role, password
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))