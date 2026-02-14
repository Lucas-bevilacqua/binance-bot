#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INICIALIZAR BANCO DE DADOS
===========================
Aplica o schema.sql no PostgreSQL.
"""

import asyncio
import sys
import codecs
import asyncpg

# UTF-8 no Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())


async def init_database():
    """Criar todas as tabelas do schema."""

    conn = await asyncpg.connect(
        "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"
    )

    try:
        print("Criando tabelas...")

        # Tabela symbols
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                symbol VARCHAR(20) PRIMARY KEY,
                is_active BOOLEAN DEFAULT true,
                last_scan_time TIMESTAMP,
                last_signal_score INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("  [OK] symbols")

        # Tabela trades
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL REFERENCES symbols(symbol),
                side VARCHAR(10) NOT NULL,
                quantity NUMERIC(20, 8) NOT NULL,
                entry_price NUMERIC(20, 8) NOT NULL,
                exit_price NUMERIC(20, 8),
                sl_price NUMERIC(20, 8),
                tp_price NUMERIC(20, 8),
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                pnl NUMERIC(20, 8) DEFAULT 0,
                pnl_percent NUMERIC(10, 4) DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
                exit_reason VARCHAR(20),
                entry_order_id BIGINT,
                sl_order_id BIGINT,
                tp_order_id BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("  [OK] trades")

        # Tabela positions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol VARCHAR(20) PRIMARY KEY REFERENCES symbols(symbol),
                side VARCHAR(10) NOT NULL,
                quantity NUMERIC(20, 8) NOT NULL,
                entry_price NUMERIC(20, 8) NOT NULL,
                current_price NUMERIC(20, 8),
                sl_price NUMERIC(20, 8),
                tp_price NUMERIC(20, 8),
                unrealized_pnl NUMERIC(20, 8) DEFAULT 0,
                unrealized_percent NUMERIC(10, 4) DEFAULT 0,
                opened_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                entry_order_id BIGINT,
                sl_order_id BIGINT,
                tp_order_id BIGINT
            )
        """)
        print("  [OK] positions")

        # Tabela daily_metrics
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date DATE PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl NUMERIC(20, 8) DEFAULT 0,
                max_drawdown NUMERIC(20, 8) DEFAULT 0,
                sharpe_ratio NUMERIC(10, 4),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("  [OK] daily_metrics")

        # Tabela ohlcv
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                id BIGSERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL REFERENCES symbols(symbol),
                timestamp TIMESTAMP NOT NULL,
                open_price NUMERIC(20, 8),
                high_price NUMERIC(20, 8),
                low_price NUMERIC(20, 8),
                close_price NUMERIC(20, 8),
                volume NUMERIC(30, 8),
                UNIQUE(symbol, timestamp)
            )
        """)
        print("  [OK] ohlcv")

        # Tabela trade_executions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_executions (
                id BIGSERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL REFERENCES symbols(symbol),
                trade_id INTEGER REFERENCES trades(trade_id),
                order_id BIGINT NOT NULL,
                execution_type VARCHAR(20) NOT NULL,
                price NUMERIC(20, 8) NOT NULL,
                quantity NUMERIC(20, 8) NOT NULL,
                execution_time TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("  [OK] trade_executions")

        # Indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
            CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
            CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time DESC);
            CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv(symbol, timestamp DESC);
        """)
        print("  [OK] indexes")

        # Views
        await conn.execute("""
            CREATE OR REPLACE VIEW v_active_trades AS
            SELECT
                t.symbol,
                t.side,
                t.quantity,
                t.entry_price,
                t.sl_price,
                t.tp_price,
                t.entry_time,
                t.pnl,
                t.pnl_percent
            FROM trades t
            WHERE t.status = 'OPEN';
        """)
        print("  [OK] view v_active_trades")

        await conn.execute("""
            CREATE OR REPLACE VIEW v_trade_history AS
            SELECT
                t.symbol,
                t.side,
                t.entry_price,
                t.exit_price,
                t.pnl,
                t.pnl_percent,
                t.entry_time,
                t.exit_time,
                t.exit_reason
            FROM trades t
            WHERE t.status = 'CLOSED'
            ORDER BY t.entry_time DESC;
        """)
        print("  [OK] view v_trade_history")

        print("\n✅ Schema criado com sucesso!")

        # Verificar tabelas
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"\n📊 Tabelas criadas ({len(tables)}):")
        for t in tables:
            print(f"   - {t['table_name']}")

    finally:
        await conn.close()


if __name__ == "__main__":
    try:
        asyncio.run(init_database())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
