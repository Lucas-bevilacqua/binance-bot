"""
DASHBOARD DE DEBUG PARA VERIFICAR CONEXÃO
"""
import streamlit as st
import asyncio
import asyncpg
import os

st.set_page_config(
    page_title="Debug Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("# 🔍 DEBUG: Conexão com Banco de Dados")

# Mostrar variáveis de ambiente
st.markdown("## Variáveis de Ambiente")

env_vars = {
    'DATABASE_URL': os.getenv('DATABASE_URL', 'NÃO DEFINIDA'),
    'PORT': os.getenv('PORT', 'NÃO DEFINIDA'),
    'PYTHON_VERSION': os.getenv('PYTHON_VERSION', 'NÃO DEFINIDA'),
}

st.json(env_vars)

st.markdown("---")

# Verificar conexão
st.markdown("## Teste de Conexão")

async def test_connection():
    DATABASE_URL = os.getenv('DATABASE_URL',
        'postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance')

    st.write(f"**DATABASE_URL sendo usado:**")
    st.code(DATABASE_URL)

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        st.success("✅ Conexão bem-sucedida!")

        # Verificar tabelas
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        st.write(f"**Tabelas encontradas:** {len(tables)}")
        st.json([t['table_name'] for t in tables])

        # Verificar trades
        trades_count = await conn.fetchval("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
        st.write(f"**Trades CLOSED:** {trades_count}")

        if trades_count > 0:
            sample = await conn.fetchrow("""
                SELECT symbol, side, pnl, entry_time
                FROM trades
                WHERE status = 'CLOSED'
                ORDER BY entry_time DESC
                LIMIT 5
            """)
            st.write(f"**Último trade:** {sample['symbol']} {sample['side']} PnL: ${sample['pnl']}")
        else:
            st.warning("⚠️ Nenhum trade encontrado!")

        await conn.close()

    except Exception as e:
        st.error(f"❌ Erro na conexão: {e}")
        st.write(f"**Erro detalhado:**")
        st.code(str(e))

# Botão para testar
if st.button("🔍 Testar Conexão"):
    asyncio.run(test_connection())

st.markdown("---")
st.markdown("## Informações de Sistema")

st.write(f"**Working Directory:**")
    st.code(os.getcwd())

st.write(f"**Arquivos no diretório:**")
    try:
        files = os.listdir('.')
        st.json(files)
    except Exception as e:
        st.code(f"Erro: {e}")

st.markdown("---")
st.info("Se DATA_URL aparecer como 'NÃO DEFINIDA', é necessário configurar no Render!")
