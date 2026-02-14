# Checklist de Deploy - Binance Bot no Render.com

## Pré-Deploy

### Código
- [x] render.yaml criado e validado
- [x] Procfile configurado
- [x] runtime.txt especifica Python 3.11
- [x] requirements.txt completo
- [x] .env.example atualizado
- [x] database/schema.sql pronto

### Configuração Render
- [x] Blueprint render.yaml pronto
- [x] Worker service configurado
- [x] Dashboard service configurado
- [x] Database PostgreSQL configurado
- [x] Variáveis de ambiente documentadas

### Scripts Auxiliares
- [x] setup_render.sh criado
- [x] apply_schema.py criado
- [x] health_check.py criado
- [x] Documentação completa

## Deploy Manual no Dashboard Render

### 1. Conectar Repositório
- [ ] Fazer push do código para GitHub
- [ ] No Render: New → Blueprint
- [ ] Autorizar acesso ao repositório
- [ ] Selecionar repositório

### 2. Criar Banco PostgreSQL
- [ ] New → PostgreSQL
- [ ] Name: binance-bot-db
- [ ] Database: binance_bot
- [ ] User: binance_bot_user
- [ ] Region: Oregon (ou mais próximo)
- [ ] Plan: Free
- [ ] Aguardar disponibilidade (status "Available")

### 3. Criar Worker Service (Bot)
- [ ] New → Worker Service
- [ ] Name: binance-bot-worker
- [ ] Runtime: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python bot_master.py`
- [ ] Branch: main
- [ ] Plan: Free

### 4. Configurar Environment Variables (Worker)
- [ ] DATABASE_URL (do banco criado)
- [ ] BINANCE_API_KEY
- [ ] BINANCE_API_SECRET
- [ ] PYTHON_VERSION: 3.11.0
- [ ] SCAN_INTERVAL: 60
- [ ] MONITOR_INTERVAL: 15
- [ ] MAX_POSITIONS: 3
- [ ] MIN_SIGNAL_STRENGTH: 28
- [ ] ALAVANCAGEM_PADRAO: 50
- [ ] RISCO_MAXIMO_POR_OPERACAO: 0.12
- [ ] STOP_LOSS_PERCENTUAL: 0.015
- [ ] TAKE_PROFIT_PERCENTUAL: 0.025
- [ ] OPENAI_API_KEY (opcional)
- [ ] TELEGRAM_BOT_TOKEN (opcional)
- [ ] TELEGRAM_CHAT_ID (opcional)

### 5. Criar Web Service (Dashboard)
- [ ] New → Web Service
- [ ] Name: binance-dashboard
- [ ] Runtime: Python 3
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
- [ ] Branch: main
- [ ] Plan: Free

### 6. Aplicar Schema SQL
- [ ] Obter External Connection URL
- [ ] Conectar via pgAdmin ou psql
- [ ] Executar database/schema.sql
- [ ] Verificar tabelas criadas (symbols, trades, positions, daily_metrics)

## Pós-Deploy (Primeiros 30 min)

### Verificação Inicial (5 min)
- [ ] Worker service status: "Live"
- [ ] Dashboard service status: "Live"
- [ ] Database status: "Available"

### Logs do Bot (10 min)
- [ ] Abrir Logs → binance-bot-worker
- [ ] Verificar: "✅ Persistência PostgreSQL ativa"
- [ ] Verificar: "🤖 BOT AUTÔNOMO INTELIGENTE"
- [ ] Verificar: "[HH:MM:SS] Buscando oportunidades..."
- [ ] Sem erros de conexão

### Funcionalidade (20 min)
- [ ] Bot sincronizou posições existentes
- [ ] Bot scannea mercados
- [ ] Dashboard acessível via URL
- [ ] Dashboard mostra dados atualizados

### Testes de Integração (30 min)
- [ ] Testar health check (se implementado)
- [ ] Verificar dados no PostgreSQL
- [ ] Verificar que posições são salvas
- [ ] Verificar histórico sendo gravado

## Validação Final

### Banco de Dados
```sql
-- Verificar tabelas existem
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
-- Esperado: symbols, trades, positions, daily_metrics

-- Verificar dados iniciais
SELECT COUNT(*) FROM symbols;
-- Esperado: ~16 symbols (BTC, ETH, etc.)
```

### Logs Esperados
```
✅ Persistência PostgreSQL ativa
📥 0 posições recuperadas do banco
🤖 BOT AUTÔNOMO INTELIGENTE
======================================================================
  🤖 BOT AUTÔNOMO INTELIGENTE
======================================================================
  Iniciado: 2025-02-14 HH:MM:SS
  Alavancagem: 50x
  Risco por trade: 12.0%
  Max posições: 3
======================================================================
[HH:MM:SS] Buscando oportunidades... (0/3 posições)
[HH:MM:SS] Aguardando 15s...
```

### Dashboard Access
- [ ] URL responde (status 200)
- [ ] Dashboard mostra configurações
- [ ] Dashboard mostra símbolos
- [ ] Auto-refresh funciona

## Troubleshooting Checklist

### Se Worker falha em start
- [ ] Verificar requirements.txt tem todas as dependências
- [ ] Verificar syntax do bot_master.py
- [ ] Verificar variáveis de ambiente configuradas
- [ ] Logs mostram erro específico

### Se Dashboard não carrega
- [ ] STREAMLIT_SERVER_HEADLESS = true
- [ ] PORT está sendo usado corretamente
- [ ] Build command instalou streamlit

### Se PostgreSQL não conecta
- [ ] DATABASE_URL está correta
- [ ] Usar Internal URL (não External)
- [ ] Database está "Available"

### Se bot reinicia constantemente
- [ ] Memory limit (free: 512MB)
- [ ] CPU usage está normal
- [ ] Loop infinito no código

## Monitoramento Contínuo

### Diário
- [ ] Verificar logs por erros
- [ ] Verificar trades executados
- [ ] Verificar PnL acumulado

### Semanal
- [ ] Backup manual do banco
- [ ] Revisar configurações
- [ ] Atualizar dependências

### Mensal
- [ ] Rotacionar API Keys
- [ ] Revisar performance
- [ ] Limpar logs antigos

## Rollback Plan

Se algo der errado:

1. **Parar Worker**
   - Render → binance-bot-worker → Manual Deploy → Pause

2. **Reverter Código**
   ```bash
   git revert HEAD
   git push origin main
   ```

3. **Reiniciar Worker**
   - Render → binance-bot-worker → Manual Deploy

## Upgrade Plan (Free → Paid)

Se precisar de mais recursos:

- **Starter ($7/mês)**: 512MB → 512MB (mais CPU)
- **Standard ($25/mês)**: 2GB RAM, 0.1 vCPU
- **Pro Plus ($85/mês)**: 8GB RAM, 1 vCPU + Priority Support

Quando considerar upgrade:
- [ ] Bot fica sem memória
- [ ] Muitos timeouts
- [ ] Dashboard lento
- [ ] Mais de 10 posições simultâneas

---

**Status Checklist**: Pronto para Deploy
**Data**: 2025-02-14
**Versão**: 1.0
