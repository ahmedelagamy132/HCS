from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.database import get_db_connection
from app.schemas.horses import HorseCreate
import random
import string

router = APIRouter(prefix="/api/horses", tags=["horses"])

def generate_horse_code():
    return 'HRS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.get("/")
async def get_horses(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        records = await conn.fetch("SELECT * FROM public.v_horse_summary ORDER BY created_at DESC")
        return [dict(record) for record in records]
    except Exception as e:
        print(f"DB Error fetching horses: {e}")
        return []

@router.post("/")
async def create_horse(horse: HorseCreate, conn: asyncpg.Connection = Depends(get_db_connection)):
    horse_code = generate_horse_code()
    try:
        await conn.execute(
            """INSERT INTO horses (horse_code, name, breed, color, health_status, is_active)
               VALUES ($1, $2, $3, $4, 'good', true)""",
            horse_code, horse.name, horse.breed, horse.color
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))