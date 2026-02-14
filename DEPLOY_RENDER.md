# 🚀 GUÍA DEPLOY NO RENDER.COM

## ⚠️ O QUE PRECISA ANTES DO DEPLOY

### 1. Modificar bot_master.py (OBRIGATÓRIO)

**Arquivo:** `bot_master.py`

**No final do arquivo, ANTES da função `main()`, adicionar:**

```python
# ========================================
# PERSISTÊNCIA POSTGRESQL (Render)
# ========================================
try:
    from database import BotWithPersistence, close_repos
    # Substituir AutonomousBot por versão com persistência
    AutonomousBot = BotWithPersistence
except ImportError:
    pass  # Fallback para bot sem persistência
```

**E modificar a função `main()` para:**

```python
async def main():
    """Função principal."""
    from colorama import Fore
    try:
        bot = AutonomousBot()
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")
    finally:
        try:
            from database import close_repos
            await close_repos()
        except:
            pass
```

### 2. Criar Banco PostgreSQL no Render

**Passo a passo:**

1. **Acesse o Dashboard do Render**
   - https://dashboard.render.com

2. **Crie novo serviço PostgreSQL**
   - New → PostgreSQL
   - Name: `binance-bot-db`
   - Database: `binance_bot`
   - Region: Mais próxima ao Brasil (ex: Oregon)
   - Plan: Free (gratuito)

3. **Copie a Database URL**
   - Depois de criar, clique no serviço
   - Internal Database URL (parece: `postgresql://...`)

4. **Adicione ao bot (Web Service)**
   - Seu serviço do bot → Settings → Environment Variables
   - Key: `DATABASE_URL`
   - Value: Cole a URL copiada

5. **Deploy para aplicar**
   - Manual Deploy → Deploy latest commit

### 3. Rodar o Schema SQL

**Opção A: Via pgAdmin (Fácil)**
1. No serviço PostgreSQL do Render
2. Clique em "External Connection"
3. Use pgAdmin conectado com as credenciais
4. Cole todo o conteúdo de `database/schema.sql`
5. Execute

**Opção B: Via terminal (Se tiver acesso)**
```bash
psql $DATABASE_URL -f database/schema.sql
```

---

## ✅ O QUE JÁ FUNCIONA

- ✅ Bot opera normalmente
- ✅ Dashboard lê JSON (mas você pode perder dados ao reiniciar!)
- ✅ Todas as estratégias funcionam
- ✅ Sistema de SL/TP funciona

---

## ⚠️ O QUE NÃO FUNCIONA AINDA

**Se NÃO fizer as modificações acima:**
- ❌ PostgreSQL não será usado
- ❌ Ainda vai perder dados ao reiniciar
- ❌ Dashboard ainda lê JSON antigo

**Depois de modificar bot_master.py + configurar DB:**
- ✅ Dados salvos no PostgreSQL
- ✅ Posições recuperadas ao reiniciar
- ✅ Histórico completo
- ❌ Dashboard ainda lê JSON (precisa de update ou fallback)

---

## 🔄 Dashboard - 2 Opções

### Opção A: Fallback (Simles - Já funciona)

O dashboard **continua lendo JSON**, mas o bot **salva no PostgreSQL também**.

**Como funciona:**
1. Bot salva trades no PostgreSQL
2. Bot também atualiza JSON periodicamente (para o dashboard)
3. Dashboard não precisa ser alterado

**Modificação necessária no bot_master.py:**

```python
async def save_dashboard_state(self):
    """Salvar estado para dashboard (JSON fallback)."""
    try:
        import json
        # ... código existente que salva JSON ...
    except Exception as e:
        print(f"{Fore.RED}Erro ao salvar estado do dashboard: {e}")
```

### Opção B: Dashboard com PostgreSQL (Completo)

Modificar `dashboard.py` para ler do PostgreSQL:

```python
# No topo de dashboard.py
def load_data():
    """Carregar dados do PostgreSQL ou JSON fallback."""
    try:
        from database import get_dashboard_data_from_db
        import asyncio

        # Tentar buscar do PostgreSQL
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(get_dashboard_data_from_db())

        if data and (data.get('active_trades') or data.get('history')):
            return data
    except Exception as e:
        print(f"⚠️ DB indisponível: {e}")

    # Fallback para JSON
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None
```

---

## 📋 CHECKLIST DEPLOY

### Antes do Push

- [ ] Modificar `bot_master.py` (ver seção 1 acima)
- [ ] Criar PostgreSQL no Render
- [ ] Configurar `DATABASE_URL` no Render
- [ ] Rodar schema SQL no banco
- [ ] Testar localmente com DATABASE_URL configurada

### Push para GitHub

```bash
git add .
git commit -m "Add PostgreSQL persistence for Render"
git push
```

### Deploy no Render

1. **Render Dashboard** → Seu serviço do bot
2. **Manual Deploy** → Deploy latest commit
3. **Acompanhar os logs**:
   ```
   ✅ Conectado ao PostgreSQL
   ✅ Persistência PostgreSQL ativa
   📥 5 posições recuperadas do banco
   ```

---

## 🔍 Como Saber que Funcionou

**Logs no Render (use o botão "Logs" no serviço):**

**COM PostgreSQL funcionando:**
```
✅ Conectado ao PostgreSQL
✅ Persistência PostgreSQL ativa
🔄 Migrando dados de trade_history.json para PostgreSQL...
✅ Migração concluída: 47 trades migrados
📥 5 posições recuperadas do banco
🤖 BOT AUTÔNOMO INTELIGENTE
```

**SEM PostgreSQL (fallback):**
```
⚠️ PostgreSQL não configurado
🤖 BOT AUTÔNOMO INTELIGENTE
(Sem mensagem de conexão DB)
```

---

## 🚨 Problemas Comuns

### Erro: "relation trades does not exist"
**Causa:** Schema não foi rodado
**Solução:** Execute o SQL de `database/schema.sql`

### Erro: "DATABASE_URL not configured"
**Causa:** Variável de ambiente não configurada
**Solução:** Adicione DATABASE_URL nas Environment Variables

### Dashboard vazio
**Causa:** JSON não existe ainda
**Solução:** Normal na primeira vez, espere alguns minutos

### Erro: "no such table: trades"
**Causa:** Conectando no SQLite ao invés de PostgreSQL
**Solução:** Verifique se DATABASE_URL começa com `postgresql://`

---

## ✅ Resumo

**MÍNIMO PARA FUNCIONAR NO RENDER:**
1. Modificar `bot_master.py` (3 linhas)
2. Criar PostgreSQL no Render
3. Configurar DATABASE_URL
4. Rodar schema SQL

**OPCIONAL (recomendado):**
- Atualizar dashboard.py para ler do PostgreSQL
- Configurar Telegram alerts
- Adicionar testes no CI/CD

---

**Pergunta:** Quer que eu faça a modificação do `bot_master.py` para você? Basta dizer "sim" e eu aplico as mudanças necessárias.
