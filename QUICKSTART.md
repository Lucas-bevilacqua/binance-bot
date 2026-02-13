# 🚀 GUIA RÁPIDO - BINANCE FUTURES AGENT

## 1. CONFIGURAÇÃO INICIAL (5 MINUTOS)

### Passo 1: Instalar dependências
```bash
# Windows - Duplo clique em:
INSTALL.bat

# Ou manualmente:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Passo 2: Obter API Keys da Binance

1. Acesse: https://www.binance.com/en/my/settings/api-management
2. Clique em "Create API"
3. Dê um nome (ex: "Futures Bot")
4. **IMPORTANTE:** Marque apenas "Enable Futures"
5. **NUNCA** marque "Enable Withdrawals"
6. (Opcional) Configure restrição de IP para segurança
7. Salve suas chaves

### Passo 3: Configurar .env

Abra o arquivo `.env` e preencha:

```env
BINANCE_API_KEY=sua_chave_aqui  # Cole sua API Key
BINANCE_API_SECRET=seu_secreto_aqui  # Cole seu Secret

# Configurações (ajuste conforme preferência)
CAPITAL_INICIAL=100  # Seu capital em USDT
RISCO_MAXIMO_POR_OPERACAO=0.05  # 5% do capital por trade
ALAVANCAGEM_PADRAO=20  # Alavancagem 1-125x
```

## 2. INICIAR O AGENTE

### Opção A: Duplo clique (Windows)
```
START.bat
```

### Opção B: Terminal
```bash
venv\Scripts\activate
python binance_futures_agent.py
```

## 3. PRIMEIRO USO

Quando o bot abrir, você verá o menu:

```
[1] 💡 Pedir entrada/sinal agora
[2] 🔬 Escanear oportunidades (auto)
[3] 📊 Análise completa de par específico
...
```

### Para obter um sinal agora:

1. Digite `1` e ENTER
2. Digite `BTCUSDT` (ou deixe em branco para scan automático)
3. O bot fará análise completa e mostrará:

```
══════════════════════════════════════════════════════════════
  BTCUSDT - LONG 🚀 (Força: 75/100)
══════════════════════════════════════════════════════════════
💰 Preço de entrada: $43250.00
🎯 Targets:
   TP1: $43800.00
   TP2: $44100.00
   TP3: $44700.00
🛑 Invalidation (SL): $42800.00

📋 SINAIS CONFIRMADOS:
   📈 EMA's em ordem bullish (9 > 21 > 50)
   ✅ MACD bullish
   📊 Volume alto (2.3x média)
```

4. O bot pergunta se deseja abrir posição
5. Digite `s` para confirmar ou `n` para cancelar

## 4. COMO FUNCIONA O SISTEMA

### Score de Sinal
- **0-40**: Ignorar (sem setup claro)
- **40-60**: Fraco (esperar confirmação)
- **60-80**: Moderado (considerar entrada)
- **80-100**: Forte (entrada recomendada)

### Indicadores Usados
- **EMA 9/21/50**: Tendência principal
- **RSI 14**: Overbought/Oversold
- **MACD**: Momentum
- **Bollinger Bands**: Volatilidade
- **ATR**: Stop Loss dinâmico
- **Volume**: Confirmação

### Gestão de Risco Automática
```
Tamanho da posição = (Capital × Risco) / (Entry - Stop Loss)

Exemplo com $100 e 5% de risco:
- Risco: $5
- Entry: $43000
- SL: $42800
- Diferença: $200
- Tamanho: $5 / $200 = 0.025 BTC
```

## 5. DICAS PARA MULTIPLICAR CAPITAL

### ✅ FAZER
1. **Comece pequeno** - Teste com valores mínimos
2. **Use Testnet primeiro** - http://testnet.binancefuture.com
3. **Respeite o Stop Loss** - Nunca mova SL contra você
4. **Diversifique** - Não coloque tudo em um par
5. **Acompanhe os resultados** - Use o backtest.py

### ❌ NÃO FAZER
1. **Overtrade** - Não faça operações impulsivas
2. **Revenge trading** - Não tente recuperar perdas imediatamente
3. **Alavancagem excessiva** - Comece com 5-10x
4. **Ignorar o mercado** - Verifique notícias importantes
5. **Mudar estratégia toda hora** - Dê tempo para funcionar

## 6. FLUXO DE TRADING RECOMENDADO

```
1. Escanear oportunidades [2]
   ↓
2. Analisar os 3 melhores sinais
   ↓
3. Escolher 1-2 pares para operar
   ↓
4. Abrir posição com gerenciamento automático
   ↓
5. Monitorar com [5] - Monitorar posições
   ↓
6. Fechar no TP ou deixar rodar
```

## 7. COMANDOS ÚTEIS

| Comando | Descrição |
|---------|-----------|
| `[1]` | Pedir sinal imediato |
| `[2]` | Scan automático de 12 pares |
| `[3]` | Análise profunda de 1 par |
| `[5]` | Ver posições abertas |
| `[6]` | Fechar posição |
| `[7]` | Ver saldo |

## 8. TESTAR ANTES DE USAR CAPITAL REAL

### Backtest
```bash
python backtest.py
```

Escolha:
- Par: BTCUSDT
- Timeframe: 15m
- Dias: 30

Verá o desempenho da estratégia nos últimos 30 dias!

## 9. SOLUÇÃO DE PROBLEMAS

| Erro | Solução |
|------|---------|
| "Invalid API-key" | Verifique se a chave está correta e se "Futures" está habilitado |
| "Lot size filter" | Ajuste RISCO_MAXIMO_POR_OPERACAO ou CAPITAL_INICIAL |
| "Connection error" | Verifique sua internet ou tente VPN |
| "Permission denied" | Verifique permissões da API Key |

## 10. CONFIGURAÇÕES RECOMENDADAS

### Conservador (iniciantes)
```env
ALAVANCAGEM_PADRAO=5
RISCO_MAXIMO_POR_OPERACAO=0.02  # 2%
STOP_LOSS_PERCENTUAL=0.02
```

### Moderado (intermediários)
```env
ALAVANCAGEM_PADRAO=20
RISCO_MAXIMO_POR_OPERACAO=0.05  # 5%
STOP_LOSS_PERCENTUAL=0.015
```

### Agressivo (avançados)
```env
ALAVANCAGEM_PADRAO=50
RISCO_MAXIMO_POR_OPERACAO=0.10  # 10%
STOP_LOSS_PERCENTUAL=0.01
```

## ⚠️ AVISO FINAL

**TRADING É RISCO.** Você pode perder dinheiro.
- Comece com $10-50 em Testnet
- Teste estratégias por 1-2 semanas
- Só depois use capital real
- Nunca invista o que não pode perder

---

**Boas trades! 💰🚀**

Dúvidas? Leia o README.md completo
