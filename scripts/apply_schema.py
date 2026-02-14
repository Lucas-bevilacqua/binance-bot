#!/usr/bin/env python3
"""
Script para aplicar o schema SQL do Binance Bot no PostgreSQL Render.

Uso:
    python scripts/apply_schema.py

Pré-requisitos:
    - Variável de ambiente DATABASE_URL configurada
    - Arquivo database/schema.sql existente
"""

import os
import sys
import asyncio
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


async def apply_schema():
    """Lê e executa o schema.sql no banco PostgreSQL."""
    from colorama import Fore, Style, init
    import asyncpg

    init(autoreset=True)

    # Verificar DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print(f"{Fore.RED}ERRO: DATABASE_URL não configurada!")
        print(f"{Fore.YELLOW}Configure a variável de ambiente antes de executar.")
        sys.exit(1)

    schema_path = ROOT_DIR / 'database' / 'schema.sql'
    if not schema_path.exists():
        print(f"{Fore.RED}ERRO: {schema_path} não encontrado!")
        sys.exit(1)

    print(f"{Fore.CYAN}=== Aplicando Schema PostgreSQL ===")
    print(f"{Fore.WHITE}Banco: {db_url.split('@')[1] if '@' in db_url else 'desconhecido'}")
    print(f"{Fore.WHITE}Schema: {schema_path}")

    try:
        # Ler schema SQL
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Conectar ao banco
        print(f"{Fore.CYAN}Conectando ao banco...")
        conn = await asyncpg.connect(db_url)

        try:
            # Executar schema
            print(f"{Fore.CYAN}Executando schema.sql...")
            await conn.execute(schema_sql)
            print(f"{Fore.GREEN}✅ Schema aplicado com sucesso!")

            # Verificar tabelas criadas
            tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)

            print(f"{Fore.GREEN}✅ Tabelas criadas:")
            for row in tables:
                print(f"  {Fore.WHITE}  - {row['tablename']}")

            # Verificar views criadas
            views = await conn.fetch("""
                SELECT viewname
                FROM pg_views
                WHERE schemaname = 'public'
                ORDER BY viewname;
            """)

            if views:
                print(f"{Fore.GREEN}✅ Views criadas:")
                for row in views:
                    print(f"  {Fore.WHITE}  - {row['viewname']}")

        finally:
            await conn.close()
            print(f"{Fore.CYAN}Conexão fechada.")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao aplicar schema: {e}")
        sys.exit(1)


async def verify_schema():
    """Verifica se o schema foi aplicado corretamente."""
    import asyncpg
    from colorama import Fore, init

    init(autoreset=True)

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        return

    print(f"{Fore.CYAN}=== Verificando Schema ===")

    try:
        conn = await asyncpg.connect(db_url)

        try:
            # Verificar tabela symbols
            symbols_count = await conn.fetchval("SELECT COUNT(*) FROM symbols;")
            print(f"{Fore.GREEN}✅ symbols: {symbols_count} registros")

            # Verificar tabela trades
            trades_count = await conn.fetchval("SELECT COUNT(*) FROM trades;")
            print(f"{Fore.GREEN}✅ trades: {trades_count} registros")

            # Verificar tabela positions
            positions_count = await conn.fetchval("SELECT COUNT(*) FROM positions;")
            print(f"{Fore.GREEN}✅ positions: {positions_count} registros")

            # Verificar tabela daily_metrics
            metrics_count = await conn.fetchval("SELECT COUNT(*) FROM daily_metrics;")
            print(f"{Fore.GREEN}✅ daily_metrics: {metrics_count} registros")

        finally:
            await conn.close()

    except Exception as e:
        print(f"{Fore.RED}Erro na verificação: {e}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Aplicar schema PostgreSQL do Binance Bot')
    parser.add_argument('--verify', '-v', action='store_true',
                      help='Apenas verificar se schema está aplicado')
    args = parser.parse_args()

    if args.verify:
        asyncio.run(verify_schema())
    else:
        asyncio.run(apply_schema())
        # Verificar após aplicar
        print()
        asyncio.run(verify_schema())
