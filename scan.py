#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scanner rápido de oportunidades - Multiplique seu capital!"""

import asyncio
import os
import sys
import codecs

# Configurar UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

import pandas as pd
from binance import AsyncClient
import dotenv
from colorama import Fore, Style, init

init(autoreset=True)
dotenv.load_dotenv()

async def scan():
    """Scan rápido de oportunidades."""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    leverage = int(os.getenv('ALAVANCAGEM_PADRAO', 50))

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "  SCANNER AGRESSIVO - MULTIPLICAR CAPITAL")
    print(Fore.CYAN + "=" * 60)
    print()

    client = await AsyncClient.create(api_key, api_secret)

    # Pares para escanear
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
        'MATICUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT'
    ]

    opportunities = []

    for symbol in symbols:
        try:
            # Obter candles
            klines = await client.futures_klines(symbol=symbol, interval='15m', limit=100)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)

            # Indicadores
            df['ema_9'] = df['close'].ewm(span=9).mean()
            df['ema_21'] = df['close'].ewm(span=21).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()

            # Bollinger
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

            latest = df.iloc[-1]

            # Score
            bullish_score = 0
            bearish_score = 0

            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                bullish_score += 25
            elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                bearish_score += 25

            if latest['rsi'] < 30:
                bullish_score += 20
            elif latest['rsi'] > 70:
                bearish_score += 20

            if latest['macd'] - latest['macd_signal'] > 0:
                bullish_score += 15
            else:
                bearish_score += 15

            if latest['close'] < latest['bb_lower']:
                bullish_score += 15
            elif latest['close'] > latest['bb_upper']:
                bearish_score += 15

            # Volume
            vol_ma = df['volume'].rolling(20).mean().iloc[-1]
            if latest['volume'] > vol_ma * 1.5:
                bullish_score += 10
                bearish_score += 10

            trend = 'NEUTRAL'
            strength = max(bullish_score, bearish_score)

            if bullish_score > bearish_score + 20:
                trend = 'LONG'
            elif bearish_score > bullish_score + 20:
                trend = 'SHORT'

            if strength >= 40:  # Reduzi de 50 para 40 (mais oportunidades)
                # Calcular TP e SL
                entry = latest['close']
                atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]

                if trend == 'LONG':
                    sl = entry - (atr * 1.5)
                    tp1 = entry + (atr * 2)
                    tp2 = entry + (atr * 4)
                else:
                    sl = entry + (atr * 1.5)
                    tp1 = entry - (atr * 2)
                    tp2 = entry - (atr * 4)

                # Calcular ganho potencial com alavancagem
                if trend == 'LONG':
                    potencial = (tp1 - entry) / entry * leverage * 100
                else:
                    potencial = (entry - tp1) / entry * leverage * 100

                opportunities.append({
                    'symbol': symbol,
                    'trend': trend,
                    'strength': strength,
                    'entry': entry,
                    'sl': sl,
                    'tp1': tp1,
                    'tp2': tp2,
                    'potencial': potencial
                })

        except Exception as e:
            print(Fore.RED + f"Erro em {symbol}: {e}")

    await client.close_connection()

    # Ordenar por força
    opportunities.sort(key=lambda x: x['strength'], reverse=True)

    # Mostrar top 5
    if opportunities:
        print(Fore.GREEN + f"\n✨ {len(opportunities)} OPORTUNIDADE(S) ENCONTRADA(S)!\n")
        print(Fore.YELLOW + "TOP 5 - MAIORES POTENCIAIS DE MULTIPLICAÇÃO:\n")

        for i, opp in enumerate(opportunities[:5], 1):
            if opp['trend'] == 'LONG':
                trend_color = Fore.GREEN
                trend_icon = "LONG 🚀"
            else:
                trend_color = Fore.RED
                trend_icon = "SHORT 🔻"

            print(trend_color + f"[{i}] {opp['symbol']} - {trend_icon} (Força: {opp['strength']}/100)")
            print(Fore.WHITE + f"    Entry: ${opp['entry']:.4f}")
            print(Fore.GREEN + f"    TP1: ${opp['tp1']:.4f} | TP2: ${opp['tp2']:.4f}")
            print(Fore.RED + f"    SL: ${opp['sl']:.4f}")
            print(Fore.CYAN + f"    POTENCIAL DE GANHO: {opp['potencial']:.1f}% (com {leverage}x)")
            print()
    else:
        print(Fore.YELLOW + "⚠️  Nenhuma oportunidade de alta qualidade encontrada no momento.")
        print(Fore.WHITE + "Aguardar melhores setups...")

    print(Fore.CYAN + "=" * 60)

if __name__ == "__main__":
    asyncio.run(scan())
