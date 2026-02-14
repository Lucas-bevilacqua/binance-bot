# 🔌 COMO ACESSAR O POSTGRESQL NO RENDER

## Opção 1: Psql no Browser (Mais Fácil)

### Passo a Passo:

1. **Acessar dashboard do Render:**
   - Vá para: https://dashboard.render.com
   - Logue na sua conta

2. **Encontrar o banco de dados:**
   - No menu lateral, clique em "Databases"
   - Procure por: `bot_binance`
   - Clique no banco

3. **Conectar via psql (navegador):**
   - No seu banco, procure o botão "Connect" ou "External Connection"
   - Render mostra um comando tipo:
   ```bash
   psql "postgresql://postgres:senha@host:porta/bot_binance"
   ```
   - Use essa URL para conectar

4. **Queries úteis:**

```sql
-- Ver todas as tabelas
\dt

-- Ver trades abertos
SELECT * FROM trades WHERE status = 'OPEN';

-- Ver histórico de trades (últimos 10)
SELECT symbol, side, entry_price, exit_price, pnl, exit_reason
FROM trades
WHERE status = 'CLOSED'
ORDER BY entry_time DESC
LIMIT 10;

-- Ver posições ativas
SELECT * FROM positions;

-- Ver métricas diárias
SELECT * FROM daily_metrics
ORDER BY date DESC
LIMIT 7;

-- PnL total por dia
SELECT
    date,
    COUNT(*) as total_trades,
    SUM(pnl) as total_pnl
FROM daily_metrics
GROUP BY date
ORDER BY date DESC;

-- Ver últimos trades de um símbolo específico
SELECT * FROM trades
WHERE symbol = 'BTCUSDT'
ORDER BY entry_time DESC
LIMIT 5;

-- Estatísticas gerais
SELECT
    COUNT(*) as total_trades,
    COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
    COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
    AVG(pnl) as avg_pnl,
    SUM(pnl) as total_pnl
FROM trades
WHERE status = 'CLOSED';
```

---

## Opção 2: Terminal Local (psql)

### Instalar psql (se não tiver):
- **Windows:** Baixe PostgreSQL installer: https://www.postgresql.org/download/windows/
- **Mac:** `brew install postgresql`
- **Linux:** `sudo apt install postgresql-client`

### Conectar:
```bash
psql "postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"
```

### Comandos úteis:
```sql
-- Listar tabelas
\dt

-- Descrever estrutura de uma tabela
\d trades

-- Sair
\q

-- Formatar output bonito
\x on

-- Ver trades
SELECT * FROM trades;

-- Salvar query em arquivo
\o trades.csv
SELECT * FROM trades;
\o
```

---

## Opção 3: pgAdmin (Interface Gráfica)

1. **Baixar pgAdmin:** https://www.pgadmin.org/download/
2. **Adicionar servidor:**
   - Host: `dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com`
   - Port: `5432`
   - Database: `bot_binance`
   - Username: `bot_binance_user`
   - Password: `2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq`

---

## Opção 4: DBeaver (Gratuito, Multi-banco)

1. **Baixar DBeaver:** https://dbeaver.io/download/
2. **Nova conexão → PostgreSQL**
3. **Preencher:**
   - Host: `dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com`
   - Port: `5432`
   - Database: `bot_binance`
   - Username: `bot_binance_user`
   - Password: `2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq`

---

## Estrutura do Banco

### Tabelas disponíveis:

**trades** - Histórico completo de trades
- trade_id (PK)
- symbol
- side (LONG/SHORT)
- entry_price
- exit_price
- sl_price
- tp_price
- entry_time
- exit_time
- pnl
- pnl_percent
- status (OPEN/CLOSED)
- exit_reason (TP/SL/MANUAL)

**positions** - Posições atualmente abertas
- symbol (PK)
- side
- quantity
- entry_price
- current_price
- sl_price
- tp_price
- unrealized_pnl
- unrealized_percent

**daily_metrics** - Métricas diárias
- date (PK)
- total_trades
- winning_trades
- losing_trades
- total_pnl
- max_drawdown
- sharpe_ratio

**symbols** - Símbolos configurados
- symbol (PK)
- is_active
- last_scan_time
- last_signal_score

**ohlcv** - Dados de candlestick (histórico)
- id (PK)
- symbol
- timestamp
- open, high, low, close
- volume

**trade_executions** - Execuções de ordens
- id (PK)
- symbol
- order_id
- execution_type (ENTRY/SL/TP)
- price
- quantity
- execution_time

---

## Views Úteis

### v_active_trades - Posições abertas
```sql
SELECT * FROM v_active_trades;
```

### v_trade_history - Histórico formatado
```sql
SELECT * FROM v_trade_history;
```

### v_daily_metrics - Métricas diárias
```sql
SELECT * FROM v_daily_metrics;
```

---

## Queries de Análise

### Performance por símbolo:
```sql
SELECT
    symbol,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
    COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
    ROUND(100.0 * COUNT(CASE WHEN pnl > 0 THEN 1 END) / COUNT(*), 2) as win_rate
FROM trades
WHERE status = 'CLOSED'
GROUP BY symbol
ORDER BY total_pnl DESC;
```

### PnL por dia da semana:
```sql
SELECT
    TO_CHAR(entry_time, 'Day') as day_of_week,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl
FROM trades
WHERE status = 'CLOSED'
GROUP BY day_of_week
ORDER BY total_pnl DESC;
```

### Trades com maior profit:
```sql
SELECT
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    pnl_percent,
    entry_time
FROM trades
WHERE status = 'CLOSED' AND pnl > 0
ORDER BY pnl DESC
LIMIT 10;
```

### Trades com maior loss:
```sql
SELECT
    symbol,
    side,
    entry_price,
    exit_price,
    pnl,
    pnl_percent,
    entry_time
FROM trades
WHERE status = 'CLOSED' AND pnl < 0
ORDER BY pnl ASC
LIMIT 10;
```

---

## Alertas e Monitoramento

### Configurar alerta de grandes perdas (exemplo):
```sql
-- Criar função de alerta
CREATE OR REPLACE FUNCTION check_large_loss()
RETURNS TABLE(symbol TEXT, pnl NUMERIC)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT symbol, pnl
    FROM trades
    WHERE status = 'CLOSED'
      AND pnl < -50  -- Loss maior que $50
      AND exit_time > NOW() - INTERVAL '1 hour';
END;
$$;

-- Usar:
SELECT * FROM check_large_loss();
```

---

## Backup e Export

### Exportar trades para CSV:
```sql
COPY (
    SELECT * FROM trades WHERE status = 'CLOSED'
) TO '/tmp/trades.csv' WITH CSV HEADER;
```

### Exportar tudo para JSON (via psql):
```bash
psql "..." -t -A -F"," -c "SELECT * FROM trades" > trades.csv
```

---

## 🔒 SEGURANÇA

**IMPORTANTE:** Nunca comite credenciais reais!
- Use environment variables
- Render já tem as credenciais configuradas
- Para acesso local, use o External Connection string do dashboard Render

---

*Última atualização: 2026-02-14*
