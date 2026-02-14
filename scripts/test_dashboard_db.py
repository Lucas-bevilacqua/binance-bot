#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testar se o banco retorna dados para o dashboard
"""
import asyncio
import sys
import codecs
import asyncpg
from datetime import datetime

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

async def test_dashboard_data():
    """Testar query do dashboard."""
    DATABASE_URL = "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"

    print("Conectando ao banco...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Test 1: Trade history query
        print("\n[TEST 1] Query de history (como dashboard faz):")
        history_rows = await conn.fetch("""
            SELECT
                symbol,
                side,
                entry_price,
                exit_price,
                pnl,
                pnl_percent,
                entry_time,
                exit_time,
                exit_reason
            FROM trades
            WHERE status = 'CLOSED'
            ORDER BY entry_time DESC
            LIMIT 100
        """)

        print(f"  Rows retornados: {len(history_rows)}")

        if history_rows:
            print(f"  Primeiro trade:")
            h = history_rows[0]
            print(f"    Symbol: {h['symbol']}")
            print(f"    Side: {h['side']}")
            print(f"    Entry: ${h['entry_price']}")
            print(f"    Exit: ${h.get('exit_price', 0)}")
            print(f"    PnL: ${h.get('pnl', 0)}")
            print(f"    Time: {h['entry_time']}")

        # Test 2: Active positions
        print("\n[TEST 2] Query de active_positions:")
        positions = await conn.fetch("""
            SELECT
                symbol,
                side,
                entry_price,
                current_price,
                sl_price,
                tp_price,
                unrealized_pnl,
                unrealized_percent
            FROM positions
        """)

        print(f"  Rows retornados: {len(positions)}")

        # Test 3: Overall stats
        print("\n[TEST 3] Query de overall stats:")
        overall = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trades
            WHERE status = 'CLOSED'
        """)

        print(f"  Total trades: {overall['total_trades']}")
        print(f"  Winning trades: {overall['winning_trades']}")
        print(f"  Losing trades: {overall['losing_trades']}")
        print(f"  Total PnL: ${overall.get('total_pnl', 0):.2f}")
        print(f"  Win rate: {100.0 * overall['winning_trades'] / overall['total_trades']:.1f}%")

        # Test 4: Daily metrics
        print("\n[TEST 4] Query de daily_metrics:")
        metrics_rows = await conn.fetch("""
            SELECT
                date,
                total_trades,
                winning_trades,
                losing_trades,
                total_pnl as pnl
            FROM daily_metrics
            ORDER BY date DESC
            LIMIT 30
        """)

        print(f"  Rows retornados: {len(metrics_rows)}")

        if metrics_rows:
            print(f"  Primeiro dia:")
            m = metrics_rows[0]
            print(f"    Date: {m['date']}")
            print(f"    Trades: {m['total_trades']}")
            print(f"    PnL: ${m.get('pnl', 0):.2f}")

    finally:
        await conn.close()

    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    try:
        asyncio.run(test_dashboard_data())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
