#!/usr/bin/env python3
"""
🚀 BINANCE FUTURES TRADING AGENT
================================
Agente especializado em trading de futuros na Binance com múltiplas skills de análise.

⚠️ AVISO: Trading envolve riscos significativos. Use por sua conta e risco.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import AsyncClient, BinanceSocketManager
import dotenv
from colorama import Fore, Style, init

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Inicializar colorama
init(autoreset=True)

# Carregar variáveis de ambiente
dotenv.load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL DO AGENTE
# ═══════════════════════════════════════════════════════════════

class BinanceFuturesAgent:
    """Agente especializado em trading de futuros da Binance."""

    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.capital = float(os.getenv('CAPITAL_INICIAL', 100))
        self.risk_per_trade = float(os.getenv('RISCO_MAXIMO_POR_OPERACAO', 0.05))
        self.leverage = int(os.getenv('ALAVANCAGEM_PADRAO', 20))
        self.sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))
        self.tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.03))

        if not self.api_key or not self.api_secret:
            print(f"{Fore.RED}❌ ERRO: Configure BINANCE_API_KEY e BINANCE_API_SECRET no arquivo .env")
            sys.exit(1)

        self.client = None
        self.async_client = None
        self.positions = {}

    async def connect(self):
        """Conectar à API da Binance."""
        try:
            self.async_client = await AsyncClient.create(self.api_key, self.api_secret)
            self.client = Client(self.api_key, self.api_secret)
            print(f"{Fore.GREEN}✅ Conectado à Binance Futures API")
            await self.print_account_info()
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao conectar: {e}")
            sys.exit(1)

    async def print_account_info(self):
        """Exibir informações da conta."""
        try:
            account = await self.async_client.futures_account()
            balance = float(account['totalWalletBalance'])
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}📊 CONTA FUTURES")
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.WHITE}Saldo disponível: {Fore.GREEN}${balance:.2f} USDT")
            print(f"{Fore.WHITE}Alavancagem padrão: {Fore.YELLOW}1:{self.leverage}x")
            print(f"{Fore.WHITE}Risco por operação: {Fore.YELLOW}{self.risk_per_trade*100:.1f}%")
            print(f"{Fore.CYAN}{'='*60}\n")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Não foi possível obter saldo: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SKILL 1: ANÁLISE TÉCNICA AVANÇADA
    # ═══════════════════════════════════════════════════════════════

    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Obter candles e retornar como DataFrame."""
        try:
            klines = await self.async_client.futures_klines(
                symbol=symbol.upper(),
                interval=interval,
                limit=limit
            )
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['open'] = df['open'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao obter candles: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos."""
        if df.empty:
            return df

        df = df.copy()

        # EMA's
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()

        # RSI (14)
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
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

        # ATR (Stop Loss dinâmico)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        df['atr'] = ranges.max(axis=1).rolling(window=14).mean()

        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        return df

    async def analyze_market(self, symbol: str, interval: str = '15m') -> Dict:
        """
        SKILL 1: Análise técnica completa do mercado.

        Retorna:
            - trend: 'BULLISH', 'BEARISH', ou 'NEUTRAL'
            - strength: 0-100 (força do sinal)
            - signals: lista de sinais confirmados
            - entry_price: preço sugerido de entrada
            - targets: take profits
            - invalidation: stop loss
        """
        print(f"{Fore.CYAN}🔍 Analisando {symbol}...")

        df = await self.get_klines(symbol, interval)
        if df.empty:
            return {'error': 'Não foi possível obter dados'}

        df = self.calculate_indicators(df)
        latest = df.iloc[-1]

        signals = []
        bullish_score = 0
        bearish_score = 0

        # Análise de EMA's
        if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
            bullish_score += 20
            signals.append("📈 EMA's em ordem bullish (9 > 21 > 50)")
        elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
            bearish_score += 20
            signals.append("📉 EMA's em ordem bearish (9 < 21 < 50)")

        # RSI
        if latest['rsi'] < 30:
            bullish_score += 15
            signals.append(f"💎 RSI oversold ({latest['rsi']:.1f})")
        elif latest['rsi'] > 70:
            bearish_score += 15
            signals.append(f"🔴 RSI overbought ({latest['rsi']:.1f})")

        # MACD
        if latest['macd_hist'] > 0 and latest['macd'] > 0:
            bullish_score += 15
            signals.append("✅ MACD bullish")
        elif latest['macd_hist'] < 0 and latest['macd'] < 0:
            bearish_score += 15
            signals.append("❌ MACD bearish")

        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            bullish_score += 10
            signals.append("💚 Preço abaixo da BB inferior (oversold)")
        elif latest['close'] > latest['bb_upper']:
            bearish_score += 10
            signals.append("🔴 Preço acima da BB superior (overbought)")

        # Volume
        if latest['volume_ratio'] > 1.5:
            signals.append(f"📊 Volume alto ({latest['volume_ratio']:.1f}x média)")

        # Tendência do preço
        price_change = (latest['close'] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        if price_change > 0.02:
            bullish_score += 10
        elif price_change < -0.02:
            bearish_score += 10

        total_score = bullish_score + bearish_score
        trend = 'NEUTRAL'
        strength = 0

        if bullish_score > bearish_score + 20:
            trend = 'BULLISH'
            strength = min(bullish_score, 100)
        elif bearish_score > bullish_score + 20:
            trend = 'BEARISH'
            strength = min(bearish_score, 100)

        entry_price = latest['close']
        atr = latest['atr']

        if trend == 'BULLISH':
            invalidation = entry_price - (atr * 1.5)
            targets = [
                entry_price + (atr * 2),
                entry_price + (atr * 3),
                entry_price + (atr * 5)
            ]
        elif trend == 'BEARISH':
            invalidation = entry_price + (atr * 1.5)
            targets = [
                entry_price - (atr * 2),
                entry_price - (atr * 3),
                entry_price - (atr * 5)
            ]
        else:
            invalidation = entry_price - (atr * 2) if bullish_score > bearish_score else entry_price + (atr * 2)
            targets = [entry_price * 1.02, entry_price * 1.04, entry_price * 1.06]

        return {
            'symbol': symbol,
            'trend': trend,
            'strength': strength,
            'signals': signals,
            'entry_price': entry_price,
            'targets': targets,
            'invalidation': invalidation,
            'indicators': {
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'macd_signal': latest['macd_signal'],
                'volume_ratio': latest['volume_ratio'],
            }
        }

    # ═══════════════════════════════════════════════════════════════
    # SKILL 2: ESCANEAMENTO DE OPORTUNIDADES
    # ═══════════════════════════════════════════════════════════════

    async def scan_opportunities(self, symbols: List[str] = None) -> List[Dict]:
        """
        SKILL 2: Escanear múltiplos pares em busca de oportunidades.

        Procura setups com alta probabilidade.
        """
        if symbols is None:
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
                'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
                'MATICUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT'
            ]

        print(f"\n{Fore.CYAN}🔬 ESCANEANDO OPORTUNIDADES...")
        print(f"{Fore.CYAN}{'='*60}\n")

        opportunities = []

        for symbol in symbols:
            analysis = await self.analyze_market(symbol, '15m')
            if analysis.get('strength', 0) >= 60 and analysis.get('trend') != 'NEUTRAL':
                opportunities.append(analysis)

        # Ordenar por força
        opportunities.sort(key=lambda x: x['strength'], reverse=True)

        return opportunities

    def print_opportunity(self, opp: Dict):
        """Exibir oportunidade formatada."""
        trend_color = Fore.GREEN if opp['trend'] == 'BULLISH' else Fore.RED
        trend_icon = "🚀 LONG" if opp['trend'] == 'BULLISH' else "🔻 SHORT"

        print(f"\n{trend_color}{Style.BRIGHT}{'='*60}")
        print(f"{trend_color}{Style.BRIGHT}  {opp['symbol']} - {trend_icon} (Força: {opp['strength']}/100)")
        print(f"{trend_color}{Style.BRIGHT}{'='*60}")
        print(f"{Fore.WHITE}💰 Preço de entrada: {Fore.CYAN}${opp['entry_price']:.4f}")
        print(f"{Fore.WHITE}🎯 Targets:")
        for i, target in enumerate(opp['targets'], 1):
            print(f"{Fore.WHITE}   TP{i}: {Fore.GREEN}${target:.4f}")
        print(f"{Fore.WHITE}🛑 Invalidation (SL): {Fore.RED}${opp['invalidation']:.4f}")
        print(f"\n{Fore.YELLOW}📋 SINAIS CONFIRMADOS:")
        for signal in opp['signals']:
            print(f"   {signal}")
        print(f"\n{Fore.CYAN}📊 INDICADORES:")
        print(f"   RSI: {opp['indicators']['rsi']:.1f} | "
              f"Volume Ratio: {opp['indicators']['volume_ratio']:.2f}x")

    # ═══════════════════════════════════════════════════════════════
    # SKILL 3: GERENCIAMENTO DE POSIÇÕES
    # ═══════════════════════════════════════════════════════════════

    async def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """Calcular tamanho da posição baseado no risco."""
        account = await self.async_client.futures_account()
        balance = float(account['totalWalletBalance'])

        risk_amount = balance * self.risk_per_trade
        risk_per_unit = abs(entry_price - stop_loss)
        quantity = risk_amount / risk_per_unit

        # Obter informação do símbolo para arredondar
        info = await self.async_client.futures_exchange_info()
        symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
        step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])

        # Arredondar para o step size
        precision = len(str(step_size).rstrip('0').split('.')[-1])
        quantity = round(quantity, precision)

        return quantity

    async def set_leverage(self, symbol: str, leverage: int):
        """Configurar alavancagem para o par."""
        try:
            await self.async_client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            print(f"{Fore.GREEN}✅ Alavancagem definida: {leverage}x")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Erro ao definir alavancagem: {e}")

    async def open_position(self, symbol: str, side: str, analysis: Dict) -> Dict:
        """
        SKILL 3: Abrir posição com gerenciamento de risco completo.

        Args:
            symbol: Par de trading
            side: 'BUY' ou 'SELL'
            analysis: Dicionário com análise completa

        Returns:
            Dict com informações da ordem
        """
        try:
            print(f"\n{Fore.CYAN}🎯 Abrindo posição em {symbol}...")

            # Configurar alavancagem
            await self.set_leverage(symbol, self.leverage)

            # Calcular tamanho
            entry_price = analysis['entry_price']
            stop_loss = analysis['invalidation']
            quantity = await self.calculate_position_size(symbol, entry_price, stop_loss)

            # Calcular stop loss e take profit em percentual
            if side == 'BUY':
                sl_price = stop_loss
                tp_prices = analysis['targets']
            else:
                sl_price = stop_loss
                tp_prices = analysis['targets']

            # Ordem principal
            order = await self.async_client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )

            print(f"{Fore.GREEN}✅ Ordem enviada: {side} {quantity} {symbol}")
            print(f"{Fore.WHITE}   Entry: ${entry_price:.4f}")
            print(f"{Fore.RED}   SL: ${sl_price:.4f}")

            # Guardar informações da posição
            self.positions[symbol] = {
                'side': side,
                'quantity': quantity,
                'entry': entry_price,
                'sl': sl_price,
                'tp': tp_prices,
                'orderId': order['orderId']
            }

            return order

        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao abrir posição: {e}")
            return {}

    async def close_position(self, symbol: str):
        """Fechar posição aberta."""
        try:
            position = await self.async_client.futures_position_information(symbol=symbol)
            pos_amt = float(position[0]['positionAmt'])

            if abs(pos_amt) > 0:
                side = 'SELL' if pos_amt > 0 else 'BUY'
                order = await self.async_client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=abs(pos_amt)
                )
                print(f"{Fore.GREEN}✅ Posição fechada: {symbol}")
                if symbol in self.positions:
                    del self.positions[symbol]
                return order
            else:
                print(f"{Fore.YELLOW}⚠️  Nenhuma posição aberta em {symbol}")

        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao fechar posição: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SKILL 4: MONITORAMENTO EM TEMPO REAL
    # ═══════════════════════════════════════════════════════════════

    async def monitor_positions(self):
        """
        SKILL 4: Monitorar posições abertas em tempo real.

        Fecha automaticamente no TP ou SL.
        """
        if not self.positions:
            return

        print(f"\n{Fore.CYAN}👀 Monitorando posições...")
        print(f"{Fore.CYAN}{'='*60}")

        for symbol, pos in list(self.positions.items()):
            try:
                # Obter preço atual
                ticker = await self.async_client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])

                print(f"{Fore.WHITE}{symbol}: ${current_price:.4f} | "
                      f"SL: ${pos['sl']:.4f} | "
                      f"TP1: ${pos['tp'][0]:.4f}")

                # Verificar Stop Loss
                if pos['side'] == 'BUY' and current_price <= pos['sl']:
                    print(f"{Fore.RED}🛑 Stop Loss atingido! Fechando {symbol}...")
                    await self.close_position(symbol)
                    continue
                elif pos['side'] == 'SELL' and current_price >= pos['sl']:
                    print(f"{Fore.RED}🛑 Stop Loss atingido! Fechando {symbol}...")
                    await self.close_position(symbol)
                    continue

                # Verificar Take Profit
                if pos['side'] == 'BUY' and current_price >= pos['tp'][0]:
                    print(f"{Fore.GREEN}🎯 TP1 atingido! Fechando {symbol}...")
                    await self.close_position(symbol)
                elif pos['side'] == 'SELL' and current_price <= pos['tp'][0]:
                    print(f"{Fore.GREEN}🎯 TP1 atingido! Fechando {symbol}...")
                    await self.close_position(symbol)

            except Exception as e:
                print(f"{Fore.RED}❌ Erro ao monitorar {symbol}: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SKILL 5: STREAM DE PREÇOS
    # ═══════════════════════════════════════════════════════════════

    async def stream_price(self, symbol: str):
        """
        SKILL 5: Stream de preços em tempo real via WebSocket.
        """
        print(f"\n{Fore.CYAN}📡 Conectando stream de preços: {symbol}")

        try:
            bsm = BinanceSocketManager(self.async_client)
            ts = bsm.futures_symbol_ticker_socket(symbol)

            async with ts as tscm:
                while True:
                    res = await tscm.recv()
                    price = float(res['c'])
                    print(f"{Fore.CYAN}{symbol}: ${price:.4f} | "
                          f"Volume: {float(res['v']):.2f}", end='\r')
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  Stream interrompido")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Erro no stream: {e}")

    # ═══════════════════════════════════════════════════════════════
    # MENUS E INTERFACE
    # ═══════════════════════════════════════════════════════════════

    def print_menu(self):
        """Exibir menu principal."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}    🚀 BINANCE FUTURES AGENT - MENU")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.WHITE}[1] {Fore.GREEN}💡 Pedir entrada/sinal agora")
        print(f"{Fore.WHITE}[2] {Fore.GREEN}🔬 Escanear oportunidades (auto)")
        print(f"{Fore.WHITE}[3] {Fore.GREEN}📊 Análise completa de par específico")
        print(f"{Fore.WHITE}[4] {Fore.GREEN}📡 Stream de preços em tempo real")
        print(f"{Fore.WHITE}[5] {Fore.GREEN}👀 Monitorar posições abertas")
        print(f"{Fore.WHITE}[6] {Fore.GREEN}❌ Fechar posição")
        print(f"{Fore.WHITE}[7] {Fore.GREEN}💰 Ver saldo da conta")
        print(f"{Fore.WHITE}[8] {Fore.GREEN}⚙️  Configurações")
        print(f"{Fore.WHITE}[0] {Fore.RED}🚪 Sair")
        print(f"{Fore.CYAN}{'='*60}")

    async def menu_signal_now(self):
        """Pedir sinal de entrada agora."""
        print(f"\n{Fore.YELLOW}Digite o par (ex: BTCUSDT) ou pressione ENTER para scan automático:")
        symbol_input = input(f"{Fore.CYAN}>>> {Fore.WHITE}").strip().upper()

        if symbol_input:
            analysis = await self.analyze_market(symbol_input, '15m')
            self.print_opportunity(analysis)

            if analysis['strength'] >= 50:
                print(f"\n{Fore.YELLOW}Deseja abrir posição? (s/n)")
                choice = input(f"{Fore.CYAN}>>> {Fore.WHITE}").lower()

                if choice == 's':
                    side = 'BUY' if analysis['trend'] == 'BULLISH' else 'SELL'
                    await self.open_position(symbol_input, side, analysis)
        else:
            opportunities = await self.scan_opportunities()
            if opportunities:
                print(f"\n{Fore.GREEN}✨ {len(opportunities)} oportunidade(s) encontrada(s)!")
                for opp in opportunities[:3]:
                    self.print_opportunity(opp)
            else:
                print(f"{Fore.YELLOW}⚠️  Nenhuma oportunidade de alta qualidade encontrada")

    async def menu_analyze_pair(self):
        """Análise completa de um par."""
        symbol = input(f"\n{Fore.CYAN}Digite o par: {Fore.WHITE}").strip().upper()

        # Timeframes
        print(f"\n{Fore.CYY}Timeframes disponíveis: 1m, 5m, 15m, 1h, 4h, 1d")
        timeframe = input(f"{Fore.CYAN}Escolha o timeframe (padrão: 15m): {Fore.WHITE}").strip()
        if not timeframe:
            timeframe = '15m'

        analysis = await self.analyze_market(symbol, timeframe)
        self.print_opportunity(analysis)

    async def menu_stream_price(self):
        """Stream de preços."""
        symbol = input(f"\n{Fore.CYAN}Digite o par: {Fore.WHITE}").strip().upper()
        await self.stream_price(symbol)

    async def menu_close_position(self):
        """Fechar posição."""
        symbol = input(f"\n{Fore.CYAN}Digite o par: {Fore.WHITE}").strip().upper()
        await self.close_position(symbol)

    async def menu_settings(self):
        """Configurações."""
        print(f"\n{Fore.CYAN}⚙️  CONFIGURAÇÕES")
        print(f"{Fore.CYAN}{'='*60}")

        print(f"\n{Fore.WHITE}Configurações atuais:")
        print(f"  Capital: ${self.capital}")
        print(f"  Risco/operação: {self.risk_per_trade*100}%")
        print(f"  Alavancagem: {self.leverage}x")
        print(f"  Stop Loss: {self.sl_percent*100}%")
        print(f"  Take Profit: {self.tp_percent*100}%")

        print(f"\n{Fore.YELLOW}Deseja alterar algo? (s/n)")
        choice = input(f"{Fore.CYAN}>>> {Fore.WHITE}").lower()

        if choice == 's':
            print(f"\n{Fore.CYAN}[1] Alavancagem [2] Risco [3] SL/TP")
            setting = input(f"{Fore.CYAN}>>> {Fore.WHITE}").strip()

            if setting == '1':
                self.leverage = int(input(f"{Fore.CYAN}Nova alavancagem (1-125): {Fore.WHITE}"))
            elif setting == '2':
                self.risk_per_trade = float(input(f"{Fore.CYAN}Novo risco (0.01-0.10): {Fore.WHITE}"))
            elif setting == '3':
                self.sl_percent = float(input(f"{Fore.CYAN}Novo SL (0.01-0.05): {Fore.WHITE}"))
                self.tp_percent = float(input(f"{Fore.CYAN}Novo TP (0.02-0.10): {Fore.WHITE}"))

            print(f"{Fore.GREEN}✅ Configurações atualizadas!")

    async def run(self):
        """Executar o agente com menu interativo."""
        await self.connect()

        while True:
            self.print_menu()
            choice = input(f"\n{Fore.CYAN}Escolha uma opção: {Fore.WHITE}").strip()

            if choice == '1':
                await self.menu_signal_now()
            elif choice == '2':
                await self.scan_opportunities()
            elif choice == '3':
                await self.menu_analyze_pair()
            elif choice == '4':
                await self.menu_stream_price()
            elif choice == '5':
                await self.monitor_positions()
            elif choice == '6':
                await self.menu_close_position()
            elif choice == '7':
                await self.print_account_info()
            elif choice == '8':
                await self.menu_settings()
            elif choice == '0':
                print(f"{Fore.YELLOW}👋 Até logo!")
                break
            else:
                print(f"{Fore.RED}❌ Opção inválida")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    """Função principal."""
    print(f"\n{Fore.CYAN}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║        🚀 BINANCE FUTURES TRADING AGENT v1.0                ║")
    print("║        Agente especializado em multiplicação de capital     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n{Fore.YELLOW}⚠️  AVISO: Trading envolve riscos. Use por sua conta e risco.")

    agent = BinanceFuturesAgent()
    await agent.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Programa interrompido")
    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}")
