# COMO FORÇAR DEPLOY MANUAL NO RENDER

O render.yaml está configurado corretamente, mas às vezes o deploy automático não funciona.

## SOLUÇÃO: Deploy Manual

### Passo 1: Acessar o Dashboard Render

1. Vá para: https://dashboard.render.com
2. Faça login
3. Encontre seu serviço: "binance-dashboard" (web service)

### Passo 2: Fazer Deploy Manual

**Opção A: Manual Deploy (Recomendado)**

1. No serviço "binance-dashboard"
2. Clique em "Manual Deploy"
3. Selecione o branch: `main`
4. Clique "Deploy Now"
5. Acompanhe os logs em "Events"

**Opção B: Push + Deploy (Forçar atualização)**

1. No serviço "binance-dashboard"
2. Vá em "Settings"
3. Role até "Branch"
4. Confirme que está em `main`
5. Volte para "Events"
6. Clique "Manual Deploy" → branch `main`

### Passo 3: Acompanhar o Deploy

**O que procurar nos logs:**

```
✅ Building...
✅ Installing dependencies (incluindo plotly)
✅ Build successful
✅ Deploying...
✅ Service is live
```

**Se der erro, pode ser:**

- Erro de plotly: `pip install plotly` falhou
- Erro de dashboard: Arquivo não encontrado
- Erro de DATABASE_URL: Variável não configurada

### Passo 4: Verificar se funcionou

1. Acesse: https://binance-bot-026n.onrender.com
2. Deve aparecer o **novo dashboard profissional** (sem emojis)
3. Clique na aba "Trade History"
4. Deve aparecer **35 trades** no histórico

## Alternativa: Usar o GitHub Diretamente

Se o Render Blueprint não funcionar:

1. No Render: New → Web Service
2. Connect GitHub → binance-bot
3. Configure manualmente:
   - **Name**: binance-dashboard-v2
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && pip install plotly`
   - **Start Command**: `streamlit run dashboard_pro.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
   - **Environment Variables**:
     - `PORT = 8501`
     - `DATABASE_URL = postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance`
4. Deploy

## Solução Rápida (TESTE LOCAL)

Para testar localmente se o dashboard funciona:

```bash
# Instalar plotly
pip install plotly

# Rodar dashboard
streamlit run dashboard_pro.py
```

Se funcionar localmente, o problema é só o Render não fazer deploy.

## Logs Importantes

**Ver estes logs no Render:**

```
# Logs de sucesso:
Building from branch main...
Installing dependencies...
Successfully installed plotly-5.x.x
Starting Streamlit...
You can now view your Streamlit app in your browser.

# Logs de erro:
ModuleNotFoundError: No module named 'plotly'
FileNotFoundError: dashboard_pro.py not found
Connection refused: DATABASE_URL invalid
```

## Contingência: Usar URL Diferente

Se o deploy manual não funcionar, o Render pode criar uma URL nova.

Procure por:
- https://binance-dashboard-XXXX.onrender.com
- https://binance-bot-XXXX.onrender.com

A URL antiga (binance-bot-026n.onrender.com) pode não atualizar se for um serviço separado.

---

**RESUMO RÁPIDO:**

1. Dashboard Render → binance-dashboard
2. Manual Deploy → Branch main → Deploy Now
3. Aguardar 2-3 minutos
4. Acessar URL e verificar histórico de 35 trades
