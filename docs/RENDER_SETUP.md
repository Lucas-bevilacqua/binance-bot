# Binance Bot - Render Setup Guide

Complete guide to deploy the Binance Bot on Render with PostgreSQL database.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Deploying to Render](#deploying-to-render)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- [ ] Git repository with your bot code
- [ ] Render account (free tier works)
- [ ] Binance API credentials (Futures trading enabled)
- [ ] (Optional) OpenAI API key for AI filtering

---

## Quick Start

### 1. Test Database Connection Locally

```bash
# Set the DATABASE_URL environment variable
export DATABASE_URL="postgresql://bot_binance_user:2yT3u1JBiSintBfwmNlkJlSMmNJnJq@dpg-686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance"

# Run the test script
python scripts/test_db_connection.py

# Run the setup script (creates tables)
python scripts/setup_postgresql.py
```

### 2. Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Configure Render environment"
git push origin main
```

### 3. Deploy on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" -> "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml` and create services

---

## Configuration

### Environment Variables

The following variables are configured in `render.yaml`:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | *(pre-configured)* | PostgreSQL connection string |
| `PYTHON_VERSION` | 3.11.0 | Python runtime version |
| `SCAN_INTERVAL` | 60 | Market scan interval (seconds) |
| `MONITOR_INTERVAL` | 15 | Position monitoring interval (seconds) |
| `MAX_POSITIONS` | 3 | Maximum concurrent positions |
| `MIN_SIGNAL_STRENGTH` | 28 | Minimum signal strength to enter trade |
| `ALAVANCAGEM_PADRAO` | 50 | Default leverage (1-125) |
| `RISCO_MAXIMO_POR_OPERACAO` | 0.12 | Risk per trade (12%) |
| `STOP_LOSS_PERCENTUAL` | 0.015 | Stop loss (1.5%) |
| `TAKE_PROFIT_PERCENTUAL` | 0.025 | Take profit (2.5%) |

### Sensitive Variables (Configure via Dashboard)

**Do NOT commit these to git!** Configure in Render Dashboard:

1. Go to your service in Render Dashboard
2. Click "Environment" tab
3. Add the following:

| Variable | Required | Description |
|----------|----------|-------------|
| `BINANCE_API_KEY` | Yes | Your Binance API key |
| `BINANCE_API_SECRET` | Yes | Your Binance API secret |
| `OPENAI_API_KEY` | No | OpenAI key for AI signal filtering |
| `TELEGRAM_BOT_TOKEN` | No | For Telegram notifications |
| `TELEGRAM_CHAT_ID` | No | Your Telegram chat ID |

---

## Database Setup

The PostgreSQL database is automatically configured on first deploy via `scripts/init_render_env.py`.

### Schema

The database includes these tables:

- **symbols** - Trading pairs metadata
- **trades** - Trade history
- **positions** - Active positions
- **daily_metrics** - Daily performance stats

### Manual Schema Application

If you need to manually apply the schema:

```bash
# Via psql
psql $DATABASE_URL < database/schema.sql

# Or via Python script
python scripts/setup_postgresql.py
```

---

## Deploying to Render

### Using Blueprint (Recommended)

1. Push your code to GitHub/GitLab
2. In Render Dashboard: "New +" -> "Blueprint"
3. Select your repository
4. Render reads `render.yaml` and creates services automatically

### Manual Deployment

If not using Blueprint, create services manually:

#### Worker Service

- Type: Worker
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `python scripts/init_render_env.py && python bot_master.py`

#### Dashboard Service

- Type: Web Service
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`

---

## Monitoring

### Logs

Access logs in Render Dashboard:

1. Go to your service
2. Click "Logs" tab
3. Look for:
   - `Conexão com PostgreSQL OK!` - Database connected
   - `✅ Schema aplicado com sucesso!` - Tables created
   - `🤖 BOT AUTÔNOMO INTELIGENTE` - Bot started

### Dashboard

After deployment, access your dashboard at:
`https://binance-dashboard.onrender.com`

### Health Checks

- **Worker**: Runs 24/7, check logs for heartbeat
- **Dashboard**: Health check at `/_stcore/health`

---

## Troubleshooting

### Database Connection Issues

```
Error: DATABASE_URL não configurada
```

**Solution**: Ensure `DATABASE_URL` is set in `render.yaml`

### Import Errors

```
Error: No module named 'asyncpg'
```

**Solution**: Check `requirements.txt` includes:
```
asyncpg>=0.29.0
python-dotenv>=1.0.0
```

### Bot Not Starting

Check logs for these messages:

| Error | Solution |
|-------|----------|
| `BINANCE_API_KEY` not configured | Add via Render Dashboard |
| `table "symbols" does not exist` | Run `scripts/setup_postgresql.py` locally first |
| `Connection timeout` | Check Render database status |

### Schema Not Applied

If tables aren't created automatically:

```bash
# Run setup locally
DATABASE_URL="your_url" python scripts/setup_postgresql.py

# Or check logs for schema application errors
```

---

## File Structure

```
binance-bot-main/
├── .render/                    # Render environment files
│   ├── bot-worker.env          # Worker variables
│   └── dashboard.env           # Dashboard variables
├── database/
│   ├── schema.sql              # Database schema
│   ├── db_integration.py       # Database integration
│   └── repositories.py         # Repository layer
├── scripts/
│   ├── init_render_env.py      # Auto-setup on deploy
│   ├── setup_postgresql.py     # Manual database setup
│   └── test_db_connection.py  # Connection tester
├── bot_master.py              # Main bot logic
├── dashboard.py               # Streamlit dashboard
├── render.yaml                # Render Blueprint
└── .env.example              # Environment template
```

---

## Security Notes

1. **DATABASE_URL** - Can be committed (contains only database credentials)
2. **API Keys** - NEVER commit these to git
3. **Secrets** - Always use Render Dashboard for sensitive data

---

## Support

For issues:
1. Check Render logs first
2. Run `python scripts/test_db_connection.py` locally
3. Verify all environment variables are set
4. Check Binance API permissions (Futures trading required)

---

**Deploy URL**: https://binance-bot-worker.onrender.com
**Dashboard URL**: https://binance-dashboard.onrender.com
