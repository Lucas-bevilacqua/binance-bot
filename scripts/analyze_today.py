#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise de Performance - Hoje vs Histórico
"""
import asyncio
import sys
import codecs
from datetime import datetime

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Dados de HOJE
TODAYS_TRADES = [
    {'time': '21:06:50', 'symbol': 'LINKUSDT', 'side': 'LONG', 'entry': 9.067, 'exit': 9.192, 'pnl': 2.27625},
    {'time': '20:36:37', 'symbol': 'DOTUSDT', 'side': 'LONG', 'entry': 1.429, 'exit': 1.411, 'pnl': -2.8296},
    {'time': '20:02:26', 'symbol': 'XRPUSDT', 'side': 'LONG', 'entry': 1.4826, 'exit': 1.5064, 'pnl': 3.0464},
    {'time': '19:32:24', 'symbol': 'NEARUSDT', 'side': 'LONG', 'entry': 1.068, 'exit': 1.088, 'pnl': 2.98},
    {'time': '18:34:08', 'symbol': 'AVAXUSDT', 'side': 'LONG', 'entry': 9.378, 'exit': 9.501, 'pnl': 1.476},
    {'time': '17:21:31', 'symbol': 'DOTUSDT', 'side': 'LONG', 'entry': 1.391, 'exit': 1.414, 'pnl': 2.5277},
    {'time': '16:53:10', 'symbol': 'ADAUSDT', 'side': 'LONG', 'entry': 0.2843, 'exit': 0.2895, 'pnl': 2.1528},
    {'time': '16:21:44', 'symbol': 'BNBUSDT', 'side': 'LONG', 'entry': 635.17, 'exit': 631.07, 'pnl': -0.82},
    {'time': '15:58:46', 'symbol': 'DOTUSDT', 'side': 'LONG', 'entry': 1.376, 'exit': 1.397, 'pnl': 0.966},
    {'time': '15:19:56', 'symbol': 'SOLUSDT', 'side': 'LONG', 'entry': 86.36, 'exit': 87.53, 'pnl': 1.8486},
    {'time': '14:57:30', 'symbol': 'ATOMUSDT', 'side': 'LONG', 'entry': 2.143, 'exit': 2.168, 'pnl': 0.729},
    {'time': '14:51:42', 'symbol': 'BNBUSDT', 'side': 'LONG', 'entry': 629.44, 'exit': 635.55, 'pnl': 1.4053},
    {'time': '14:37:23', 'symbol': 'OPUSDT', 'side': 'SHORT', 'entry': 0.1927, 'exit': 0.1944, 'pnl': -2.8135},
    {'time': '14:32:16', 'symbol': 'DOTUSDT', 'side': 'LONG', 'entry': 1.358, 'exit': 1.376, 'pnl': 1.3176},
]

def analyze_today():
    """Analisar performance de hoje."""

    print("=" * 80)
    print("ANÁLISE DE PERFORMANCE - HOJE vs HISTÓRICO")
    print("=" * 80)

    # Estatísticas de hoje
    total_trades = len(TODAYS_TRADES)
    wins = sum(1 for t in TODAYS_TRADES if t['pnl'] > 0)
    losses = sum(1 for t in TODAYS_TRADES if t['pnl'] < 0)
    total_pnl = sum(t['pnl'] for t in TODAYS_TRADES)
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    win_rate = 100.0 * wins / total_trades if total_trades > 0 else 0

    print(f"\n📊 HOJE ({datetime.now().strftime('%Y-%m-%d')})")
    print("-" * 80)
    print(f"Total Trades:     {total_trades}")
    print(f"Winning Trades:  {wins}")
    print(f"Losing Trades:   {losses}")
    print(f"Win Rate:        {win_rate:.1f}%")
    print(f"Total PnL:       ${total_pnl:+.2f}")
    print(f"Avg PnL/Trade:   ${avg_pnl:+.2f}")

    # Análise por símbolo
    print(f"\n🔍 POR SÍMBOLO")
    print("-" * 80)

    by_symbol = {}
    for trade in TODAYS_TRADES:
        sym = trade['symbol']
        if sym not in by_symbol:
            by_symbol[sym] = {'trades': 0, 'wins': 0, 'pnl': 0}
        by_symbol[sym]['trades'] += 1
        if trade['pnl'] > 0:
            by_symbol[sym]['wins'] += 1
        by_symbol[sym]['pnl'] += trade['pnl']

    for sym, stats in sorted(by_symbol.items(), key=lambda x: x[1]['pnl'], reverse=True):
        win_rate_sym = 100.0 * stats['wins'] / stats['trades']
        print(f"{sym:12} | {stats['trades']:2} trades | {stats['wins']:2}W | {win_rate_sym:5.1f}% WR | ${stats['pnl']:+6.2f}")

    # Análise por lado (LONG/SHORT)
    print(f"\n⬆️⬇️ POR LADO")
    print("-" * 80)

    by_side = {'LONG': {'trades': 0, 'wins': 0, 'pnl': 0}, 'SHORT': {'trades': 0, 'wins': 0, 'pnl': 0}}

    for trade in TODAYS_TRADES:
        side = trade['side']
        by_side[side]['trades'] += 1
        if trade['pnl'] > 0:
            by_side[side]['wins'] += 1
        by_side[side]['pnl'] += trade['pnl']

    for side, stats in by_side.items():
        if stats['trades'] > 0:
            win_rate_side = 100.0 * stats['wins'] / stats['trades']
            print(f"{side:6} | {stats['trades']:2} trades | {stats['wins']:2}W | {win_rate_side:5.1f}% WR | ${stats['pnl']:+6.2f}")

    # Melhores e piores trades
    print(f"\n🏆 MELHORES TRADES")
    print("-" * 80)
    sorted_trades = sorted(TODAYS_TRADES, key=lambda x: x['pnl'], reverse=True)
    for i, trade in enumerate(sorted_trades[:5], 1):
        print(f"{i}. {trade['symbol']:10} {trade['side']:5} | ${trade['pnl']:+6.2f}")

    print(f"\n📉 PIORES TRADES")
    print("-" * 80)
    for i, trade in enumerate(sorted_trades[-3:], 1):
        print(f"{i}. {trade['symbol']:10} {trade['side']:5} | ${trade['pnl']:+6.2f}")

    # Símbolos para evitar
    print(f"\n⚠️  ANÁLISE DE RISCO")
    print("-" * 80)

    # DOTUSDT teve losses significativos
    dot_trades = [t for t in TODAYS_TRADES if t['symbol'] == 'DOTUSDT']
    if dot_trades:
        dot_pnl = sum(t['pnl'] for t in dot_trades)
        dot_wins = sum(1 for t in dot_trades if t['pnl'] > 0)
        print(f"DOTUSDT: {len(dot_trades)} trades | {dot_wins}/{len(dot_trades)} wins | ${dot_pnl:+.2f}")
        if dot_pnl < 0:
            print(f"  ⚠️ ATENÇÃO: DOTUSDT teve prejuízo hoje. Considerar reduzir tamanho da posição.")

    # OPUSDT SHORT teve loss
    op_trades = [t for t in TODAYS_TRADES if t['symbol'] == 'OPUSDT' and t['side'] == 'SHORT']
    if op_trades and op_trades[0]['pnl'] < 0:
        print(f"OPUSDT SHORT: ${op_trades[0]['pnl']:+.2f}")
        print(f"  ⚠️ ATENÇÃO: SHORT em OPUSDT teve loss. Trend pode não estar favorável.")

    # Sequência de wins/losses
    print(f"\n📈 SEQUÊNCIA")
    print("-" * 80)

    current_streak = 0
    best_streak = 0
    worst_streak = 0

    for trade in TODAYS_TRADES:
        if trade['pnl'] > 0:
            if current_streak >= 0:
                current_streak += 1
            else:
                current_streak = 1
            best_streak = max(best_streak, current_streak)
        else:
            if current_streak <= 0:
                current_streak -= 1
            else:
                current_streak = -1
            worst_streak = min(worst_streak, current_streak)

    print(f"Melhor sequência de wins:  {best_streak}")
    print(f"Pior sequência de losses: {abs(worst_streak)}")

    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES")
    print("-" * 80)

    if win_rate > 75:
        print(f"✅ EXCELENTE: Win rate de {win_rate:.1f}% hoje!")
        print(f"   Manter estratégia atual.")
    elif win_rate > 60:
        print(f"✅ BOM: Win rate de {win_rate:.1f}% hoje.")
        print(f"   Estratégia está funcionando, mas monitorar DOTUSDT.")
    else:
        print(f"⚠️ ATENÇÃO: Win rate de {win_rate:.1f}% hoje.")
        print(f"   Considerar reduzir MAX_POSITIONS ou aumentar MIN_SIGNAL_STRENGTH.")

    # DOTUSDT específico
    dot_pnl = sum(t['pnl'] for t in TODAYS_TRADES if t['symbol'] == 'DOTUSDT')
    if dot_pnl < 0:
        print(f"\n⚠️ DOTUSDT específico:")
        print(f"   - Reduzir tamanho de posição em DOTUSDT")
        print(f"   - Ou aumentar MIN_SIGNAL_STRENGTH para DOTUSDT (+5 pontos)")
        print(f"   - Ou remover DOTUSDT da lista de símbolos monitorados")

    # LONG vs SHORT
    long_pnl = by_side['LONG']['pnl']
    short_pnl = by_side['SHORT']['pnl']

    if long_pnl > 0 and short_pnl < 0:
        print(f"\n⚠️ LONG vs SHORT:")
        print(f"   LONG está funcionando bem: ${long_pnl:+.2f}")
        print(f"   SHORT teve prejuízo: ${short_pnl:+.2f}")
        print(f"   Recomendação: Considerar desabilitar trades SHORT temporariamente")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_today()
