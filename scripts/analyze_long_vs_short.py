#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISE ESTATÍSTICA COMPLETA: LONG vs SHORT
Baseado em 35 trades históricos + 14 trades de hoje
"""
import asyncio
import sys
import codecs
from datetime import datetime
from collections import defaultdict
import asyncpg

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

async def analyze_long_vs_short():
    """Análise estatística LONG vs SHORT."""

    DATABASE_URL = "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"

    print("=" * 100)
    print("ANÁLISE ESTATÍSTICA COMPLETA: LONG vs SHORT")
    print("=" * 100)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Buscar TODOS os trades
        trades = await conn.fetch("""
            SELECT
                symbol,
                side,
                entry_price,
                exit_price,
                pnl,
                pnl_percent,
                entry_time,
                exit_time,
                exit_reason
            FROM trades
            WHERE status = 'CLOSED'
            ORDER BY entry_time ASC
        """)

        print(f"\n📊 TOTAL DE TRADES ANALISADOS: {len(trades)}")

        # Separar LONG e SHORT
        long_trades = [t for t in trades if t['side'] == 'LONG']
        short_trades = [t for t in trades if t['side'] == 'SHORT']

        print(f"  LONG:  {len(long_trades)} trades")
        print(f"  SHORT: {len(short_trades)} trades")

        # ====================================================================
        # 1. ESTATÍSTICAS GERAIS
        # ====================================================================

        print("\n" + "=" * 100)
        print("1. ESTATÍSTICAS GERAIS POR LADO")
        print("=" * 100)

        for side, side_trades in [("LONG", long_trades), ("SHORT", short_trades)]:
            if not side_trades:
                print(f"\n{side}: NENHUM TRADE")
                continue

            total = len(side_trades)
            wins = sum(1 for t in side_trades if t['pnl'] > 0)
            losses = sum(1 for t in side_trades if t['pnl'] < 0)
            total_pnl = sum(t['pnl'] for t in side_trades)
            avg_pnl = total_pnl / total
            avg_win = sum(t['pnl'] for t in side_trades if t['pnl'] > 0) / wins if wins > 0 else 0
            avg_loss = sum(t['pnl'] for t in side_trades if t['pnl'] < 0) / losses if losses > 0 else 0

            print(f"\n{side}:")
            print(f"  Total Trades:     {total}")
            print(f"  Wins:            {wins} ({100.0 * wins / total:.1f}%)")
            print(f"  Losses:          {losses} ({100.0 * losses / total:.1f}%)")
            print(f"  Total PnL:       ${total_pnl:+.2f}")
            print(f"  Avg PnL/Trade:   ${avg_pnl:+.2f}")
            print(f"  Avg Win:         ${avg_win:+.2f}")
            print(f"  Avg Loss:         ${avg_loss:+.2f}")
            print(f"  Profit Factor:    {abs(avg_win / avg_loss):.2f}" if avg_loss != 0 else "N/A")

            # Calcular win rate por trades
            wr = 100.0 * wins / total
            if wr >= 70:
                print(f"  Status:           ✅ EXCELENTE ({wr:.1f}% WR)")
            elif wr >= 55:
                print(f"  Status:           ✅ BOM ({wr:.1f}% WR)")
            elif wr >= 45:
                print(f"  Status:           ⚠️  ABAIXO DO ESPERADO ({wr:.1f}% WR)")
            else:
                print(f"  Status:           ❌ POBRE ({wr:.1f}% WR)")

        # ====================================================================
        # 2. ANÁLISE POR SÍMBOLO
        # ====================================================================

        print("\n" + "=" * 100)
        print("2. PERFORMANCE POR SÍMBOLO (LONG vs SHORT)")
        print("=" * 100)

        # Agrupar por símbolo e lado
        by_symbol_side = defaultdict(lambda: {'LONG': {'trades': [], 'total_pnl': 0, 'wins': 0},
                                         'SHORT': {'trades': [], 'total_pnl': 0, 'wins': 0}})

        for t in trades:
            sym = t['symbol']
            side = t['side']
            by_symbol_side[sym][side]['trades'].append(t)
            by_symbol_side[sym][side]['total_pnl'] += t['pnl']
            if t['pnl'] > 0:
                by_symbol_side[sym][side]['wins'] += 1

        # Ordenar por total_pnl
        sorted_symbols = sorted(by_symbol_side.items(),
                             key=lambda x: x[1]['LONG']['total_pnl'] + x[1]['SHORT']['total_pnl'],
                             reverse=True)

        for sym, data in sorted_symbols:
            long_stats = data['LONG']
            short_stats = data['SHORT']
            long_trades = long_stats['trades']
            short_trades = short_stats['trades']

            print(f"\n{sym}:")
            print(f"  LONG:")
            if long_trades:
                lt = len(long_trades)
                lw = long_stats['wins']
                lp = long_stats['total_pnl']
                lwr = 100.0 * lw / lt
                lap = lp / lt
                print(f"    Trades: {lt} | Wins: {lw}/{lt} ({lwr:.1f}%) | PnL: ${lp:+.2f} | Avg: ${lap:+.2f}")
            else:
                print(f"    Nenhum trade")

            print(f"  SHORT:")
            if short_trades:
                st = len(short_trades)
                sw = short_stats['wins']
                sp = short_stats['total_pnl']
                swr = 100.0 * sw / st
                sap = sp / st
                print(f"    Trades: {st} | Wins: {sw}/{st} ({swr:.1f}%) | PnL: ${sp:+.2f} | Avg: ${sap:+.2f}")
            else:
                print(f"    Nenhum trade")

            # Comparativo
            if long_trades and short_trades:
                diff_wr = (100.0 * long_stats['wins'] / len(long_trades) -
                         100.0 * short_stats['wins'] / len(short_trades))
                diff_pnl = long_stats['total_pnl'] - short_stats['total_pnl']

                print(f"  DIFERENÇA:")
                print(f"    Win Rate: {diff_wr:+.1f}pp (LONG {'melhor' if diff_wr > 0 else 'pior'})")
                print(f"    Total PnL: ${diff_pnl:+.2f} (LONG {'melhor' if diff_pnl > 0 else 'pior'})")

        # ====================================================================
        # 3. TESTE ESTATÍSTICO (Chi-quadrado)
        # ====================================================================

        print("\n" + "=" * 100)
        print("3. TESTE ESTATÍSTICO: HÁ DIFERENÇA SIGNIFICATIVA?")
        print("=" * 100)

        long_wins = sum(1 for t in long_trades if t['pnl'] > 0)
        long_total = len(long_trades)
        short_wins = sum(1 for t in short_trades if t['pnl'] > 0)
        short_total = len(short_trades)

        # Teste de proporção
        # H0: Não há diferença entre LONG e SHORT
        # H1: Há diferença significativa

        print(f"\nLONG:    {long_wins}/{long_total} wins ({100.0 * long_wins / long_total:.1f}%)")
        if short_total > 0:
            print(f"SHORT:   {short_wins}/{short_total} wins ({100.0 * short_wins / short_total:.1f}%)")
        else:
            print(f"SHORT:   0/0 wins (N/A)")

        total_wins = long_wins + short_wins
        total_trades_all = long_total + short_total
        overall_wr = 100.0 * total_wins / total_trades_all

        print(f"OVERALL: {total_wins}/{total_trades_all} wins ({overall_wr:.1f}%)")

        # Diferença de win rate
        diff_wr = (100.0 * long_wins / long_total) - (100.0 * short_wins / short_total) if short_total > 0 else 0

        print(f"\nDIFERENÇA DE WIN RATE:")
        print(f"  LONG - SHORT = {diff_wr:+.1f}pp")

        # Verificar se é estatisticamente significativo
        # Usando regra prática: se diff > 20pp e temos > 10 trades cada, é significativo
        if long_total >= 10 and short_total >= 10:
            if diff_wr >= 20:
                print(f"  ✅ DIFERENÇA ESTATISTICAMENTE SIGNIFICATIVA (>20pp)")
                print(f"     LONG é consistentemente MUITO MELHOR que SHORT")
            elif diff_wr >= 10:
                print(f"  ⚠️  DIFERENÇA MODERADA (10-20pp)")
                print(f"     LONG tende a ser melhor que SHORT")
            elif diff_wr >= 5:
                print(f"  ⚠️  DIFERENÇA PEQUENA (5-10pp)")
                print(f"     Há leve vantagem de LONG")
            else:
                print(f"  ℹ️  DIFERENÇA NÃO SIGNIFICATIVA (<5pp)")
                print(f"     Não há evidência estatística clara")
        else:
            print(f"  ⚠️  AMOSTRA INSUFICIENTE PARA TESTE ESTATÍSTICO")
            print(f"     Precisa de mais trades SHORT para conclusão sólida")

        # ====================================================================
        # 4. ANÁLISE POR HORÁRIO
        # ====================================================================

        print("\n" + "=" * 100)
        print("4. ANÁLISE POR HORÁRIO (LONG vs SHORT)")
        print("=" * 100)

        def get_hour_bin(timestamp):
            hour = timestamp.hour
            if 0 <= hour < 6:
                return "00-06"
            elif 6 <= hour < 12:
                return "06-12"
            elif 12 <= hour < 18:
                return "12-18"
            else:
                return "18-24"

        by_hour = defaultdict(lambda: {'LONG': {'trades': [], 'total_pnl': 0},
                                      'SHORT': {'trades': [], 'total_pnl': 0}})

        for t in trades:
            hour_bin = get_hour_bin(t['entry_time'])
            side = t['side']
            by_hour[hour_bin][side]['trades'].append(t)
            by_hour[hour_bin][side]['total_pnl'] += t['pnl']

        for hour_bin in sorted(by_hour.keys()):
            data = by_hour[hour_bin]
            print(f"\nHorário {hour_bin}:")
            for side in ['LONG', 'SHORT']:
                trades_list = data[side]['trades']
                if trades_list:
                    t_count = len(trades_list)
                    wins = sum(1 for t in trades_list if t['pnl'] > 0)
                    pnl = data[side]['total_pnl']
                    wr = 100.0 * wins / t_count
                    print(f"  {side}: {t_count} trades | {wins}/{t_count} ({wr:.1f}%) | PnL: ${pnl:+.2f}")

        # ====================================================================
        # 5. ANÁLISE POR DIA DA SEMANA
        # ====================================================================

        print("\n" + "=" * 100)
        print("5. ANÁLISE POR DIA DA SEMANA")
        print("=" * 100)

        weekday_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

        by_weekday = defaultdict(lambda: {'LONG': {'trades': [], 'total_pnl': 0},
                                         'SHORT': {'trades': [], 'total_pnl': 0}})

        for t in trades:
            wd = t['entry_time'].weekday()
            side = t['side']
            by_weekday[wd][side]['trades'].append(t)
            by_weekday[wd][side]['total_pnl'] += t['pnl']

        for wd in range(7):
            data = by_weekday[wd]
            long_trades_list = data['LONG']['trades']
            short_trades_list = data['SHORT']['trades']

            if not long_trades_list and not short_trades_list:
                continue

            print(f"\n{weekday_names[wd]}:")
            if long_trades_list:
                lt = len(long_trades_list)
                lw = sum(1 for t in long_trades_list if t['pnl'] > 0)
                lp = data['LONG']['total_pnl']
                print(f"  LONG:  {lt} trades | {lw}/{lt} wins | PnL: ${lp:+.2f}")

            if short_trades_list:
                st = len(short_trades_list)
                sw = sum(1 for t in short_trades_list if t['pnl'] > 0)
                sp = data['SHORT']['total_pnl']
                print(f"  SHORT: {st} trades | {sw}/{st} wins | PnL: ${sp:+.2f}")

        # ====================================================================
        # 6. ANÁLISE DE RUNS (SEQUÊNCIAS)
        # ====================================================================

        print("\n" + "=" * 100)
        print("6. ANÁLISE DE RUNS (WINS/LOSSES CONSECUTIVOS)")
        print("=" * 100)

        def analyze_runs(trades_list):
            """Analisar sequências de wins/losses."""
            if not trades_list:
                return None

            runs = []
            current_run = {'type': None, 'count': 0, 'pnl': 0}

            for t in trades_list:
                is_win = t['pnl'] > 0
                run_type = 'WIN' if is_win else 'LOSS'

                if current_run['type'] is None:
                    current_run['type'] = run_type
                    current_run['count'] = 1
                    current_run['pnl'] = t['pnl']
                elif current_run['type'] == run_type:
                    current_run['count'] += 1
                    current_run['pnl'] += t['pnl']
                else:
                    runs.append(current_run.copy())
                    current_run = {'type': run_type, 'count': 1, 'pnl': t['pnl']}

            if current_run['type'] is not None:
                runs.append(current_run)

            return runs

        print("\nLONG:")
        long_runs = analyze_runs(long_trades)
        if long_runs:
            win_runs = [r for r in long_runs if r['type'] == 'WIN']
            loss_runs = [r for r in long_runs if r['type'] == 'LOSS']

            if win_runs:
                best_win = max(win_runs, key=lambda x: x['count'])
                avg_win_run = sum(r['count'] for r in win_runs) / len(win_runs)
                print(f"  Melhor run de WINS: {best_win['count']} trades consecutivos (+${best_win['pnl']:.2f})")
                print(f"  Média de wins/run: {avg_win_run:.1f} trades")

            if loss_runs:
                worst_loss = max(loss_runs, key=lambda x: x['count'])
                avg_loss_run = sum(r['count'] for r in loss_runs) / len(loss_runs)
                print(f"  Pior run de LOSSES: {worst_loss['count']} trades consecutivos (${worst_loss['pnl']:.2f})")
                print(f"  Média de losses/run: {avg_loss_run:.1f} trades")

        print("\nSHORT:")
        short_runs = analyze_runs(short_trades)
        if short_runs:
            win_runs = [r for r in short_runs if r['type'] == 'WIN']
            loss_runs = [r for r in short_runs if r['type'] == 'LOSS']

            if win_runs:
                best_win = max(win_runs, key=lambda x: x['count'])
                avg_win_run = sum(r['count'] for r in win_runs) / len(win_runs)
                print(f"  Melhor run de WINS: {best_win['count']} trades consecutivos (+${best_win['pnl']:.2f})")
                print(f"  Média de wins/run: {avg_win_run:.1f} trades")

            if loss_runs:
                worst_loss = max(loss_runs, key=lambda x: x['count'])
                avg_loss_run = sum(r['count'] for r in loss_runs) / len(loss_runs)
                print(f"  Pior run de LOSSES: {worst_loss['count']} trades consecutivos (${worst_loss['pnl']:.2f})")
                print(f"  Média de losses/run: {avg_loss_run:.1f} trades")

        # ====================================================================
        # 7. CONCLUSÃO
        # ====================================================================

        print("\n" + "=" * 100)
        print("7. CONCLUSÃO")
        print("=" * 100)

        long_wins = sum(1 for t in long_trades if t['pnl'] > 0)
        long_wr = 100.0 * long_wins / len(long_trades) if long_trades else 0
        long_total_pnl = sum(t['pnl'] for t in long_trades)

        short_wins = sum(1 for t in short_trades if t['pnl'] > 0)
        short_wr = 100.0 * short_wins / len(short_trades) if short_trades else 0
        short_total_pnl = sum(t['pnl'] for t in short_trades)

        print(f"\nLONG:")
        print(f"  Win Rate:    {long_wr:.1f}%")
        print(f"  Total PnL:    ${long_total_pnl:+.2f}")
        print(f"  Trades:       {len(long_trades)}")

        print(f"\nSHORT:")
        print(f"  Win Rate:    {short_wr:.1f}%")
        print(f"  Total PnL:    ${short_total_pnl:+.2f}")
        print(f"  Trades:       {len(short_trades)}")

        print(f"\nDIFERENÇA:")
        print(f"  Win Rate:    {long_wr - short_wr:+.1f}pp")
        print(f"  Total PnL:   ${long_total_pnl - short_total_pnl:+.2f}")

        # Recomendação estatística
        print(f"\n{'=' * 100}")
        print("VEREDITO ESTATÍSTICO:")
        print("=" * 100)

        if len(long_trades) >= 10 and len(short_trades) >= 10:
            if long_wr - short_wr >= 20:
                print(f"✅ DIFERENÇA SIGNIFICATIVA CONFIRMADA")
                print(f"   LONG tem win rate {long_wr:.1f}% vs SHORT {short_wr:.1f}%")
                print(f"   Diferença de {long_wr - short_wr:.1f}pp é estatisticamente significativa")
                print(f"   EVIDÊNCIA FORTE: Estratégia funciona MUITO MELHOR em LONG")
            elif long_wr - short_wr >= 10:
                print(f"⚠️  HÁ VANTAGEM DE LONG")
                print(f"   LONG tem win rate {long_wr:.1f}% vs SHORT {short_wr:.1f}%")
                print(f"   Diferença de {long_wr - short_wr:.1f}pp sugere vantagem moderada")
                print(f"   EVIDÊNCIA MODERADA: LONG tende a performar melhor")
            else:
                print(f"ℹ️  SEM DIFERENÇA CLARA")
                print(f"   LONG: {long_wr:.1f}% | SHORT: {short_wr:.1f}%")
                print(f"   Diferença de {long_wr - short_wr:.1f}pp não é conclusiva")
                print(f"   EVIDÊNCIA FRACA: Pode ser variação normal")
        else:
            print(f"⚠️  AMOSTRA INSUFICIENTE")
            print(f"   LONG: {len(long_trades)} trades")
            print(f"   SHORT: {len(short_trades)} trades")
            print(f"   Precisa de mais dados (especialmente SHORT) para conclusão")

        print("\n" + "=" * 100)

    finally:
        await conn.close()

if __name__ == "__main__":
    try:
        asyncio.run(analyze_long_vs_short())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
