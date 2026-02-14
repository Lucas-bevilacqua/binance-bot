# 🚀 Guia de Migração: JSON → PostgreSQL

## 📋 Resumo

Este guia mostra como migrar o bot de armazenamento JSON para PostgreSQL, **resolvendo o problema de perda de dados ao reiniciar no Render**.

---

## ⚡ Opção 1: Migração Rápida (Recomendado para Render)

### Passo 1: Criar Banco de Dados Gratuito

**Opção A: Neon (PostgreSQL Serverless)**
```bash
1. Acesse: https://neon.tech
2. Crie conta gratuita
3. Crie novo projeto "binance-bot"
4. Copie Connection String (postgresql://...)
```

**Opção B: Supabase (PostgreSQL + Dashboard)**
```bash
1. Acesse: https://supabase.com
2. Crie projeto novo
3. Vá em Settings → Database
4. Copie Connection String
```

### Passo 2: Configurar Variáveis de Ambiente

No **Render Dashboard**, adicione a variável de ambiente:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```

### Passo 3: Instalar Dependências

```bash
pip install asyncpg==0.29.0
```

Ou no Render `requirements.txt` já está atualizado.

### Passo 4: Rodar Schema SQL

No **Dashboard do seu provedor PostgreSQL** (Neon/Supabase), rode:

```sql
-- Copie todo o conteúdo de database/schema.sql
-- E cole no SQL Editor do seu dashboard
```

Ou via linha de comando:

```bash
psql $DATABASE_URL -f database/schema.sql
```

### Passo 5: Modificar bot_master.py (3 linhas)

No final do arquivo `bot_master.py`, adicione:

```python
# ========================================
# PERSISTÊNCIA POSTGRESQL (Adicionar)
# ========================================
try:
    from database import BotWithPersistence
    AutonomousBot = BotWithPersistence
except ImportError:
    pass  # Fallback para bot sem persistência


async def main():
    """Função principal."""
    try:
        bot = AutonomousBot()
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Programa interrompido")
```

### Passo 6: Deploy!

```bash
git add .
git commit -m "Add PostgreSQL persistence"
git push
```

**Pronto!** O bot agora vai:
- ✅ Salvar todos os trades no PostgreSQL
- ✅ Recuperar posições ao reiniciar
- ✅ Manter histórico completo (não mais 500 trades)
- ✅ Auto-migrar JSON existente no primeiro start

---

## 🔧 Opção 2: Modificação Completa (Recomendado Local)

### Modificar o ponto de entrada do bot

Substituir a função `main()` em `bot_master.py` por:

```python
async def main_with_persistence():
    """Main function com persistência PostgreSQL."""
    from colorama import Fore
    try:
        bot = BotWithPersistence()
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")
    finally:
        from database import close_repos
        await close_repos()


if __name__ == "__main__":
    try:
        asyncio.run(main_with_persistence())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Programa interrompido")
```

---

## 📊 Modificar dashboard.py para Ler do Banco

Substituir a função `load_data()` em `dashboard.py`:

```python
def load_data():
    """Carrega dados do PostgreSQL."""
    try:
        from database import get_dashboard_data_from_db
        import asyncio

        data = asyncio.run(get_dashboard_data_from_db())
        return data if data else None

    except Exception as e:
        # Fallback para JSON se DB falhar
        if os.path.exists(DATA_FILE):
            import json
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return None
```

---

## ✅ Verificação

Após deploy, verifique os logs:

```
✅ Conectado ao PostgreSQL
✅ Persistência PostgreSQL ativa
📥 5 posições recuperadas do banco
✅ Migração concluída: 47 trades migrados
📦 JSON original salvo como trade_history.json.backup
```

---

## 🔍 Troubleshooting

### Erro: "relation trades does not exist"
**Causa:** Schema não foi executado
**Solução:** Rode o SQL completo do `database/schema.sql`

### Erro: "DATABASE_URL not configured"
**Causa:** Variável de ambiente não configurada
**Solução:** Adicione `DATABASE_URL` nas variáveis do Render

### Erro: "no such table: trades"
**Causa:** Conectando ao SQLite ao invés de PostgreSQL
**Solução:** Verifique se DATABASE_URL começa com `postgresql://`

---

## 📦 Estrutura Criada

```
database/
├── __init__.py           # Exports
├── schema.sql            # Estrutura do banco
├── repositories.py       # Camada de acesso aos dados
└── db_integration.py     # Wrapper para bot_master.py
```

---

## 🎯 Próximos Passos

Após migração bem-sucedida:

1. ✅ **Task 1 completa** - Persistência PostgreSQL funcionando
2. → **Task 2** - Adicionar testes unitários
3. → **Task 3** - Implementar logging estruturado

---

**Data:** 2026-02-14
**Status:** Ready for Deploy
