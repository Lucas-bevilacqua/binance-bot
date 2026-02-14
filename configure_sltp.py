#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configura Stop Loss e Take Profit em posições abertas"""

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


async def get_tick_size_and_step_size(client, symbol):
    """Obter tick size (precisão de preço) e step size do símbolo."""
    try:
        info = await client.futures_exchange_info()
        symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)

        # PRICE_FILTER - tick size
        price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
        tick_size = float(price_filter['tickSize']) if price_filter else 0.01

        # LOT_SIZE - step size
        lot_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
        step_size = float(lot_filter['stepSize']) if lot_filter else 0.001

        # Calcular precisão
        tick_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0

        return tick_size, tick_precision
    except Exception as e:
        print(f"Erro ao obter info: {e}")
        return 0.01, 2


async def configure_sltp_for_position(client, symbol):
    """Configura SL e TP para uma posição."""
    try:
        # Obter posição
        positions = await client.futures_position_information(symbol=symbol)
        position = next(p for p in positions if p['symbol'] == symbol)

        pos_amt = float(position['positionAmt'])

        if abs(pos_amt) == 0:
            print(f"{Fore.YELLOW}⚠️  Nenhuma posição em {symbol}")
            return False

        side = 'LONG' if pos_amt > 0 else 'SHORT'
        entry_price = float(position['entryPrice'])

        # Obter precisão do par
        tick_size, tick_precision = await get_tick_size_and_step_size(client, symbol)

        # Calcular SL e TP
        tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))
        sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))

        if side == 'LONG':
            tp_price = entry_price * (1 + tp_percent)
            sl_price = entry_price * (1 - sl_percent)
            stop_side = 'SELL'
        else:
            tp_price = entry_price * (1 - tp_percent)
            sl_price = entry_price * (1 + sl_percent)
            stop_side = 'BUY'

        # Arredondar para precisão correta
        tp_price = round(tp_price, tick_precision)
        sl_price = round(sl_price, tick_precision)

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  {symbol} - {side}")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.WHITE}Entry: ${entry_price:.{tick_precision}f}")
        print(f"{Fore.GREEN}TP: ${tp_price:.{tick_precision}f} ({tp_percent*100:.1f}%)")
        print(f"{Fore.RED}SL: ${sl_price:.{tick_precision}f} ({sl_percent*100:.1f}%)")

        # Cancelar ordens existentes
        await client.futures_cancel_all_open_orders(symbol=symbol)
        print(f"{Fore.YELLOW}Ordens antigas canceladas")

        # Colocar Stop Loss
        try:
            sl_order = await client.futures_create_order(
                symbol=symbol,
                side=stop_side,
                type='STOP_MARKET',
                stopPrice=sl_price,
                closePosition='true'
            )
            print(f"{Fore.GREEN}✅ SL configurado: ${sl_price:.{tick_precision}f}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no SL: {e}")
            # Tentar com stopPrice em string
            try:
                sl_order = await client.futures_create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='STOP_MARKET',
                    stopPrice=str(sl_price),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ SL configurado (string): ${sl_price:.{tick_precision}f}")
            except Exception as e2:
                print(f"{Fore.RED}❌ Erro no SL (tentativa 2): {e2}")

        # Colocar Take Profit
        try:
            tp_order = await client.futures_create_order(
                symbol=symbol,
                side=stop_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price,
                closePosition='true'
            )
            print(f"{Fore.GREEN}✅ TP configurado: ${tp_price:.{tick_precision}f}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no TP: {e}")
            try:
                tp_order = await client.futures_create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=str(tp_price),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ TP configurado (string): ${tp_price:.{tick_precision}f}")
            except Exception as e2:
                print(f"{Fore.RED}❌ Erro no TP (tentativa 2): {e2}")

        return True

    except Exception as e:
        print(f"{Fore.RED}❌ Erro em {symbol}: {e}")
        return False


async def main():
    """Configura SL/TP para todas as posições abertas."""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    try:
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  CONFIGURAR STOP LOSS E TAKE PROFIT")
        print(f"{Fore.CYAN}{'='*60}\n")

        # Obter posições abertas
        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        if not open_positions:
            print(f"{Fore.YELLOW}⚠️  Nenhuma posição aberta")
            return

        print(f"{Fore.WHITE}Encontradas {len(open_positions)} posição(ões):\n")

        for pos in open_positions:
            symbol = pos['symbol']
            side = 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'
            qty = abs(float(pos['positionAmt']))
            entry = float(pos['entryPrice'])
            pnl = float(pos['unRealizedProfit'])

            pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
            side_color = Fore.GREEN if side == 'LONG' else Fore.RED

            print(f"{side_color}[{symbol}] {side} | Qtd: {qty} | Entry: ${entry:.4f} | PnL: {pnl_color}${pnl:.4f}")

        print()
        confirm = input(f"{Fore.YELLOW}Configurar SL/TP para todas? (s/n): ").lower()

        if confirm != 's':
            print(f"{Fore.YELLOW}Cancelado")
            return

        # Configurar cada posição
        for pos in open_positions:
            await configure_sltp_for_position(client, pos['symbol'])

        print()
        print(f"{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}  CONFIGURAÇÃO CONCLUÍDA!")
        print(f"{Fore.GREEN}{'='*60}")

        # Mostrar ordens abertas
        print()
        print(f"{Fore.CYAN}Verificando ordens abertas...\n")

        for pos in open_positions:
            symbol = pos['symbol']
            try:
                orders = await client.futures_get_open_orders(symbol=symbol)
                if orders:
                    print(f"{Fore.WHITE}{symbol}:")
                    for order in orders:
                        order_type = order['type']
                        order_side = order['side']
                        stop_price = float(order.get('stopPrice', 0))
                        qty = order['origQty']

                        if order_type == 'STOP':
                            color = Fore.RED
                            print(f"  {color}STOP MARKET | {order_side} | Stop: ${stop_price:.4f} | Qtd: {qty}")
                        elif order_type == 'TAKE_PROFIT':
                            color = Fore.GREEN
                            print(f"  {color}TAKE_PROFIT MARKET | {order_side} | Stop: ${stop_price:.4f} | Qtd: {qty}")
                else:
                    print(f"{Fore.YELLOW}{symbol}: Nenhuma ordem aberta")
            except Exception as e:
                print(f"{Fore.RED}Erro ao verificar ordens de {symbol}: {e}")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")

    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
