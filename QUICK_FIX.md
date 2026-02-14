# 🔧 QUICK FIX - bot_master.py para Render

## O QUE MUDAR

### Localização 1: Topo do arquivo (após imports)

```python
# ========================================
# IMPORT ADICIONAL
# ========================================
try:
    from database import BotWithPersistence, close_repos
    HAS_PERSISTENCE = True
except ImportError:
    HAS_PERSISTENCE = False
```

### Localização 2: Função main() (final do arquivo)

**SUBSTITUIR a função `main()` EXISTENTE por:**

```python
async def main():
    """Função principal."""
    from colorama import Fore
    try:
        # ========================================
        # CRIAR BOT COM OU SEM PERSISTÊNCIA
        # ========================================
        if HAS_PERSISTENCE:
            bot = BotWithPersistence()
        else:
            from bot_master import AutonomousBot
            bot = AutonomousBot()

        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")
    finally:
        if HAS_PERSISTENCE:
            try:
                await close_repos()
            except Exception as e:
                print(f"{Fore.YELLOW}Aviso: {e}")
```

---

## ✅ PRONTO PARA DEPLOY

Depois dessas mudanças:

1. **Commit:**
   ```bash
   git add .
   git commit -m "Add PostgreSQL persistence"
   ```

2. **Push:**
   ```bash
   git push
   ```

3. **Render:** Manual Deploy → Deploy latest commit

---

## 🎯 RESULTADO

**COM DATABASE_URL configurada:**
- ✅ Usa PostgreSQL
- ✅ Recupera posições ao reiniciar
- ✅ Histórico completo

**SEM DATABASE_URL:**
- ✅ Funciona normal (fallback)
- ⚠️ Perde dados ao reiniciar (igual antes)
