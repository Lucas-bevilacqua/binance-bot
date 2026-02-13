#!/bin/bash
echo "🚀 Iniciando Bot + Dashboard..."

# 1. Iniciar Bot em segundo plano
python bot_master.py &

# 2. Iniciar Dashboard (Frontend)
echo "📊 Iniciando Streamlit na porta $PORT..."
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 &

# Esperar por qualquer um dos processos
wait -n
exit $?
