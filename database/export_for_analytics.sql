-- ============================================================================
-- BINANCE BOT - COMPLETE ANALYTICS QUERIES
-- ============================================================================
-- Run these queries in the Supabase SQL Editor or Render SQL Dashboard
-- ============================================================================

-- ============================================================================
-- 1. EXECUTIVE SUMMARY
-- ============================================================================

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
FROM summary;

-- ============================================================================
-- 2. PERFORMANCE BY SYMBOL
-- ============================================================================

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
ORDER BY total_pnl DESC;

-- ============================================================================
-- 3. PERFORMANCE BY DAY OF WEEK
-- ============================================================================

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
ORDER BY day_of_week;

-- ============================================================================
-- 4. PERFORMANCE BY HOUR OF DAY
-- ============================================================================

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
LIMIT 10;

-- ============================================================================
-- 5. PROFIT FACTOR
-- ============================================================================

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
FROM profit_factor;

-- ============================================================================
-- 6. DRAWDOWN ANALYSIS (with equity curve)
-- ============================================================================

WITH equity_curve AS (
    SELECT
        entry_time,
        pnl,
        SUM(pnl) OVER (ORDER BY entry_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_pnl,
        SUM(pnl) OVER (ORDER BY entry_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as peak
    FROM trades
    WHERE status = 'CLOSED' AND pnl IS NOT NULL
    ORDER BY entry_time ASC
),
drawdown_calculations AS (
    SELECT
        entry_time,
        pnl,
        cumulative_pnl,
        peak,
        (peak - cumulative_pnl) as drawdown,
        CASE WHEN peak > 0 THEN ((peak - cumulative_pnl) / peak * 100) ELSE 0 END as drawdown_percent
    FROM (
        SELECT
            entry_time,
            pnl,
            cumulative_pnl,
            MAX(cumulative_pnl) OVER (ORDER BY entry_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as peak
        FROM equity_curve
    ) sub
)
SELECT
    entry_time,
    pnl,
    cumulative_pnl,
    peak,
    ROUND(drawdown, 2) as drawdown,
    ROUND(drawdown_percent, 2) as drawdown_percent
FROM drawdown_calculations
ORDER BY entry_time DESC
LIMIT 50;

-- ============================================================================
-- 7. MAX DRAWDOWN SUMMARY
-- ============================================================================

WITH equity_curve AS (
    SELECT
        entry_time,
        pnl,
        SUM(pnl) OVER (ORDER BY entry_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_pnl
    FROM trades
    WHERE status = 'CLOSED' AND pnl IS NOT NULL
),
peaks AS (
    SELECT
        entry_time,
        cumulative_pnl,
        MAX(cumulative_pnl) OVER (ORDER BY entry_time ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as peak
    FROM equity_curve
),
drawdowns AS (
    SELECT
        entry_time,
        cumulative_pnl,
        peak,
        (peak - cumulative_pnl) as drawdown,
        CASE WHEN peak > 0 THEN ((peak - cumulative_pnl) / peak * 100) ELSE 0 END as drawdown_percent
    FROM peaks
)
SELECT
    ROUND(MAX(drawdown), 2) as max_drawdown,
    ROUND(MAX(drawdown_percent), 2) as max_drawdown_percent,
    (SELECT entry_time FROM drawdowns WHERE drawdown = (SELECT MAX(drawdown) FROM drawdowns) LIMIT 1) as max_drawdown_date,
    (SELECT peak FROM drawdowns WHERE drawdown = (SELECT MAX(drawdown) FROM drawdowns) LIMIT 1) as peak_before_drawdown
FROM drawdowns;

-- ============================================================================
-- 8. STREAK ANALYSIS
-- ============================================================================

WITH numbered_trades AS (
    SELECT
        entry_time,
        pnl,
        ROW_NUMBER() OVER (ORDER BY entry_time ASC) as rn
    FROM trades
    WHERE status = 'CLOSED' AND pnl IS NOT NULL
),
win_streaks AS (
    SELECT
        pnl,
        rn,
        ROW_NUMBER() OVER (ORDER BY rn) - ROW_NUMBER() OVER (PARTITION BY (pnl > 0) ORDER BY rn) as grp
    FROM numbered_trades
    WHERE pnl > 0
),
loss_streaks AS (
    SELECT
        pnl,
        rn,
        ROW_NUMBER() OVER (ORDER BY rn) - ROW_NUMBER() OVER (PARTITION BY (pnl < 0) ORDER BY rn) as grp
    FROM numbered_trades
    WHERE pnl < 0
)
SELECT
    'MAX WIN STREAK' as metric,
    COUNT(*) as value
FROM win_streaks
GROUP BY grp
ORDER BY COUNT(*) DESC
LIMIT 1

UNION ALL

SELECT
    'MAX LOSS STREAK' as metric,
    COUNT(*) as value
FROM loss_streaks
GROUP BY grp
ORDER BY COUNT(*) DESC
LIMIT 1;

-- ============================================================================
-- 9. STATISTICAL PROJECTION METRICS
-- ============================================================================

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
    ROUND(mean_pnl::numeric, 2) as mean_pnl,
    ROUND(stddev_pnl::numeric, 2) as stddev_pnl,
    total_trades,
    ROUND(100.0 * wins / total_trades, 1) as win_rate,
    EXTRACT(DAY FROM (last_trade - first_trade)) as days_active,
    ROUND(total_trades::numeric / EXTRACT(DAY FROM (last_trade - first_trade)), 2) as trades_per_day
FROM stats;

-- ============================================================================
-- 10. RECENT TRADES (Last 30)
-- ============================================================================

SELECT
    TO_CHAR(entry_time, 'YYYY-MM-DD HH24:MI:SS') as entry_time,
    symbol,
    side,
    ROUND(entry_price::numeric, 4) as entry_price,
    ROUND(exit_price::numeric, 4) as exit_price,
    ROUND(pnl::numeric, 2) as pnl,
    ROUND(pnl_percent::numeric, 2) as pnl_percent,
    status,
    close_reason
FROM trades
WHERE status = 'CLOSED' AND pnl IS NOT NULL
ORDER BY entry_time DESC
LIMIT 30;

-- ============================================================================
-- 11. TODAY'S PERFORMANCE
-- ============================================================================

SELECT
    COUNT(*) as trades_today,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins_today,
    ROUND(SUM(pnl)::numeric, 2) as total_pnl_today,
    ROUND(AVG(pnl)::numeric, 2) as avg_pnl_today,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate_today
FROM trades
WHERE DATE(entry_time) = CURRENT_DATE
  AND status = 'CLOSED' AND pnl IS NOT NULL;

-- ============================================================================
-- 12. CONFIDENCE INTERVAL FOR MEAN PnL (95%)
-- ============================================================================

WITH stats AS (
    SELECT
        AVG(pnl) as mean_pnl,
        STDDEV(pnl) as stddev_pnl,
        COUNT(*) as n
    FROM trades
    WHERE status = 'CLOSED' AND pnl IS NOT NULL
)
SELECT
    ROUND(mean_pnl::numeric, 2) as mean_pnl,
    ROUND(mean_pnl - (1.96 * stddev_pnl / SQRT(CAST(n AS FLOAT)))::numeric, 2) as ci_95_lower,
    ROUND(mean_pnl + (1.96 * stddev_pnl / SQRT(CAST(n AS FLOAT)))::numeric, 2) as ci_95_upper,
    ROUND((1.96 * stddev_pnl / SQRT(CAST(n AS FLOAT)))::numeric, 2) as margin_of_error
FROM stats;
