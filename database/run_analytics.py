"""
BINANCE BOT - ADVANCED ANALYTICS MODULE (ASYNC VERSION)
======================================
Deep performance analysis with statistical modeling
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List

import asyncpg
from colorama import Fore, Style, init

init(autoreset=True)


class TradingAnalytics:
    """Advanced analytics engine for trading performance."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None

    async def connect(self):
        """Connect to PostgreSQL."""
        # Add SSL for Render databases
        if '?' not in self.db_url and 'sslmode=' not in self.db_url:
            self.db_url += '?sslmode=require'

        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print(f"{Fore.GREEN}✅ Connected to database")

    async def close(self):
        """Close connection."""
        if self.pool:
            await self.pool.close()
            print(f"{Fore.CYAN}🔌 Database connection closed")

    async def generate_summary(self):
        """Generate executive summary."""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}📋 EXECUTIVE SUMMARY")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
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

            print(f"{Fore.CYAN}Overall Performance:")
            print(f"{Fore.WHITE}  Total Trades: {row['total_trades']}")
            print(f"{Fore.WHITE}  Win Rate: {row['win_rate']}% ({row['wins']}W / {row['losses']}L)")
            print(f"{Fore.GREEN if row['total_pnl'] > 0 else Fore.RED}  Total PnL: ${row['total_pnl']}")
            print(f"{Fore.WHITE}  Average PnL: ${row['avg_pnl']} ({row['avg_pnl_percent']}%)")
            print(f"{Fore.WHITE}  Best Trade: ${row['max_win']}")
            print(f"{Fore.WHITE}  Worst Trade: ${row['max_loss']}")
            print(f"{Fore.WHITE}  Volatility: ${row['volatility']}")

            # Profit factor
            pf = await conn.fetchrow("""
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

            return dict(row)

    async def analyze_by_symbol(self):
        """1. PERFORMANCE BY SYMBOL"""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}1️⃣  PERFORMANCE BY SYMBOL")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
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
                    max_loss
                FROM symbol_stats
                ORDER BY total_pnl DESC
            """)

            print(f"{Fore.CYAN}{'Symbol':<12} {'Trades':<8} {'Win Rate':<10} {'Avg PnL':<10} {'Total PnL':<12} {'Volatility':<12} {'Max Win':<10} {'Max Loss':<10}")
            print(f"{Fore.CYAN}{'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*10} {'-'*10}")

            for row in rows:
                win_rate_str = f"{row['win_rate']}%"
                vol_str = f"±${row['volatility']}" if row['volatility'] else "N/A"

                symbol_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{symbol_color}{row['symbol']:<12} {Fore.WHITE}{row['total_trades']:<8} {Fore.CYAN}{win_rate_str:<10} {Fore.WHITE}${row['avg_pnl']:<9} {symbol_color}${row['total_pnl']:<11} {Fore.YELLOW}{vol_str:<12} {Fore.GREEN}${row['max_win']:<9} {Fore.RED}${row['max_loss']:<9}")

            if rows:
                best = max(rows, key=lambda x: x['total_pnl'])
                worst = min(rows, key=lambda x: x['total_pnl'])
                highest_winrate = max(rows, key=lambda x: x['win_rate'])

                print(f"\n{Fore.GREEN}🏆 Best Performing Symbol: {best['symbol']} (${best['total_pnl']})")
                print(f"{Fore.RED}📉 Worst Performing Symbol: {worst['symbol']} (${worst['total_pnl']})")
                print(f"{Fore.CYAN}🎯 Highest Win Rate: {highest_winrate['symbol']} ({highest_winrate['win_rate']}%)")

            return rows

    async def analyze_temporal_patterns(self):
        """2. TEMPORAL PATTERNS"""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}2️⃣  TEMPORAL PATTERNS (Day of Week & Hour)")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        async with self.pool.acquire() as conn:
            # Day of week
            dow_rows = await conn.fetch("""
                WITH dow_stats AS (
                    SELECT
                        EXTRACT(DOW FROM entry_time) as day_of_week,
                        COUNT(*) as trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                        ROUND(SUM(pnl)::numeric, 2) as total_pnl,
                        ROUND(AVG(pnl)::numeric, 2) as avg_pnl
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

            print(f"{Fore.CYAN}{'Day':<12} {'Trades':<8} {'Win Rate':<10} {'Total PnL':<12} {'Avg PnL':<10}")
            print(f"{Fore.CYAN}{'-'*12} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

            for row in dow_rows:
                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{Fore.WHITE}{row['day_name']:<12} {row['trades']:<8} {Fore.CYAN}{row['win_rate']}% {pnl_color}${row['total_pnl']:<11} {Fore.WHITE}${row['avg_pnl']:<9}")

            if dow_rows:
                best_day = max(dow_rows, key=lambda x: x['total_pnl'])
                worst_day = min(dow_rows, key=lambda x: x['total_pnl'])
                best_wr = max(dow_rows, key=lambda x: x['win_rate'])

                print(f"\n{Fore.GREEN}📅 Best Day: {best_day['day_name']} (${best_day['total_pnl']})")
                print(f"{Fore.RED}📅 Worst Day: {worst_day['day_name']} (${worst_day['total_pnl']})")
                print(f"{Fore.CYAN}🎯 Highest Win Rate Day: {best_wr['day_name']} ({best_wr['win_rate']}%)")

            # Hour of day
            print(f"\n{Fore.CYAN}Performance by Hour of Day - Top 10:")
            print(f"{Fore.CYAN}{'Hour':<8} {'Trades':<8} {'Win Rate':<10} {'Total PnL':<12} {'Avg PnL':<10}")
            print(f"{Fore.CYAN}{'-'*8} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

            hour_rows = await conn.fetch("""
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

            for row in hour_rows:
                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{Fore.WHITE}{int(row['hour']):02d}:00   {row['trades']:<8} {Fore.CYAN}{row['win_rate']}% {pnl_color}${row['total_pnl']:<11} {Fore.WHITE}${row['avg_pnl']:<9}")

            return dow_rows

    async def analyze_drawdown(self):
        """3. DRAWDOWN ANALYSIS"""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}3️⃣  DRAWDOWN & STREAK ANALYSIS")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        async with self.pool.acquire() as conn:
            trades = await conn.fetch("""
                SELECT
                    entry_time,
                    pnl,
                    pnl_percent
                FROM trades
                WHERE status = 'CLOSED' AND pnl IS NOT NULL
                ORDER BY entry_time ASC
            """)

            if not trades:
                print(f"{Fore.YELLOW}No trades to analyze")
                return {}

            # Calculate cumulative PnL
            cumulative = 0
            peak = 0
            max_drawdown = 0
            max_drawdown_date = None

            for trade in trades:
                cumulative += float(trade['pnl'])

                if cumulative > peak:
                    peak = cumulative

                drawdown = peak - cumulative
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_date = trade['entry_time']

            max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else 0

            print(f"{Fore.RED}Maximum Drawdown: ${max_drawdown:.2f} ({max_drawdown_pct:.2f}%)")
            print(f"{Fore.WHITE}Peak Before DD: ${peak:.2f}")
            print(f"{Fore.CYAN}Date of Max DD: {max_drawdown_date.strftime('%Y-%m-%d %H:%M') if max_drawdown_date else 'N/A'}")

            # Streaks
            current_streak = max_loss_streak = 0
            max_win_streak = 0

            for trade in trades:
                if trade['pnl'] < 0:
                    current_streak += 1
                    max_loss_streak = max(max_loss_streak, current_streak)
                else:
                    current_streak = 0

                if trade['pnl'] > 0:
                    max_win_streak += 1
                else:
                    max_win_streak = 0

            print(f"\n{Fore.RED}🔥 Maximum Loss Streak: {max_loss_streak} consecutive losses")
            print(f"{Fore.GREEN}✨ Maximum Win Streak: {max_win_streak} consecutive wins")

            return {
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown_pct,
                'max_loss_streak': max_loss_streak,
                'max_win_streak': max_win_streak
            }

    async def project_to_1m(self):
        """4. PROJECTION TO $1M"""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}4️⃣  PROJECTION TO $1,000,000")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
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

            # Current PnL
            current_pnl_row = await conn.fetchrow("""
                SELECT ROUND(SUM(pnl)::numeric, 2) as total_pnl
                FROM trades
                WHERE status = 'CLOSED' AND pnl IS NOT NULL
            """)
            current_pnl = float(current_pnl_row['total_pnl'] or 0)

            print(f"\n{Fore.CYAN}Current Capital (PnL): ${current_pnl:.2f}")

            # Scenarios
            print(f"\n{Fore.YELLOW}📊 Scenario Analysis (Monte Carlo-style Projection)")
            print(f"{Fore.CYAN}{'Scenario':<20} {'Daily Growth':<15} {'Days to $1M':<18} {'Years':<10}")
            print(f"{Fore.CYAN}{'-'*20} {'-'*15} {'-'*18} {'-'*10}")

            # Optimistic
            opt_daily = mean_pnl * trades_per_day * 1.5
            opt_days = (1000000 - current_pnl) / opt_daily if opt_daily > 0 else float('inf')
            print(f"{Fore.GREEN}{'Optimistic':<20} ${opt_daily:>13.2f}/day {opt_days:>15.0f} {opt_days/365:>9.1f}")

            # Realistic
            real_daily = mean_pnl * trades_per_day
            real_days = (1000000 - current_pnl) / real_daily if real_daily > 0 else float('inf')
            print(f"{Fore.CYAN}{'Realistic':<20} ${real_daily:>13.2f}/day {real_days:>15.0f} {real_days/365:>9.1f}")

            # Pessimistic
            pess_daily = mean_pnl * trades_per_day * 0.5
            pess_days = (1000000 - current_pnl) / pess_daily if pess_daily > 0 else float('inf')
            print(f"{Fore.RED}{'Pessimistic':<20} ${pess_daily:>13.2f}/day {pess_days:>15.0f} {pess_days/365:>9.1f}")

            # Risk assessment
            print(f"\n{Fore.YELLOW}⚠️ Risk Assessment:")

            if mean_pnl > 0 and stddev_pnl > 0:
                sharpe = mean_pnl / stddev_pnl
                print(f"{Fore.WHITE}  Sharpe-like Ratio: {sharpe:.3f}")

                if sharpe > 1.0:
                    risk_level, risk_color = "LOW", Fore.GREEN
                elif sharpe > 0.5:
                    risk_level, risk_color = "MODERATE", Fore.YELLOW
                else:
                    risk_level, risk_color = "HIGH", Fore.RED

                print(f"{risk_color}  Risk Level: {risk_level}")

            # Probability
            if win_rate >= 60:
                prob, prob_color = "HIGH (>70%)", Fore.GREEN
            elif win_rate >= 50:
                prob, prob_color = "MODERATE (50-70%)", Fore.YELLOW
            else:
                prob, prob_color = "LOW (<50%)", Fore.RED

            print(f"{prob_color}  Probability of Success: {prob}")

            # Confidence interval
            if stddev_pnl > 0:
                margin = 1.96 * (stddev_pnl / (total_trades ** 0.5))
                ci_lower = mean_pnl - margin
                ci_upper = mean_pnl + margin

                print(f"\n{Fore.CYAN}📈 95% Confidence Interval for Mean PnL:")
                print(f"{Fore.WHITE}  ${ci_lower:.2f} to ${ci_upper:.2f} per trade")

                cons_days = (1000000 - current_pnl) / (ci_lower * trades_per_day) if ci_lower > 0 else float('inf')
                agg_days = (1000000 - current_pnl) / (ci_upper * trades_per_day) if ci_upper > 0 else float('inf')

                print(f"{Fore.YELLOW}  Conservative: {cons_days:.0f} days ({cons_days/365:.1f} years)")
                print(f"{Fore.GREEN}  Aggressive: {agg_days:.0f} days ({agg_days/365:.1f} years)")

            return {
                'current_pnl': current_pnl,
                'win_rate': win_rate,
                'mean_pnl': mean_pnl,
                'stddev_pnl': stddev_pnl
            }


async def main():
    """Run complete analysis."""
    print(f"{Fore.MAGENTA}")
    print("=" * 70)
    print(" " * 15 + "BINANCE BOT - ADVANCED ANALYTICS")
    print("=" * 70)
    print(f"{Style.RESET_ALL}")

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print(f"{Fore.RED}DATABASE_URL not found in environment")
        return

    analytics = TradingAnalytics(db_url)

    try:
        await analytics.connect()

        # Run all analyses
        await analytics.generate_summary()
        await analytics.analyze_by_symbol()
        await analytics.analyze_temporal_patterns()
        await analytics.analyze_drawdown()
        await analytics.project_to_1m()

        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}✅ ANALYSIS COMPLETE")
        print(f"{Fore.GREEN}{'='*70}\n")

    finally:
        await analytics.close()


if __name__ == "__main__":
    asyncio.run(main())
