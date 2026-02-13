#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fechar posição"""

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

async def close_position(symbol: str):
    """Fecha uma posição"""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + f"  FECHAR POSIÇÃO: {symbol}")
    print(Fore.CYAN + "=" * 60)
    print()

    try:
        # Obter posição
        position = await client.futures_position_information(symbol=symbol)
        pos_amt = float(position[0]['positionAmt'])
        entry_price = float(position[0]['entryPrice'])
        unrealized_pnl = float(position[0]['unRealizedProfit'])

        if abs(pos_amt) == 0:
            print(Fore.YELLOW + f"⚠️  Nenhuma posição aberta em {symbol}")
            return

        side = 'LONG 🚀' if pos_amt > 0 else 'SHORT 🔻'
        print(Fore.WHITE + f"Posição atual: {side}")
        print(Fore.WHITE + f"Quantidade: {abs(pos_amt)}")
        print(Fore.WHITE + f"Entry: ${entry_price:.4f}")
        print(Fore.WHITE + f"PnL não realizado: ${unrealized_pnl:.4f}")
        print()

        # Confirmar
        confirm = input(Fore.YELLOW + "Confirmar fechamento? (s/n): ").lower()

        if confirm != 's':
            print(Fore.YELLOW + "Operação cancelada")
            return

        # Fechar posição
        close_side = 'SELL' if pos_amt > 0 else 'BUY'

        print()
        print(Fore.CYAN + "Fechando posição...")

        # Cancelar ordens abertas primeiro
        await client.futures_cancel_all_open_orders(symbol=symbol)

        order = await client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type='MARKET',
            quantity=abs(pos_amt),
            reduceOnly='true'
        )

        print(Fore.GREEN + f"✅ Posição fechada!")
        print(Fore.WHITE + f"   Order ID: {order['orderId']}")
        print(Fore.WHITE + f"   Quantidade: {abs(pos_amt)}")

        # Obter resultado final
        await asyncio.sleep(1)
        new_position = await client.futures_position_information(symbol=symbol)
        new_pnl = float(new_position[0]['unRealizedProfit'])

        print()
        if unrealized_pnl > 0:
            print(Fore.GREEN + f"🎉 LUCRO: ${unrealized_pnl:.4f}")
        else:
            print(Fore.RED + f"📉 PREJUÍZO: ${unrealized_pnl:.4f}")

    except Exception as e:
        print(Fore.RED + f"❌ Erro: {e}")

    finally:
        await client.close_connection()

    print()


async def close_all():
    """Fecha todas as posições"""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "  FECHAR TODAS AS POSIÇÕES")
    print(Fore.CYAN + "=" * 60)
    print()

    try:
        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        if not open_positions:
            print(Fore.YELLOW + "⚠️  Nenhuma posição aberta")
            return

        total_pnl = 0

        for pos in open_positions:
            symbol = pos['symbol']
            pos_amt = float(pos['positionAmt'])
            pnl = float(pos['unRealizedProfit'])

            print(Fore.WHITE + f"Fechando {symbol}...")

            # Cancelar ordens
            await client.futures_cancel_all_open_orders(symbol=symbol)

            # Fechar posição
            close_side = 'SELL' if pos_amt > 0 else 'BUY'

            await client.futures_create_order(
                symbol=symbol,
                side=close_side,
                type='MARKET',
                quantity=abs(pos_amt),
                reduceOnly='true'
            )

            print(Fore.GREEN + f"✅ {symbol} fechada | PnL: ${pnl:.4f}")
            total_pnl += pnl

        print()
        print(Fore.CYAN + "-" * 60)
        if total_pnl > 0:
            print(Fore.GREEN + f"TOTAL LUCRO: ${total_pnl:.4f}")
        else:
            print(Fore.RED + f"TOTAL PREJUÍZO: ${total_pnl:.4f}")
        print(Fore.CYAN + "-" * 60)

    except Exception as e:
        print(Fore.RED + f"❌ Erro: {e}")

    finally:
        await client.close_connection()


async def main():
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()

        if symbol == "ALL":
            await close_all()
        else:
            await close_position(symbol)
    else:
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + "  FECHAR POSIÇÃO")
        print(Fore.CYAN + "=" * 60)
        print()
        print(Fore.WHITE + "Uso:")
        print(Fore.WHITE + "  python close.py <PAR>")
        print(Fore.WHITE + "  python close.py ALL")
        print()
        print(Fore.WHITE + "Exemplos:")
        print(Fore.GREEN + "  python close.py SOLUSDT")
        print(Fore.GREEN + "  python close.py ETHUSDT")
        print(Fore.GREEN + "  python close.py ALL")


if __name__ == "__main__":
    asyncio.run(main())
