import streamlit as st
import pandas as pd
import asyncio
import asyncpg
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Binance Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size:1.8rem !important;
        }
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius:10px;
        border:1px solid #333;
        margin-bottom:10px;
        }
    .stDataFrame {
        border:1px solid #333;
        }
    .main-title {
        color: #00ff00;
        font-size:1.5rem !important;
        font-weight: bold;
        text-align: center;
        }
    @media (min-width:768px) {
        .main-title {
            font-size:2.5rem !important;
            text-align: left;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL',
    'postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance'
)

async def load_data_from_db():
    """Load data from PostgreSQL."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Active positions
        positions = await conn.fetch("""
            SELECT
                symbol,
                side,
                entry_price,
                current_price,
                sl_price,
                tp_price,
                unrealized_pnl,
                unrealized_percent
            FROM positions
        """)

        active_trades = {}
        for p in positions:
            active_trades[p['symbol']] = {
                'side': p['side'],
                'entry': float(p['entry_price']),
                'current_price': float(p.get('current_price', p['entry_price'])),
                'sl': float(p['sl_price']),
                'tp': float(p['tp_price']),
                'current_pnl': float(p.get('unrealized_pnl', 0)),
                'current_pnl_percent': float(p.get('unrealized_percent', 0))
            }

        # Trade history
        history_rows = await conn.fetch("""
            SELECT
                symbol,
                side,
                entry_price,
                exit_price,
                pnl,
                entry_time,
                exit_time
            FROM trades
            WHERE status = 'CLOSED'
            ORDER BY entry_time DESC
            LIMIT 100
        """)

        history = []
        for h in history_rows:
            history.append({
                'time': h['entry_time'].strftime('%H:%M:%S'),
                'symbol': h['symbol'],
                'side': h['side'],
                'entry': float(h['entry_price']),
                'exit': float(h.get('exit_price', 0)),
                'pnl': float(h.get('pnl', 0))
            })

        # Daily metrics
        metrics_rows = await conn.fetch("""
            SELECT
                date,
                total_trades,
                winning_trades,
                losing_trades,
                total_pnl as pnl
            FROM daily_metrics
            ORDER BY date DESC
            LIMIT 30
        """)

        metrics = []
        for m in metrics_rows:
            metrics.append({
                'date': m['date'].isoformat(),
                'trades': m['total_trades'],
                'wins': m['winning_trades'],
                'losses': m['losing_trades'],
                'pnl': float(m.get('pnl', 0))
            })

        await conn.close()

        return {
            'active_trades': active_trades,
            'history': history,
            'daily_metrics': metrics,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'leverage': 50,
                'max_positions': 5,
                'risk': 0.12
            },
            'symbols': list(active_trades.keys())
        }

    except Exception as e:
        st.error(f"Erro ao carregar do banco: {e}")
        return None

def load_data():
    """Load data from PostgreSQL."""
    return asyncio.run(load_data_from_db())

# Sidebar
st.sidebar.title("🤖 Status do Bot")
data = load_data()

if data:
    st.sidebar.success("🟢 ONLINE")
    st.sidebar.markdown(f"**Última Atualização:**\n{data.get('last_update', 'N/A')}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configurações")
    config = data.get('config', {})
    st.sidebar.write(f"**Alavancagem:** {config.get('leverage')}x")
    st.sidebar.write(f"**Max Posições:** {config.get('max_positions')}")
    st.sidebar.write(f"**Risco p/ Trade:** {config.get('risk', 0)*100}%")
    st.sidebar.write(f"**Símbolos:** {len(data.get('symbols', []))} ativos")
else:
    st.sidebar.error("🔴 OFFLINE / AGUARDANDO")

# Title
st.markdown('<p class="main-title">🤖 Binance Trading Intelligence</p>', unsafe_allow_html=True)

if not data:
    st.warning("⏳ Aguardando dados iniciais do bot...")
    import time
    time.sleep(5)
    st.rerun()

# Tabs
tabs = st.tabs(["📊 Monitoramento", "📜 Histórico de Trades", "📈 Analytics"])

with tabs[0]:
    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    active_trades = data.get('active_trades', {})
    history = data.get('history', [])
    metrics = data.get('daily_metrics', [])

    total_realized_pnl = sum([t.get('pnl', 0) for t in history])
    unrealized_pnl = sum([t.get('current_pnl', 0) for t in active_trades.values()])

    col1.metric("Posições Abertas", f"{len(active_trades)}/{config.get('max_positions')}")
    col2.metric("PnL Não Realizado", f"${unrealized_pnl:.2f}")
    col3.metric("Lucro Total Acumulado", f"${total_realized_pnl:.2f}")
    col4.metric("Total de Trades", len(history))

    # Active positions table
    st.subheader("⚡ Posições em Execução")
    if active_trades:
        df_data = []
        for symbol, info in active_trades.items():
            pnl = info.get('current_pnl', 0)
            df_data.append({
                "Ativo": symbol,
                "Lado": info.get('side'),
                "Entrada": f"${info.get('entry', 0):.4f}",
                "Preço Atual": f"${info.get('current_price', 0):.4f}",
                "PnL ($)": round(pnl, 2),
                "PnL (%)": f"{info.get('current_pnl_percent', 0):.2f}%",
                "SL": f"${info.get('sl', 0):.4f}",
                "TP": f"${info.get('tp', 0):.4f}"
            })
        df = pd.DataFrame(df_data)

        def color_pnl(val):
            try:
                val_float = float(val)
                color = '#00ff00' if val_float > 0 else '#ff4b4b'
                return f'color: {color}'
            except: return ''

        st.dataframe(df.style.applymap(color_pnl, subset=['PnL ($)']), use_container_width=True, hide_index=True)
    else:
        st.info("Buscando novas oportunidades no mercado...")

with tabs[1]:
    st.subheader("📜 Histórico de Ordens Encerradas")
    if history:
        df_hist = pd.DataFrame(history)
        df_hist = df_hist[['time', 'symbol', 'side', 'entry', 'exit', 'pnl']]
        df_hist.columns = ['Horário', 'Ativo', 'Lado', 'Entrada', 'Saída', 'Resultado ($)']

        def color_pnl(val):
            try:
                val_float = float(val)
                color = '#00ff00' if val_float > 0 else '#ff4b4b'
                return f'color: {color}'
            except: return ''

        st.dataframe(
            df_hist.sort_values(by='Horário', ascending=False).style.applymap(color_pnl, subset=['Resultado ($)']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("Ainda não há trades encerrados neste ciclo.")

with tabs[2]:
    st.subheader("📈 Performance Dia a Dia")
    if metrics:
        df_metrics = pd.DataFrame(metrics)
        df_metrics['Lucro Acumulado'] = df_metrics['pnl'].cumsum()

        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("**Tabela Diária**")
            st.dataframe(df_metrics[['date', 'pnl', 'trades']].iloc[::-1], hide_index=True)

        with c2:
            st.write("**Curva de Capital**")
            st.line_chart(df_metrics.set_index('date')['Lucro Acumulado'])
    else:
        st.write("Dados insuficientes para gerar gráficos.")

# Footer
st.markdown("---")
st.caption(f"Bot Heartbeat: {data.get('last_update')} | Auto-refresh: 10s")
import time
time.sleep(10)
st.rerun()
