#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor de posições em tempo real"""

import asyncio
import os
import sys
import codecs
from datetime import datetime

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from binance import AsyncClient
from colorama import Fore, Style, init
import dotenv

init(autoreset=True)
dotenv.load_dotenv()

async def monitor():
    """Monitora posições em tempo real"""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    tp_target = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))

    client = await AsyncClient.create(api_key, api_secret)

    print(Fore.CYAN + "=" * 70)
    print(Fore.CYAN + "  MONITOR DE POSIÇÕES - TEMPO REAL")
    print(Fore.CYAN + "=" * 70)
    print(Fore.YELLOW + "Pressione Ctrl+C para parar")
    print()

    try:
        while True:
            # Limpar tela (opcional)
            # os.system('cls' if os.name == 'nt' else 'clear')

            print(Fore.CYAN + "=" * 70)
            print(Fore.WHITE + f"  Atualizado: {datetime.now().strftime('%H:%M:%S')}")
            print(Fore.CYAN + "=" * 70)
            print()

            # Obter posições
            positions = await client.futures_position_information()

            # Filtrar apenas posições abertas
            open_positions = [p for p in positions if float(p['positionAmt']) != 0]

            if not open_positions:
                print(Fore.YELLOW + "⚠️  Nenhuma posição aberta")
            else:
                print(Fore.WHITE + f"Posições abertas: {len(open_positions)}")
                print()

                total_pnl = 0
                total_roe = 0

                for pos in open_positions:
                    symbol = pos['symbol']
                    side = 'LONG 🚀' if float(pos['positionAmt']) > 0 else 'SHORT 🔻'
                    quantity = abs(float(pos['positionAmt']))
                    entry_price = float(pos['entryPrice'])
                    mark_price = float(pos['markPrice'])
                    unrealized_pnl = float(pos['unRealizedProfit'])
                    # Calcular ROE manualmente
                    notional = float(pos.get('notional', entry_price * quantity))
                    if notional > 0:
                        roe = (unrealized_pnl / notional) * 100
                    else:
                        roe = 0

                    total_pnl += unrealized_pnl
                    total_roe += roe

                    # Cores baseadas em lucro/prejuízo
                    pnl_color = Fore.GREEN if unrealized_pnl > 0 else Fore.RED
                    roe_color = Fore.GREEN if roe > 0 else Fore.RED
                    side_color = Fore.GREEN if float(pos['positionAmt']) > 0 else Fore.RED

                    # Calcular distância do TP
                    if side == 'LONG 🚀':
                        tp_price = entry_price * (1 + tp_target)
                        sl_price = entry_price * 0.985
                        dist_tp = ((tp_price - mark_price) / entry_price) * 100
                        dist_sl = ((mark_price - sl_price) / entry_price) * 100
                    else:
                        tp_price = entry_price * (1 - tp_target)
                        sl_price = entry_price * 1.015
                        dist_tp = ((mark_price - tp_price) / entry_price) * 100
                        dist_sl = ((sl_price - mark_price) / entry_price) * 100

                    print(side_color + f"[{symbol}]")
                    print(Fore.WHITE + f"   Side:     {side}")
                    print(Fore.WHITE + f"   Quant:    {quantity}")
                    print(Fore.WHITE + f"   Entry:    ${entry_price:.4f}")
                    print(Fore.WHITE + f"   Atual:    ${mark_price:.4f}")
                    print(pnl_color + f"   PnL:      ${unrealized_pnl:.4f}")
                    print(roe_color + f"   ROE:      {roe:.2f}%")
                    print(Fore.CYAN + f"   TP:       ${tp_price:.4f} (dist: {abs(dist_tp):.2f}%)")
                    print(Fore.RED + f"   SL:       ${sl_price:.4f} (dist: {abs(dist_sl):.2f}%)")
                    print()

                # Total
                total_color = Fore.GREEN if total_pnl > 0 else Fore.RED
                print(Fore.CYAN + "-" * 70)
                print(total_color + f"   TOTAL PnL: ${total_pnl:.4f}")
                print(total_color + f"   TOTAL ROE: {total_roe:.2f}%")
                print(Fore.CYAN + "-" * 70)

            print()
            print(Fore.YELLOW + "Atualizando em 5 segundos...", end="\r")

            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print()
        print()
        print(Fore.YELLOW + "Monitor encerrado")
    finally:
        await client.close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print()
        print(Fore.YELLOW + "Encerrado...")
