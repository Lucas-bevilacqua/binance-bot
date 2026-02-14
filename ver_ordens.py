#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ver ordens abertas"""

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
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  VERIFICAR ORDENS ABERTAS")
        print(f"{Fore.CYAN}{'='*60}\n")

        # Obter TODAS as ordens abertas
        print(f"{Fore.WHITE}Buscando todas as ordens abertas...\n")
        all_orders = await client.futures_get_open_orders()

        if not all_orders:
            print(f"{Fore.YELLOW}⚠️  NENHUMA ORDEM ABERTA ENCONTRADA!")
            print()
            print(f"{Fore.WHITE}Isso significa que SL/TP NÃO estão configurados.")
            print(f"{Fore.WHITE}Vou tentar configurar novamente...\n")

            # Configurar novamente
            positions = await client.futures_position_information()
            open_positions = [p for p in positions if float(p['positionAmt']) != 0]

            for pos in open_positions:
                symbol = pos['symbol']
                pos_amt = float(pos['positionAmt'])
                side = 'SHORT' if pos_amt < 0 else 'LONG'
                entry = float(pos['entryPrice'])

                print(f"{Fore.CYAN}Configurando {symbol}...")

                # Calcular SL e TP
                tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))
                sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))

                if side == 'LONG':
                    tp_price = entry * (1 + tp_percent)
                    sl_price = entry * (1 - sl_percent)
                    stop_side = 'SELL'
                else:
                    tp_price = entry * (1 - tp_percent)
                    sl_price = entry * (1 + sl_percent)
                    stop_side = 'BUY'

                # Usar OCO order (One-Cancels-the-Other)
                try:
                    print(f"  Entry: ${entry:.4f}")
                    print(f"  TP: ${tp_price:.4f}")
                    print(f"  SL: ${sl_price:.4f}")

                    # Tentar OCO
                    oco_order = await client.futures_create_oco_order(
                        symbol=symbol,
                        side=stop_side,
                        quantity=abs(pos_amt),
                        price=str(tp_price),
                        stopPrice=str(sl_price),
                        stopLimitPrice=str(sl_price),
                        stopLimitTimeInForce='GTX'
                    )

                    print(f"  {Fore.GREEN}✅ OCO order criada!")

                except Exception as e:
                    print(f"  {Fore.RED}❌ Erro OCO: {e}")
                    print(f"  {Fore.YELLOW}Tentando ordens separadas...")

                    # Tentar ordens separadas
                    try:
                        # Stop Loss
                        sl_order = await client.futures_create_order(
                            symbol=symbol,
                            side=stop_side,
                            type='STOP_MARKET',
                            stopPrice=sl_price,
                            closePosition='true'
                        )
                        print(f"  {Fore.GREEN}✅ SL criado (ID: {sl_order['orderId']})")
                    except Exception as e2:
                        print(f"  {Fore.RED}❌ Erro SL: {e2}")

                    try:
                        # Take Profit
                        tp_order = await client.futures_create_order(
                            symbol=symbol,
                            side=stop_side,
                            type='LIMIT_MAKER',
                            price=tp_price,
                            quantity=abs(pos_amt),
                            timeInForce='GTC'
                        )
                        print(f"  {Fore.GREEN}✅ TP criado (ID: {tp_order['orderId']})")
                    except Exception as e3:
                        print(f"  {Fore.RED}❌ Erro TP: {e3}")

                print()

            # Verificar novamente
            print(f"{Fore.CYAN}Verificando novamente...\n")
            all_orders = await client.futures_get_open_orders()

        # Mostrar ordens encontradas
        if all_orders:
            print(f"{Fore.GREEN}✅ {len(all_orders)} ordem(ns) encontrada(s):\n")

            for order in all_orders:
                symbol = order['symbol']
                order_type = order['type']
                side = order['side']
                price = float(order.get('price', 0))
                stop_price = float(order.get('stopPrice', 0))
                qty = order['origQty']
                order_id = order['orderId']

                if order_type == 'STOP':
                    color = Fore.RED
                    print(f"{color}[{symbol}] STOP | {side}")
                    print(f"   Stop: ${stop_price:.4f} | Qtd: {qty} | ID: {order_id}")
                elif order_type == 'LIMIT_MAKER' or order_type == 'LIMIT':
                    color = Fore.GREEN
                    print(f"{color}[{symbol}] TAKE PROFIT | {side}")
                    print(f"   Price: ${price:.4f} | Qtd: {qty} | ID: {order_id}")
                elif order_type == 'MARKET':
                    color = Fore.YELLOW
                    print(f"{color}[{symbol}] MARKET | {side} | Qtd: {qty}")
                else:
                    print(f"[{symbol}] {order_type} | {side} | ${price:.4f}")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")

    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
