from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.database import get_db_connection
from app.schemas.stables import StableCreate
import random
import string

router = APIRouter(prefix="/api/stables", tags=["stables"])

def generate_stable_code():
    return 'STB-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.get("/")
async def get_stables(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        records = await conn.fetch(
            """
            SELECT
                s.id,
                s.stable_code,
                s.name,
                s.address,
                s.city,
                s.region,
                s.country,
                s.capacity,
                s.occupied,
                s.status::text AS status,
                s.owner_id,
                o.full_name      AS owner_name,
                o.client_code    AS owner_code,
                (SELECT COUNT(*) FROM horses h WHERE h.stable_id = s.id AND h.is_active = TRUE) AS horse_count,
                s.created_at,
                s.updated_at
            FROM stables s
            LEFT JOIN clients o ON s.owner_id = o.id
            ORDER BY s.created_at DESC
            """
        )
        return [dict(record) for record in records]
    except Exception as e:
        print(f"DB Error fetching stables: {e}")
        return []

@router.post("/")
async def create_stable(stable: StableCreate, conn: asyncpg.Connection = Depends(get_db_connection)):
    stable_code = generate_stable_code()
    try:
        await conn.execute(
            """INSERT INTO stables (stable_code, name, city, capacity, status)
               VALUES ($1, $2, $3, $4, 'active')""",
            stable_code, stable.name, stable.location, stable.capacity
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))