#!/usr/bin/env python3
"""Simple database connection test."""

import asyncio
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def get_ssl_url(url: str) -> str:
    """Add SSL to database URL."""
    if '?' not in url:
        return url + '?sslmode=require'
    if 'sslmode=' not in url:
        return url + '&sslmode=require'
    return url


async def main():
    """Test database connection."""
    db_url = os.getenv('DATABASE_URL',
        'postgresql://bot_binance_user:2yT3u1JBiSintBfwmNlkJlSMmNJnJq@dpg-686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance')

    ssl_url = get_ssl_url(db_url)

    print('[INFO] Testing PostgreSQL connection...')
    print(f'[INFO] Host: {db_url.split("@")[-1].split("/")[0] if "@" in db_url else "unknown"}')

    try:
        import asyncpg

        start = time.time()
        conn = await asyncio.wait_for(asyncpg.connect(ssl_url), timeout=15)
        latency = (time.time() - start) * 1000

        version = await conn.fetchval('SELECT version()')
        pg_version = version.split()[1] if version else 'unknown'

        await conn.close()

        print(f'[OK] Connected! PostgreSQL {pg_version}')
        print(f'[OK] Latency: {latency:.0f}ms')
        print('[OK] DATABASE CONNECTION TEST PASSED!')
        return 0

    except asyncio.TimeoutError:
        print('[ERROR] Timeout (15s). Check if database is running.')
        return 1
    except Exception as e:
        print(f'[ERROR] {e}')
        print('[WARN] The database may not be created yet on Render.')
        print('[INFO] After creating the database on Render, run this test again.')
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
