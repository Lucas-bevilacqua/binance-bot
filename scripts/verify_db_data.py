#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar dados no banco PostgreSQL
"""
import asyncio
import asyncpg
import sys
import codecs

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

async def verify_data():
    """Verificar dados no banco."""
    conn = await asyncpg.connect(
        "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"
    )

    try:
        # Ver trades
        trades_count = await conn.fetchval("SELECT COUNT(*) FROM trades")
        print(f"Trades no banco: {trades_count}")

        if trades_count > 0:
            trades = await conn.fetch("SELECT * FROM trades LIMIT 5")
            print("\nPrimeiros 5 trades:")
            for t in trades:
                print(f"  - {t['symbol']} {t['side']} Entry: ${t['entry_price']} PnL: ${t['pnl']}")

        # Ver positions
        positions_count = await conn.fetchval("SELECT COUNT(*) FROM positions")
        print(f"\nPositions no banco: {positions_count}")

        if positions_count > 0:
            positions = await conn.fetch("SELECT * FROM positions")
            print("\nPositions:")
            for p in positions:
                print(f"  - {p['symbol']} {p['side']} Entry: ${p['entry_price']}")

        # Ver symbols
        symbols = await conn.fetch("SELECT symbol FROM symbols")
        print(f"\nSimbolos no banco: {len(symbols)}")
        for s in symbols:
            print(f"  - {s['symbol']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_data())
