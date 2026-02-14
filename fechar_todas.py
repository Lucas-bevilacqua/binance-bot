#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fechar todas as posições e ordens"""

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


async def close_all():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    try:
        print(f"\n{Fore.RED}{'='*70}")
        print(f"{Fore.RED}  FECHAR TUDO - Posições e Ordens")
        print(f"{Fore.RED}{'='*70}\n")

        # 1. Cancelar todas as ordens
        print(f"{Fore.YELLOW}[1/3] Cancelando todas as ordens...")
        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        total_orders_cancelled = 0
        for pos in open_positions:
            symbol = pos['symbol']
            try:
                result = await client.futures_cancel_all_open_orders(symbol=symbol)
                total_orders_cancelled += len(result) if isinstance(result, list) else 1
                print(f"  {Fore.GREEN}✅ {symbol} - ordens canceladas")
            except Exception as e:
                print(f"  {Fore.YELLOW}⚠️  {symbol}: {e}")

        print(f"{Fore.GREEN}✅ Total: {total_orders_cancelled} ordens canceladas\n")

        # 2. Fechar todas as posições
        print(f"{Fore.YELLOW}[2/3] Fechando todas as posições...")

        total_pnl = 0
        for pos in open_positions:
            symbol = pos['symbol']
            pos_amt = float(pos['positionAmt'])
            entry = float(pos['entryPrice'])
            pnl = float(pos['unRealizedProfit'])

            if abs(pos_amt) == 0:
                continue

            side = 'SELL' if pos_amt > 0 else 'BUY'

            try:
                order = await client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=abs(pos_amt),
                    reduceOnly='true'
                )

                pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
                print(f"  {pnl_color}{symbol}: ${pnl:+.4f}")

                total_pnl += pnl

            except Exception as e:
                print(f"  {Fore.RED}❌ {symbol}: {e}")

        print()
        pnl_color = Fore.GREEN if total_pnl > 0 else Fore.RED
        print(f"{pnl_color}{'='*70}")
        print(f"{pnl_color}  TOTAL PnL: ${total_pnl:.4f}")
        print(f"{pnl_color}{'='*70}\n")

        # 3. Verificar se ficou algo aberto
        print(f"{Fore.YELLOW}[3/3] Verificando...")
        await asyncio.sleep(1)

        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        if open_positions:
            print(f"{Fore.RED}⚠️  Ainda há posições abertas:")
            for pos in open_positions:
                print(f"   {pos['symbol']}: {pos['positionAmt']}")
        else:
            print(f"{Fore.GREEN}✅ TUDO FECHADO!")

        print()

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(close_all())
