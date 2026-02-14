#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configurar SL/TP com PRECISÃO CORRETA"""

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


async def get_symbol_info(client, symbol):
    """Obter informações do símbolo incluindo precisão."""
    try:
        info = await client.futures_exchange_info()
        symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)

        # Encontrar PRICE_FILTER
        price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)

        if price_filter:
            tick_size = float(price_filter['tickSize'])
            # Calcular número de casas decimais
            precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
            return precision, tick_size

        return 2, 0.01
    except Exception as e:
        print(f"Erro ao obter info: {e}")
        return 2, 0.01


async def configure_sltp():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    client = await AsyncClient.create(api_key, api_secret)

    try:
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  CONFIGURAR SL/TP (COM PRECISÃO CORRETA)")
        print(f"{Fore.CYAN}{'='*60}\n")

        # Obter posições
        positions = await client.futures_position_information()
        open_positions = [p for p in positions if float(p['positionAmt']) != 0]

        if not open_positions:
            print(f"{Fore.YELLOW}Nenhuma posição aberta")
            return

        tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))
        sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))

        for pos in open_positions:
            symbol = pos['symbol']
            pos_amt = float(pos['positionAmt'])
            entry = float(pos['entryPrice'])
            side = 'SHORT' if pos_amt < 0 else 'LONG'

            # Obter precisão do símbolo
            precision, tick_size = await get_symbol_info(client, symbol)

            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.WHITE}{symbol} - {side}")
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.WHITE}Entry: ${entry:.{precision}f}")
            print(f"{Fore.WHITE}Precisão: {precision} casas decimais")

            # Calcular preços
            if side == 'LONG':
                tp_price = entry * (1 + tp_percent)
                sl_price = entry * (1 - sl_percent)
                stop_side = 'SELL'
            else:
                tp_price = entry * (1 - tp_percent)
                sl_price = entry * (1 + sl_percent)
                stop_side = 'BUY'

            # Arredondar para precisão correta
            tp_rounded = round(tp_price, precision)
            sl_rounded = round(sl_price, precision)

            print(f"{Fore.GREEN}TP: ${tp_rounded:.{precision}f} ({tp_percent*100:.1f}%)")
            print(f"{Fore.RED}SL: ${sl_rounded:.{precision}f} ({sl_percent*100:.1f}%)")

            # Cancelar ordens antigas
            try:
                await client.futures_cancel_all_open_orders(symbol=symbol)
                print(f"{Fore.YELLOW}Ordens antigas canceladas")
            except:
                pass

            # Criar STOP MARKET order
            try:
                sl_order = await client.futures_create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='STOP_MARKET',
                    stopPrice=str(sl_rounded),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ SL criado: ${sl_rounded:.{precision}f} (ID: {sl_order['orderId']})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro SL: {e}")
                # Tentar com price protection
                try:
                    if side == 'SHORT':
                        protected_price = sl_rounded * 1.001  # 0.1% acima
                    else:
                        protected_price = sl_rounded * 0.999  # 0.1% abaixo

                    sl_order = await client.futures_create_order(
                        symbol=symbol,
                        side=stop_side,
                        type='STOP',
                        price=str(round(protected_price, precision)),
                        stopPrice=str(sl_rounded),
                        quantity=str(abs(pos_amt)),
                        timeInForce='GTC'
                    )
                    print(f"{Fore.GREEN}✅ SL criado (STOP): ${sl_rounded:.{precision}f}")
                except Exception as e2:
                    print(f"{Fore.RED}❌ Erro SL (tentativa 2): {e2}")

            # Criar TAKE PROFIT MARKET order
            try:
                tp_order = await client.futures_create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=str(tp_rounded),
                    closePosition='true'
                )
                print(f"{Fore.GREEN}✅ TP criado: ${tp_rounded:.{precision}f} (ID: {tp_order['orderId']})")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro TP: {e}")
                # Tentar LIMIT order
                try:
                    tp_order = await client.futures_create_order(
                        symbol=symbol,
                        side=stop_side,
                        type='LIMIT',
                        price=str(tp_rounded),
                        quantity=str(abs(pos_amt)),
                        timeInForce='GTC'
                    )
                    print(f"{Fore.GREEN}✅ TP criado (LIMIT): ${tp_rounded:.{precision}f}")
                except Exception as e2:
                    print(f"{Fore.RED}❌ Erro TP (tentativa 2): {e2}")

            print()

        # Verificar ordens criadas
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  VERIFICANDO ORDENS CRIADAS")
        print(f"{Fore.CYAN}{'='*60}\n")

        all_orders = await client.futures_get_open_orders()

        if all_orders:
            print(f"{Fore.GREEN}✅ {len(all_orders)} ordem(ns) ativa(s):\n")

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
                    print(f"{color}[{symbol}] STOP LOSS")
                    print(f"   Stop: ${stop_price:.4f} | Qtd: {qty} | ID: {order_id}")
                elif 'TAKE_PROFIT' in order_type:
                    color = Fore.GREEN
                    print(f"{color}[{symbol}] TAKE PROFIT")
                    print(f"   Stop: ${stop_price:.4f} | Qtd: {qty} | ID: {order_id}")
                elif order_type == 'LIMIT':
                    color = Fore.GREEN
                    print(f"{color}[{symbol}] TAKE PROFIT (LIMIT)")
                    print(f"   Price: ${price:.4f} | Qtd: {qty} | ID: {order_id}")
                else:
                    print(f"[{symbol}] {order_type}")
                print()
        else:
            print(f"{Fore.YELLOW}⚠️  Nenhuma ordem ativa encontrada")
            print(f"{Fore.WHITE}Pode haver um problema com a API ou as ordens foram rejeitadas.")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(configure_sltp())
