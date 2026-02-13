"""
📚 ESTRATÉGIAS AVANÇADAS PARA BINANCE FUTURES
==============================================

Este módulo contém estratégias adicionais que podem ser
adicionadas ao agente principal.
"""

from enum import Enum
from typing import Dict, List
import pandas as pd
import numpy as np


class StrategyType(Enum):
    SCALPING = "scalping"
    SWING = "swing"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    FUNDING_ARBITRAGE = "funding_arbitrage"


class AdvancedStrategies:
    """Estratégias avançadas de trading."""

    @staticmethod
    def scalping_strategy(df: pd.DataFrame) -> Dict:
        """
        ESTRATÉGIA 1: SCALPING DE 1-5 MINUTOS

        Características:
        - Múltiplas operações por dia
        - Alvos curtos (0.5-1%)
        - Stop loss apertado
        - Alta frequência

        Indicadores:
        - EMA 9/21 para direção
        - Volume acima da média
        - Preço puxando de VWAP
        """
        if len(df) < 20:
            return {'signal': 0, 'reason': 'Dados insuficientes'}

        latest = df.iloc[-1]

        # VWAP
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        vwap = df['vwap'].iloc[-1]
        volume_ma = df['volume'].rolling(20).mean().iloc[-1]

        signal = 0
        reasons = []

        # Long: Preço abaixo VWAP + Volume alto + EMA bullish
        if (latest['close'] < vwap * 0.995 and
            latest['volume'] > volume_ma * 1.2 and
            latest['ema_9'] > latest['ema_21']):
            signal = 1
            reasons = [
                "Preço abaixo de VWAP",
                f"Volume alto ({latest['volume']/volume_ma:.1f}x)",
                "EMA 9 > 21"
            ]

        # Short: Preço acima VWAP + Volume alto + EMA bearish
        elif (latest['close'] > vwap * 1.005 and
              latest['volume'] > volume_ma * 1.2 and
              latest['ema_9'] < latest['ema_21']):
            signal = -1
            reasons = [
                "Preço acima de VWAP",
                f"Volume alto ({latest['volume']/volume_ma:.1f}x)",
                "EMA 9 < 21"
            ]

        # TP e SL para scalping
        atr = latest.get('atr', latest['close'] * 0.01)

        if signal == 1:
            entry = latest['close']
            tp = entry + (atr * 1)
            sl = entry - (atr * 0.8)
        elif signal == -1:
            entry = latest['close']
            tp = entry - (atr * 1)
            sl = entry + (atr * 0.8)
        else:
            entry = tp = sl = 0

        return {
            'strategy': StrategyType.SCALPING,
            'signal': signal,
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'reasons': reasons,
            'timeframe': '1m-5m'
        }

    @staticmethod
    def breakout_strategy(df: pd.DataFrame) -> Dict:
        """
        ESTRATÉGIA 2: BREAKOUT DE CONSOLIDAÇÃO

        Características:
        - Espera consolidação (baixa volatilidade)
        - Entra no rompimento
        - Alvos maiores (2-5%)
        - Pyramiding em tendance forte

        Indicadores:
        - Bollinger Bands squeeze
        - ATR baixo (consolidação)
        - Volume de confirmação
        """
        if len(df) < 50:
            return {'signal': 0, 'reason': 'Dados insuficientes'}

        latest = df.iloc[-1]
        bb_std = df['bb_std'].iloc[-1]
        atr = latest.get('atr', latest['close'] * 0.01)
        atr_ma = df['atr'].rolling(20).mean().iloc[-1]

        signal = 0
        reasons = []

        # Detectar squeeze (bandas apertadas)
        is_squeeze = bb_std < df['bb_std'].rolling(20).mean().iloc[-1] * 0.7
        is_low_vol = atr < atr_ma * 0.8

        # Breakout bullish
        if (is_squeeze and
            latest['close'] > latest['bb_upper'] and
            latest['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.5):
            signal = 1
            reasons = [
                "BB Squeeze detectado",
                "Rompimento da banda superior",
                "Volume de confirmação"
            ]

        # Breakout bearish
        elif (is_squeeze and
              latest['close'] < latest['bb_lower'] and
              latest['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.5):
            signal = -1
            reasons = [
                "BB Squeeze detectado",
                "Rompimento da banda inferior",
                "Volume de confirmação"
            ]

        # TP e SL para breakout
        if signal == 1:
            entry = latest['close']
            tp = entry + (atr * 4)
            sl = entry - (atr * 1.5)
        elif signal == -1:
            entry = latest['close']
            tp = entry - (atr * 4)
            sl = entry + (atr * 1.5)
        else:
            entry = tp = sl = 0

        return {
            'strategy': StrategyType.BREAKOUT,
            'signal': signal,
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'reasons': reasons,
            'timeframe': '15m-1h'
        }

    @staticmethod
    def mean_reversion_strategy(df: pd.DataFrame) -> Dict:
        """
        ESTRATÉGIA 3: MEAN REVERSION (RETORNO À MÉDIA)

        Características:
        - Contrária à tendência de curto prazo
        - Baseada em extremos (overbought/oversold)
        - Funciona bem em mercado lateral
        - Rápida entrada e saída

        Indicadores:
        - RSI extremo (<25 ou >75)
        - Distância das EMA's
        - Bollinger Bands extremas
        """
        if len(df) < 30:
            return {'signal': 0, 'reason': 'Dados insuficientes'}

        latest = df.iloc[-1]
        rsi = latest['rsi']
        bb_width = (latest['bb_upper'] - latest['bb_lower']) / latest['bb_middle']

        signal = 0
        reasons = []

        # Oversold extremo - Buy
        if (rsi < 25 and
            latest['close'] < latest['bb_lower'] * 0.99):
            signal = 1
            reasons = [
                f"RSI extremo oversold ({rsi:.1f})",
                "Preço abaixo da BB inferior"
            ]

        # Overbought extremo - Sell
        elif (rsi > 75 and
              latest['close'] > latest['bb_upper'] * 1.01):
            signal = -1
            reasons = [
                f"RSI extremo overbought ({rsi:.1f})",
                "Preço acima da BB superior"
            ]

        # TP e SL para mean reversion
        atr = latest.get('atr', latest['close'] * 0.01)

        if signal == 1:
            entry = latest['close']
            tp = entry + (atr * 1.5)
            sl = entry - (atr * 0.8)
        elif signal == -1:
            entry = latest['close']
            tp = entry - (atr * 1.5)
            sl = entry + (atr * 0.8)
        else:
            entry = tp = sl = 0

        return {
            'strategy': StrategyType.MEAN_REVERSION,
            'signal': signal,
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'reasons': reasons,
            'timeframe': '5m-15m'
        }

    @staticmethod
    def swing_strategy(df: pd.DataFrame) -> Dict:
        """
        ESTRATÉGIA 4: SWING TRADING (Longo Prazo)

        Características:
        - Operações de dias a semanas
        - Segue tendência principal
        - Alvos maiores (5-20%)
        - Stop loss mais largo

        Indicadores:
        - EMA's de longo prazo (50/200)
        - Estrutura de mercado (HH/HL ou LH/LL)
        - Níveis de suporte/resistência
        """
        if len(df) < 200:
            return {'signal': 0, 'reason': 'Dados insuficientes'}

        latest = df.iloc[-1]
        ema_50 = df['ema_50'].iloc[-1]

        # EMA 200
        ema_200 = df['close'].ewm(span=200).mean().iloc[-1]

        signal = 0
        reasons = []

        # Tendência bullish forte
        if (ema_50 > ema_200 and
            latest['close'] > ema_50 and
            latest['ema_9'] > latest['ema_21']):
            signal = 1
            reasons = [
                "EMA 50 > 200 (tendência de alta)",
                "Preço acima da EMA 50",
                "EMA de curto prazo bullish"
            ]

        # Tendência bearish forte
        elif (ema_50 < ema_200 and
              latest['close'] < ema_50 and
              latest['ema_9'] < latest['ema_21']):
            signal = -1
            reasons = [
                "EMA 50 < 200 (tendência de baixa)",
                "Preço abaixo da EMA 50",
                "EMA de curto prazo bearish"
            ]

        # TP e SL para swing
        atr = latest.get('atr', latest['close'] * 0.01)

        if signal == 1:
            entry = latest['close']
            tp = entry + (atr * 8)
            sl = entry - (atr * 2)
        elif signal == -1:
            entry = latest['close']
            tp = entry - (atr * 8)
            sl = entry + (atr * 2)
        else:
            entry = tp = sl = 0

        return {
            'strategy': StrategyType.SWING,
            'signal': signal,
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'reasons': reasons,
            'timeframe': '4h-1d'
        }

    @staticmethod
    def funding_arbitrage(funding_rate: float, price_diff: float) -> Dict:
        """
        ESTRATÉGIA 5: FUNDING RATE ARBITRAGE

        Características:
        - Aproveita taxas de funding
        - Delta neutro (long spot + short perpetual)
        - Baixo risco
        - Requer capital em ambos os lados

        Quando usar:
        - Funding rate muito positivo (>0.05%): Long Spot + Short Perp
        - Funding rate muito negativo (<-0.05%): Short Spot + Long Perp
        """
        signal = 0
        reasons = []

        if funding_rate > 0.05:
            signal = 1  # Long Spot, Short Perp
            reasons = [
                f"Funding rate muito alto ({funding_rate:.3f}%)",
                "Arbitragem: Long Spot + Short Perp"
            ]
        elif funding_rate < -0.05:
            signal = -1  # Short Spot (se disponível), Long Perp
            reasons = [
                f"Funding rate muito baixo ({funding_rate:.3f}%)",
                "Arbitragem: Short Spot + Long Perp"
            ]

        return {
            'strategy': StrategyType.FUNDING_ARBITRAGE,
            'signal': signal,
            'funding_rate': funding_rate,
            'reasons': reasons,
            'risk_level': 'BAIXO'
        }

    @staticmethod
    def combine_strategies(df: pd.DataFrame, strategies: List[str] = None) -> Dict:
        """
        COMBINAR MÚLTIPLAS ESTRATÉGIAS

        Quando 2+ estratégias concordam, aumenta a probabilidade.
        """
        if strategies is None:
            strategies = ['scalping', 'breakout', 'mean_reversion', 'swing']

        results = {}

        if 'scalping' in strategies:
            results['scalping'] = AdvancedStrategies.scalping_strategy(df)
        if 'breakout' in strategies:
            results['breakout'] = AdvancedStrategies.breakout_strategy(df)
        if 'mean_reversion' in strategies:
            results['mean_reversion'] = AdvancedStrategies.mean_reversion_strategy(df)
        if 'swing' in strategies:
            results['swing'] = AdvancedStrategies.swing_strategy(df)

        # Contar sinais
        long_signals = sum(1 for r in results.values() if r.get('signal') == 1)
        short_signals = sum(1 for r in results.values() if r.get('signal') == -1)

        # Decisão final
        if long_signals >= 2:
            final_signal = 1
            consensus = f"{long_signals}/{len(results)} estratégias bullish"
        elif short_signals >= 2:
            final_signal = -1
            consensus = f"{short_signals}/{len(results)} estratégias bearish"
        else:
            final_signal = 0
            consensus = "Sem consenso"

        return {
            'final_signal': final_signal,
            'consensus': consensus,
            'individual_signals': results,
            'confidence': max(long_signals, short_signals) / len(results) * 100
        }


# ═══════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════

def print_strategy_signal(result: Dict):
    """Imprimir resultado da estratégia formatado."""
    from colorama import Fore, Style

    if result['signal'] == 0:
        print(f"{Fore.YELLOW}⏸️  Nenhum sinal da estratégia")
        return

    strategy = result.get('strategy', 'UNKNOWN')
    signal_type = "LONG 🚀" if result['signal'] == 1 else "SHORT 🔻"
    color = Fore.GREEN if result['signal'] == 1 else Fore.RED

    print(f"\n{color}{'='*60}")
    print(f"{color}  {strategy.value.upper()} - {signal_type}")
    print(f"{color}{'='*60}")
    print(f"{Fore.WHITE}⏱️  Timeframe: {Fore.CYAN}{result.get('timeframe', 'N/A')}")
    print(f"{Fore.WHITE}💰 Entry: ${Fore.CYAN}{result['entry']:.4f}")
    print(f"{Fore.WHITE}🎯 TP: ${Fore.GREEN}{result['tp']:.4f}")
    print(f"{Fore.WHITE}🛑 SL: ${Fore.RED}{result['sl']:.4f}")
    print(f"\n{Fore.YELLOW}📋 Razões:")
    for reason in result.get('reasons', []):
        print(f"   • {reason}")


if __name__ == "__main__":
    print("Módulo de estratégias avançadas para Binance Futures")
    print("Importe no agente principal para usar")
