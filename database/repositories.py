"""
🗄️ DATABASE REPOSITORIES
====================================
Camada de persistência com PostgreSQL para evitar perda de dados no Render.
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from decimal import Decimal

import asyncpg
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# REPOSITORY BASE
# ============================================================================

class DatabaseRepository:
    """Repository base com conexão PostgreSQL."""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL nao configurado!")

        # Add SSL for Render databases
        if '?' not in self.database_url and 'sslmode=' not in self.database_url:
            self.database_url += '?sslmode=require'

        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Criar pool de conexoes."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            print(f"Conectado ao PostgreSQL")

    async def close(self):
        """Fechar pool de conexões."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("🔌 Conexões PostgreSQL fechadas")

    async def execute(self, query: str, *args, fetch: str = None) -> Optional[List]:
        """Executar query com tratamento de erro."""
        async with self._lock:
            if not self.pool:
                await self.connect()

            async with self.pool.acquire() as conn:
                if fetch == 'one':
                    return await conn.fetchrow(query, *args)
                elif fetch == 'all':
                    return await conn.fetch(query, *args)
                elif fetch == 'val':
                    return await conn.fetchval(query, *args)
                else:
                    await conn.execute(query, *args)
                    return None


# ============================================================================
# TRADE REPOSITORY
# ============================================================================

class TradeRepository(DatabaseRepository):
    """Repository para trades históricos."""

    async def save_trade(self, trade_data: Dict) -> int:
        """Salvar novo trade."""
        query = """
        INSERT INTO trades (
            symbol, side, quantity, entry_price, exit_price,
            sl_price, tp_price, entry_time, pnl, pnl_percent,
            status, entry_order_id, sl_order_id, tp_order_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (entry_order_id) DO UPDATE SET
            exit_price = EXCLUDED.exit_price,
            pnl = EXCLUDED.pnl,
            pnl_percent = EXCLUDED.pnl_percent,
            status = EXCLUDED.status,
            exit_time = EXCLUDED.exit_time,
            updated_at = NOW()
        RETURNING id
        """

        result = await self.execute(
            query,
            trade_data['symbol'],
            trade_data['side'],
            trade_data['quantity'],
            trade_data['entry_price'],
            trade_data.get('exit_price'),
            trade_data.get('sl_price'),
            trade_data.get('tp_price'),
            trade_data['entry_time'],
            trade_data.get('pnl', 0),
            trade_data.get('pnl_percent', 0),
            trade_data.get('status', 'OPEN'),
            trade_data.get('entry_order_id'),
            trade_data.get('sl_order_id'),
            trade_data.get('tp_order_id'),
            fetch='val'
        )

        return result

    async def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        pnl: float,
        pnl_percent: float,
        close_reason: str = 'MANUAL'
    ):
        """Fechar trade com PnL final."""
        query = """
        UPDATE trades SET
            exit_price = $2,
            pnl = $3,
            pnl_percent = $4,
            status = 'CLOSED',
            close_reason = $5,
            exit_time = NOW(),
            duration_seconds = EXTRACT(EPOCH FROM (NOW() - entry_time)),
            updated_at = NOW()
        WHERE id = $1
        """

        await self.execute(query, trade_id, exit_price, pnl, pnl_percent, close_reason)

    async def get_open_trades(self) -> List[Dict]:
        """Buscar trades abertos."""
        query = """
        SELECT id, symbol, side, quantity, entry_price,
               sl_price, tp_price, entry_time, opened_at
        FROM trades
        WHERE status = 'OPEN'
        ORDER BY entry_time DESC
        """

        rows = await self.execute(query, fetch='all')
        return [dict(row) for row in rows] if rows else []

    async def get_trade_history(self, limit: int = 500) -> List[Dict]:
        """Buscar histórico de trades fechados."""
        query = """
        SELECT
            TO_CHAR(entry_time, 'YYYY-MM-DD HH24:MI:SS') as time,
            symbol, side,
            ROUND(entry_price::numeric, 4) as entry,
            ROUND(exit_price::numeric, 4) as exit,
            ROUND(pnl::numeric, 2) as pnl
        FROM trades
        WHERE status = 'CLOSED'
        ORDER BY entry_time DESC
        LIMIT $1
        """

        rows = await self.execute(query, limit, fetch='all')
        return [dict(row) for row in rows] if rows else []

    async def get_daily_metrics(self, days: int = 30) -> List[Dict]:
        """Buscar métricas diárias agregadas."""
        query = """
        SELECT
            date::text as date,
            ROUND(total_pnl::numeric, 2) as pnl,
            trade_count as trades
        FROM daily_metrics
        ORDER BY date DESC
        LIMIT $1
        """

        rows = await self.execute(query, days, fetch='all')
        return [dict(row) for row in rows] if rows else []


# ============================================================================
# POSITION REPOSITORY
# ============================================================================

class PositionRepository(DatabaseRepository):
    """Repository para posições ativas."""

    async def save_position(self, pos_data: Dict) -> None:
        """Salvar ou atualizar posição."""
        query = """
        INSERT INTO positions (
            symbol, side, quantity, entry_price, current_price,
            sl_price, tp_price, entry_order_id, sl_order_id, tp_order_id,
            unrealized_pnl, unrealized_percent
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (symbol) DO UPDATE SET
            current_price = EXCLUDED.current_price,
            unrealized_pnl = EXCLUDED.unrealized_pnl,
            unrealized_percent = EXCLUDED.unrealized_percent,
            sl_price = EXCLUDED.sl_price,
            tp_price = EXCLUDED.tp_price,
            sl_order_id = EXCLUDED.sl_order_id,
            tp_order_id = EXCLUDED.tp_order_id,
            updated_at = NOW()
        """

        await self.execute(
            query,
            pos_data['symbol'],
            pos_data['side'],
            pos_data['quantity'],
            pos_data['entry_price'],
            pos_data.get('current_price'),
            pos_data.get('sl_price'),
            pos_data.get('tp_price'),
            pos_data.get('entry_order_id'),
            pos_data.get('sl_order_id'),
            pos_data.get('tp_order_id'),
            pos_data.get('unrealized_pnl', 0),
            pos_data.get('unrealized_percent', 0)
        )

    async def get_all_positions(self) -> Dict[str, Dict]:
        """Buscar todas as posições ativas."""
        query = """
        SELECT symbol, side, quantity, entry_price, current_price,
               sl_price as sl, tp_price as tp,
               unrealized_pnl as current_pnl,
               ROUND(unrealized_percent, 2) as current_pnl_percent,
               opened_at, sl_order_id, tp_order_id
        FROM positions
        ORDER BY opened_at DESC
        """

        rows = await self.execute(query, fetch='all')
        return {row['symbol']: dict(row) for row in rows} if rows else {}

    async def delete_position(self, symbol: str) -> None:
        """Remover posição (quando fechada)."""
        query = "DELETE FROM positions WHERE symbol = $1"
        await self.execute(query, symbol)


# ============================================================================
# MIGRATION HELPER
# ============================================================================

async def migrate_json_to_db(trade_repo: TradeRepository, json_file: str = "trade_history.json"):
    """Migrar dados existentes de JSON para PostgreSQL."""

    if not os.path.exists(json_file):
        print(f"⚠️ Arquivo {json_file} não encontrado - pulando migração")
        return

    print(f"🔄 Migrando dados de {json_file} para PostgreSQL...")

    try:
        with open(json_file, 'r') as f:
            history = json.load(f)

        migrated = 0
        for trade in history:
            try:
                await trade_repo.save_trade({
                    'symbol': trade['symbol'],
                    'side': trade['side'],
                    'quantity': trade['quantity'],
                    'entry_price': trade['entry'],
                    'exit_price': trade.get('exit'),
                    'pnl': trade.get('pnl', 0),
                    'entry_time': datetime.fromisoformat(trade['time']),
                    'status': 'CLOSED',
                    'close_reason': 'MIGRATED'
                })
                migrated += 1
            except Exception as e:
                print(f"⚠️ Erro ao migrar trade {trade.get('symbol')}: {e}")

        print(f"✅ Migração concluída: {migrated} trades migrados")

        # Backup do arquivo JSON
        backup_file = f"{json_file}.backup"
        os.rename(json_file, backup_file)
        print(f"📦 JSON original salvo como {backup_file}")

    except Exception as e:
        print(f"❌ Erro na migração: {e}")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_trade_repo: Optional[TradeRepository] = None
_position_repo: Optional[PositionRepository] = None


async def get_trade_repo() -> TradeRepository:
    """Get singleton TradeRepository."""
    global _trade_repo
    if _trade_repo is None:
        _trade_repo = TradeRepository()
        await _trade_repo.connect()
    return _trade_repo


async def get_position_repo() -> PositionRepository:
    """Get singleton PositionRepository."""
    global _position_repo
    if _position_repo is None:
        _position_repo = PositionRepository()
        await _position_repo.connect()
    return _position_repo


async def close_repos():
    """Fechar todos os repositories."""
    global _trade_repo, _position_repo
    if _trade_repo:
        await _trade_repo.close()
        _trade_repo = None
    if _position_repo:
        await _position_repo.close()
        _position_repo = None
