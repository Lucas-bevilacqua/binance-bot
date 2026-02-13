#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuração FINAL de SL/TP - cancela tudo e recria"""

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
    """Obter precisão de preço do símbolo."""
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
        print(f"{Fore.CYAN}  CONFIGURAÇÃO FINAL DE SL/TP")
        print(f"{Fore.CYAN}{'='*70}\n")

        # Obter posições
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
            print(f"{Fore.WHITE}Qtd: {abs(pos_amt)}")

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

            # Cancelar TODAS as ordens
            print(f"{Fore.YELLOW}\nCancelando todas as ordens...")
            try:
                result = await client.futures_cancel_all_open_orders(symbol=symbol)
                print(f"{Fore.GREEN}✅ Ordens canceladas")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  {e}")

            # Pequeno delay para garantir cancelamento
            await asyncio.sleep(0.5)

            # Criar STOP LOSS
            print(f"{Fore.WHITE}Criando STOP LOSS...")
            try:
                # Para SHORT: stopPrice é acima, tipo STOP_MARKET
                sl_order = await client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='STOP_MARKET',
                    stopPrice=str(sl_rounded),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ SL criado: ${sl_rounded:.{precision}f} (ID: {sl_order.get('orderId', 'N/A')})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro SL (STOP_MARKET): {e}")

                # Tentar com tipo STOP
                try:
                    sl_order = await client.futures_create_order(
                        symbol=symbol,
                        side=close_side,
                        type='STOP',
                        stopPrice=str(sl_rounded),
                        quantity=str(abs(pos_amt)),
                        timeInForce='GTC'
                    )
                    print(f"{Fore.GREEN}✅ SL criado (STOP): ${sl_rounded:.{precision}f}")
                except Exception as e2:
                    print(f"{Fore.RED}❌ Erro SL (STOP): {e2}")

            # Criar TAKE PROFIT
            print(f"{Fore.WHITE}Criando TAKE PROFIT...")
            try:
                tp_order = await client.futures_create_order(
                    symbol=symbol,
                    side=close_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=str(tp_rounded),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ TP criado: ${tp_rounded:.{precision}f} (ID: {tp_order.get('orderId', 'N/A')})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro TP (TAKE_PROFIT_MARKET): {e}")

                # Tentar com LIMIT
                try:
                    tp_order = await client.futures_create_order(
                        symbol=symbol,
                        side=close_side,
                        type='LIMIT',
                        price=str(tp_rounded),
                        quantity=str(abs(pos_amt)),
                        timeInForce='GTC'
                    )
                    print(f"{Fore.GREEN}✅ TP criado (LIMIT): ${tp_rounded:.{precision}f}")
                except Exception as e2:
                    print(f"{Fore.RED}❌ Erro TP (LIMIT): {e2}")

            print()

        # Verificar resultado final
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.WHITE}VERIFICAÇÃO FINAL")
        print(f"{Fore.CYAN}{'='*70}\n")

        for pos in open_positions:
            symbol = pos['symbol']
            try:
                orders = await client.futures_get_open_orders(symbol=symbol)

                has_sl = any('STOP' in o['type'] for o in orders)
                has_tp = any('TAKE_PROFIT' in o['type'] or o['type'] == 'LIMIT' for o in orders)

                sl_icon = Fore.GREEN + "✅" if has_sl else Fore.RED + "❌"
                tp_icon = Fore.GREEN + "✅" if has_tp else Fore.RED + "❌"

                print(f"{symbol}: {sl_icon} SL | {tp_icon} TP")

                if orders:
                    print(f"   Ordens: {len(orders)}")
                    for o in orders:
                        print(f"   - {o['type']}")
                else:
                    print(f"   Nenhuma ordem!")
            except Exception as e:
                print(f"{symbol}: Erro - {e}")

        print()
        print(f"{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}  CONCLUÍDO!")
        print(f"{Fore.GREEN}{'='*70}")
        print(f"{Fore.WHITE}Verifique na Binance se as ordens estão visíveis")
        print(f"{Fore.WHITE}Futures > Open Orders")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
