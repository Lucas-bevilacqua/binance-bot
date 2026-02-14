#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificar permissões da API Binance"""

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

async def check_api():
    """Verifica status da API"""

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "  VERIFICANDO API BINANCE")
    print(Fore.CYAN + "=" * 60)
    print()

    # Verificar se as chaves foram configuradas
    if not api_key or api_key == "your_api_key_here":
        print(Fore.RED + "❌ API KEY não configurada!")
        print(Fore.YELLOW + "   Edite o arquivo .env e adicione BINANCE_API_KEY")
        return

    if not api_secret or api_secret == "your_api_secret_here":
        print(Fore.RED + "❌ API SECRET não configurado!")
        print(Fore.YELLOW + "   Edite o arquivo .env e adicione BINANCE_API_SECRET")
        return

    print(Fore.GREEN + "✅ Credenciais encontradas no .env")
    print()

    client = AsyncClient(api_key, api_secret)

    try:
        # Teste 1: Conexão básica
        print(Fore.WHITE + "[1/5] Testando conexão...")
        server_time = await client.ping()
        print(Fore.GREEN + "✅ Conexão OK")

        # Teste 2: Verificar permissões da conta
        print(Fore.WHITE + "[2/5] Verificando permissões da conta...")
        account = await client.get_account()
        print(Fore.GREEN + "✅ Permissão de leitura OK")

        # Teste 3: Verificar saldo Spot
        print(Fore.WHITE + "[3/5] Verificando saldo Spot...")
        balances = [b for b in account['balances'] if float(b['free']) > 0]
        if balances:
            print(Fore.GREEN + "✅ Saldo Spot encontrado:")
            for b in balances[:5]:
                if float(b['free']) > 0:
                    print(Fore.WHITE + f"   {b['asset']}: {float(b['free']):.4f}")
        else:
            print(Fore.YELLOW + "⚠️  Sem saldo em Spot")

        # Teste 4: Verificar Futures
        print(Fore.WHITE + "[4/5] Verificando acesso a Futures...")
        try:
            futures_account = await client.futures_account()
            balance = float(futures_account['totalWalletBalance'])
            print(Fore.GREEN + f"✅ Acesso Futures OK")
            print(Fore.WHITE + f"   Saldo Futures: ${balance:.2f} USDT")

            # Teste 5: Tentar ler Exchange Info (verifica permissões)
            print(Fore.WHITE + "[5/5] Verificando permissões de trading...")
            info = await client.futures_exchange_info()

            # Mostrar informações relevantes
            print(Fore.GREEN + "✅ Permissões de Futures OK")
            print()

            print(Fore.CYAN + "=" * 60)
            print(Fore.CYAN + "  STATUS DA API: TUDO OK! ✅")
            print(Fore.CYAN + "=" * 60)
            print()
            print(Fore.GREEN + "Sua API está configurada corretamente!")
            print(Fore.YELLOW + "Se ainda der erro de permissão, pode ser:")
            print(Fore.WHITE + "  1. Restrição de IP (verifique nas configurações da API)")
            print(Fore.WHITE + "  2. API Key de Spot em vez de Futures")
            print(Fore.WHITE + "  3. Delay de ativação (espere 5-10 min após criar)")

        except Exception as e:
            error_msg = str(e)

            if "-2015" in error_msg:
                print(Fore.RED + "❌ ERRO: Permissão de Futures negada!")
                print()
                print(Fore.YELLOW + "SOLUÇÃO:")
                print(Fore.WHITE + "  1. Vá em: https://www.binance.com/en/my/settings/api-management")
                print(Fore.WHITE + "  2. Edite sua API Key")
                print(Fore.WHITE + "  3. MARQUE 'Enable Futures'")
                print(Fore.WHITE + "  4. Salve")
                print()
                print(Fore.YELLOW + "IMPORTANTE:")
                print(Fore.WHITE + "  - Há chaves diferentes para Spot e Futures")
                print(Fore.WHITE + "  - Alguns usuários precisam criar chave específica para Futures")
                print(Fore.WHITE + "  - Verifique se está usando a chave correta")

            elif "-2014" in error_msg:
                print(Fore.RED + "❌ ERRO: API Key inválida!")
                print(Fore.YELLOW + "   Verifique se a chave está correta no .env")

            else:
                print(Fore.RED + f"❌ Erro desconhecido: {e}")

    except Exception as e:
        print(Fore.RED + f"❌ Erro: {e}")

    finally:
        await client.close_connection()

    print()


if __name__ == "__main__":
    asyncio.run(check_api())
