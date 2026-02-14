# 🚀 Deploy no Fly.io - Guia Completo

## 📋 Pré-requisitos

1. **Instalar o flyctl**
```bash
# Windows (PowerShell)
powershell -c "irm https://fly.io/install.ps1 | iex"

# Linux/Mac
curl -L https://fly.io/install.sh | sh
```

2. **Criar conta no Fly.io**
   - Acesse: https://fly.io
   - Faça signup com GitHub ou email
   - Confirme o email

---

## 🔧 Passo 1: Configurar e Fazer Deploy

### 1.1 Login no Fly.io
```bash
flyctl auth login
```
Isso abrirá o navegador para fazer login.

### 1.2 Inicializar o app
```bash
cd C:\Users\lucas\Documents\Crypto
flyctl launch
```

**Responda as perguntas:**
- **App name**: `binance-trading-bot` (ou outro nome)
- **Select region**: `Amsterdam (ams)` ← IMPORTANTE!
- **Would you like to setup a database?**: `No`

### 1.3 Configurar variáveis de ambiente
No painel do Fly.io ou via comando:

```bash
flyctl secrets set BINANCE_API_KEY=sua_chave_aqui
flyctl secrets set BINANCE_API_SECRET=sua_secret_aqui
flyctl secrets set ALAVANCAGEM_PADRAO=50
flyctl secrets set RISCO_MAXIMO_POR_OPERACAO=0.12
flyctl secrets set TAKE_PROFIT_PERCENTUAL=0.025
flyctl secrets set STOP_LOSS_PERCENTUAL=0.015
```

### 1.4 Fazer o deploy
```bash
flyctl deploy
```

---

## 🌍 Passo 2: Obter o IP Fixo

### 2.1 Verificar o IP do app
```bash
flyctl ips list
```

Você verá algo como:
```
TYPE    IPV4                                   IPV6
v4      37.16.10.123                           ...
```

### 2.2 Adicionar IP na Binance
1. Acesse: https://www.binance.com/en/my/settings/api-management
2. Edite suas restrições de IP
3. Adicione o IP que apareceu (ex: `37.16.10.123`)

---

## 🔍 Passo 3: Monitorar o Bot

### Ver logs em tempo real
```bash
flyctl logs
```

### Ver status do app
```bash
flyctl status
```

### Reiniciar o bot
```bash
flyctl apps restart binance-trading-bot
```

### Abrir shell no servidor
```bash
flyctl ssh console
```

---

## 📝 Comandos Úteis

| Comando | Descrição |
|---------|-----------|
| `flyctl deploy` | Fazer novo deploy |
| `flyctl logs` | Ver logs em tempo real |
| `flyctl logs --tail 100` | Ver últimas 100 linhas |
| `flyctl apps restart` | Reiniciar o app |
| `flyctl ips list` | Listar IPs |
| `flyctl status` | Status do app |
| `flyctl scale count 1` | Garantir 1 instância rodando |
| `flyctl secrets list` | Listar variáveis de ambiente |

---

## ⚠️ Troubleshooting

### Bot caindo (crash loop)
```bash
flyctl logs --tail 50
```
Verifique os logs para identificar o erro.

### Precisa trocar de região?
```bash
flyctl regions set ams
flyctl deploy
```

### Atualizar código
```bash
git add .
git commit -m "Atualização"
git push
flyctl deploy
```

---

## 💰 Custos

**Plano Free do Fly.io:**
- 3 VMs pequenas (256MB RAM, 1 CPU)
- 160GB de transferência/mês
- Perfeitamente suficiente para o bot!

Se precisar de mais recursos:
- Plano pago inicia em ~$5/mês

---

## ✅ Checklist

- [ ] Instalado flyctl
- [ ] Criado app com região Amsterdam (ams)
- [ ] Configurado variáveis de ambiente
- [ ] Feito deploy com sucesso
- [ ] Obtido IP fixo
- [ ] Adicionado IP na Binance
- [ ] Bot rodando sem erros

---

**Regiões permitidas pela Binance (fora dos EUA):**
- `ams` - Amsterdã, Holanda ⭐
- `fra` - Frankfurt, Alemanha
- `lhr` - Londres, UK
- `gru` - São Paulo, Brasil
- `hkg` - Hong Kong
- `sin` - Singapura
- `syd` - Sydney, Austrália
- `nrt` - Tóquio, Japão
