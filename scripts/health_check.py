#!/usr/bin/env python3
"""
Health Check Script para Binance Bot no Render.

Uso:
    python scripts/health_check.py [--verbose]

Retorna:
    0 - Saúde OK
    1 - Saúde com problemas
    2 - Erro crítico
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class HealthChecker:
    """Verificador de saúde do bot."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Any] = {}
        self.status = 'OK'

    def log(self, message: str, level: str = 'info'):
        """Log mensagem se verbose."""
        if self.verbose:
            from colorama import Fore, Style
            colors = {
                'info': Fore.CYAN,
                'ok': Fore.GREEN,
                'warning': Fore.YELLOW,
                'error': Fore.RED,
            }
            print(f"{colors.get(level, Fore.WHITE)}{message}{Style.RESET_ALL}")

    async def check_database(self) -> bool:
        """Verificar conexão com banco PostgreSQL."""
        try:
            import asyncpg
            from colorama import Fore, Style

            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.log('DATABASE_URL não configurada', 'warning')
                self.results['database'] = {'status': 'warning', 'message': 'DATABASE_URL não configurada'}
                return True  # Não é crítico se não tiver DB

            self.log(f'Conectando ao banco...', 'info')
            conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=5)

            try:
                # Verificar se schema existe
                tables = await conn.fetchval("""
                    SELECT COUNT(*) FROM pg_tables
                    WHERE schemaname = 'public';
                """)

                self.log(f'Banco OK ({tables} tabelas)', 'ok')
                self.results['database'] = {
                    'status': 'ok',
                    'tables': tables,
                    'message': 'Conexão OK'
                }
                return True

            finally:
                await conn.close()

        except asyncio.TimeoutError:
            self.log('Timeout conectando ao banco', 'error')
            self.results['database'] = {'status': 'error', 'message': 'Timeout'}
            self.status = 'ERROR'
            return False
        except Exception as e:
            self.log(f'Erro no banco: {e}', 'error')
            self.results['database'] = {'status': 'error', 'message': str(e)}
            self.status = 'ERROR'
            return False

    async def check_binance_api(self) -> bool:
        """Verificar conexão com API Binance."""
        try:
            from binance import AsyncClient
            from colorama import Fore, Style

            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')

            if not api_key or not api_secret:
                self.log('Credenciais Binance não configuradas', 'warning')
                self.results['binance'] = {'status': 'warning', 'message': 'Sem credenciais'}
                return True  # Não crítico para health check

            self.log('Testando conexão Binance...', 'info')
            client = await asyncio.wait_for(
                AsyncClient.create(api_key, api_secret),
                timeout=10
            )

            try:
                # Ping simples
                pong = await asyncio.wait_for(client.ping(), timeout=5)
                self.log('Binance API OK', 'ok')

                # Obter saldo
                account = await asyncio.wait_for(
                    client.futures_account(),
                    timeout=5
                )
                balance = float(account['totalWalletBalance'])
                self.log(f'Saldo: ${balance:.2f}', 'info')

                self.results['binance'] = {
                    'status': 'ok',
                    'balance': balance,
                    'message': 'API OK'
                }
                return True

            finally:
                await client.close_connection()

        except asyncio.TimeoutError:
            self.log('Timeout na API Binance', 'warning')
            self.results['binance'] = {'status': 'warning', 'message': 'Timeout'}
            return True  # Ainda considera OK
        except Exception as e:
            self.log(f'Erro na API Binance: {e}', 'error')
            self.results['binance'] = {'status': 'error', 'message': str(e)}
            self.status = 'ERROR'
            return False

    def check_dashboard_data(self) -> bool:
        """Verificar se há dados do dashboard."""
        dashboard_file = ROOT_DIR / 'dashboard_data.json'

        if dashboard_file.exists():
            try:
                import json
                with open(dashboard_file, 'r') as f:
                    data = json.load(f)

                last_update = data.get('last_update', 'N/A')
                active_trades = len(data.get('active_trades', {}))

                self.log(f'Dashboard: {active_trades} posições ativas', 'info')
                self.log(f'Última atualização: {last_update}', 'info')

                # Verificar se atualizado recentemente
                if last_update != 'N/A':
                    try:
                        update_time = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                        age = datetime.now() - update_time
                        if age > timedelta(minutes=5):
                            self.log(f'Dados antigos ({age.total_seconds()/60:.0f} min)', 'warning')
                            self.results['dashboard'] = {'status': 'warning', 'age_minutes': age.total_seconds() / 60}
                            return True
                    except:
                        pass

                self.results['dashboard'] = {'status': 'ok', 'active_trades': active_trades}
                return True

            except Exception as e:
                self.log(f'Erro ao ler dashboard: {e}', 'warning')
                self.results['dashboard'] = {'status': 'warning', 'message': str(e)}
                return True
        else:
            self.log('Dashboard data não existe ainda', 'warning')
            self.results['dashboard'] = {'status': 'warning', 'message': 'Sem dados ainda'}
            return True

    def check_disk_space(self) -> bool:
        """Verificar espaço em disco."""
        try:
            import shutil
            from colorama import Fore

            total, used, free = shutil.disk_usage(ROOT_DIR)
            free_gb = free / (1024**3)
            used_pct = (used / total) * 100

            self.log(f'Disco: {free_gb:.1f} GB livre ({used_pct:.0f}% usado)', 'info')

            if free_gb < 0.1:  # Menos de 100MB
                self.log('Disco cheio!', 'error')
                self.results['disk'] = {'status': 'error', 'free_gb': free_gb}
                self.status = 'ERROR'
                return False
            elif free_gb < 0.5:  # Menos de 500MB
                self.log('Disco quase cheio', 'warning')
                self.results['disk'] = {'status': 'warning', 'free_gb': free_gb}
                return True

            self.results['disk'] = {'status': 'ok', 'free_gb': free_gb, 'used_pct': used_pct}
            return True

        except Exception as e:
            self.log(f'Erro ao verificar disco: {e}', 'warning')
            return True

    async def run(self) -> int:
        """Executar todos os checks."""
        self.log(f'=== Health Check Binance Bot ===', 'info')

        checks = [
            ('Database', self.check_database()),
            ('Binance API', self.check_binance_api()),
            ('Dashboard Data', self.check_dashboard_data()),
            ('Disk Space', self.check_disk_space()),
        ]

        for name, coro in checks:
            self.log(f'Checking {name}...', 'info')
            result = await coro if asyncio.iscoroutine(coro) else coro
            # Resultado já salvo no método

        # Resumo
        import json
        print(json.dumps({
            'status': self.status,
            'timestamp': datetime.now().isoformat(),
            'checks': self.results
        }, indent=2))

        if self.status == 'ERROR':
            return 2
        elif any(r.get('status') == 'warning' for r in self.results.values()):
            return 1
        return 0


async def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Health Check do Binance Bot')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Output detalhado')
    args = parser.parse_args()

    checker = HealthChecker(verbose=args.verbose)
    exit_code = await checker.run()

    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
