# 🚀 COMO SUBIR O BOT NA NUVEM (GRATUITO)

Guia passo a passo para rodar seu bot 24/7 sem custo.

---

## 🎯 MELHOR OPÇÃO: RAILWAY.APP

Railway é gratuito, rápido e fácil de configurar.

### Passo 1: Criar conta Railway
1. Acesse: https://railway.app/
2. Clique em "Start Free" ou "Login with GitHub"
3. Crie sua conta (é gratuito)

### Passo 2: Fazer deploy do bot
1. No dashboard Railway, clique em **"New Project"**
2. Clique em **"Deploy from GitHub repo"**
3. Conecte seu GitHub (se ainda não conectou)
4. Clique em **"New Repository"** para criar um repo

#### Opção A: Criar repo no GitHub
1. Crie um novo repositório no GitHub (ex: `binance-bot`)
2. Suba os arquivos do bot
3. No Railway, selecione esse repositório
4. Clique em **"Deploy Now"**

#### Opção B: Upload direto (sem GitHub)
1. No seu computador, crie um arquivo ZIP com os arquivos
2. No Railway, clique em **"New Project"** → **"CLI"**
3. Siga as instruções para instalar a CLI Railway

### Passo 3: Configurar variáveis de ambiente
1. No projeto Railway, vá em **"Variables"**
2. Adicione estas variáveis:

```
BINANCE_API_KEY=sua_chave_aqui
BINANCE_API_SECRET=seu_secreto_aqui
CAPITAL_INICIAL=15
RISCO_MAXIMO_POR_OPERACAO=0.12
ALAVANCAGEM_PADRAO=50
STOP_LOSS_PERCENTUAL=0.015
TAKE_PROFIT_PERCENTUAL=0.025
```

### Passo 4: Deploy!
1. Clique em **"Deploy"**
2. Aguarde alguns segundos
3. Seu bot estará rodando! 🎉

### Passo 5: Monitorar
1. No dashboard Railway, clique em **"Logs"**
2. Veja seu bot funcionando em tempo real

---

## 🎮 OPÇÃO 2: REPLIT (Alternativa)

Replit também é gratuito e muito fácil.

### Passo 1: Criar projeto Replit
1. Acesse: https://replit.com/
2. Clique em **"+ Create Repl"**
3. Escolha **"Python"** como template
4. Dê um nome (ex: "binance-bot")
5. Clique em **"Create Repl"**

### Passo 2: Adicionar arquivos
1. Copie TODOS os arquivos do bot para o Replit
2. Arraste os arquivos ou cole o código

### Passo 3: Configurar variáveis
1. No Replit, vá em **"Secrets"** (ícone de cadeado)
2. Adicione as variáveis:
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`
   - E as outras variáveis do .env

### Passo 4: Rodar
1. No arquivo `replit.nix`, adicione:
   ```
   { deps = [ (import ./pkgs/python-with-packages.nix) ]; }
   ```
2. Clique em **"Run"** (botão verde)

### Passo 5: Manter rodando (Always On)
1. No Replit, vá em **"Tools"** → **"Deployments"**
2. Clique em **"Configure"**
3. Em **"Healthcheck"**, configure para verificar `/`
4. Deploy!

---

## 📁 ARQUIVOS NECESSÁRIOS

Para subir na nuvem, você precisa destes arquivos:

```
binance-bot/
├── bot_auto.py          ← Bot autônomo (obrigatório)
├── requirements.txt     ← Dependências
├── Dockerfile           ← Config Docker (opcional)
├── Procfile             ← Config Railway (opcional)
├── runtime.txt          ← Versão Python (opcional)
├── .env                 ← NÃO suba isso!
└── .gitignore           ← Ignora arquivos sensíveis
```

### .gitignore (IMPORTANTE!)
```
.env
venv/
__pycache__/
*.pyc
*.log
```

---

## 🔧 ARQUIVOS JÁ CRIADOS

Já criei tudo para você:
- ✅ `bot_auto.py` - Bot autônomo
- ✅ `requirements.txt` - Dependências
- ✅ `Dockerfile` - Configuração Docker
- ✅ `Procfile` - Configuração Railway
- ✅ `runtime.txt` - Versão Python
- ✅ `.gitignore` - Arquivos ignorados

---

## ⚡ COMO SUBIR NO GITHUB (FÁCIL)

### 1. Instalar Git (se não tiver)
- Windows: https://git-scm.com/download/win

### 2. Criar repositório no GitHub
1. Acesse: https://github.com/new
2. Nome: `binance-bot`
3. Marque "Private" (privado é mais seguro)
4. Clique em "Create repository"

### 3. Enviar arquivos
Abra o terminal na pasta do bot e execute:

```bash
# Iniciar git
git init

# Adicionar arquivos
git add .

# Commit
git commit -m "Initial commit - Binance bot"

# Adicionar origem (SUBSTITUA SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/binance-bot.git

# Enviar
git branch -M main
git push -u origin main
```

### 4. Conectar Railway ao GitHub
1. Acesse: https://railway.app/new
2. Clique em **"Deploy from GitHub repo"**
3. Selecione `binance-bot`
4. Configure as variáveis de ambiente
5. Deploy!

---

## 🔐 SEGURANÇA IMPORTANTE

⚠️ **NUNCA** suba o arquivo `.env` para o GitHub!

1. O arquivo `.gitignore` já está configurado para ignorar `.env`
2. No Railway/Replit, configure as variáveis manualmente
3. Seus segredos ficarão seguros

---

## 📊 MONITORAR BOT NA NUVEM

### Railway
1. Acesse seu projeto no Railway
2. Clique em **"Logs"** ou **"Metrics"**
3. Veja o bot rodando em tempo real

### Replit
1. Acesse seu Repl
2. Aba **"Console"** mostra logs em tempo real

---

## 💰 CUSTOS

**Plano gratuito Railway:**
- ✅ $5/month de crédito grátis
- ✅ Suficiente para rodar o bot 24/7
- ✅ 512MB RAM
- ✅ Suporta Python perfeitamente

**Plano gratuito Replit:**
- ✅ Always On gratuito
- ✅ 500MB-1GB RAM
- ✅ Rodar contínuo

---

## 🚀 COMEÇAR AGORA

### Opção mais rápida (5 minutos):

**COM RAILWAY:**
1. Entre: https://railway.app/
2. Login com GitHub
3. "New Project" → "Deploy from GitHub"
4. Conecte seu repo
5. Configure variáveis
6. Deploy! 🎉

### Dúvidas?

Railway docs: https://docs.railway.app/
Replit docs: https://docs.replit.com/

---

## ⚙️ CONFIGURAÇÕES DO BOT AUTÔNOMO

O `bot_auto.py` já vem configurado:

```python
scan_interval = 300  # 5 min entre scans
monitor_interval = 30  # 30s monitoramento
max_positions = 3  # Máx 3 posições
min_signal_strength = 40  # Força mínima
```

Para alterar, edite `bot_auto.py` antes de subir.

---

**Boa sorte! Seu bot vai rodar 24/7 multiplicando capital! 🚀💰**
