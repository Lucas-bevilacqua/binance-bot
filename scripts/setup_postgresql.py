#!/usr/bin/env python3
"""
Setup Script - PostgreSQL Database for Binance Bot
=================================================

Este script configura automaticamente o banco de dados PostgreSQL:
1. Testa a conexão
2. Aplica o schema.sql
3. Insere dados iniciais (symbols)
4. Verifica configuração

Uso:
    python scripts/setup_postgresql.py

Ambiente:
    Requer DATABASE_URL configurado em .env ou variável de ambiente
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class Colors:
    """Códigos de terminal ANSI para cores."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = 'info') -> None:
    """Log colorido no terminal."""
    import sys
    if sys.platform == 'win32':
        import codecs
        if hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

    colors = {
        'info': Colors.CYAN,
        'ok': Colors.GREEN,
        'warning': Colors.YELLOW,
        'error': Colors.RED,
        'header': Colors.BOLD + Colors.WHITE,
    }
    color = colors.get(level, Colors.WHITE)
    prefix = {
        'ok': '[OK]',
        'error': '[ERROR]',
        'warning': '[WARN]',
        'info': '[INFO]',
        'header': '',
    }.get(level, '')

    print(f"{color}{prefix} {message}{Colors.RESET}")


def get_database_url() -> Optional[str]:
    """
    Obter DATABASE_URL do ambiente.

    Procura em:
    1. Variável de ambiente DATABASE_URL
    2. Arquivo .env
    """
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    # Tentar carregar de .env
    try:
        from dotenv import load_dotenv
        env_file = ROOT_DIR / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                return db_url
    except ImportError:
        pass

    return None


async def test_connection(db_url: str) -> bool:
    """
    Testar conexão com o PostgreSQL.

    Returns:
        True se conectou com sucesso, False caso contrário
    """
    try:
        import asyncpg

        log("Testando conexão com PostgreSQL...", 'info')
        log(f"Host: {db_url.split('@')[-1] if '@' in db_url else 'N/A'}", 'info')

        conn = await asyncio.wait_for(
            asyncpg.connect(db_url),
            timeout=10
        )

        version = await conn.fetchval('SELECT version()')
        await conn.close()

        # Extrair versão do PostgreSQL
        pg_version = version.split()[1] if version else 'unknown'

        log(f"Conectado com sucesso! PostgreSQL versão: {pg_version}", 'ok')
        return True

    except asyncio.TimeoutError:
        log("Timeout ao conectar (10s). Verifique a URL.", 'error')
        return False
    except Exception as e:
        log(f"Erro ao conectar: {e}", 'error')
        return False


async def apply_schema(db_url: str) -> bool:
    """
    Aplicar schema.sql ao banco de dados.

    Returns:
        True se aplicou com sucesso, False caso contrário
    """
    try:
        import asyncpg

        log("Aplicando schema.sql...", 'info')

        schema_path = ROOT_DIR / 'database' / 'schema.sql'
        if not schema_path.exists():
            log(f"schema.sql não encontrado em: {schema_path}", 'error')
            return False

        # Ler o schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Conectar e executar
        conn = await asyncpg.connect(db_url)

        # Dividir o schema em comandos individuais
        # (para melhor tratamento de erros)
        statements = []
        current = []
        in_extension = False

        for line in schema_sql.split('\n'):
            line = line.strip()

            # Pular comentários e vazias
            if not line or line.startswith('--'):
                continue

            # Detectar início de CREATE EXTENSION
            if line.upper().startswith('CREATE EXTENSION'):
                in_extension = True

            current.append(line)

            # Detectar fim de statement
            if line.endswith(';'):
                statement = '\n'.join(current)
                statements.append(statement)
                current = []
                in_extension = False

        # Executar cada statement
        executed = 0
        for stmt in statements:
            try:
                await conn.execute(stmt)
                executed += 1
            except Exception as e:
                # Se já existe, ignorar
                if 'already exists' not in str(e):
                    log(f"Aviso: {str(e)[:100]}", 'warning')

        await conn.close()

        log(f"Schema aplicado com sucesso! ({executed} comandos)", 'ok')
        return True

    except Exception as e:
        log(f"Erro ao aplicar schema: {e}", 'error')
        return False


async def verify_setup(db_url: str) -> bool:
    """
    Verificar se o banco foi configurado corretamente.

    Returns:
        True se tudo está OK, False caso contrário
    """
    try:
        import asyncpg

        log("Verificando configuração...", 'info')

        conn = await asyncpg.connect(db_url)

        # Verificar tabelas
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        tables = await conn.fetch(tables_query)
        table_names = [row['table_name'] for row in tables]

        expected_tables = ['symbols', 'trades', 'positions', 'daily_metrics']
        missing_tables = [t for t in expected_tables if t not in table_names]

        if missing_tables:
            log(f"Tabelas faltando: {missing_tables}", 'error')
            await conn.close()
            return False

        log(f"Tabelas criadas: {', '.join(expected_tables)}", 'ok')

        # Verificar symbols
        symbols_count = await conn.fetchval('SELECT COUNT(*) FROM symbols;')

        if symbols_count == 0:
            log("Aviso: Tabela symbols vazia. Os INSERTs do schema.sql podem ter falhado.", 'warning')
        else:
            log(f"Symbols configurados: {symbols_count} ativos", 'ok')

        # Verificar views
        views_query = """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        views = await conn.fetch(views_query)
        view_names = [row['table_name'] for row in views]

        expected_views = ['v_active_trades', 'v_trade_history', 'v_daily_metrics']
        missing_views = [v for v in expected_views if v not in view_names]

        if missing_views:
            log(f"Views faltando: {missing_views}", 'warning')
        else:
            log(f"Views criadas: {', '.join(expected_views)}", 'ok')

        # Verificar functions/triggers
        functions = await conn.fetch("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION';
        """)
        func_names = [row['routine_name'] for row in functions]

        log(f"Functions criadas: {len(funcs)}", 'ok')

        await conn.close()
        return True

    except Exception as e:
        log(f"Erro na verificação: {e}", 'error')
        return False


async def run_initial_tests(db_url: str) -> None:
    """
    Executar testes básicos no banco configurado.

    Testa:
    1. Inserção de um trade
    2. Consulta de posições
    3. Atualização de métricas
    """
    try:
        import asyncpg

        log("Executando testes de integração...", 'info')

        conn = await asyncpg.connect(db_url)

        # Teste 1: Inserir trade
        log("Teste 1: Inserindo trade de teste...", 'info')
        await conn.execute("""
            INSERT INTO trades (
                symbol, side, quantity, entry_price,
                sl_price, tp_price, status
            ) VALUES (
                'BTCUSDT', 'LONG', 0.001, 50000.0,
                49000.0, 51000.0, 'OPEN'
            );
        """)

        test_trade = await conn.fetchrow(
            "SELECT * FROM trades WHERE symbol = 'BTCUSDT' LIMIT 1;"
        )

        if test_trade:
            log("Trade inserido e recuperado com sucesso!", 'ok')
        else:
            log("Falha ao recuperar trade inserido", 'error')

        # Teste 2: Consultar views
        log("Teste 2: Consultando views...", 'info')
        active_trades = await conn.fetch("SELECT * FROM v_active_trades LIMIT 1;")
        log(f"View v_active_trades funcionando! ({len(active_trades)} registros)", 'ok')

        # Teste 3: Limpar dados de teste
        log("Teste 3: Limpando dados de teste...", 'info')
        await conn.execute("DELETE FROM trades WHERE symbol = 'BTCUSDT';")
        log("Dados de teste removidos", 'ok')

        await conn.close()

    except Exception as e:
        log(f"Erro nos testes: {e}", 'warning')


def print_summary(success: bool) -> None:
    """Imprimir resumo do setup."""
    log("", 'header')
    log("=" * 70, 'header')
    if success:
        log("SETUP CONCLUÍDO COM SUCESSO!", 'ok')
        log("", 'header')
        log("Próximos passos:", 'info')
        log("  1. Configure as variáveis de ambiente no Render:", 'info')
        log("     - BINANCE_API_KEY", 'info')
        log("     - BINANCE_API_SECRET", 'info')
        log("     - (Opcional) OPENAI_API_KEY", 'info')
        log("", 'info')
        log("  2. Faça push do código para o repositório", 'info')
        log("", 'info')
        log("  3. Conecte o repositório ao Render:", 'info')
        log("     - Vá em dashboard.render.com", 'info')
        log("     - Clique em 'New +' -> 'Blueprint'", 'info')
        log("     - Selecione o repositório", 'info')
        log("", 'info')
        log("  4. Acompanhe os logs no primeiro deploy", 'info')
        log("     - Procure por: 'Conexão com PostgreSQL OK!'", 'info')
    else:
        log("SETUP FALHOU!", 'error')
        log("", 'header')
        log("Verifique:", 'warning')
        log("  - DATABASE_URL está correta?", 'warning')
        log("  - O banco PostgreSQL está ativo?", 'warning')
        log("  - As credenciais estão válidas?", 'warning')
    log("=" * 70, 'header')


async def main() -> int:
    """Função principal."""
    log("", 'header')
    log("=" * 70, 'header')
    log("BINANCE BOT - SETUP POSTGRESQL", 'header')
    log("=" * 70, 'header')
    log(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'info')
    log("", 'header')

    # 1. Obter DATABASE_URL
    db_url = get_database_url()
    if not db_url:
        log("DATABASE_URL não encontrada!", 'error')
        log("", 'header')
        log("Configure a variável de ambiente:", 'warning')
        log("  export DATABASE_URL='postgresql://...'", 'warning')
        log("Ou adicione ao arquivo .env", 'warning')
        return 1

    log("DATABASE_URL configurada", 'ok')

    # 2. Testar conexão
    if not await test_connection(db_url):
        return 1

    # 3. Aplicar schema
    if not await apply_schema(db_url):
        return 1

    # 4. Verificar setup
    if not await verify_setup(db_url):
        return 1

    # 5. Testes iniciais (opcional)
    await run_initial_tests(db_url)

    # 6. Resumo
    print_summary(True)

    return 0


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\nSetup cancelado pelo usuário", 'warning')
        sys.exit(1)
    except Exception as e:
        log(f"\nErro inesperado: {e}", 'error')
        import traceback
        traceback.print_exc()
        sys.exit(1)
