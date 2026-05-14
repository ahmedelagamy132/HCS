from fastapi import APIRouter, Depends, HTTPException, Request
import asyncpg
import hashlib
import secrets
from app.database import get_db_connection
from app.schemas.owners import OwnerLogin

router = APIRouter(prefix="/api/user", tags=["owner-portal"])


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def _get_owner_from_token(request: Request, conn: asyncpg.Connection):
    """Extract and validate the client/owner token from the request."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    raw_token = auth_header.split(" ")[1]
    token_hash = _hash_token(raw_token)

    row = await conn.fetchrow(
        """
        SELECT c.id, c.client_code, c.full_name, c.email, c.region, c.city
        FROM client_sessions s
        JOIN clients c ON s.client_id = c.id
        WHERE s.token_hash = $1 AND s.is_valid = TRUE AND s.expires_at > NOW()
        """,
        token_hash
    )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return dict(row)


@router.post("/login")
async def owner_login(login_data: OwnerLogin, request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    # Look up client by email, verify password with pgcrypto crypt()
    row = await conn.fetchrow(
        """
        SELECT id, client_code, full_name, email, region, city, photo_url
        FROM clients
        WHERE email = $1
          AND password_hash IS NOT NULL
          AND password_hash = crypt($2, password_hash)
          AND status = 'active'
        """,
        login_data.email, login_data.password
    )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    await conn.execute(
        """
        INSERT INTO client_sessions (client_id, token_hash, ip_address, user_agent, expires_at)
        VALUES ($1, $2, $3, $4, NOW() + INTERVAL '7 days')
        """,
        row["id"], token_hash, client_ip, user_agent
    )

    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "user": {
            "id": str(row["id"]),
            "full_name": row["full_name"],
            "email": row["email"],
            "client_code": row["client_code"],
            "photo_url": row["photo_url"],
        }
    }


@router.get("/me")
async def get_me(request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    owner = await _get_owner_from_token(request, conn)
    return owner


@router.post("/logout")
async def owner_logout(request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": True}

    raw_token = auth_header.split(" ")[1]
    token_hash = _hash_token(raw_token)

    await conn.execute(
        "UPDATE client_sessions SET is_valid = FALSE, revoked_at = NOW() WHERE token_hash = $1",
        token_hash
    )
    return {"success": True}


@router.get("/stables")
async def get_my_stables(request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    owner = await _get_owner_from_token(request, conn)

    rows = await conn.fetch(
        """
        SELECT
            s.id,
            s.stable_code,
            s.name,
            s.city,
            s.region,
            s.country,
            s.address,
            COUNT(h.id) FILTER (WHERE h.is_active = TRUE) AS horse_count,
            COUNT(h.id) FILTER (WHERE h.is_active = TRUE AND h.health_status IN ('fair','poor','critical')) AS attention_count
        FROM stables s
        JOIN horses h ON h.stable_id = s.id
        WHERE h.owner_id = $1::uuid AND h.is_active = TRUE
        GROUP BY s.id, s.stable_code, s.name, s.city, s.region, s.country, s.address
        ORDER BY s.name
        """,
        owner["id"]
    )

    STABLE_LOGOS = {
        "STB-ERS": "/user/assets/egyptian-riding-school.png",
    }

    STABLE_IMAGES = {
        "STB-ERS": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=1200&q=80",
    }

    return [
        {
            "id": str(r["id"]),
            "code": r["stable_code"],
            "name": r["name"],
            "city": r["city"],
            "region": r["region"],
            "country": r["country"],
            "address": r["address"],
            "horse_count": r["horse_count"],
            "attention_count": r["attention_count"],
            "logo": STABLE_LOGOS.get(r["stable_code"]),
            "image": STABLE_IMAGES.get(r["stable_code"], "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=1200&q=80"),
        }
        for r in rows
    ]


@router.get("/horses")
async def get_my_horses(request: Request, conn: asyncpg.Connection = Depends(get_db_connection), stable: str = ""):
    owner = await _get_owner_from_token(request, conn)

    if stable:
        rows = await conn.fetch(
            """
            SELECT
                h.id,
                h.horse_code   AS code,
                h.name,
                h.breed,
                h.gender::text AS gender,
                EXTRACT(YEAR FROM age(NOW(), h.date_of_birth))::int AS age,
                h.color,
                h.weight_kg,
                h.height_cm,
                s.name         AS stable,
                s.stable_code  AS stable_code,
                h.health_status::text AS health,
                h.rtsp_url     AS rtsp_url,
                h.is_active,
                h.created_at
            FROM horses h
            LEFT JOIN stables s ON h.stable_id = s.id
            WHERE h.owner_id = $1::uuid AND h.is_active = TRUE AND s.stable_code = $2
            ORDER BY h.created_at DESC
            """,
            owner["id"], stable
        )
    else:
        rows = await conn.fetch(
            """
            SELECT
                h.id,
                h.horse_code   AS code,
                h.name,
                h.breed,
                h.gender::text AS gender,
                EXTRACT(YEAR FROM age(NOW(), h.date_of_birth))::int AS age,
                h.color,
                h.weight_kg,
                h.height_cm,
                s.name         AS stable,
                s.stable_code  AS stable_code,
                h.health_status::text AS health,
                h.rtsp_url     AS rtsp_url,
                h.is_active,
                h.created_at
            FROM horses h
            LEFT JOIN stables s ON h.stable_id = s.id
            WHERE h.owner_id = $1::uuid AND h.is_active = TRUE
            ORDER BY h.created_at DESC
            """,
            owner["id"]
        )

    HEALTH_MAP = {
        "excellent": "Healthy",
        "good": "Healthy",
        "fair": "Observation",
        "critical": "Critical",
        "observation": "Observation"
    }

    RTSP_URLS = {
        "HRS-101": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "HRS-102": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "HRS-103": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "HRS-104": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "HRS-ERS-01": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
    }

    IMAGES = {
        "HRS-101": "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800&q=80",
        "HRS-102": "https://images.unsplash.com/photo-1534773728080-33d31da27ae5?w=800&q=80",
        "HRS-103": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&q=80",
        "HRS-104": "https://images.unsplash.com/photo-1501700493788-fa1a2fc9fc62?w=800&q=80",
        "HRS-ERS-01": "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=800&q=80",
    }

    STABLE_LOGOS = {
        "STB-ERS": "/user/assets/egyptian-riding-school.png",
    }

    def _health_txt(hs):
        return HEALTH_MAP.get(hs, "Healthy")

    def _vitals(hs):
        base = {
            "excellent": {"hr": 40, "temp": 37.7, "resp": 13, "activity": 80},
            "good": {"hr": 43, "temp": 37.9, "resp": 15, "activity": 65},
            "fair": {"hr": 48, "temp": 38.2, "resp": 18, "activity": 50},
            "critical": {"hr": 62, "temp": 39.5, "resp": 26, "activity": 30},
            "observation": {"hr": 46, "temp": 38.0, "resp": 17, "activity": 55},
        }
        return base.get(hs, {"hr": 42, "temp": 37.8, "resp": 14, "activity": 70})

    horses = []
    for r in rows:
        code = r["code"]
        hs = r["health"]
        horses.append({
            "id": str(r["id"]),
            "code": code,
            "name": r["name"],
            "breed": r["breed"] or "Arabian",
            "gender": r["gender"] or "Stallion",
            "age": r["age"] or 5,
            "color": r["color"] or "Bay",
            "weight_kg": float(r["weight_kg"]) if r["weight_kg"] else None,
            "height_cm": float(r["height_cm"]) if r["height_cm"] else None,
            "stable": r["stable"] or "Egyptian Riding School",
            "stable_code": r["stable_code"] or "STB-ERS",
            "stable_logo": STABLE_LOGOS.get(r["stable_code"] or "STB-ERS", None),
            "box": "B-01",
            "stable_full": f"{r['stable'] or 'Egyptian Riding School'} · Box B-01",
            "registered": r["created_at"].strftime("%b %Y") if r["created_at"] else "Jan 2024",
            "health": hs,
            "healthTxt": _health_txt(hs),
            "lastCheck": "1 hour ago",
            "stream": "live",
            "cam": code[4:7] if len(code) > 5 else "D12",
            "rtspUrl": r["rtsp_url"] or RTSP_URLS.get(code, RTSP_URLS["HRS-101"]),
            "image": IMAGES.get(code, IMAGES["HRS-101"]),
            "vitals": _vitals(hs),
        })

    return horses


@router.get("/horses/{horse_id}")
async def get_horse(horse_id: str, request: Request, conn: asyncpg.Connection = Depends(get_db_connection)):
    owner = await _get_owner_from_token(request, conn)

    row = await conn.fetchrow(
        """
        SELECT
            h.id,
            h.horse_code   AS code,
            h.name,
            h.breed,
            h.gender::text AS gender,
            EXTRACT(YEAR FROM age(NOW(), h.date_of_birth))::int AS age,
            h.color,
            h.weight_kg,
            h.height_cm,
            s.name         AS stable,
            s.stable_code  AS stable_code,
            h.health_status::text AS health,
            h.rtsp_url     AS rtsp_url,
            h.created_at
        FROM horses h
        LEFT JOIN stables s ON h.stable_id = s.id
        WHERE h.id = $1::uuid AND h.owner_id = $2::uuid
        """,
        horse_id, owner["id"]
    )

    if not row:
        raise HTTPException(status_code=404, detail="Horse not found")

    code = row["code"]
    hs = row["health"]
    HEALTH_MAP = {"excellent": "Healthy", "good": "Healthy", "fair": "Observation", "critical": "Critical", "observation": "Observation"}

    return {
        "id": str(row["id"]),
        "code": code,
        "name": row["name"],
        "breed": row["breed"] or "Arabian",
        "gender": row["gender"] or "Stallion",
        "age": row["age"] or 5,
        "color": row["color"] or "Bay",
        "weight_kg": float(row["weight_kg"]) if row["weight_kg"] else None,
        "height_cm": float(row["height_cm"]) if row["height_cm"] else None,
        "stable": row["stable"] or "Al-Rayyan",
        "stable_code": row["stable_code"] or "STB-001",
        "box": code[4:7] if len(code) > 5 else "D-12",
        "stableFull": f"{row['stable'] or 'Al-Rayyan'} Stable · Block {code[4] if len(code)>4 else 'D'}, Box {code[5:7] if len(code)>5 else '12'}",
        "registered": row["created_at"].strftime("%b %Y") if row["created_at"] else "Jan 2024",
        "health": hs,
        "healthTxt": HEALTH_MAP.get(hs, "Healthy"),
        "lastCheck": "1 hour ago",
        "cam": code[4:7] if len(code) > 5 else "D12",
        "rtspUrl": row["rtsp_url"] or "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
    }
