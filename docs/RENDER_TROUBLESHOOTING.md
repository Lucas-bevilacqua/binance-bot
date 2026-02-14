# Troubleshooting - Binance Bot no Render.com

## Resumo de Problemas Comuns

| Problema | Sintoma | Solução |
|----------|----------|----------|
| Sem DATABASE_URL | Logs mostram "DB não configurado" | Configurar DATABASE_URL no dashboard Render |
| Schema não aplicado | Erro "relation trades does not exist" | Rodar scripts/apply_schema.py |
| Memória insuficiente | Worker reinicia constantemente | Reduzir MAX_POSITIONS ou fazer upgrade |
| Timeout na Binance | "Error connecting to Binance" | Verificar API Key/Secret válidos |
| Dashboard vazio | "Nenhum trade encontrado" | Aguardar bot sincronizar (5-10 min) |

---

## 1. Problemas de Conexão com Banco

### Erro: "connection to server at [...] failed"

**Diagnóstico:**
```bash
# No Shell do Render
echo $DATABASE_URL
# Deve mostrar algo como: postgres://user:pass@host/db
```

**Soluções:**

1. **Verificar DATABASE_URL está configurada:**
   - Render → binance-bot-worker → Environment
   - Key: `DATABASE_URL`
   - Value: Use "Internal Database URL" (não External)

2. **Verificar database está disponível:**
   - Render → binance-bot-db → Status
   - Deve mostrar "Available"

3. **Testar conexão manualmente:**
   ```bash
   # No Shell do Render
   python -c "import asyncpg, asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"
   # Se não der erro, conexão OK
   ```

---

## 2. Problemas de Schema

### Erro: "relation trades does not exist"

**Causa:** Tabelas não foram criadas ainda.

**Solução A - Via Script:**
```bash
# No Shell do Render
export DATABASE_URL="postgresql://..."
python scripts/apply_schema.py
```

**Solução B - Via psql:**
```bash
# Obter External Connection URL do banco
psql <database-url> -f database/schema.sql
```

**Solução C - Automático:**
O script `init_render_env.py` deve criar tabelas automaticamente. Verificar logs:
```
Tabelas não encontradas. Aplicando schema.sql...
Schema aplicado com sucesso!
```

---

## 3. Problemas de Memória/CPU

### Worker reinicia constantemente

**Diagnóstico:**
```bash
# Ver memory usage
ps aux | grep python
# Ou no Render Dashboard: Metrics
```

**Causas:**

1. **Muitas posições simultâneas**
   - Solução: Reduzir `MAX_POSITIONS` de 3 para 1 ou 2
   - Ou reduzir `ALAVANCAGEM_PADRAO`

2. **Muitos símbolos sendo scaneados**
   - Solução: Reduzir lista de symbols
   - Aumentar `SCAN_INTERVAL` de 60 para 120

3. **Memory leak no código**
   - Verificar se há listas crescendo sem limite
   - Usar `sys.getsizeof()` para debugar

**Ajuste de variáveis:**
```
MAX_POSITIONS=1          # Reduzir carga
SCAN_INTERVAL=120        # Menos scaneamentos
MONITOR_INTERVAL=30      # Menor frequência de updates
MIN_SIGNAL_STRENGTH=40   # Filtros mais estritos
```

---

## 4. Problemas com API Binance

### Erro: "-1021: Timestamp for this request is outside of the recvWindow"

**Causa:** Relógio do servidor desincronizado.

**Solução:**
- O Render sincroniza automaticamente o relógio
- Se persistir, pode ser latência muito alta

### Erro: "-2015: Invalid API-key, IP, or permissions for action"

**Causa:** API Key inválida ou sem permissão.

**Solução:**
1. Verificar BINANCE_API_KEY está correta
2. Verificar API Key tem permissão "Futures Trading"
3. No Binance Dashboard: API Management → Edit API Key → Enable Futures

### Erro: "Connection timeout"

**Causa:** Latência ou firewall.

**Solução:**
```python
# Em bot_master.py, aumentar timeout
self.client = await AsyncClient.create(
    self.api_key,
    self.api_secret,
    requests_params={'timeout': 30}  # Aumentar de 9 para 30s
)
```

---

## 5. Problemas com Dashboard

### Dashboard mostra "Aguardando dados..."

**Causa 1:** Bot ainda não salvou dados.

**Solução:**
- Aguardar 5-10 minutos
- Verificar logs do bot: "Salvando estado do dashboard..."

**Causa 2:** Dashboard não consegue ler dados.

**Solução:**
```bash
# Ver se arquivo existe
ls -la dashboard_data.json

# Ver conteúdo
cat dashboard_data.json
```

### Dashboard não carrega (página branca)

**Causa:** Streamlit não iniciando corretamente.

**Diagnóstico:**
```bash
# Ver logs do dashboard service
# Procurar por: "streamlit"
```

**Solução:**
Verificar start command:
```
streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

---

## 6. Problemas de Deploy

### Deploy falha no build step

**Erro comum:** "ModuleNotFoundError: No module named 'binance'"

**Causa:** requirements.txt incompleto ou erro no pip install.

**Solução:**
```txt
# Verificar requirements.txt tem:
python-binance==1.0.19
asyncpg==0.29.0
streamlit==1.30.0
# ... outras dependências
```

### Build demora muito

**Causa:** Reinstalando tudo do zero.

**Otimização:**
- Render faz cache automático de dependências
- Se sempre reinstala, verificar se requirements.txt muda frequentemente

---

## 7. Logs Úteis para Debug

### Ver logs em tempo real:

```bash
# No Shell do Render
tail -f /var/log/app.log
```

### Grep por erros específicos:

```bash
# Procurar erros PostgreSQL
grep -i "error\|exception" logs/app.log | tail -20

# Procurar trades
grep "Ordem executada" logs/app.log | tail -10
```

### Ativar debug mode:

Adicionar ao bot_master.py:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 8. Recuperação de Desastres

### Bot parou de funcionar

**Passo 1: Verificar status dos serviços**
- Dashboard Render → Overview
- Todos devem estar "Live"

**Passo 2: Verificar logs recentes**
- Procurar por último erro antes de parar
- Identificar se é crash ou loop infinito

**Passo 3: Restart manual**
- binance-bot-worker → Manual Deploy → Clear build cache & deploy

### Perder todas as posições após restart

**Causa:** Persistência PostgreSQL não funcionando.

**Verificar:**
1. DATABASE_URL configurada
2. Schema aplicado
3. Logs mostram "PostgreSQL ativa"

**Recuperar da Binance:**
```python
# O bot deve fazer sync automático de posições abertas
await self.sync_open_positions()
```

### Restaurar backup do banco

```bash
# No Shell do Render
pg_dump $DATABASE_URL > backup.sql
# Depois:
psql $DATABASE_URL < backup.sql
```

---

## 9. Performance Optimization

### Se bot está lento:

1. **Aumentar scan interval:**
   ```
   SCAN_INTERVAL=120  # Em vez de 60
   ```

2. **Reducir lista de symbols:**
   ```python
   # Em vez de 19 symbols, usar top 5
   self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
   ```

3. **Usar websockets em vez de polling:**
   - O bot atual usa polling (futures_klines)
   - Melhorar para websockets reduz API calls

### Se dashboard está lento:

1. **Limitar dados:**
   ```python
   # Em bot_master.py.save_dashboard_state()
   'history': history[-20:]  # Em vez de [-50:]
   ```

2. **Aumentar refresh interval:**
   ```python
   # Em dashboard.py
   time.sleep(30)  # Em vez de 10
   ```

---

## 10. Contato e Suporte

### Render Support:
- Dashboard → Help → Contact Support
- Status page: https://status.render.com/

### Binance API Support:
- Telegram: @binance_api_english
- Email: support@binance.com

### Logs de erro para reportar:
```bash
# Coletar logs relevantes
grep -i "error" logs/app.log | tail -50 > debug.log
```

---

**Última atualização:** 2025-02-14
**Versão do Bot:** 1.0
**Versão do Python:** 3.11
