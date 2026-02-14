"""
Binance Trading Bot - Professional Dashboard
===========================================
Premium trading analytics dashboard
"""

import streamlit as st
import pandas as pd
import asyncio
import asyncpg
from datetime import datetime, timedelta
import os
import plotly.graph_objects as go
import plotly.express as px

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Trading Analytics Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# PREMIUM STYLING
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Premium cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
    }

    /* Metric values */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
    }

    /* Professional tables */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Headers */
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        margin-bottom: 0 !important;
    }

    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.3px;
    }

    h3 {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #8892b0 !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0f0f1a;
    }

    ::-webkit-scrollbar-thumb {
        background: #2a2a40;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #3a3a55;
    }

    /* Status indicators */
    .status-online {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00d4aa;
        box-shadow: 0 0 10px rgba(0, 212, 170, 0.5);
        margin-right: 8px;
        animation: pulse 2s ease-in-out infinite;
    }

    .status-offline {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ff4b4b;
        margin-right: 8px;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Professional sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Tab styling */
    .stTabs [data-baseweb="base16-shell"] {
        gap: 1rem;
    }

    [data-testid="stTab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #8892b0;
        transition: all 0.2s ease;
    }

    [data-testid="stTab"][aria-selected="true"] {
        color: #ffffff;
        border-bottom-color: #00d4aa;
    }

    [data-testid="stTab"]:hover {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

DATABASE_URL = os.getenv('DATABASE_URL',
    'postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance'
)

async def load_data_from_db():
    """Load trading data from PostgreSQL."""
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
                'unrealized_pnl': float(p.get('unrealized_pnl', 0)),
                'unrealized_percent': float(p.get('unrealized_percent', 0))
            }

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
                'date': h['entry_time'].strftime('%Y-%m-%d'),
                'symbol': h['symbol'],
                'side': h['side'],
                'entry': float(h['entry_price']),
                'exit': float(h.get('exit_price', 0)),
                'pnl': float(h.get('pnl', 0)),
                'pnl_percent': float(h.get('pnl_percent', 0)),
                'exit_reason': h.get('exit_reason', 'N/A')
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
                'date': m['date'],
                'trades': m['total_trades'],
                'wins': m['winning_trades'],
                'losses': m['losing_trades'],
                'pnl': float(m.get('pnl', 0))
            })

        # Overall stats
        overall = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trades
            WHERE status = 'CLOSED'
        """)

        await conn.close()

        return {
            'active_trades': active_trades,
            'history': history,
            'daily_metrics': metrics,
            'overall': {
                'total_trades': overall['total_trades'],
                'winning_trades': overall['winning_trades'],
                'losing_trades': overall['losing_trades'],
                'total_pnl': float(overall['total_pnl'] or 0),
                'avg_pnl': float(overall['avg_pnl'] or 0),
                'best_trade': float(overall['best_trade'] or 0),
                'worst_trade': float(overall['worst_trade'] or 0),
                'win_rate': 100.0 * overall['winning_trades'] / overall['total_trades'] if overall['total_trades'] > 0 else 0
            },
            'last_update': datetime.now(),
            'config': {
                'leverage': 50,
                'max_positions': 5,
                'risk': 0.12
            }
        }

    except Exception as e:
        return {'error': str(e)}

def load_data():
    """Load data wrapper."""
    return asyncio.run(load_data_from_db())

# =============================================================================
# FORMATTING FUNCTIONS
# =============================================================================

def format_pnl(value, prefix="$"):
    """Format PnL values."""
    if value is None:
        return "N/A"
    color = "#00d4aa" if value >= 0 else "#ff4b4b"
    return f'<span style="color: {color}; font-weight: 600;">{prefix}{value:,.2f}</span>'

def format_percent(value):
    """Format percentage values."""
    if value is None:
        return "N/A"
    color = "#00d4aa" if value >= 0 else "#ff4b4b"
    return f'<span style="color: {color}; font-weight: 500;">{value:+.2f}%</span>'

def format_price(value):
    """Format price values."""
    return f"${value:,.4f}" if value else "N/A"

# =============================================================================
# SIDEBAR
# =============================================================================

data = load_data()

with st.sidebar:
    st.markdown("""
        ### Trading Bot

        **System Status**
    """)

    if 'error' in data:
        st.markdown('<span class="status-offline"></span>Offline', unsafe_allow_html=True)
        st.error(f"Connection Error: {data['error']}")
    else:
        st.markdown('<span class="status-online"></span>Online', unsafe_allow_html=True)
        st.caption(f"Last update: {data.get('last_update', datetime.now()).strftime('%H:%M:%S')}")

        st.markdown("---")

        st.markdown("**Configuration**")

        config = data.get('config', {})
        st.metric("Leverage", f"{config.get('leverage')}x", help="Trading leverage")
        st.metric("Max Positions", str(config.get('max_positions')), help="Maximum concurrent positions")
        st.metric("Risk per Trade", f"{config.get('risk', 0)*100}%", help="Maximum risk per trade")

        st.markdown("---")

        # Quick stats
        overall = data.get('overall', {})
        st.markdown("**Performance**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Win Rate", f"{overall.get('win_rate', 0):.1f}%")
        with col2:
            st.metric("Avg Trade", format_pnl(overall.get('avg_pnl', 0), ""))

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

st.markdown("# Trading Analytics Dashboard")

if 'error' in data:
    st.error("Unable to connect to database. Please try again later.")
    st.stop()

# =============================================================================
# KEY METRICS
# =============================================================================

st.markdown("### Portfolio Overview")

overall = data.get('overall', {})
active_trades = data.get('active_trades', {})

# Calculate metrics
unrealized_pnl = sum([t.get('unrealized_pnl', 0) for t in active_trades.values()])
total_realized = overall.get('total_pnl', 0)
total_pnl = total_realized + unrealized_pnl

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    delta_color = "normal" if total_realized >= 0 else "inverse"
    st.metric(
        "Realized PnL",
        f"${total_realized:,.2f}",
        delta=f"{total_realized:+,.2f}",
        delta_color=delta_color
    )

with col2:
    delta_color = "normal" if unrealized_pnl >= 0 else "inverse"
    st.metric(
        "Unrealized PnL",
        f"${unrealized_pnl:,.2f}",
        delta=f"{unrealized_pnl:+,.2f}",
        delta_color=delta_color
    )

with col3:
    st.metric(
        "Total PnL",
        f"${total_pnl:,.2f}",
        delta=f"{total_pnl:+,.2f}",
        delta_color="normal" if total_pnl >= 0 else "inverse"
    )

with col4:
    st.metric(
        "Win Rate",
        f"{overall.get('win_rate', 0):.1f}%",
        delta=None
    )

with col5:
    st.metric(
        "Total Trades",
        str(overall.get('total_trades', 0)),
        delta=None
    )

st.markdown("---")

# =============================================================================
# TABS
# =============================================================================

tabs = st.tabs(["Active Positions", "Trade History", "Performance Analytics"])

# =============================================================================
# ACTIVE POSITIONS TAB
# =============================================================================

with tabs[0]:
    st.markdown("#### Open Positions")

    if active_trades:
        # Create DataFrame
        df_data = []
        for symbol, trade in active_trades.items():
            pnl = trade.get('unrealized_pnl', 0)
            pnl_pct = trade.get('unrealized_percent', 0)

            df_data.append({
                'Symbol': symbol,
                'Side': trade['side'],
                'Entry Price': format_price(trade['entry']),
                'Current Price': format_price(trade['current_price']),
                'PnL ($)': pnl,
                'PnL (%)': pnl_pct,
                'Stop Loss': format_price(trade['sl']),
                'Take Profit': format_price(trade['tp'])
            })

        df = pd.DataFrame(df_data)

        # Style the dataframe
        def highlight_pnl(val):
            if isinstance(val, (int, float)):
                color = '#00d4aa' if val >= 0 else '#ff4b4b'
                return f'color: {color}; font-weight: 600;'
            return ''

        styled_df = df.style.applymap(highlight_pnl, subset=['PnL ($)', 'PnL (%)'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    else:
        st.info("No active positions. Scanning for opportunities...")

# =============================================================================
# TRADE HISTORY TAB
# =============================================================================

with tabs[1]:
    st.markdown("#### Closed Trades")

    history = data.get('history', [])

    if history:
        df_hist = pd.DataFrame(history)
        df_hist = df_hist[['date', 'time', 'symbol', 'side', 'entry', 'exit', 'pnl', 'exit_reason']]
        df_hist.columns = ['Date', 'Time', 'Symbol', 'Side', 'Entry', 'Exit', 'PnL ($)', 'Exit Reason']

        def style_pnl_column(val):
            if isinstance(val, (int, float)):
                color = '#00d4aa' if val >= 0 else '#ff4b4b'
                return f'color: {color}; font-weight: 600;'
            return ''

        styled_hist = df_hist.style.applymap(style_pnl_column, subset=['PnL ($)'])
        st.dataframe(
            styled_hist,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.info("No closed trades available.")

# =============================================================================
# PERFORMANCE ANALYTICS TAB
# =============================================================================

with tabs[2]:
    metrics = data.get('daily_metrics', [])

    if metrics:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Daily Performance")

            # Prepare data
            df_metrics = pd.DataFrame(metrics)
            df_metrics = df_metrics.sort_values('date')
            df_metrics['cumulative_pnl'] = df_metrics['pnl'].cumsum()
            df_metrics['date_str'] = df_metrics['date'].dt.strftime('%b %d')

            # Create chart
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_metrics['date_str'],
                y=df_metrics['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative PnL',
                line=dict(color='#00d4aa', width=2),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(0, 212, 170, 0.1)'
            ))

            fig.update_layout(
                title="Cumulative Returns",
                xaxis_title="Date",
                yaxis_title="PnL ($)",
                hovermode='x unified',
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8892b0'),
                margin=dict(l=0, r=0, t=30, b=0),
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Statistics")

            # Calculate stats
            win_days = len([m for m in metrics if m['pnl'] > 0])
            loss_days = len([m for m in metrics if m['pnl'] < 0])

            st.metric(
                "Profitable Days",
                f"{win_days}/{len(metrics)}",
                delta=f"{100*win_days/len(metrics):.1f}%"
            )

            best_day = max(metrics, key=lambda x: x['pnl'])
            worst_day = min(metrics, key=lambda x: x['pnl'])

            st.metric("Best Day", f"${best_day['pnl']:+,.2f}")
            st.metric("Worst Day", f"${worst_day['pnl']:+,.2f}")

            st.markdown("---")

            st.markdown("**Recent Performance**")
            recent = df_metrics.tail(7).to_dict('records')
            for day in recent[::-1]:
                pnl_color = "#00d4aa" if day['pnl'] >= 0 else "#ff4b4b"
                st.markdown(
                    f"<div style='padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);'>"
                    f"<span style='color: #8892b0;'>{day['date'].strftime('%b %d')}</span> "
                    f"<span style='color: {pnl_color}; font-weight: 600; float: right;'>${day['pnl']:+,.2f}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("Insufficient data for analytics.")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.85rem;'>"
    f"Last Updated: {data.get('last_update', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Auto-refresh: 10s"
    f"</div>",
    unsafe_allow_html=True
)

# Auto-refresh
import time
time.sleep(10)
st.rerun()
