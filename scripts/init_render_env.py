#!/usr/bin/env python3
"""
Script de inicialização automática para Binance Bot no Render.

Este script roda automaticamente no primeiro deploy e:
1. Cria tabelas se não existirem
2. Aplica schema SQL
3. Migrar dados JSON existentes
4. Configura conexões

Uso automático pelo render.yaml:
  startCommand: python scripts/init_render_env.py && python bot_master.py

Ou chamar explicitamente:
  python scripts/init_render_env.py
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def log(message: str, level: str = 'info'):
    """Log colorido."""
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        colors = {
            'info': Fore.CYAN,
            'ok': Fore.GREEN,
            'warning': Fore.YELLOW,
            'error': Fore.RED,
        }
        color = colors.get(level, Fore.WHITE)
        print(f"{color}{message}{Style.RESET_ALL}")
    except ImportError:
        print(message)


async def check_database_connection() -> bool:
    """Verificar se DATABASE_URL esta configurada."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        log("DATABASE_URL nao configurada. Persistencia PostgreSQL desativada.", 'warning')
        return False

    # Add SSL for Render databases
    if '?' not in db_url and 'sslmode=' not in db_url:
        db_url += '?sslmode=require'

    try:
        import asyncpg
        conn = await asyncio.wait_for(
            asyncpg.connect(db_url),
            timeout=10
        )
        await conn.close()
        log("Conexao com PostgreSQL OK!", 'ok')
        return True
    except Exception as e:
        log(f"Erro ao conectar ao PostgreSQL: {e}", 'error')
        return False


async def ensure_tables_exist():
    """Criar tabelas se nao existirem."""
    try:
        import asyncpg
        from colorama import Fore, Style

        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return

        # Add SSL for Render databases
        if '?' not in db_url and 'sslmode=' not in db_url:
            db_url += '?sslmode=require'

        conn = await asyncpg.connect(db_url)

        try:
            # Verificar se tabela symbols existe
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'symbols'
                );
            """)

            if not table_exists:
                log("Tabelas não encontradas. Aplicando schema.sql...", 'info')

                # Ler schema.sql
                schema_path = ROOT_DIR / 'database' / 'schema.sql'
                if not schema_path.exists():
                    log("schema.sql não encontrado!", 'error')
                    return

                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()

                await conn.execute(schema_sql)
                log("Schema aplicado com sucesso!", 'ok')
            else:
                log("Tabelas já existem. Pulando criação.", 'info')

            # Verificar Symbols iniciais
            symbols_count = await conn.fetchval("SELECT COUNT(*) FROM symbols;")
            if symbols_count == 0:
                log("Symbols iniciais não encontrados. Inserindo...", 'warning')
                # O schema.sql já tem INSERT, mas se falhar:
                await conn.execute("""
                    INSERT INTO symbols (symbol, name, base_asset, quote_asset, tick_size, lot_size, min_notional, max_leverage)
                    VALUES
                        ('BTCUSDT', 'Bitcoin', 'BTC', 'USDT', 0.01, 0.00001, 5, 125),
                        ('ETHUSDT', 'Ethereum', 'ETH', 'USDT', 0.01, 0.00001, 5, 125),
                        ('BNBUSDT', 'Binance Coin', 'BNB', 'USDT', 0.01, 0.001, 5, 125)
                    ON CONFLICT (symbol) DO NOTHING;
                """)
                log("Symbols iniciais inseridos.", 'ok')

        finally:
            await conn.close()

    except Exception as e:
        log(f"Erro ao verificar/criar tabelas: {e}", 'error')


async def migrate_json_to_db():
    """Migrar dados JSON existentes para PostgreSQL."""
    try:
        import asyncpg
        from colorama import Fore, Style

        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return

        # Add SSL for Render databases
        if '?' not in db_url and 'sslmode=' not in db_url:
            db_url += '?sslmode=require'

        # Verificar se ha JSON para migrar
        history_file = ROOT_DIR / 'trade_history.json'
        if not history_file.exists():
            log("Nenhum JSON historico para migrar.", 'info')
            return

        import json
        with open(history_file, 'r') as f:
            history = json.load(f)

        if not history:
            log("Historico JSON vazio.", 'info')
            return

        log(f"Migrando {len(history)} trades do JSON para PostgreSQL...", 'info')

        conn = await asyncpg.connect(db_url)
        try:
            migrated = 0
            for trade in history:
                try:
                    # Verificar se já existe
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT 1 FROM trades
                            WHERE symbol = $1
                            AND entry_time::text = $2
                        );
                    """, trade['symbol'], trade['time'])

                    if not exists:
                        await conn.execute("""
                            INSERT INTO trades (
                                symbol, side, entry_price, exit_price,
                                quantity, pnl, status, entry_time
                            ) VALUES ($1, $2, $3, $4, $5, $6, 'CLOSED', $7::timestamp)
                        """,
                            trade['symbol'],
                            trade['side'],
                            float(trade['entry']),
                            float(trade['exit']),
                            float(trade['quantity']),
                            float(trade['pnl']),
                            trade['time']
                        )
                        migrated += 1
                except Exception as e:
                    log(f"Erro ao migrar trade {trade.get('symbol', 'unknown')}: {e}", 'warning')

            if migrated > 0:
                log(f"{migrated} trades migrados com sucesso!", 'ok')

                # Backup do JSON
                backup_file = history_file.with_suffix('.json.bak')
                import shutil
                shutil.copy(history_file, backup_file)
                log(f"JSON original backupado em {backup_file.name}", 'info')

        finally:
            await conn.close()

    except Exception as e:
        log(f"Erro na migração: {e}", 'warning')


async def check_environment():
    """Verificar e logar configuração de ambiente."""
    log("=== Configuração do Ambiente ===", 'info')

    # Python version
    log(f"Python: {sys.version.split()[0]}", 'info')

    # Database
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Esconder credenciais no log
        safe_url = db_url.split('@')[-1] if '@' in db_url else db_url[:20] + '...'
        log(f"Database: {safe_url}", 'info')
    else:
        log("Database: Não configurado", 'warning')

    # Binance API (verificar se configurado)
    api_key = os.getenv('BINANCE_API_KEY')
    if api_key and api_key != 'your_api_key_here':
        log(f"Binance API: Configurada (prefix: {api_key[:4]}...)", 'ok')
    else:
        log("Binance API: Não configurada", 'warning')

    # Outras configs
    log(f"Max Posições: {os.getenv('MAX_POSITIONS', '3')}", 'info')
    log(f"Alavancagem: {os.getenv('ALAVANCAGEM_PADRAO', '50')}x", 'info')
    log(f"Risco: {float(os.getenv('RISCO_MAXIMO_POR_OPERACAO', '0.05'))*100:.0f}%", 'info')

    # OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        log("OpenAI API: Configurada", 'ok')
    else:
        log("OpenAI API: Não configurada (bot funcionará sem IA)", 'info')

    log("============================", 'info')


async def main():
    """Função principal."""
    log("=== Inicialização Binance Bot - Render ===", 'info')
    log(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'info')
    log()

    # 1. Verificar ambiente
    await check_environment()
    log()

    # 2. Verificar banco
    has_db = await check_database_connection()
    log()

    if has_db:
        # 3. Criar tabelas se necessário
        await ensure_tables_exist()
        log()

        # 4. Migrar JSON existente
        await migrate_json_to_db()
        log()

    log("=== Inicialização concluída! ===", 'ok')
    log("O bot pode ser iniciado agora.", 'info')


if __name__ == '__main__':
    asyncio.run(main())
