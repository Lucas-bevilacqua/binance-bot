# COMO CRIAR DASHBOARD NOVO (PASSO A PASSO)

O problema: Dashboard antigo não atualiza.
A solução: Criar NOVO serviço limpo.

## PASSO 1: Acessar Render

Vá: https://dashboard.render.com

Faça login na sua conta.

## PASSO 2: Criar Novo Serviço

1. Clique no botão **"New +"** (canto superior esquerdo)
2. Selecione **"Web Service"**

## PASSO 3: Conectar GitHub

1. Em "Connect", selecione **"GitHub"**
2. Encontre o repositório: **lucas-bevilacqua/binance-bot**
3. Clique **"Connect"**

## PASSO 4: Configurar Blueprint

NÃO selecione blueprint existente!

Em vez disso, use "Manual" configuration:

### Nome e Região:
- **Name**: `binance-dashboard-pro` (EXATAMENTE isso)
- **Region**: Frankfurt (ou o mais próximo)

### Branch:
- **Branch**: `main`

### Runtime:
- **Runtime**: Python 3

### Build Command:
```
pip install -r requirements.txt && pip install plotly
```

### Start Command:
```
streamlit run dashboard_pro.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### Environment Variables (CLIQUE "ADVANCED"):

Clique em "+" para adicionar cada variável:

1. **PORT** = `8501`
2. **DATABASE_URL** = `postgresql://bot_binance_user:2yT3u1JBiSintBbYfwmNlkJlSMmNJnJq@dpg-d686o9jnv86c73e914jg-a.frankfurt-postgres.render.com/bot_binance`
3. **PYTHON_VERSION** = `3.11.0`
4. **STREAMLIT_SERVER_ADDRESS** = `0.0.0.0`
5. **STREAMLIT_SERVER_HEADLESS** = `true`

## PASSO 5: Deploy

1. Clique **"Create Web Service"**
2. Aguarde 2-3 minutos
3. Acompanhe em "Events"

## PASSO 6: Acessar NOVO Dashboard

Deploy pronto? A URL será algo como:

```
https://binance-dashboard-pro.onrender.com
```

Clique na URL!

## O QUE VOCÊ DEVE VER:

✅ **Design profissional** (sem emojis)
✅ **35 trades no histórico**
✅ **Win rate: 74.3%**
✅ **Gráficos Plotly** (interativos)
✅ **Performance Analytics** com curva
✅ **Tabela profissional** com cores

## NÃO FUNCIONOU?

### Se der erro no build:

**Erro: "ModuleNotFoundError: plotly"**
- Build command está errado
- Use: `pip install -r requirements.txt && pip install plotly`

**Erro: "FileNotFoundError: dashboard_pro.py"**
- Branch errado
- Confirme que está em `main`
- Ou arquivo não existe no repositório

**Erro: DATABASE_URL**
- Variável não configurada
- Adicione em Environment Variables

### Se deploy ficar parado:

1. Vá em "Events"
2. Procure por erros vermelhos
3. Copie o erro e me mande

## LIMPEZA (DEPOIS)

Depois que o NOVO dashboard funcionar:

1. Volte para o dashboard antigo
2. Settings → Delete Service
3. Confirme deletar

## RESUMO RÁPIDO:

```
New + → Web Service → GitHub → binance-bot
Nome: binance-dashboard-pro
Branch: main
Runtime: Python 3
Build: pip install -r requirements.txt && pip install plotly
Start: streamlit run dashboard_pro.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

Env vars:
PORT=8501
DATABASE_URL=postgresql://bot_binance_user:...
PYTHON_VERSION=3.11.0
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

Deploy → Aguardar 3min → Acessar URL
```

Pronto! Dashboard profissional com 35 trades! 🚀
