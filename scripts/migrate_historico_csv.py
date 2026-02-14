#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRAR HISTORICO DE TRADES CSV -> POSTGRESQL
Script para importar trades históricos do CSV para o banco.
"""

import asyncio
import sys
import codecs
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg

# Configurar UTF-8 no Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())


# ============================================================================
# HISTÓRICO DE TRADES (CSV)
# ============================================================================

HISTORICO_CSV = """
23:38:12,APTUSDT,LONG,0.9500645028759,0.9367,-1.62645999
18:42:09,INJUSDT,LONG,3.123,3.111,-0.366
18:42:09,OPUSDT,LONG,0.1865,0.1896,1.53977
18:42:09,ARBUSDT,LONG,0.1135,0.1157,1.80378
18:41:43,ATOMUSDT,LONG,2.073,2.081,1.5252
18:41:42,DOTUSDT,LONG,1.305,1.319,0.9912
16:32:33,BNBUSDT,SHORT,610.55,618.35,-0.936
16:32:32,ATOMUSDT,LONG,2.041,2.081,1.5252
15:37:32,XRPUSDT,LONG,1.3906,1.4205,1.58171
15:32:45,ADAUSDT,LONG,0.2672,0.2723,1.3464
15:27:10,BNBUSDT,SHORT,604.8,610.62,-0.6984
15:27:09,ARBUSDT,LONG,0.1118,0.114,1.1572
15:12:10,DOTUSDT,LONG,1.284,1.304,0.868
15:12:09,SOLUSDT,LONG,80.88,82.34,1.0074
14:48:35,BTCUSDT,LONG,67248.3,67904.9,1.3132
14:48:10,ADAUSDT,LONG,0.2638,0.2672,0.7344
14:34:30,AVAXUSDT,LONG,8.88,8.988,0.54
14:33:08,XRPUSDT,LONG,1.3674,1.383,0.64272
14:33:08,ETHUSDT,LONG,1955.76,1981.57,0.72268
13:30:21,NEARUSDT,LONG,0.977,0.99,0.676
13:25:59,APTUSDT,SHORT,0.9084,0.917,-0.13846
13:07:32,SOLUSDT,LONG,80.48,79.7,-0.5538
11:22:42,OPUSDT,LONG,0.1896,0.1943,2.85149
11:21:54,ETHUSDT,LONG,2075.01,2101.45,1.48064
11:21:50,ARBUSDT,LONG,0.1156,0.1186,2.9925
11:21:29,BTCUSDT,LONG,69579.3,70182.4,1.2062
10:43:33,ATOMUSDT,LONG,2.135,2.121,-0.25046
09:59:15,BNBUSDT,LONG,618.23,629.5,2.1413
09:37:22,ATOMUSDT,LONG,2.115,2.136,0.8988
08:36:50,XRPUSDT,LONG,1.4255,1.4367,0.75712
08:06:30,ETHUSDT,LONG,2054.88,2065.39,0.48346
07:46:51,BTCUSDT,LONG,68852.1,69178.9,0.6536
06:08:05,SUIUSDT,LONG,0.9738905692438,0.9565,-2.04686999
03:22:42,APTUSDT,LONG,0.952,0.9424,-0.83712
00:43:42,APTUSDT,LONG,0.937,0.9502,1.46784
"""


# ============================================================================
# PARSER CSV
# ============================================================================

def parse_csv_trades(csv_text: str) -> list:
    """
    Converter CSV texto para lista de dicts.

    Retorna trades sorted do mais antigo para o mais recente.
    """
    trades = []

    for line in csv_text.strip().split('\n'):
        if not line.strip():
            continue

        parts = line.split(',')
        if len(parts) != 6:
            print(f"⚠️ Linha ignorada (formato inválido): {line}")
            continue

        time_str, symbol, side, entry_str, exit_str, pnl_str = parts

        trade = {
            'time': time_str.strip(),
            'symbol': symbol.strip(),
            'side': side.strip().upper(),
            'entry_price': float(entry_str.strip()),
            'exit_price': float(exit_str.strip()),
            'pnl': float(pnl_str.strip())
        }

        trades.append(trade)

    # Ordenar do mais antigo para o mais recente
    trades.reverse()

    return trades


def generate_timestamps(trades: list) -> list:
    """
    Gerar entry_time e exit_time para cada trade.

    Assume que trades são de hoje (2026-02-14) e dias anteriores.
    Usa o horário do trade como base.
    """
    today = datetime(2026, 2, 14)

    # Distribuir trades pelos últimos 3 dias
    total_trades = len(trades)
    trades_per_day = total_trades // 3

    result = []

    for i, trade in enumerate(trades):
        # Calcular qual dia (0=há 2 dias, 1=há 1 dia, 2=hoje)
        day_offset = i // trades_per_day
        if day_offset > 2:
            day_offset = 2

        trade_date = today - timedelta(days=(2 - day_offset))

        # Parse horário
        hour, minute, second = map(int, trade['time'].split(':'))

        # Entry time (assumir 15min antes do horário listado)
        entry_time = trade_date.replace(
            hour=hour,
            minute=minute,
            second=second
        ) - timedelta(minutes=15)

        # Exit time (horário listado)
        exit_time = trade_date.replace(
            hour=hour,
            minute=minute,
            second=second
        )

        # Calcular PnL percent
        if trade['side'] == 'LONG':
            pnl_percent = ((trade['exit_price'] - trade['entry_price']) / trade['entry_price']) * 100
        else:  # SHORT
            pnl_percent = ((trade['entry_price'] - trade['exit_price']) / trade['entry_price']) * 100

        # Exit reason baseado no PnL
        exit_reason = 'TP' if trade['pnl'] > 0 else 'SL'

        result.append({
            'symbol': trade['symbol'],
            'side': trade['side'],
            'entry_price': trade['entry_price'],
            'exit_price': trade['exit_price'],
            'pnl': trade['pnl'],
            'pnl_percent': round(pnl_percent, 2),
            'entry_time': entry_time,
            'exit_time': exit_time,
            'exit_reason': exit_reason,
            'status': 'CLOSED',
            # Quantidade estimada (assumir 1 trade = $10 notional aprox)
            'quantity': round(10.0 / trade['entry_price'], 4)
        })

    return result


# ============================================================================
# INSERT POSTGRESQL
# ============================================================================

async def migrate_trades():
    """Conectar ao banco e inserir trades históricos."""

    # Conectar
    conn = await asyncpg.connect(
        "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"
    )

    try:
        # Parse CSV
        print("📋 Parseando CSV...")
        parsed_trades = parse_csv_trades(HISTORICO_CSV)
        print(f"   {len(parsed_trades)} trades encontrados")

        # Gerar timestamps
        print("🕐 Gerando timestamps...")
        trades_to_insert = generate_timestamps(parsed_trades)

        # Inserir símbolos primeiro
        print("📝 Inserindo símbolos...")
        symbols = set(t['symbol'] for t in trades_to_insert)
        symbols_inserted = 0

        for symbol in symbols:
            exists = await conn.fetchval(
                "SELECT COUNT(*) FROM symbols WHERE symbol = $1",
                symbol
            )

            if exists == 0:
                await conn.execute(
                    "INSERT INTO symbols (symbol, is_active) VALUES ($1, true)",
                    symbol
                )
                symbols_inserted += 1

        print(f"   {symbols_inserted} símbolos inseridos")

        # Verificar quantos trades já existem
        existing = await conn.fetchval(
            "SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'"
        )
        print(f"📊 Trades existentes no banco: {existing}")

        # Inserir trades
        print("💾 Inserindo trades no banco...")

        inserted = 0
        skipped = 0

        for trade in trades_to_insert:
            # Verificar se já existe (symbol + entry_time)
            exists = await conn.fetchval(
                """
                SELECT COUNT(*) FROM trades
                WHERE symbol = $1
                  AND entry_time = $2
                  AND status = 'CLOSED'
                """,
                trade['symbol'],
                trade['entry_time']
            )

            if exists > 0:
                skipped += 1
                continue

            # Inserir
            await conn.execute(
                """
                INSERT INTO trades (
                    symbol, side, entry_price, exit_price,
                    sl_price, tp_price, quantity, pnl, pnl_percent,
                    entry_time, exit_time, status, exit_reason
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7, $8, $9,
                    $10, $11, $12, $13
                )
                """,
                trade['symbol'],
                trade['side'],
                trade['entry_price'],
                trade['exit_price'],
                # SL/TP estimados (assumir 1.5x ATR)
                trade['entry_price'] * 0.985 if trade['side'] == 'LONG' else trade['entry_price'] * 1.015,  # SL
                trade['entry_price'] * 1.03 if trade['side'] == 'LONG' else trade['entry_price'] * 0.97,   # TP
                trade['quantity'],
                trade['pnl'],
                trade['pnl_percent'],
                trade['entry_time'],
                trade['exit_time'],
                trade['status'],
                trade['exit_reason']
            )

            inserted += 1

            if inserted % 5 == 0:
                print(f"   {inserted}/{len(trades_to_insert)} trades inseridos...")

        print(f"\n✅ Migração concluída!")
        print(f"   📥 Inseridos: {inserted}")
        print(f"   ⏭️  Pulados (já existiam): {skipped}")

        # Estatísticas
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl
            FROM trades
            WHERE status = 'CLOSED'
        """)

        print(f"\n📊 Estatísticas atualizadas:")
        print(f"   Total trades: {stats['total']}")
        print(f"   Wins: {stats['wins']}")
        print(f"   Losses: {stats['losses']}")
        print(f"   Win rate: {100.0 * stats['wins'] / stats['total']:.1f}%")
        print(f"   Total PnL: ${stats['total_pnl']:.2f}")
        print(f"   Avg PnL: ${stats['avg_pnl']:.2f}")

    finally:
        await conn.close()
        print("\n🔌 Conexão fechada")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  📥 MIGRAR HISTÓRICO CSV → POSTGRESQL                      ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        asyncio.run(migrate_trades())
        print("\n✅ Migração concluída com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
