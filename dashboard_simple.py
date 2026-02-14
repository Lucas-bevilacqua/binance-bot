"""
Binance Trading Dashboard - SIMPLE VERSION
Guaranteed to work with PostgreSQL data
"""
import streamlit as st
import pandas as pd
import asyncio
import asyncpg
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #00d4aa !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }
    .stDataFrame {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL',
    'postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance')

async def load_data():
    """Load data from PostgreSQL."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Trade history
        history_rows = await conn.fetch("""
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
                'pnl': float(h.get('pnl', 0)),
                'pnl_percent': float(h.get('pnl_percent', 0)),
                'exit_reason': h.get('exit_reason', 'N/A')
            })

        # Overall stats
        overall = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl
            FROM trades
            WHERE status = 'CLOSED'
        """)

        await conn.close()

        return {
            'history': history,
            'overall': {
                'total_trades': overall['total_trades'],
                'winning_trades': overall['winning_trades'],
                'losing_trades': overall['losing_trades'],
                'total_pnl': float(overall.get('total_pnl', 0)),
                'avg_pnl': float(overall.get('avg_pnl', 0)),
                'win_rate': 100.0 * overall['winning_trades'] / overall['total_trades'] if overall['total_trades'] > 0 else 0
            },
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def load_data_sync():
    """Synchronous wrapper."""
    return asyncio.run(load_data())

# Sidebar
data = load_data_sync()

st.sidebar.title("Trading Bot Status")

if data:
    st.sidebar.success("ONLINE")
    st.sidebar.caption(f"Last update: {data.get('last_update', 'N/A')}")

    overall = data.get('overall', {})
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Performance**")
    st.sidebar.metric("Win Rate", f"{overall.get('win_rate', 0):.1f}%")
    st.sidebar.metric("Avg Trade", f"${overall.get('avg_pnl', 0):.2f}")
else:
    st.sidebar.error("OFFLINE")

# Title
st.markdown("# Trading Analytics Dashboard")

if not data:
    st.warning("Loading data...")
    import time
    time.sleep(3)
    st.rerun()

# Key Metrics
overall = data.get('overall', {})
history = data.get('history', [])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Trades", str(overall.get('total_trades', 0)))

with col2:
    st.metric("Winning Trades", str(overall.get('winning_trades', 0)))

with col3:
    st.metric("Losing Trades", str(overall.get('losing_trades', 0)))

with col4:
    total_pnl = overall.get('total_pnl', 0)
    delta_color = "normal" if total_pnl >= 0 else "inverse"
    st.metric("Total PnL", f"${total_pnl:.2f}", delta=f"{total_pnl:+.2f}", delta_color=delta_color)

st.markdown("---")

# Trade History
st.markdown("## Trade History")

if history:
    df_hist = pd.DataFrame(history)
    df_hist = df_hist[['time', 'symbol', 'side', 'entry', 'exit', 'pnl', 'pnl_percent', 'exit_reason']]
    df_hist.columns = ['Time', 'Symbol', 'Side', 'Entry', 'Exit', 'PnL ($)', 'PnL (%)', 'Exit Reason']

    def highlight_pnl(val):
        if isinstance(val, (int, float)):
            color = '#00d4aa' if val >= 0 else '#ff4b4b'
            return f'color: {color}; font-weight: 600;'
        return ''

    styled_hist = df_hist.style.applymap(highlight_pnl, subset=['PnL ($)', 'PnL (%)'])
    st.dataframe(
        styled_hist,
        use_container_width=True,
        hide_index=True,
        height=600
    )
else:
    st.info("No trade history available.")

# Footer
st.markdown("---")
st.caption(f"Last Updated: {data.get('last_update')} | Auto-refresh: 10s")
import time
time.sleep(10)
st.rerun()
