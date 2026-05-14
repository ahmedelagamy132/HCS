from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.database import get_db_connection

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/dashboard/charts")
async def get_dashboard_charts(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        alerts_res = await conn.fetch("SELECT severity as type, title, description as detail, created_at FROM health_alerts WHERE status = 'active' ORDER BY created_at DESC LIMIT 5")
        
        bar_items = await conn.fetch(
            """SELECT
                (SELECT COUNT(*) FROM horse_health_records) as health_count,
                (SELECT COUNT(*) FROM gait_analyses) as gait_count,
                (SELECT COUNT(*) FROM behavior_records) as behavior_count,
                (SELECT COUNT(*) FROM diet_plans) as diet_count,
                (SELECT COUNT(*) FROM medical_records) as disease_count"""
        )
        
        reg_res = await conn.fetch(
            """WITH months AS (
              SELECT generate_series(date_trunc('month', current_date) - interval '11 months', date_trunc('month', current_date), '1 month'::interval) as m_start
            )
            SELECT to_char(m.m_start, 'Mon') as month, COUNT(h.id) as count
            FROM months m
            LEFT JOIN horses h ON date_trunc('month', h.created_at) = m.m_start
            GROUP BY m.m_start
            ORDER BY m.m_start"""
        )

        return {
            "alerts": [dict(r) for r in alerts_res],
            "bar": dict(bar_items[0]) if bar_items else {},
            "reg": [dict(r) for r in reg_res]
        }
    except Exception as e:
        print(f"DB Error fetching dashboard charts: {e}")
        return {"alerts": [], "bar": {}, "reg": []}


@router.get("/kpis")
async def get_kpis(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        stats = await conn.fetch("SELECT * FROM public.v_system_kpis LIMIT 1")
        if stats:
            return dict(stats[0])
        return {}
    except Exception as e:
        print(f"DB Error fetching KPIs: {e}")
        return {}

@router.get("/recent-activity")
async def get_recent_activity(conn: asyncpg.Connection = Depends(get_db_connection)):
    try:
        activity = await conn.fetch("SELECT * FROM public.v_recent_activity LIMIT 10")
        return [dict(a) for a in activity]
    except Exception as e:
        print(f"DB Error fetching recent activity: {e}")
        return []