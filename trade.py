#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOT DE EXECUÇÃO RÁPIDA - Abre posições automaticamente"""

import asyncio
import os
import sys
import codecs

# Configurar UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from binance import AsyncClient
import dotenv
from colorama import Fore, Style, init

init(autoreset=True)
dotenv.load_dotenv()

async def execute_trade(symbol: str, side: str, quantity: float = None):
    """Executa uma operação de futuros."""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    leverage = int(os.getenv('ALAVANCAGEM_PADRAO', 50))
    risk_percent = float(os.getenv('RISCO_MAXIMO_POR_OPERACAO', 0.12))

    client = await AsyncClient.create(api_key, api_secret)

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + f"  EXECUTANDO OPERAÇÃO: {symbol} - {side}")
    print(Fore.CYAN + "=" * 60)

    try:
        # Obter saldo
        account = await client.futures_account()
        balance = float(account['totalWalletBalance'])

        print(Fore.WHITE + f"Saldo disponível: ${balance:.2f} USDT")
        print(Fore.WHITE + f"Alavancagem: {leverage}x")
        print(Fore.WHITE + f"Risco por operação: {risk_percent * 100:.1f}%")
        print()

        # Configurar alavancagem
        await client.futures_change_leverage(symbol=symbol, leverage=leverage)
        print(Fore.GREEN + f"✅ Alavancagem definida: {leverage}x")

        # Obter preço atual
        ticker = await client.futures_symbol_ticker(symbol=symbol)
        entry_price = float(ticker['price'])
        print(Fore.WHITE + f"Preço atual: ${entry_price:.4f}")

        # Calcular quantidade baseado no risco
        risk_amount = balance * risk_percent

        # SL e TP automáticos (1.5% ATR aprox)
        if side == 'BUY':
            sl_price = entry_price * 0.985  # 1.5% abaixo
            tp_price = entry_price * 1.025  # 2.5% acima
            risk_per_unit = entry_price - sl_price
        else:
            sl_price = entry_price * 1.015  # 1.5% acima
            tp_price = entry_price * 0.975  # 2.5% abaixo
            risk_per_unit = sl_price - entry_price

        # Calcular quantidade
        if quantity is None:
            quantity = (risk_amount * leverage) / entry_price

        # Arredondar para precisão correta
        info = await client.futures_exchange_info()
        symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
        lot_size = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size['stepSize'])
        precision = len(str(step_size).rstrip('0').split('.')[-1])
        quantity = round(quantity, precision)

        print(Fore.WHITE + f"Quantidade: {quantity}")
        print(Fore.RED + f"Stop Loss: ${sl_price:.4f}")
        print(Fore.GREEN + f"Take Profit: ${tp_price:.4f}")

        # Confirmar
        print()
        print(Fore.YELLOW + f"⚠️  CONFIRMAÇÃO DA OPERAÇÃO:")
        print(Fore.WHITE + f"   Par: {symbol}")
        print(Fore.WHITE + f"   Side: {Fore.GREEN if side == 'BUY' else Fore.RED}{side}")
        print(Fore.WHITE + f"   Quantidade: {quantity}")
        print(Fore.WHITE + f"   Entry: ~${entry_price:.4f}")
        print(Fore.RED + f"   SL: ${sl_price:.4f} (1.5%)")
        print(Fore.GREEN + f"   TP: ${tp_price:.4f} (2.5%)")

        # Calcular potencial
        if side == 'BUY':
            potencial_percent = (tp_price - entry_price) / entry_price * leverage * 100
            risco_percent = (entry_price - sl_price) / entry_price * leverage * 100
        else:
            potencial_percent = (entry_price - tp_price) / entry_price * leverage * 100
            risco_percent = (sl_price - entry_price) / entry_price * leverage * 100

        print(Fore.GREEN + f"   POTENCIAL: +{potencial_percent:.1f}%")
        print(Fore.RED + f"   RISCO: -{risco_percent:.1f}%")
        print(Fore.WHITE + f"   Valor em risco: ${risk_amount:.2f}")
        print()

        # Executar ordem
        print(Fore.CYAN + "Enviando ordem...")

        order = await client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )

        print(Fore.GREEN + f"✅ ORDEM EXECUTADA!")
        print(Fore.WHITE + f"   Order ID: {order['orderId']}")

        # Colocar Stop Loss e Take Profit (OCO)
        try:
            # Cancelar ordens existentes primeiro
            await client.futures_cancel_all_open_orders(symbol=symbol)

            # Obter posição real para saber o preço de entrada exato
            position = await client.futures_position_information(symbol=symbol)
            real_entry = float(position[0]['entryPrice'])
            pos_qty = float(position[0]['positionAmt'])

            print()
            print(Fore.CYAN + "Configurando Stop Loss e Take Profit...")
            print(Fore.WHITE + f"   Entry real: ${real_entry:.4f}")

            if side == 'BUY':
                sl = real_entry * 0.985
                tp = real_entry * 1.025
                stop_side = 'SELL'
            else:
                sl = real_entry * 1.015
                tp = real_entry * 0.975
                stop_side = 'BUY'

            # Stop Loss order
            await client.futures_create_order(
                symbol=symbol,
                side=stop_side,
                type='STOP_MARKET',
                stopPrice=sl,
                closePosition='true'
            )

            # Take Profit order
            await client.futures_create_order(
                symbol=symbol,
                side=stop_side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=tp,
                closePosition='true'
            )

            print(Fore.GREEN + f"✅ SL configurado: ${sl:.4f}")
            print(Fore.GREEN + f"✅ TP configurado: ${tp:.4f}")

        except Exception as e:
            print(Fore.YELLOW + f"⚠️  Erro ao configurar SL/TP: {e}")
            print(Fore.YELLOW + f"   Configure manualmente se necessário")

        print()
        print(Fore.GREEN + "=" * 60)
        print(Fore.GREEN + "  OPERAÇÃO ABERTA COM SUCESSO!")
        print(Fore.GREEN + "=" * 60)

    except Exception as e:
        print(Fore.RED + f"❌ Erro: {e}")

    finally:
        await client.close_connection()


async def main():
    """Menu principal."""

    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        side = sys.argv[2].upper() if len(sys.argv) > 2 else 'SELL'
        await execute_trade(symbol, side)
    else:
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + "  BOT DE EXECUÇÃO RÁPIDA")
        print(Fore.CYAN + "=" * 60)
        print()
        print(Fore.WHITE + "Uso:")
        print(Fore.WHITE + "  python trade.py <PAR> <SIDE>")
        print(Fore.WHITE + "")
        print(Fore.WHITE + "Exemplos:")
        print(Fore.GREEN + "  python trade.py ETHUSDT SELL")
        print(Fore.GREEN + "  python trade.py SOLUSDT SELL")
        print(Fore.GREEN + "  python trade.py BTCUSDT BUY")
        print()

        # Executar nas oportunidades do scan
        print(Fore.YELLOW + "Oportunidades do último scan:")
        print(Fore.WHITE + "[1] ETHUSDT SHORT")
        print(Fore.WHITE + "[2] SOLUSDT SHORT")
        print(Fore.WHITE + "[0] Sair")
        print()

        choice = input(Fore.CYAN + "Escolha: ").strip()

        if choice == '1':
            await execute_trade('ETHUSDT', 'SELL')
        elif choice == '2':
            await execute_trade('SOLUSDT', 'SELL')


if __name__ == "__main__":
    asyncio.run(main())
