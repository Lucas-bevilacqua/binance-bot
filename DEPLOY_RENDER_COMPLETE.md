# Deploy Binance Bot no Render.com - Guia Completo

## Resumo Executivo

Este guia fornece configuração completa para deploy do Binance Bot no Render.com com PostgreSQL persistência.

## Arquivos de Configuração Criados

| Arquivo | Descrição |
|---------|-----------|
| `render.yaml` | Blueprint principal (Worker + Dashboard + Database) |
| `.render/apps.yaml` | Configurações detalhadas dos serviços |
| `.render/bot.yaml` | Configuração isolada do Bot Worker |
| `.render/dashboard.yaml` | Configuração isolada do Dashboard |
| `scripts/setup_render.sh` | Script automatizado de setup |
| `scripts/apply_schema.py` | Script para aplicar schema SQL |
| `scripts/health_check.py` | Health check do bot |

## Arquitetura do Deploy

```
┌─────────────────────────────────────────────────────────────────┐
│                      Render.com                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ binance-bot      │         │ binance-bot-db   │             │
│  │ (Worker Service) │◄────────│ (PostgreSQL)     │             │
│  │                 │         │                  │             │
│  │ bot_master.py   │         │ - symbols        │             │
│  │ 24/7 running   │         │ - trades         │             │
│  └──────────────────┘         │ - positions      │             │
│                              │ - daily_metrics  │             │
│  ┌──────────────────┐        └──────────────────┘             │
│  │ binance-        │                                        │
│  │ dashboard        │                                        │
│  │ (Web Service)   │                                        │
│  │                 │                                        │
│  │ dashboard.py     │                                        │
│  │ Streamlit       │                                        │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Preparação Local

### 1.1 Verificar pré-requisitos

```bash
# Verificar Python
python --version  # Deve ser 3.11+

# Verificar Git
git status

# Instalar dependências
pip install -r requirements.txt
```

### 1.2 Configurar .env

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

Variáveis obrigatórias:
- `BINANCE_API_KEY` - Chave API da Binance
- `BINANCE_API_SECRET` - Segredo API da Binance

Variáveis opcionais:
- `OPENAI_API_KEY` - Para análise AI
- `TELEGRAM_BOT_TOKEN` - Notificações
- `TELEGRAM_CHAT_ID` - Chat para notificações

## 2. Deploy no Render.com

### 2.1 Método A: Blueprint (Recomendado)

1. **Fazer push do código para GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **No Dashboard Render:**
   - New → Blueprint
   - Selecionar repositório GitHub
   - O arquivo `render.yaml` será detectado automaticamente

3. **Confirmar criação dos recursos:**
   - Service: binance-bot-worker (Worker)
   - Service: binance-dashboard (Web)
   - Database: binance-bot-db (PostgreSQL)

### 2.2 Método B: Manual

1. **Criar Banco PostgreSQL:**
   - New → PostgreSQL
   - Name: binance-bot-db
   - Database: binance_bot
   - User: binance_bot_user
   - Plan: Free

2. **Criar Worker Service (Bot):**
   - New → Worker Service
   - Connect: GitHub repo
   - Name: binance-bot-worker
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot_master.py`

3. **Criar Web Service (Dashboard):**
   - New → Web Service
   - Connect: GitHub repo
   - Name: binance-dashboard
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`

## 3. Configuração do Banco de Dados

### 3.1 Aplicar Schema

**Opção A - Via External Connection (pgAdmin):**

1. No Render → binance-bot-db → Connect
2. Usar credenciais fornecidas
3. Executar `database/schema.sql`

**Opção B - Via Script Python:**

```bash
# Localmente, com DATABASE_URL exportada
export DATABASE_URL="postgresql://..."
python scripts/apply_schema.py
```

**Opção C - Automático (recomendado):**

O `database/db_integration.py` cria tabelas automaticamente no primeiro deploy.

## 4. Environment Variables

Configure no Dashboard Render para cada serviço:

### binance-bot-worker:

| Key | Valor | Sync |
|-----|-------|------|
| `DATABASE_URL` | (Internal DB URL) | Auto |
| `BINANCE_API_KEY` | Sua chave API | No |
| `BINANCE_API_SECRET` | Seu segredo API | No |
| `PYTHON_VERSION` | 3.11.0 | Yes |
| `SCAN_INTERVAL` | 60 | Yes |
| `MONITOR_INTERVAL` | 15 | Yes |
| `MAX_POSITIONS` | 3 | Yes |

### binance-dashboard:

| Key | Valor | Sync |
|-----|-------|------|
| `DATABASE_URL` | (Internal DB URL) | Auto |
| `PORT` | 8501 | Yes |
| `STREAMLIT_SERVER_HEADLESS` | true | Yes |

## 5. Checklist Pós-Deploy

### 5.1 Imediato (5 min)

- [ ] Serviço "binance-bot-worker" está "Live"
- [ ] Serviço "binance-dashboard" está "Live"
- [ ] Banco "binance-bot-db" está "Available"

### 5.2 Configuração (10 min)

- [ ] DATABASE_URL configurada no Worker
- [ ] Credenciais Binance configuradas
- [ ] Schema SQL aplicado
- [ ] Health check passando

### 5.3 Verificação (30 min)

- [ ] Bot está gerando logs
- [ ] Posições sendo salvas no banco
- [ ] Dashboard acessível via URL
- [ ] Histórico sincronizado

## 6. Acompanhamento

### 6.1 Logs no Render

```
Dashboard → binance-bot-worker → Logs
```

**Logs esperados:**
```
✅ Persistência PostgreSQL ativa
📥 5 posições recuperadas do banco
🤖 BOT AUTÔNOMO INTELIGENTE
[HH:MM:SS] Buscando oportunidades... (0/3 posições)
```

### 6.2 Health Check

Use o script de verificação:
```bash
# No Render, abrir Shell
python scripts/health_check.py -v
```

Saída esperada:
```json
{
  "status": "OK",
  "checks": {
    "database": {"status": "ok"},
    "binance": {"status": "ok"},
    "dashboard": {"status": "ok"}
  }
}
```

## 7. Troubleshooting

### 7.1 Erro: "relation trades does not exist"

**Causa:** Schema não aplicado

**Solução:**
```bash
psql $DATABASE_URL -f database/schema.sql
```

### 7.2 Erro: "DATABASE_URL not configured"

**Causa:** Variável não configurada

**Solução:**
1. Render → binance-bot-worker → Environment
2. Adicionar DATABASE_URL
3. Valor: Internal Database URL do banco

### 7.3 Bot reinicia constantemente

**Causas possíveis:**
- Memória insuficiente (plano free: 512MB)
- Loop infinito no código
- Exceção não capturada

**Solução:**
1. Verificar logs completos
2. Procurar por traceback
3. Aumentar MAX_POSITIONS para reduzir carga

### 7.4 Dashboard vazio ou erro

**Causas possíveis:**
- Bot ainda não gerou dados
- DATABASE_URL diferente do bot
- Timeout na conexão

**Solução:**
1. Aguardar 5-10 min após bot iniciar
2. Verificar DATABASE_URL idêntica
3. Usar JSON fallback temporariamente

### 7.5 Posição não recuperada após restart

**Causa:** Persistência não funcionando

**Verificar:**
```python
# Logs devem mostrar:
✅ Persistência PostgreSQL ativa
📥 X posições recuperadas do banco
```

Se não mostrar, `database/db_integration.py` não está sendo importado.

## 8. Scripts Auxiliares

### 8.1 setup_render.sh

Script automatizado que cria todos os recursos:

```bash
bash scripts/setup_render.sh
```

Opções:
1. Completo (Banco + Worker + Dashboard)
2. Apenas Banco
3. Apenas Worker
4. Apenas Dashboard

### 8.2 apply_schema.py

Aplica schema SQL no banco:

```bash
export DATABASE_URL="postgresql://..."
python scripts/apply_schema.py
```

### 8.3 health_check.py

Verifica saúde do bot:

```bash
python scripts/health_check.py -v
```

## 9. Segurança

### 9.1 Proteção de API Keys

- **Nunca** commitar .env com chaves reais
- **Sempre** usar `sync: false` para variáveis sensíveis
- **Rotacionar** chaves periodicamente

### 9.2 Hardening PostgreSQL

No Render → binance-bot-db → Security:

```yaml
ipAllowList:
  - source: 0.0.0.0/0  # Remover após setup
    description: "Temporário"
```

### 9.3 Dashboard Protection

Adicionar autenticação básica (opcional):

```python
# Em dashboard.py
import streamlit as st

def check_password():
    def password_entered():
        if (st.session_state.get("password")
            == os.getenv("DASHBOARD_PASSWORD")):
            st.session_state["authenticated"] = True

    if not st.session_state.get("authenticated"):
        st.text_input("Password", type="password",
                     on_change=password_entered, key="password")
        st.stop()
```

## 10. Backup e Monitoramento

### 10.1 Backups Automáticos

Render faz backups diários para bancos PostgreSQL (plano free: 7 dias).

### 10.2 Export Manual

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 10.3 Métricas

Monitorar no dashboard Render:
- CPU usage (deve ser < 50%)
- Memory usage (deve ser < 400MB)
- Disk usage (deve ser < 90%)

## 11. Próximos Passos

Após deploy bem-sucedido:

1. **Monitorar primeiros 24h** - Acompanhar logs
2. **Ajustar parâmetros** - Baseado em performance
3. **Configurar alertas** - Render tem notificações
4. **Documentar decisões** - Anotar ajustes

## 12. Suporte

### Recursos Oficiais:
- Render Docs: https://render.com/docs
- Binance Futures API: https://binance-docs.github.io/apidocs/futures/en/

### Logs Úteis:

```
# Bot
tail -f .aios/logs/agent.log  # Se em AIOS
# Render Dashboard → Logs

# Database
psql $DATABASE_URL -c "SELECT * FROM trades ORDER BY entry_time DESC LIMIT 10;"
```

---

**Arquivo de configuração completa para deploy do Binance Bot no Render.com**

Data: 2025-02-14
Versão: 1.0
Status: Production Ready
