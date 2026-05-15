import asyncio
import asyncpg
import sys

async def test():
    urls = [
        'postgres://postgres:postgres@localhost:5432/hcs_db',
        'postgres://postgres:@localhost:5432/hcs_db',
        'postgres://postgres:postgres@localhost:5432/postgres',
    ]
    for url in urls:
        try:
            conn = await asyncio.wait_for(asyncpg.connect(url), timeout=3)
            print(f'OK: {url}')
            await conn.close()
            return
        except asyncio.TimeoutError:
            print(f'TIMEOUT: {url}')
        except Exception as e:
            print(f'ERR {type(e).__name__}: {url} -> {e}')

asyncio.run(test())
