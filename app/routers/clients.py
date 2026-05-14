from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.database import get_db_connection
from app.schemas.clients import ClientCreate
import random
import string

router = APIRouter(prefix="/api/clients", tags=["clients"])

def generate_client_code():
    return 'CLT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.get("/")
async def get_clients(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        records = await conn.fetch(
            """
            SELECT
                c.id,
                c.client_code,
                c.full_name,
                c.email,
                c.phone,
                c.region,
                c.country,
                c.city,
                c.status::text AS status,
                (c.password_hash IS NOT NULL) AS has_login,
                COALESCE(c.stable_count, 0) AS stable_count,
                COALESCE(c.horse_count, 0)  AS horse_count,
                c.created_at,
                c.updated_at
            FROM clients c
            ORDER BY c.created_at DESC
            """
        )
        return [dict(record) for record in records]
    except Exception as e:
        print(f"DB Error fetching clients: {e}")
        return []

@router.post("/")
async def create_client(client: ClientCreate, conn: asyncpg.Connection = Depends(get_db_connection)):
    client_code = generate_client_code()
    try:
        if client.password:
            await conn.execute(
                """INSERT INTO clients (client_code, full_name, email, phone, region, status, password_hash)
                   VALUES ($1, $2, $3, $4, $5, 'active', crypt($6, gen_salt('bf',12)))""",
                client_code, client.full_name, client.email, client.phone, client.region, client.password
            )
        else:
            await conn.execute(
                """INSERT INTO clients (client_code, full_name, email, phone, region, status)
                   VALUES ($1, $2, $3, $4, $5, 'active')""",
                client_code, client.full_name, client.email, client.phone, client.region
            )
        return {"success": True, "client_code": client_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))