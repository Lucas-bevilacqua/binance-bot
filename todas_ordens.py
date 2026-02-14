#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mostrar TODAS as ordens de todas as posições"""

import asyncio
import os
import sys
import codecs

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from binance import AsyncClient
from colorama import Fore, Style, init
import dotenv

init(autoreset=True)
dotenv.load_dotenv()


async def main():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    try:
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}  TODAS AS ORDENS ABERTAS")
        print(f"{Fore.CYAN}{'='*70}\n")

        # Mostrar posições
        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        print(f"{Fore.WHITE}POSIÇÕES ABERTAS:\n")
        for pos in open_positions:
            symbol = pos['symbol']
            pos_amt = float(pos['positionAmt'])
            entry = float(pos['entryPrice'])
            pnl = float(pos['unRealizedProfit'])
            side = 'LONG' if pos_amt > 0 else 'SHORT'

            pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
            side_color = Fore.GREEN if side == 'LONG' else Fore.RED

            print(f"{side_color}[{symbol}] {side} | Qtd: {abs(pos_amt)} | Entry: ${entry:.4f} | PnL: {pnl_color}${pnl:.4f}")

        print()

        # Mostrar TODAS as ordens para cada posição
        for pos in open_positions:
            symbol = pos['symbol']

            try:
                orders = await client.futures_get_open_orders(symbol=symbol)

                print(f"{Fore.CYAN}{'='*70}")
                print(f"{Fore.WHITE}ORDENS DE {symbol}:")
                print(f"{Fore.CYAN}{'='*70}")

                if orders:
                    for order in orders:
                        order_type = order['type']
                        side = order['side']
                        price = float(order.get('price', 0))
                        stop_price = float(order.get('stopPrice', 0))
                        qty = order['origQty']
                        order_id = order['orderId']
                        status = order.get('status', 'UNKNOWN')

                        if order_type == 'STOP' or 'STOP' in order_type:
                            color = Fore.RED
                            tipo = "🛑 STOP LOSS"
                        elif 'TAKE_PROFIT' in order_type or order_type == 'LIMIT':
                            color = Fore.GREEN
                            tipo = "🎯 TAKE PROFIT"
                        else:
                            color = Fore.WHITE
                            tipo = order_type

                        print(f"\n{color}{tipo}")
                        print(f"   Tipo: {order_type}")
                        print(f"   Side: {side}")
                        if stop_price > 0:
                            print(f"   Stop Price: ${stop_price:.4f}")
                        if price > 0:
                            print(f"   Price: ${price:.4f}")
                        print(f"   Quantidade: {qty}")
                        print(f"   Order ID: {order_id}")
                        print(f"   Status: {status}")
                else:
                    print(f"{Fore.YELLOW}⚠️  Nenhuma ordem para {symbol}")

            except Exception as e:
                print(f"{Fore.RED}Erro ao buscar ordens de {symbol}: {e}")

            print()

        # Resumo
        all_orders = await client.futures_get_open_orders()

        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.WHITE}RESUMO:")
        print(f"{Fore.GREEN}✅ Posições abertas: {len(open_positions)}")
        print(f"{Fore.GREEN}✅ Ordens ativas: {len(all_orders)}")
        print(f"{Fore.CYAN}{'='*70}\n")

        # Verificar se cada posição tem SL e TP
        for pos in open_positions:
            symbol = pos['symbol']
            orders = await client.futures_get_open_orders(symbol=symbol)

            has_sl = any('STOP' in o['type'] for o in orders)
            has_tp = any('TAKE_PROFIT' in o['type'] or o['type'] == 'LIMIT' for o in orders)

            sl_icon = Fore.GREEN + "✅" if has_sl else Fore.RED + "❌"
            tp_icon = Fore.GREEN + "✅" if has_tp else Fore.RED + "❌"

            print(f"{symbol}: {sl_icon} SL | {tp_icon} TP")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
