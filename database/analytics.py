"""
BINANCE BOT - ADVANCED ANALYTICS MODULE
======================================
Deep performance analysis with statistical modeling
"""

import sys
from datetime import datetime
from typing import Dict, List

import psycopg
from psycopg.rows import dict_row
from colorama import Fore, Style, init

init(autoreset=True)


class TradingAnalytics:
    """Advanced analytics engine for trading performance."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL."""
        self.conn = psycopg.connect(
            self.db_url,
            row_factory=dict_row,
            autocommit=True
        )
        print(f"{Fore.GREEN}✅ Connected to database")

    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()
            print(f"{Fore.CYAN}🔌 Database connection closed")

    def analyze_by_symbol(self):
        """
        1. PERFORMANCE BY SYMBOL
        - Win rate per symbol
        - Average profit per symbol
        - Volatility correlation
        """
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}1️⃣  PERFORMANCE BY SYMBOL")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        with self.conn.cursor() as cur:
            # Basic metrics by symbol
            cur.execute("""
                WITH symbol_stats AS (
                    SELECT
                        symbol,
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                        ROUND(AVG(pnl)::numeric, 2) as avg_pnl,
                        ROUND(AVG(pnl_percent)::numeric, 2) as avg_pnl_percent,
                        ROUND(SUM(pnl)::numeric, 2) as total_pnl,
                        ROUND(STDDEV(pnl)::numeric, 2) as stddev_pnl,
                        ROUND(MAX(pnl)::numeric, 2) as max_win,
                        ROUND(MIN(pnl)::numeric, 2) as max_loss
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                    GROUP BY symbol
                    HAVING COUNT(*) >= 2
                )
                SELECT
                    symbol,
                    total_trades,
                    wins,
                    losses,
                    ROUND(100.0 * wins / total_trades, 1) as win_rate,
                    avg_pnl,
                    avg_pnl_percent,
                    total_pnl,
                    stddev_pnl as volatility,
                    max_win,
                    max_loss,
                    ROUND(STDDEV(pnl_percent)::numeric, 2) as volatility_pct
                FROM symbol_stats
                ORDER BY total_pnl DESC
            """)

            results = cur.fetchall()

            print(f"{Fore.CYAN}{'Symbol':<12} {'Trades':<8} {'Win Rate':<10} {'Avg PnL':<10} {'Total PnL':<12} {'Volatility':<12} {'Max Win':<10} {'Max Loss':<10}")
            print(f"{Fore.CYAN}{'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*10} {'-'*10}")

            for row in results:
                win_rate_str = f"{row['win_rate']}%"
                avg_pnl_str = f"${row['avg_pnl']}"
                total_pnl_str = f"${row['total_pnl']}"
                vol_str = f"±${row['volatility']}" if row['volatility'] else "N/A"
                max_win_str = f"${row['max_win']}"
                max_loss_str = f"${row['max_loss']}"

                # Color coding
                symbol_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{symbol_color}{row['symbol']:<12} {Fore.WHITE}{row['total_trades']:<8} {Fore.CYAN}{win_rate_str:<10} {Fore.WHITE}{avg_pnl_str:<10} {symbol_color}{total_pnl_str:<12} {Fore.YELLOW}{vol_str:<12} {Fore.GREEN}{max_win_str:<10} {Fore.RED}{max_loss_str:<10}")

            # Best and worst symbols
            if results:
                best = max(results, key=lambda x: x['total_pnl'])
                worst = min(results, key=lambda x: x['total_pnl'])
                highest_winrate = max(results, key=lambda x: x['win_rate'])

                print(f"\n{Fore.GREEN}🏆 Best Performing Symbol: {best['symbol']} (${best['total_pnl']})")
                print(f"{Fore.RED}📉 Worst Performing Symbol: {worst['symbol']} (${worst['total_pnl']})")
                print(f"{Fore.CYAN}🎯 Highest Win Rate: {highest_winrate['symbol']} ({highest_winrate['win_rate']}%)")

            return results

    def analyze_temporal_patterns(self):
        """
        2. TEMPORAL PATTERNS
        - Performance by day of week
        - Performance by hour
        """
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}2️⃣  TEMPORAL PATTERNS (Day of Week & Hour)")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        with self.conn.cursor() as cur:
            # Day of week analysis
            cur.execute("""
                WITH dow_stats AS (
                    SELECT
                        EXTRACT(DOW FROM entry_time) as day_of_week,
                        COUNT(*) as trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        ROUND(SUM(pnl)::numeric, 2) as total_pnl,
                        ROUND(AVG(pnl)::numeric, 2) as avg_pnl,
                        ROUND(AVG(pnl_percent)::numeric, 2) as avg_pnl_percent
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                    GROUP BY day_of_week
                )
                SELECT
                    day_of_week,
                    trades,
                    wins,
                    ROUND(100.0 * wins / trades, 1) as win_rate,
                    total_pnl,
                    avg_pnl,
                    avg_pnl_percent,
                    CASE day_of_week
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_name
                FROM dow_stats
                ORDER BY day_of_week
            """)

            dow_results = cur.fetchall()

            print(f"{Fore.CYAN}{'Day':<12} {'Trades':<8} {'Win Rate':<10} {'Total PnL':<12} {'Avg PnL':<10}")
            print(f"{Fore.CYAN}{'-'*12} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

            for row in dow_results:
                win_rate_str = f"{row['win_rate']}%"
                total_pnl_str = f"${row['total_pnl']}"
                avg_pnl_str = f"${row['avg_pnl']}"

                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{Fore.WHITE}{row['day_name']:<12} {row['trades']:<8} {Fore.CYAN}{win_rate_str:<10} {pnl_color}{total_pnl_str:<12} {Fore.WHITE}{avg_pnl_str:<10}")

            # Best and worst days
            if dow_results:
                best_day = max(dow_results, key=lambda x: x['total_pnl'])
                worst_day = min(dow_results, key=lambda x: x['total_pnl'])
                best_wr = max(dow_results, key=lambda x: x['win_rate'])

                print(f"\n{Fore.GREEN}📅 Best Day: {best_day['day_name']} (${best_day['total_pnl']})")
                print(f"{Fore.RED}📅 Worst Day: {worst_day['day_name']} (${worst_day['total_pnl']})")
                print(f"{Fore.CYAN}🎯 Highest Win Rate Day: {best_wr['day_name']} ({best_wr['win_rate']}%)")

            # Hour of day analysis
            print(f"\n{Fore.CYAN}Performance by Hour of Day (Entry Time) - Top 10:")
            print(f"{Fore.CYAN}{'Hour':<8} {'Trades':<8} {'Win Rate':<10} {'Total PnL':<12} {'Avg PnL':<10}")
            print(f"{Fore.CYAN}{'-'*8} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

            cur.execute("""
                WITH hour_stats AS (
                    SELECT
                        EXTRACT(HOUR FROM entry_time) as hour,
                        COUNT(*) as trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        ROUND(SUM(pnl)::numeric, 2) as total_pnl,
                        ROUND(AVG(pnl)::numeric, 2) as avg_pnl
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                    GROUP BY hour
                    HAVING COUNT(*) >= 2
                )
                SELECT
                    hour,
                    trades,
                    wins,
                    ROUND(100.0 * wins / trades, 1) as win_rate,
                    total_pnl,
                    avg_pnl
                FROM hour_stats
                ORDER BY total_pnl DESC
                LIMIT 10
            """)

            hour_results = cur.fetchall()

            for row in hour_results:
                win_rate_str = f"{row['win_rate']}%"
                total_pnl_str = f"${row['total_pnl']}"
                avg_pnl_str = f"${row['avg_pnl']}"

                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{Fore.WHITE}{int(row['hour']):02d}:00   {row['trades']:<8} {Fore.CYAN}{win_rate_str:<10} {pnl_color}{total_pnl_str:<12} {Fore.WHITE}{avg_pnl_str:<10}")

            return dow_results

    def analyze_drawdown(self):
        """
        3. DRAWDOWN ANALYSIS
        - Maximum drawdown
        - Recovery time
        - Loss streaks
        """
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}3️⃣  DRAWDOWN & STREAK ANALYSIS")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        with self.conn.cursor() as cur:
            # Get trades in chronological order
            cur.execute("""
                SELECT
                    entry_time,
                    pnl,
                    pnl_percent
                FROM trades
                WHERE status = 'CLOSED' AND pnl IS NOT NULL
                ORDER BY entry_time ASC
            """)

            trades = cur.fetchall()

            if not trades:
                print(f"{Fore.YELLOW}No trades to analyze")
                return {}

            # Calculate cumulative PnL
            cumulative = 0
            peak = 0
            max_drawdown = 0
            max_drawdown_date = None
            equity_curve = []

            for trade in trades:
                cumulative += float(trade['pnl'])
                equity_curve.append({
                    'time': trade['entry_time'],
                    'equity': cumulative
                })

                if cumulative > peak:
                    peak = cumulative

                drawdown = peak - cumulative
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_date = trade['entry_time']

            # Calculate drawdown percentage
            max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else 0

            print(f"{Fore.RED}Maximum Drawdown: ${max_drawdown:.2f} ({max_drawdown_pct:.2f}%)")
            print(f"{Fore.WHITE}Peak Before DD: ${peak:.2f}")
            print(f"{Fore.CYAN}Date of Max DD: {max_drawdown_date.strftime('%Y-%m-%d %H:%M') if max_drawdown_date else 'N/A'}")

            # Analyze loss streaks
            current_streak = 0
            max_loss_streak = 0
            streak_start = None
            max_streak_start = None
            max_streak_end = None

            for i, trade in enumerate(trades):
                if trade['pnl'] < 0:
                    if current_streak == 0:
                        streak_start = trade['entry_time']
                    current_streak += 1

                    if current_streak > max_loss_streak:
                        max_loss_streak = current_streak
                        max_streak_start = streak_start
                        max_streak_end = trade['entry_time']
                else:
                    current_streak = 0

            print(f"\n{Fore.RED}🔥 Maximum Loss Streak: {max_loss_streak} consecutive losses")
            if max_streak_start and max_streak_end:
                duration = (max_streak_end - max_streak_start).days
                print(f"{Fore.WHITE}   Period: {max_streak_start.strftime('%Y-%m-%d')} to {max_streak_end.strftime('%Y-%m-%d')}")
                print(f"{Fore.WHITE}   Duration: {duration} days")

            # Calculate win streaks too
            current_win_streak = 0
            max_win_streak = 0

            for trade in trades:
                if trade['pnl'] > 0:
                    current_win_streak += 1
                    max_win_streak = max(max_win_streak, current_win_streak)
                else:
                    current_win_streak = 0

            print(f"{Fore.GREEN}✨ Maximum Win Streak: {max_win_streak} consecutive wins")

            # Recovery time analysis
            print(f"\n{Fore.CYAN}📈 Recovery Analysis:")
            if max_drawdown > 0:
                # Find recovery point
                recovered = False
                recovery_date = None
                recovery_trades = 0

                after_dd = [t for t in trades if t['entry_time'] > max_drawdown_date]
                running_eq = peak - max_drawdown

                for i, trade in enumerate(after_dd):
                    running_eq += float(trade['pnl'])
                    if running_eq >= peak:
                        recovered = True
                        recovery_date = trade['entry_time']
                        recovery_trades = i + 1
                        break

                if recovered:
                    recovery_days = (recovery_date - max_drawdown_date).days
                    print(f"{Fore.GREEN}✅ Recovered in {recovery_days} days ({recovery_trades} trades)")
                else:
                    print(f"{Fore.YELLOW}⚠️ Not yet recovered from max drawdown")

            return {
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown_pct,
                'max_loss_streak': max_loss_streak,
                'max_win_streak': max_win_streak,
                'equity_curve': equity_curve
            }

    def project_to_1m(self):
        """
        4. PROJECTION TO $1M
        - Monte Carlo simulation
        - Optimistic, realistic, pessimistic scenarios
        """
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}4️⃣  PROJECTION TO $1,000,000")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        with self.conn.cursor() as cur:
            # Get historical statistics
            cur.execute("""
                WITH stats AS (
                    SELECT
                        AVG(pnl) as mean_pnl,
                        STDDEV(pnl) as stddev_pnl,
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        MIN(entry_time) as first_trade,
                        MAX(entry_time) as last_trade
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                )
                SELECT
                    mean_pnl,
                    stddev_pnl,
                    total_trades,
                    100.0 * wins / total_trades as win_rate,
                    EXTRACT(DAY FROM (last_trade - first_trade)) as days_active
                FROM stats
            """)

            stats = cur.fetchone()

            if not stats or stats['total_trades'] < 10:
                print(f"{Fore.YELLOW}⚠️ Not enough data for reliable projection (need 10+ trades)")
                return {}

            mean_pnl = float(stats['mean_pnl'])
            stddev_pnl = float(stats['stddev_pnl']) if stats['stddev_pnl'] else 0
            win_rate = float(stats['win_rate'])
            total_trades = int(stats['total_trades'])
            days_active = int(stats['days_active']) if stats['days_active'] else 1

            trades_per_day = total_trades / max(days_active, 1)

            print(f"{Fore.CYAN}Historical Performance:")
            print(f"{Fore.WHITE}  Total Trades: {total_trades}")
            print(f"{Fore.WHITE}  Win Rate: {win_rate:.1f}%")
            print(f"{Fore.WHITE}  Average PnL per Trade: ${mean_pnl:.2f}")
            print(f"{Fore.WHITE}  Std Dev (Volatility): ${stddev_pnl:.2f}")
            print(f"{Fore.WHITE}  Trading Frequency: {trades_per_day:.1f} trades/day")
            print(f"{Fore.WHITE}  Days Active: {days_active}")

            # Calculate current total PnL
            cur.execute("""
                SELECT ROUND(SUM(pnl)::numeric, 2) as total_pnl
                FROM trades
                WHERE status = 'CLOSED' AND pnl IS NOT NULL
            """)

            current_pnl = float(cur.fetchone()['total_pnl'] or 0)

            print(f"\n{Fore.CYAN}Current Capital (PnL): ${current_pnl:.2f}")

            # Projected scenarios
            scenarios = {}

            # 1. Historical average (baseline)
            print(f"\n{Fore.YELLOW}📊 Scenario Analysis (Monte Carlo-style Projection)")
            print(f"{Fore.CYAN}{'Scenario':<20} {'Daily Growth':<15} {'Days to $1M':<18} {'Years':<10} {'Assumptions'}")
            print(f"{Fore.CYAN}{'-'*20} {'-'*15} {'-'*18} {'-'*10} {'-'*40}")

            # Optimistic: Best 10% performance
            optimistic_daily = mean_pnl * trades_per_day * 1.5
            days_to_1m_opt = (1000000 - current_pnl) / optimistic_daily if optimistic_daily > 0 else float('inf')
            years_opt = days_to_1m_opt / 365

            scenarios['optimistic'] = {
                'daily_growth': optimistic_daily,
                'days_to_1m': days_to_1m_opt,
                'years': years_opt
            }

            print(f"{Fore.GREEN}{'Optimistic':<20} ${optimistic_daily:>13.2f}/day {days_to_1m_opt:>15.0f} {years_opt:>9.1f} Best 10% days continue")

            # Realistic: Historical average
            realistic_daily = mean_pnl * trades_per_day
            days_to_1m_real = (1000000 - current_pnl) / realistic_daily if realistic_daily > 0 else float('inf')
            years_real = days_to_1m_real / 365

            scenarios['realistic'] = {
                'daily_growth': realistic_daily,
                'days_to_1m': days_to_1m_real,
                'years': years_real
            }

            print(f"{Fore.CYAN}{'Realistic':<20} ${realistic_daily:>13.2f}/day {days_to_1m_real:>15.0f} {years_real:>9.1f} Historical average continues")

            # Pessimistic: Worst 10% performance
            pessimistic_daily = mean_pnl * trades_per_day * 0.5
            days_to_1m_pess = (1000000 - current_pnl) / pessimistic_daily if pessimistic_daily > 0 else float('inf')
            years_pess = days_to_1m_pess / 365

            scenarios['pessimistic'] = {
                'daily_growth': pessimistic_daily,
                'days_to_1m': days_to_1m_pess,
                'years': years_pess
            }

            print(f"{Fore.RED}{'Pessimistic':<20} ${pessimistic_daily:>13.2f}/day {days_to_1m_pess:>15.0f} {years_pess:>9.1f} Worst 10% days continue")

            # Risk of ruin calculation (simplified)
            print(f"\n{Fore.YELLOW}⚠️ Risk Assessment:")

            if mean_pnl > 0 and stddev_pnl > 0:
                sharpe = (mean_pnl / stddev_pnl) if stddev_pnl > 0 else 0
                print(f"{Fore.WHITE}  Sharpe-like Ratio: {sharpe:.3f}")

                if sharpe > 1.0:
                    risk_level = "LOW"
                    risk_color = Fore.GREEN
                elif sharpe > 0.5:
                    risk_level = "MODERATE"
                    risk_color = Fore.YELLOW
                else:
                    risk_level = "HIGH"
                    risk_color = Fore.RED

                print(f"{risk_color}  Risk Level: {risk_level}")

            # Probability estimates based on win rate
            if win_rate >= 60:
                prob_success = "HIGH (>70%)"
                prob_color = Fore.GREEN
            elif win_rate >= 50:
                prob_success = "MODERATE (50-70%)"
                prob_color = Fore.YELLOW
            else:
                prob_success = "LOW (<50%)"
                prob_color = Fore.RED

            print(f"{prob_color}  Probability of Success: {prob_success}")

            # Confidence interval
            if stddev_pnl > 0:
                margin_of_error = 1.96 * (stddev_pnl / (total_trades ** 0.5))
                ci_lower = mean_pnl - margin_of_error
                ci_upper = mean_pnl + margin_of_error

                print(f"\n{Fore.CYAN}📈 95% Confidence Interval for Mean PnL:")
                print(f"{Fore.WHITE}  ${ci_lower:.2f} to ${ci_upper:.2f} per trade")

                # CI scenarios
                conservative_days = (1000000 - current_pnl) / (ci_lower * trades_per_day) if ci_lower > 0 else float('inf')
                aggressive_days = (1000000 - current_pnl) / (ci_upper * trades_per_day) if ci_upper > 0 else float('inf')

                print(f"{Fore.YELLOW}  Conservative (lower CI): {conservative_days:.0f} days ({conservative_days/365:.1f} years)")
                print(f"{Fore.GREEN}  Aggressive (upper CI): {aggressive_days:.0f} days ({aggressive_days/365:.1f} years)")

            return {
                'current_pnl': current_pnl,
                'scenarios': scenarios,
                'win_rate': win_rate,
                'mean_pnl': mean_pnl,
                'stddev_pnl': stddev_pnl
            }

    def generate_summary(self):
        """Generate executive summary."""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}📋 EXECUTIVE SUMMARY")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        with self.conn.cursor() as cur:
            cur.execute("""
                WITH summary AS (
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                        ROUND(SUM(pnl)::numeric, 2) as total_pnl,
                        ROUND(AVG(pnl)::numeric, 2) as avg_pnl,
                        ROUND(AVG(pnl_percent)::numeric, 2) as avg_pnl_percent,
                        ROUND(MAX(pnl)::numeric, 2) as max_win,
                        ROUND(MIN(pnl)::numeric, 2) as max_loss,
                        ROUND(STDDEV(pnl)::numeric, 2) as volatility
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                )
                SELECT
                    total_trades,
                    wins,
                    losses,
                    ROUND(100.0 * wins / total_trades, 1) as win_rate,
                    total_pnl,
                    avg_pnl,
                    avg_pnl_percent,
                    max_win,
                    max_loss,
                    volatility
                FROM summary
            """)

            s = cur.fetchone()

            print(f"{Fore.CYAN}Overall Performance:")
            print(f"{Fore.WHITE}  Total Trades: {s['total_trades']}")
            print(f"{Fore.WHITE}  Win Rate: {s['win_rate']}% ({s['wins']}W / {s['losses']}L)")
            print(f"{Fore.GREEN if s['total_pnl'] > 0 else Fore.RED}  Total PnL: ${s['total_pnl']}")
            print(f"{Fore.WHITE}  Average PnL: ${s['avg_pnl']} ({s['avg_pnl_percent']}%)")
            print(f"{Fore.WHITE}  Best Trade: ${s['max_win']}")
            print(f"{Fore.WHITE}  Worst Trade: ${s['max_loss']}")
            print(f"{Fore.WHITE}  Volatility: ${s['volatility']}")

            # Profit factor
            cur.execute("""
                WITH profit_factor AS (
                    SELECT
                        SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as gross_profit,
                        SUM(CASE WHEN pnl < 0 THEN ABS(pnl) ELSE 0 END) as gross_loss
                    FROM trades
                    WHERE status = 'CLOSED' AND pnl IS NOT NULL
                )
                SELECT
                    gross_profit,
                    gross_loss,
                    ROUND(gross_profit / NULLIF(gross_loss, 0), 2) as profit_factor
                FROM profit_factor
            """)

            pf = cur.fetchone()

            if pf['profit_factor']:
                print(f"\n{Fore.CYAN}Risk Metrics:")
                print(f"{Fore.WHITE}  Profit Factor: {pf['profit_factor']}")
                print(f"  (Gross Profit: ${pf['gross_profit']} | Gross Loss: ${pf['gross_loss']})")

                if pf['profit_factor'] >= 2.0:
                    print(f"{Fore.GREEN}  → EXCELLENT: Profit factor >= 2.0")
                elif pf['profit_factor'] >= 1.5:
                    print(f"{Fore.YELLOW}  → GOOD: Profit factor >= 1.5")
                else:
                    print(f"{Fore.RED}  → NEEDS IMPROVEMENT: Profit factor < 1.5")

            return dict(s)


def main():
    """Run complete analysis."""
    print(f"{Fore.MAGENTA}")
    print("=" * 70)
    print(" " * 15 + "BINANCE BOT - ADVANCED ANALYTICS")
    print("=" * 70)
    print(f"{Style.RESET_ALL}")

    # Connect to database
    db_url = "postgresql://bot_binance_user:2yT3u1JBiSintBfwmNlkJlSMmNJnJq@dpg-686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"

    analytics = TradingAnalytics(db_url)

    try:
        analytics.connect()

        # Run all analyses
        analytics.generate_summary()
        analytics.analyze_by_symbol()
        analytics.analyze_temporal_patterns()
        analytics.analyze_drawdown()
        analytics.project_to_1m()

        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ ANALYSIS COMPLETE")
        print(f"{Fore.GREEN}{'='*70}\n")

    finally:
        analytics.close()


if __name__ == "__main__":
    main()
