import asyncio, asyncpg, sys

async def test():
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect('postgres://postgres:postgres@localhost:5432/hcs_db'),
            timeout=5
        )
        print('DB connected!')
        await conn.close()
    except asyncio.TimeoutError:
        print('DB TIMEOUT')
    except Exception as e:
        print(f'DB ERROR: {type(e).__name__}: {e}')

asyncio.run(test())
