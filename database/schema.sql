-- ============================================================================
-- BINANCE BOT DATABASE SCHEMA
-- PostgreSQL 16+ with JSONB support
-- ============================================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- TABLE: symbols (Catálogo de ativos negociáveis)
-- ============================================================================
CREATE TABLE IF NOT EXISTS symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_asset TEXT NOT NULL,
    quote_asset TEXT NOT NULL DEFAULT 'USDT',
    tick_size NUMERIC(20, 12) NOT NULL,
    lot_size NUMERIC(20, 12) NOT NULL,
    min_notional NUMERIC(20, 8) NOT NULL,
    max_leverage INTEGER NOT NULL DEFAULT 125,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TABLE: trades (Operações de trading - tabela principal)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL REFERENCES symbols(symbol),

    -- Trade details
    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    quantity NUMERIC(20, 12) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    exit_price NUMERIC(20, 8),

    -- Stop Loss / Take Profit
    sl_price NUMERIC(20, 8),
    tp_price NUMERIC(20, 8),

    -- Timing
    entry_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMPTZ,
    duration_seconds INTERVAL,

    -- PnL
    pnl NUMERIC(20, 8),
    pnl_percent NUMERIC(10, 4),
    commission NUMERIC(20, 8) DEFAULT 0,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'CANCELED')),
    close_reason TEXT CHECK (close_reason IN ('TP', 'SL', 'MANUAL', 'SIGNAL', 'ERROR')),

    -- Exchange references
    entry_order_id BIGINT,
    exit_order_id BIGINT,
    sl_order_id BIGINT,
    tp_order_id BIGINT,

    -- AI analysis (if available)
    ai_decision JSONB,

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl DESC);

-- ============================================================================
-- TABLE: positions (Estado atual de posições - cache de memória)
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL REFERENCES symbols(symbol) UNIQUE,

    -- Position details
    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    quantity NUMERIC(20, 12) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    current_price NUMERIC(20, 8),

    -- Unrealized PnL
    unrealized_pnl NUMERIC(20, 8),
    unrealized_percent NUMERIC(10, 4),

    -- Orders
    sl_price NUMERIC(20, 8),
    tp_price NUMERIC(20, 8),
    entry_order_id BIGINT,
    sl_order_id BIGINT,
    tp_order_id BIGINT,

    -- Timestamps
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Flags
    is_hedged BOOLEAN DEFAULT FALSE,
    is_synced_from_exchange BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- TABLE: daily_metrics (Agregações pré-calculadas por dia)
-- ============================================================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE NOT NULL,
    symbol TEXT REFERENCES symbols(symbol),

    -- Trade metrics
    trade_count INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,

    -- PnL metrics
    total_pnl NUMERIC(20, 8) DEFAULT 0,
    avg_pnl NUMERIC(20, 8),
    max_win NUMERIC(20, 8),
    max_loss NUMERIC(20, 8),

    -- Risk metrics
    max_drawdown NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    profit_factor NUMERIC(10, 2),

    -- Volume metrics
    total_volume NUMERIC(30, 8) DEFAULT 0,
    avg_trade_volume NUMERIC(20, 8),

    PRIMARY KEY (date, symbol)
);

-- ============================================================================
-- VIEWS: Para compatibilidade com dashboard existente
-- ============================================================================

CREATE OR REPLACE VIEW v_active_trades AS
SELECT
    symbol,
    side,
    entry_price,
    current_price,
    sl_price AS sl,
    tp_price AS tp,
    quantity,
    unrealized_pnl AS current_pnl,
    ROUND(unrealized_percent, 2) AS current_pnl_percent,
    TO_CHAR(opened_at, 'HH24:MI:SS') AS entry_time
FROM positions
WHERE symbol IN (SELECT DISTINCT symbol FROM trades WHERE status = 'OPEN')
ORDER BY opened_at;

CREATE OR REPLACE VIEW v_trade_history AS
SELECT
    TO_CHAR(entry_time, 'YYYY-MM-DD HH24:MI:SS') AS time,
    symbol,
    side,
    ROUND(entry_price::NUMERIC, 4) AS entry,
    ROUND(exit_price::NUMERIC, 4) AS exit,
    ROUND(pnl::NUMERIC, 2) AS pnl
FROM trades
WHERE status = 'CLOSED'
ORDER BY entry_time DESC
LIMIT 500;

CREATE OR REPLACE VIEW v_daily_metrics AS
SELECT
    date::TEXT AS date,
    ROUND(total_pnl::NUMERIC, 2) AS pnl,
    trade_count AS trades
FROM daily_metrics
ORDER BY date DESC
LIMIT 30;

-- ============================================================================
-- FUNCTIONS: Para automação
-- ============================================================================

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger às tabelas
CREATE TRIGGER update_symbols_updated_at BEFORE UPDATE ON symbols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Função para atualizar métricas diárias automaticamente
CREATE OR REPLACE FUNCTION update_daily_metrics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_metrics (date, symbol, trade_count, total_pnl, avg_pnl)
    VALUES (
        NEW.exit_time::DATE,
        NEW.symbol,
        1,
        NEW.pnl,
        NEW.pnl
    )
    ON CONFLICT (date, symbol) DO UPDATE SET
        trade_count = daily_metrics.trade_count + 1,
        total_pnl = daily_metrics.total_pnl + NEW.pnl,
        avg_pnl = (daily_metrics.total_pnl + NEW.pnl) / GREATEST(daily_metrics.trade_count + 1, 1);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_metrics
AFTER INSERT OR UPDATE ON trades
FOR EACH ROW
WHEN (NEW.status = 'CLOSED' AND (OLD IS NULL OR OLD.status != 'CLOSED'))
EXECUTE FUNCTION update_daily_metrics();

-- ============================================================================
-- DADOS INICIAIS: Symbols populares
-- ============================================================================
INSERT INTO symbols (symbol, name, base_asset, quote_asset, tick_size, lot_size, min_notional, max_leverage)
VALUES
    ('BTCUSDT', 'Bitcoin', 'BTC', 'USDT', 0.01, 0.00001, 5, 125),
    ('ETHUSDT', 'Ethereum', 'ETH', 'USDT', 0.01, 0.00001, 5, 125),
    ('BNBUSDT', 'Binance Coin', 'BNB', 'USDT', 0.01, 0.001, 5, 125),
    ('SOLUSDT', 'Solana', 'SOL', 'USDT', 0.001, 0.01, 5, 125),
    ('XRPUSDT', 'Ripple', 'XRP', 'USDT', 0.0001, 0.01, 5, 125),
    ('ADAUSDT', 'Cardano', 'ADA', 'USDT', 0.0001, 0.01, 5, 125),
    ('DOGEUSDT', 'Dogecoin', 'DOGE', 'USDT', 0.00001, 0.01, 5, 125),
    ('AVAXUSDT', 'Avalanche', 'AVAX', 'USDT', 0.001, 0.01, 5, 125),
    ('MATICUSDT', 'Polygon', 'MATIC', 'USDT', 0.0001, 0.01, 5, 125),
    ('DOTUSDT', 'Polkadot', 'DOT', 'USDT', 0.001, 0.01, 5, 125),
    ('LINKUSDT', 'Chainlink', 'LINK', 'USDT', 0.001, 0.01, 5, 125),
    ('ATOMUSDT', 'Cosmos', 'ATOM', 'USDT', 0.001, 0.01, 5, 125),
    ('LTCUSDT', 'Litecoin', 'LTC', 'USDT', 0.01, 0.01, 5, 125),
    ('NEARUSDT', 'NEAR Protocol', 'NEAR', 'USDT', 0.001, 0.01, 5, 125),
    ('APTUSDT', 'Aptos', 'APT', 'USDT', 0.001, 0.01, 5, 125),
    ('ARBUSDT', 'Arbitrum', 'ARB', 'USDT', 0.0001, 0.01, 5, 125),
    ('OPUSDT', 'Optimism', 'OP', 'USDT', 0.0001, 0.01, 5, 125),
    ('INJUSDT', 'Injective', 'INJ', 'USDT', 0.001, 0.01, 5, 125),
    ('SUIUSDT', 'Sui', 'SUI', 'USDT', 0.0001, 0.01, 5, 125),
    ('PEPEUSDT', 'Pepe', 'PEPE', 'USDT', 0.0000001, 1, 5, 125)
ON CONFLICT (symbol) DO NOTHING;
