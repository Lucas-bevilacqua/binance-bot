"""
🔌 BANCÊ BOT MASTER INTEGRAÇÃO POSTGRESQL
==============================================
Adaptador para adicionar persistência PostgreSQL ao bot_master.py existente.

Modo de uso:
    No topo do bot_master.py, adicionar:
        from database.db_integration import BotWithPersistence

    E substituir:
        bot = AutonomousBot()
    por:
        bot = BotWithPersistence()  # Wrapper com persistência
"""

import asyncio
import os
from datetime import datetime
from typing import Dict

from database.repositories import get_trade_repo, get_position_repo, close_repos


class BotWithPersistence:
    """
    Wrapper que adiciona persistência PostgreSQL ao AutonomousBot.

    Intercepta chamadas críticas e salva no banco automaticamente.
    """

    def __init__(self, bot_instance=None):
        """
        Criar wrapper com ou sem instância do bot.

        Se bot_instance for None, cria instância padrão AutonomousBot.
        """
        if bot_instance is None:
            # Import tardio para evitar circular import
            from bot_master import AutonomousBot
            self._bot = AutonomousBot()
        else:
            self._bot = bot_instance

        self._trade_repo = None
        self._position_repo = None

    def __getattr__(self, name):
        """Delegar atributos não modificados para o bot original."""
        return getattr(self._bot, name)

    async def start(self):
        """Iniciar bot com persistência PostgreSQL."""
        from colorama import Fore

        try:
            # Conectar ao banco
            self._trade_repo = await get_trade_repo()
            self._position_repo = await get_position_repo()

            print(f"{Fore.GREEN}✅ Persistência PostgreSQL ativa")

            # Migrar dados JSON existentes
            from database.repositories import migrate_json_to_db
            await migrate_json_to_db(self._trade_repo)

            # Sincronizar posições do banco
            await self._sync_positions_from_db()

            # Iniciar bot original
            await self._bot.start()

        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao iniciar persistência: {e}")
            # Fallback: iniciar sem persistência
            await self._bot.start()

    async def _sync_positions_from_db(self):
        """Carregar posições salvas do banco para memória do bot."""
        from colorama import Fore

        try:
            saved_positions = await self._position_repo.get_all_positions()

            for symbol, pos in saved_positions.items():
                self._bot.active_trades[symbol] = {
                    'side': pos['side'],
                    'entry': pos['entry_price'],
                    'sl': pos['sl'],
                    'tp': pos['tp'],
                    'quantity': pos['quantity'],
                    'entry_time': pos['opened_at'],
                    'sl_order_id': pos.get('sl_order_id'),
                    'tp_order_id': pos.get('tp_order_id')
                }

            if saved_positions:
                print(f"{Fore.CYAN}📥 {len(saved_positions)} posições recuperadas do banco")

        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Aviso ao recuperar posições: {e}")

    async def enter_trade(self, opp: Dict) -> bool:
        """
        Entrar no trade E salvar no banco.

        Wrapper que:
        1. Chama enter_trade original do bot
        2. Salva trade no banco
        3. Salva posição no banco
        """
        result = await self._bot.enter_trade(opp)

        if result and self._trade_repo:
            # Trade aberto com sucesso - salvar no banco
            await self._save_trade_to_db(opp)

        return result

    async def _save_trade_to_db(self, opp: Dict):
        """Salvar trade aberto no banco de dados."""
        try:
            # Buscar ordem criada pelo bot
            symbol = opp['symbol']
            if symbol not in self._bot.active_trades:
                return

            trade = self._bot.active_trades[symbol]

            # Salvar trade
            trade_id = await self._trade_repo.save_trade({
                'symbol': symbol,
                'side': opp['trend'],
                'quantity': trade['quantity'],
                'entry_price': trade['entry'],
                'sl_price': trade['sl'],
                'tp_price': trade['tp'],
                'entry_time': trade['entry_time'],
                'status': 'OPEN',
                'entry_order_id': trade.get('order_id'),
                'sl_order_id': trade.get('sl_order_id'),
                'tp_order_id': trade.get('tp_order_id')
            })

            # Salvar posição
            await self._position_repo.save_position({
                'symbol': symbol,
                'side': trade['side'],
                'quantity': trade['quantity'],
                'entry_price': trade['entry'],
                'current_price': trade.get('current_price', trade['entry']),
                'sl_price': trade['sl'],
                'tp_price': trade['tp'],
                'entry_order_id': trade.get('order_id'),
                'sl_order_id': trade.get('sl_order_id'),
                'tp_order_id': trade.get('tp_order_id')
            })

        except Exception as e:
            print(f"⚠️ Erro ao salvar no banco: {e}")

    async def monitor_positions(self):
        """
        Monitorar posições E atualizar banco.

        Wrapper que:
        1. Chama monitor_positions original
        2. Atualiza PnL no banco
        3. Remove posições fechadas
        """
        from colorama import Fore

        # Chamar monitoramento original
        await self._bot.monitor_positions()

        # Atualizar banco se posições mudaram
        if self._position_repo:
            await self._update_positions_in_db()

    async def _update_positions_in_db(self):
        """Atualizar posições ativas no banco."""
        try:
            for symbol, trade in self._bot.active_trades.items():
                await self._position_repo.save_position({
                    'symbol': symbol,
                    'side': trade['side'],
                    'quantity': trade['quantity'],
                    'entry_price': trade['entry'],
                    'current_price': trade.get('current_price', trade['entry']),
                    'sl_price': trade['sl'],
                    'tp_price': trade['tp'],
                    'unrealized_pnl': trade.get('current_pnl', 0),
                    'unrealized_percent': trade.get('current_pnl_percent', 0),
                    'sl_order_id': trade.get('sl_order_id'),
                    'tp_order_id': trade.get('tp_order_id')
                })

        except Exception as e:
            print(f"⚠️ Erro ao atualizar posições: {e}")

    async def close_position(self, symbol: str):
        """
        Fechar posição E registrar no banco.

        Wrapper que:
        1. Fecha posição (chamando original)
        2. Registra PnL final no banco
        3. Remove da tabela de posições
        """
        from colorama import Fore

        # Buscar PnL antes de fechar
        pnl = 0.0
        pnl_percent = 0.0
        exit_price = 0.0

        if symbol in self._bot.active_trades:
            trade = self._bot.active_trades[symbol]
            pnl = trade.get('current_pnl', 0)
            pnl_percent = trade.get('current_pnl_percent', 0)
            exit_price = trade.get('current_price', trade['entry'])

        # Fechar posição (método original)
        await self._bot.close_position(symbol)

        # Atualizar banco se ainda tivermos dados
        if self._trade_repo and symbol in self._bot.active_trades:
            try:
                # Buscar trade_id (pelo entry_order_id)
                entry_order_id = self._bot.active_trades[symbol].get('order_id')

                if entry_order_id:
                    await self._trade_repo.close_trade(
                        entry_order_id,  # Usando order_id como identificador
                        exit_price,
                        pnl,
                        pnl_percent,
                        'TP' if pnl > 0 else 'SL'
                    )

                # Remover da tabela de posições
                await self._position_repo.delete_position(symbol)

            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Erro ao fechar no banco: {e}")

    def save_dashboard_state(self):
        """Salvar estado para dashboard (agora com dados do banco)."""
        # Implementação futura: buscar do banco ao invés de JSON
        self._bot.save_dashboard_state()

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await close_repos()


# ============================================================================
# FUNÇÃO MAIN MODIFICADA
# ============================================================================

async def main_with_persistence():
    """
    Main function com persistência PostgreSQL.

    Substituir a main() original por esta no bot_master.py.
    """
    from colorama import Fore

    try:
        bot = BotWithPersistence()
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")
    finally:
        await close_repos()
        print(f"{Fore.CYAN}🔌 Conexões fechadas")


# ============================================================================
# COMPATIBILIDADE COM DASHBOARD
# ============================================================================

async def get_dashboard_data_from_db() -> Dict:
    """
    Buscar dados do dashboard diretamente do PostgreSQL.

    Substitui a leitura de dashboard_data.json.
    """
    from colorama import Fore

    try:
        trade_repo = await get_trade_repo()
        position_repo = await get_position_repo()

        return {
            'active_trades': await position_repo.get_all_positions(),
            'history': await trade_repo.get_trade_history(),
            'daily_metrics': await trade_repo.get_daily_metrics(),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        print(f"{Fore.RED}Erro ao buscar dados do banco: {e}")
        return {}


if __name__ == "__main__":
    """Testar integração."""
    import asyncio
    asyncio.run(main_with_persistence())
