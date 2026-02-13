#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug detalhado da API"""

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

async def debug():
    """Debug detalhado"""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "  DEBUG DETALHADO DA API")
    print(Fore.CYAN + "=" * 60)
    print()

    client = AsyncClient(api_key, api_secret)

    try:
        # Testar mudança de alavancagem
        print(Fore.WHITE + "[1/3] Testando mudança de alavancagem...")
        try:
            result = await client.futures_change_leverage(symbol='BTCUSDT', leverage=20)
            print(Fore.GREEN + f"✅ Alavancagem: {result}")
            print(Fore.WHITE + f"   leverage: {result.get('leverage', 'N/A')}")
            print(Fore.WHITE + f"   maxNotionalValue: {result.get('maxNotionalValue', 'N/A')}")
        except Exception as e:
            print(Fore.RED + f"❌ Erro: {e}")

        print()

        # Testar obter posições
        print(Fore.WHITE + "[2/3] Testando leitura de posições...")
        try:
            positions = await client.futures_position_information()
            print(Fore.GREEN + f"✅ Posições obtidas: {len(positions)} pares")
        except Exception as e:
            print(Fore.RED + f"❌ Erro: {e}")

        print()

        # Testar obter ordens abertas
        print(Fore.WHITE + "[3/3] Testando leitura de ordens abertas...")
        try:
            orders = await client.futures_get_open_orders(symbol='BTCUSDT')
            print(Fore.GREEN + f"✅ Ordens abertas: {len(orders)}")
        except Exception as e:
            print(Fore.RED + f"❌ Erro: {e}")

        print()
        print(Fore.CYAN + "=" * 60)
        print(Fore.YELLOW + "Se deu erro em [1/3], o problema é:")
        print(Fore.WHITE + "  - API key não tem permissão de 'Enable Futures'")
        print(Fore.WHITE + "  - Ou você está usando API key de Spot")
        print(Fore.WHITE + "  - Ou há restrição de IP")
        print()
        print(Fore.YELLOW + "SOLUÇÕES:")
        print(Fore.WHITE + "  1. Vá em: binance.com > API Management")
        print(Fore.WHITE + "  2. Crie NOVA API Key especificamente para Futures")
        print(Fore.WHITE + "  3. Marque: Enable Reading + Enable Futures")
        print(Fore.WHITE + "  4. NÃO marque IP restriction (por enquanto)")
        print(Fore.WHITE + "  5. Salve e atualize o .env")
        print(Fore.CYAN + "=" * 60)

    except Exception as e:
        print(Fore.RED + f"❌ Erro geral: {e}")

    finally:
        await client.close_connection()

if __name__ == "__main__":
    asyncio.run(debug())
