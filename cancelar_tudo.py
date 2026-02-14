#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cancelar TODAS as ordens por todos os métodos"""

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
        print(f"{Fore.RED}{'='*70}")
        print(f"{Fore.RED}  CANCELAR TODAS AS ORDENS - MODO AGRESSIVO")
        print(f"{Fore.RED}{'='*70}\n")

        # Símbolos com posições
        symbols = ['SOLUSDT', 'ETHUSDT']

        for symbol in symbols:
            print(f"{Fore.CYAN}{'='*70}")
            print(f"{Fore.WHITE}Processando {symbol}...")
            print(f"{Fore.CYAN}{'='*70}")

            # 1. Listar TODAS as ordens primeiro
            try:
                orders = await client.futures_get_open_orders(symbol=symbol)
                print(f"{Fore.WHITE}Ordens encontradas: {len(orders)}")

                for o in orders:
                    print(f"   ID: {o['orderId']} | Tipo: {o['type']} | Side: {o['side']}")

                    # Cancelar cada ordem individualmente
                    try:
                        result = await client.futures_cancel_order(
                            symbol=symbol,
                            orderId=o['orderId']
                        )
                        print(f"   {Fore.GREEN}✅ Cancelada")
                    except Exception as e:
                        print(f"   {Fore.RED}❌ Erro: {e}")

            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Erro ao listar: {e}")

            # 2. Tentar cancelar todas de uma vez
            print(f"{Fore.YELLOW}Tentando cancel_all_open_orders...")
            try:
                result = await client.futures_cancel_all_open_orders(symbol=symbol)
                print(f"{Fore.GREEN}✅ cancel_all_open_orders OK")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  {e}")

            # 3. Tentar cancelar por tipo STOP
            print(f"{Fore.YELLOW}Verificando ordens STOP específicas...")
            await asyncio.sleep(0.5)

            try:
                orders = await client.futures_get_open_orders(symbol=symbol)
                stop_orders = [o for o in orders if 'STOP' in o['type']]

                if stop_orders:
                    print(f"{Fore.WHITE}Encontradas {len(stop_orders)} ordens STOP:")
                    for o in stop_orders:
                        print(f"   {o['type']} - {o['orderId']}")

                        try:
                            # Tentar método específico para STOP
                            result = await client.futures_cancel_order(
                                symbol=symbol,
                                orderId=o['orderId']
                            )
                            print(f"   {Fore.GREEN}✅ STOP cancelada")
                        except Exception as e:
                            print(f"   {Fore.RED}❌ Erro: {e}")
                else:
                    print(f"{Fore.GREEN}Nenhuma ordem STOP encontrada")

            except Exception as e:
                print(f"{Fore.RED}Erro: {e}")

            print()

        # Verificação final
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.WHITE}VERIFICAÇÃO FINAL")
        print(f"{Fore.CYAN}{'='*70}\n")

        for symbol in symbols:
            try:
                orders = await client.futures_get_open_orders(symbol=symbol)

                if orders:
                    print(f"{Fore.RED}{symbol}: AINDA TEM {len(orders)} ordem(ns)")
                    for o in orders:
                        print(f"   - {o['type']} (ID: {o['orderId']})")
                else:
                    print(f"{Fore.GREEN}{symbol}: ✅ LIMPO")
            except Exception as e:
                print(f"{symbol}: Erro - {e}")

        print()
        print(f"{Fore.YELLOW}Se ainda houver ordens, cancelec MANUALMENTE na Binance:")
        print(f"{Fore.WHITE}https://www.binance.com/en/futures/trading")
        print(f"{Fore.WHITE}> Aba 'Open Orders' > Cancel All")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close_connection()


if __name__ == "__main__":
    asyncio.run(main())
