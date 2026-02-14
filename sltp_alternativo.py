#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configurar SL/TP usando método alternativo"""

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


async def get_precision(client, symbol):
    """Obter precisão."""
    try:
        info = await client.futures_exchange_info()
        symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
        price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
        if price_filter:
            tick_size = float(price_filter['tickSize'])
            precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
            return precision
        return 2
    except:
        return 2


async def main():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    try:
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}  CONFIGURAÇÃO ALTERNATIVA DE SL/TP")
        print(f"{Fore.CYAN}{'='*70}\n")

        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))
        sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))

        for pos in open_positions:
            symbol = pos['symbol']
            pos_amt = float(pos['positionAmt'])
            entry = float(pos['entryPrice'])
            side = 'SHORT' if pos_amt < 0 else 'LONG'

            precision = await get_precision(client, symbol)

            print(f"{Fore.CYAN}{'='*70}")
            print(f"{Fore.WHITE}[{symbol}] {side}")
            print(f"{Fore.CYAN}{'='*70}")
            print(f"{Fore.WHITE}Entry: ${entry:.{precision}f}")

            # Calcular preços
            if side == 'LONG':
                tp_price = entry * (1 + tp_percent)
                sl_price = entry * (1 - sl_percent)
                close_side = 'SELL'
            else:
                tp_price = entry * (1 - tp_percent)
                sl_price = entry * (1 + sl_percent)
                close_side = 'BUY'

            tp_rounded = round(tp_price, precision)
            sl_rounded = round(sl_price, precision)

            print(f"{Fore.GREEN}TP: ${tp_rounded:.{precision}f} ({tp_percent*100:.1f}%)")
            print(f"{Fore.RED}SL: ${sl_rounded:.{precision}f} ({sl_percent*100:.1f}%)")

            # Cancelar ordens
            try:
                await client.futures_cancel_all_open_orders(symbol=symbol)
                await asyncio.sleep(0.3)
            except:
                pass

            # MÉTODO 1: Usar STOP_MARKET com reduceOnly (sem closePosition)
            print(f"\n{Fore.WHITE}Tentando STOP_MARKET com reduceOnly...")
            try:
                sl_order = await client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='STOP_MARKET',
                    stopPrice=str(sl_rounded),
                    quantity=str(abs(pos_amt)),
                    reduceOnly='true'
                )
                print(f"{Fore.GREEN}✅ SL criado: ${sl_rounded:.{precision}f} (ID: {sl_order['orderId']})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro: {e}")

            # MÉTODO 2: Usar TAKE_PROFIT_MARKET com reduceOnly
            print(f"{Fore.WHITE}Tentando TAKE_PROFIT_MARKET com reduceOnly...")
            try:
                tp_order = await client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=str(tp_rounded),
                    quantity=str(abs(pos_amt)),
                    reduceOnly='true'
                )
                print(f"{Fore.GREEN}✅ TP criado: ${tp_rounded:.{precision}f} (ID: {tp_order['orderId']})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro: {e}")
                # Fallback para LIMIT
                try:
                    tp_order = await client.futures_create_order(
                        symbol=symbol,
                        side=close_side,
                        type='LIMIT',
                        price=str(tp_rounded),
                        quantity=str(abs(pos_amt)),
                        reduceOnly='true',
                        timeInForce='GTC'
                    )
                    print(f"{Fore.GREEN}✅ TP criado (LIMIT): ${tp_rounded:.{precision}f}")
                except Exception as e2:
                    print(f"{Fore.RED}❌ Erro LIMIT: {e2}")

            print()

        # Verificar
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.WHITE}VERIFICAÇÃO")
        print(f"{Fore.CYAN}{'='*70}\n")

        for pos in open_positions:
            symbol = pos['symbol']
            orders = await client.futures_get_open_orders(symbol=symbol)

            has_sl = any('STOP' in o['type'] for o in orders)
            has_tp = any('TAKE_PROFIT' in o['type'] or 'LIMIT' in o['type'] for o in orders)

            sl_icon = Fore.GREEN + "✅" if has_sl else Fore.RED + "❌"
            tp_icon = Fore.GREEN + "✅" if has_tp else Fore.RED + "❌"

            print(f"{symbol}: {sl_icon} SL | {tp_icon} TP")

            if orders:
                print(f"   Ordens ({len(orders)}):")
                for o in orders:
                    print(f"   - {o['type']} | ID: {o['orderId']} | {o['side']}")
            print()

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
