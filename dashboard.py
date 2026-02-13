
import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime

# Configuração da página (Sidebar recolhida no mobile por padrão)
st.set_page_config(
    page_title="Binance Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS personalizado (Melhorias Mobile)
st.markdown("""
    <style>
    /* Estilo das métricas para mobile */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    /* Estilo para tabelas no mobile */
    .stDataFrame {
        border: 1px solid #333;
    }
    .main-title {
        color: #00ff00;
        font-size: 1.5rem !important; /* Menor no mobile */
        font-weight: bold;
        text-align: center;
    }
    @media (min-width: 768px) {
        .main-title {
            font-size: 2.5rem !important;
            text-align: left;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Arquivo de dados
DATA_FILE = "dashboard_data.json"

def load_data():
    """Carrega dados do arquivo JSON gerado pelo bot."""
    if not os.path.exists(DATA_FILE):
        return None
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

# Sidebar - Configurações e Status
st.sidebar.title("🤖 Status do Bot")
data = load_data()

if data:
    status_color = "🟢 ONLINE"
    st.sidebar.success(status_color)
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

# Título Principal
st.markdown('<p class="main-title">🤖 Binance Trading Intelligence</p>', unsafe_allow_html=True)

if not data:
    st.warning("⏳ Aguardando dados iniciais do bot... (Isso pode levar alguns segundos)")
    time.sleep(5)
    st.rerun()

# --- ABA DE RESUMO ---
tabs = st.tabs(["📊 Monitoramento", "📜 Histórico de Trades", "📈 Analytics"])

with tabs[0]:
    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    
    active_trades = data.get('active_trades', {})
    history = data.get('history', [])
    metrics = data.get('daily_metrics', [])
    
    total_realized_pnl = sum([t.get('pnl', 0) for t in history])
    unrealized_pnl = sum([t.get('current_pnl', 0) for t in active_trades.values()])
    
    col1.metric("Posições Abertas", f"{len(active_trades)}/{config.get('max_positions')}")
    col2.metric("PnL Não Realizado", f"${unrealized_pnl:.2f}", delta=f"{unrealized_pnl:.2f}", delta_color="normal")
    col3.metric("Lucro Total Acumulado", f"${total_realized_pnl:.2f}", delta=f"{total_realized_pnl:.2f}")
    col4.metric("Total de Trades", len(history))

    # Tabela de Posições Ativas
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
                "PnL (%)": f"{info.get('current_pnl_percent', 0):.2f}%" if 'current_pnl_percent' in info else "N/A",
                "SL": f"${info.get('sl', 0):.4f}",
                "TP": f"${info.get('tp', 0):.4f}"
            })
        df = pd.DataFrame(df_data)
        
        # Colorir PnL
        def color_pnl(val):
            try:
                val_float = float(val)
                color = '#00ff00' if val_float > 0 else '#ff4b4b'
                return f'color: {color}'
            except: return ''

        st.dataframe(df.style.applymap(color_pnl, subset=['PnL ($)']), use_container_width=True, hide_index=True)
    else:
        st.info("Buscando novas oportunidades no mercado...")
    # --- SEÇÃO DE INTELIGÊNCIA ARTIFICIAL ---
    st.markdown("---")
    st.subheader("🧠 Inteligência Artificial (Filtro Adaptativo)")
    
    ai_analysis = data.get('ai_analysis', {})
    if ai_analysis:
        # Mostrar os últimos 3 insights da IA
        cols = st.columns(3)
        for i, (symbol, analysis) in enumerate(list(ai_analysis.items())[-3:]):
            with cols[i % 3]:
                decision = analysis.get('decision', 'N/A')
                color = "#00ff00" if decision == "GO" else "#ff4b4b"
                
                st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 15px; border-radius: 10px; border-left: 5px solid {color}; border: 1px solid #333;">
                    <h4 style="margin:0; color: {color};">{symbol}: {decision}</h4>
                    <p style="margin: 5px 0; font-size: 0.9rem;"><b>Sentimento:</b> {analysis.get('sentiment', 0)}%</p>
                    <p style="margin: 0; font-style: italic; font-size: 0.85rem;">"{analysis.get('reason', '')}"</p>
                    <p style="margin-top: 5px; font-size: 0.7rem; color: #888;">{analysis.get('time', '')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("A IA está analisando o mercado. O primeiro insight aparecerá quando um sinal técnico for detectado.")

with tabs[1]:
    st.subheader("📜 Histórico de Ordens Encerradas")
    if history:
        df_hist = pd.DataFrame(history)
        df_hist = df_hist[['time', 'symbol', 'side', 'entry', 'exit', 'pnl']]
        df_hist.columns = ['Horário', 'Ativo', 'Lado', 'Entrada', 'Saída', 'Resultado ($)']
        
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

# Footer e Refresh Automático
st.markdown("---")
st.caption(f"Bot Heartbeat: {data.get('last_update')} | Auto-refresh: 10s")
time.sleep(10)
st.rerun()
