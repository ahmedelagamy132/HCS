import asyncpg
from typing import Optional
from fastapi import FastAPI
import os
import logging

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/hcs_db")
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Failed to connect to the database: {e}")
            raise e

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")

db = Database()

async def get_db_connection() -> asyncpg.Connection:
    """Dependency to get a database connection from the pool."""
    if not db.pool:
        raise Exception("Database pool not initialized")
    async with db.pool.acquire() as connection:
        yield connection