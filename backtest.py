#!/usr/bin/env python3
"""
📊 BACKTESTING MODULE
======================
Teste estratégias com dados históricos antes de usar capital real.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from binance.client import Client
from colorama import Fore, Style, init

init(autoreset=True)


class Backtester:
    """Backtester para estratégias de futures."""

    def __init__(self, api_key: str, api_secret: str):
        self.client = Client(api_key, api_secret)

    def get_historical_data(self, symbol: str, interval: str, days: int = 30) -> pd.DataFrame:
        """Obter dados históricos."""
        print(f"{Fore.CYAN}📥 Baixando dados de {days} dias...")

        klines = self.client.futures_historical_klines(
            symbol=symbol,
            interval=interval,
            start_date=str(datetime.now() - timedelta(days=days))
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

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores."""
        df = df.copy()

        # EMA's
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
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        df['atr'] = ranges.max(axis=1).rolling(window=14).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gerar sinais de entrada/saída."""
        df = df.copy()

        # Sinais LONG
        long_conditions = (
            (df['ema_9'] > df['ema_21']) &
            (df['ema_21'] > df['ema_50']) &
            (df['rsi'] > 30) & (df['rsi'] < 70) &
            (df['macd_hist'] > 0)
        )

        # Sinais SHORT
        short_conditions = (
            (df['ema_9'] < df['ema_21']) &
            (df['ema_21'] < df['ema_50']) &
            (df['rsi'] > 30) & (df['rsi'] < 70) &
            (df['macd_hist'] < 0)
        )

        df['signal'] = 0
        df.loc[long_conditions, 'signal'] = 1
        df.loc[short_conditions, 'signal'] = -1

        return df

    def run_backtest(
        self,
        symbol: str,
        interval: str = '15m',
        days: int = 30,
        initial_capital: float = 100,
        leverage: int = 10,
        risk_per_trade: float = 0.05
    ) -> Dict:
        """
        Executar backtest da estratégia.

        Retorna estatísticas completas do desempenho.
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}📊 BACKTEST: {symbol} | {interval} | {days} dias")
        print(f"{Fore.CYAN}{'='*60}")

        # Obter e preparar dados
        df = self.get_historical_data(symbol, interval, days)
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)

        capital = initial_capital
        position = None
        trades = []
        max_drawdown = 0
        peak_capital = initial_capital

        for i in range(50, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # Atualizar pico e drawdown
            if capital > peak_capital:
                peak_capital = capital
            drawdown = (peak_capital - capital) / peak_capital
            max_drawdown = max(max_drawdown, drawdown)

            # Fechar posição existente
            if position:
                entry_price = position['entry']
                sl = position['sl']
                tp = position['tp']
                side = position['side']

                # Verificar SL ou TP
                if side == 'LONG':
                    if row['low'] <= sl:
                        # Hit SL
                        pnl = (sl - entry_price) / entry_price * leverage
                        capital *= (1 + pnl * risk_per_trade)
                        trades.append({
                            'type': 'SL',
                            'side': side,
                            'entry': entry_price,
                            'exit': sl,
                            'pnl': pnl * 100,
                            'capital': capital
                        })
                        position = None
                    elif row['high'] >= tp:
                        # Hit TP
                        pnl = (tp - entry_price) / entry_price * leverage
                        capital *= (1 + pnl * risk_per_trade)
                        trades.append({
                            'type': 'TP',
                            'side': side,
                            'entry': entry_price,
                            'exit': tp,
                            'pnl': pnl * 100,
                            'capital': capital
                        })
                        position = None
                else:  # SHORT
                    if row['high'] >= sl:
                        # Hit SL
                        pnl = (entry_price - sl) / entry_price * leverage
                        capital *= (1 + pnl * risk_per_trade)
                        trades.append({
                            'type': 'SL',
                            'side': side,
                            'entry': entry_price,
                            'exit': sl,
                            'pnl': pnl * 100,
                            'capital': capital
                        })
                        position = None
                    elif row['low'] <= tp:
                        # Hit TP
                        pnl = (entry_price - tp) / entry_price * leverage
                        capital *= (1 + pnl * risk_per_trade)
                        trades.append({
                            'type': 'TP',
                            'side': side,
                            'entry': entry_price,
                            'exit': tp,
                            'pnl': pnl * 100,
                            'capital': capital
                        })
                        position = None

            # Abrir nova posição
            if not position and row['signal'] != 0:
                entry = row['close']
                atr = row['atr']

                if row['signal'] == 1:  # LONG
                    sl = entry - (atr * 1.5)
                    tp = entry + (atr * 3)
                    position = {
                        'side': 'LONG',
                        'entry': entry,
                        'sl': sl,
                        'tp': tp
                    }
                else:  # SHORT
                    sl = entry + (atr * 1.5)
                    tp = entry - (atr * 3)
                    position = {
                        'side': 'SHORT',
                        'entry': entry,
                        'sl': sl,
                        'tp': tp
                    }

        # Calcular estatísticas
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        total_return = ((capital - initial_capital) / initial_capital) * 100

        if trades:
            avg_win = np.mean([t['pnl'] for t in trades if t['pnl'] > 0])
            avg_loss = np.mean([t['pnl'] for t in trades if t['pnl'] < 0])
            profit_factor = abs(
                sum([t['pnl'] for t in trades if t['pnl'] > 0]) /
                sum([t['pnl'] for t in trades if t['pnl'] < 0])
            ) if losing_trades > 0 else 0
        else:
            avg_win = avg_loss = profit_factor = 0

        # Exibir resultados
        print(f"\n{Fore.WHITE}📈 RESULTADOS DO BACKTEST")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.WHITE}Capital inicial:     {Fore.GREEN}${initial_capital:.2f}")
        print(f"{Fore.WHITE}Capital final:       {Fore.GREEN if capital > initial_capital else Fore.RED}${capital:.2f}")
        print(f"{Fore.WHITE}Retorno total:       {Fore.GREEN if total_return > 0 else Fore.RED}{total_return:.2f}%")
        print(f"\n{Fore.WHITE}Total de trades:    {Fore.CYAN}{total_trades}")
        print(f"{Fore.WHITE}Win rate:           {Fore.GREEN}{win_rate:.1f}%")
        print(f"{Fore.WHITE}Wins:               {Fore.GREEN}{winning_trades}")
        print(f"{Fore.WHITE}Losses:             {Fore.RED}{losing_trades}")
        print(f"\n{Fore.WHITE}Avg win:            {Fore.GREEN}{avg_win:.2f}%")
        print(f"{Fore.WHITE}Avg loss:           {Fore.RED}{avg_loss:.2f}%")
        print(f"{Fore.WHITE}Profit Factor:      {Fore.CYAN}{profit_factor:.2f}")
        print(f"{Fore.WHITE}Max Drawdown:       {Fore.RED}{max_drawdown*100:.2f}%")

        # Últimos trades
        if trades:
            print(f"\n{Fore.YELLOW}📋 ÚLTIMOS 5 TRADES:")
            for trade in trades[-5:]:
                color = Fore.GREEN if trade['pnl'] > 0 else Fore.RED
                print(f"  {color}{trade['type']} {trade['side']} | "
                      f"Entry: ${trade['entry']:.2f} | "
                      f"Exit: ${trade['exit']:.2f} | "
                      f"PnL: {trade['pnl']:.2f}%")

        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'final_capital': capital
        }


def main():
    """Executar backtest."""
    import dotenv
    dotenv.load_dotenv()

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        print(f"{Fore.RED}❌ Configure API keys no .env")
        return

    backtester = Backtester(api_key, api_secret)

    print(f"\n{Fore.CYAN}📊 BACKTESTING MODE")
    print(f"{Fore.CYAN}{'='*60}")

    symbol = input(f"{Fore.WHITE}Digite o par (ex: BTCUSDT): ").strip().upper()
    interval = input(f"{Fore.WHITE}Timeframe (15m, 1h, 4h): ").strip() or '15m'
    days = int(input(f"{Fore.WHITE}Dias de dados (padrão 30): ") or "30")

    results = backtester.run_backtest(symbol, interval, days)


if __name__ == "__main__":
    import os
    main()
