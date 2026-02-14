# 🤖 COMO O BOT AUTÔNOMO FUNCIONA

## 📋 RESUMO

O **bot_master.py** é um agente de trading **100% autônomo** que:

1. ✅ **Monitora o mercado 24/7**
2. ✅ **Decide quando ENTRAR** (baseado em análise técnica)
3. ✅ **Gerencia posições automaticamente**
4. ✅ **Decide quando SAIR** (Take Profit / Stop Loss)
5. ✅ **Funciona sozinho** sem intervenção humana

---

## 🧠 COMO O BOT TOMA DECISÕES

### 1. QUANDO ENTRAR (SINAL DE COMPRA)

O bot analisa **11 pares** a cada **1 minuto** usando:

#### Indicadores Analisados:
- **EMA 9/21/50** → Tendência principal
- **RSI 14** → Sobrecompra/Sobrevenda
- **MACD** → Momentum
- **Bollinger Bands** → Volatilidade
- **Volume** → Confirmação

#### Sistema de Pontuação (0-100):
```
LONG (Compra):
├── EMA 9 > 21 > 50         = +25 pontos
├── RSI < 30 (oversold)      = +20 pontos
├── MACD positivo             = +15 pontos
├── Preço < BB inferior       = +15 pontos
└── Volume alto               = +10 pontos

TOTAL: 0-85 pontos
```

```
SHORT (Venda):
├── EMA 9 < 21 < 50         = +25 pontos
├── RSI > 70 (overbought)    = +20 pontos
├── MACD negativo             = +15 pontos
├── Preço > BB superior       = +15 pontos
└── Volume alto               = +10 pontos

TOTAL: 0-85 pontos
```

#### Regras de Entrada:
- **Score mínimo**: 45 pontos
- **Max posições simultâneas**: 2
- **Só entra se**: Score >= 45 E tendência clara (LONG/SHORT)

### 2. QUANDO SAIR (SINAL DE VENDA)

O bot monitora posições a cada **15 segundos** e decide sair quando:

#### Take Profit (Lucro):
```
LONG:  Preço atinge TP (Entry + 2.5%)
SHORT: Preço atinge TP (Entry - 2.5%)
```

#### Stop Loss (Prejuízo):
```
LONG:  Preço atinge SL (Entry - 0.8%)
SHORT: Preço atinge SL (Entry + 0.8%)
```

#### O bot MONITORA e EXECUTA automaticamente!
```python
if preco >= tp:
    fechar_posicao()  # Take Profit hit!
elif preco <= sl:
    fechar_posicao()  # Stop Loss hit!
```

---

## 🔄 CICLO DE FUNCIONAMENTO

```
┌─────────────────────────────────────────────────────────┐
│  CADA 15 SEGUNDOS                                   │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 1. Monitorar posições abertas                 │ │
│  │    - Ver PnL atual                             │ │
│  │    - Verificar se hit TP ou SL                │ │
│  │    - Fechar se necessário                      │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 2. Se posições < 2:                           │ │
│  │    - Buscar novas oportunidades                 │ │
│  │    - Analisar 11 pares                         │ │
│  │    - Encontrar melhor sinal                    │ │
│  │    - Entrar se score >= 45                     │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 3. Aguardar 15 segundos                        │ │
│  │    - Repetir ciclo                             │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 EXEMPLO DE DECISÃO

### Cenário 1: Sinal de Compra em ETHUSDT

```
Análise do Bot:
═══════════════════════════════════════════
Preço atual:    $1950
EMA 9/21/50:    9 > 21 > 50  ✅ (+25)
RSI:             28           ✅ (+20)
MACD:            Positivo     ✅ (+15)
Bollinger:        Abaixo BB    ✅ (+15)
Volume:          2x média     ✅ (+10)

SCORE TOTAL: 85/100 ✅

Decisão do Bot: "ENTRAR EM LONG"
═══════════════════════════════════════════
Entry: $1950
SL:    $1934 (-0.8%)
TP:    $2000 (+2.5%)
Risco: $0.30 (12% do capital)

✅ Ordem executada automaticamente!
```

### Cenário 2: Monitoramento de Posição

```
[14:30:15] ETHUSDT LONG | PnL: +$5.20 | Price: $1955
[14:30:30] ETHUSDT LONG | PnL: +$8.40 | Price: $1958
[14:30:45] ETHUSDT LONG | PnL: +$12.10 | Price: $1963
[14:31:00] ETHUSDT LONG | PnL: +$15.80 | Price: $1968
[14:31:15] ETHUSDT LONG | PnL: +$19.50 | Price: $1973
[14:31:30] ETHUSDT LONG | PnL: +$23.20 | Price: $1978
[14:31:45] ETHUSDT LONG | PnL: +$27.00 | Price: $1983
[14:32:00] ETHUSDT LONG | PnL: +$30.50 | Price: $1988
[14:32:15] ETHUSDT LONG | PnL: +$34.20 | Price: $1993
[14:32:30] ETHUSDT LONG | PnL: +$38.00 | Price: $1998 ✅ TP HIT!

[14:32:30] ✅ TAKE PROFIT HIT! Fechando...
[14:32:31] ✅ ETHUSDT fechada | Lucro: +$38.00
```

---

## ⚙️ CONFIGURAÇÕES DO BOT

No arquivo `.env`:

```env
# Alavancagem
ALAVANCAGEM_PADRAO=50

# Risco por operação (12% do capital)
RISCO_MAXIMO_POR_OPERACAO=0.12

# Take Profit (2.5%)
TAKE_PROFIT_PERCENTUAL=0.025

# Stop Loss (0.8%)
STOP_LOSS_PERCENTUAL=0.015
```

### No código `bot_master.py`:
```python
self.max_positions = 2           # Máx 2 posições
self.min_signal_strength = 45     # Score mínimo 45
self.monitor_interval = 15        # 15 segundos
self.scan_interval = 60          # 1 minuto
```

---

## 🚀 COMO RODAR

### Localmente:
```bash
python bot_master.py
```

### Na nuvem (Railway):
1. Subir código para GitHub
2. Conectar Railway ao repo
3. Configurar variáveis de ambiente
4. Deploy automático!

---

## 🎯 O QUE O BOT FAZ AUTOMATICAMENTE

| Ação | Automático? |
|-------|-------------|
| Analisar mercado | ✅ Sim (11 pares) |
| Calcular indicadores | ✅ Sim (EMA, RSI, MACD, BB) |
| Decidir entrada | ✅ Sim (se score >= 45) |
| Executar ordem | ✅ Sim |
| Calcular tamanho | ✅ Sim (baseado no risco) |
| Definir SL/TP | ✅ Sim (baseado em ATR) |
| Monitorar PnL | ✅ Sim (a cada 15s) |
| Fechar no TP | ✅ Sim (automático) |
| Fechar no SL | ✅ Sim (automático) |
| Gerenciar múltiplas posições | ✅ Sim (até 2) |

---

## ⚠️ RISCOS E LIMITAÇÕES

### O que o bot NÃO faz:
- ❌ Não garante lucro
- ❌ Não prevê o futuro
- ❌ Não se adapta a notícias
- ❌ Não considera fatores fundamentais

### O que o bot FAZ:
- ✅ Segue estratégia definida
- ✅ Remove emoção das decisões
- ✅ Monitora 24/7
- ✅ Executa rapidamente

---

## 📈 ESTRATÉGIA UTILIZADA

### Estratégia: Trend Following com Mean Reversion

**Entrada LONG quando:**
- Tendência de alta (EMA's bullish)
- Preço sobrevendido (RSI < 30 ou tocou BB inferior)
- Momentum favorável (MACD positivo)
- Volume confirmando

**Entrada SHORT quando:**
- Tendência de baixa (EMA's bearish)
- Preço sobrecomprado (RSI > 70 ou tocou BB superior)
- Momentum desfavorável (MACD negativo)
- Volume confirmando

**Saída:**
- Take Profit: 2.5% (risco:recompensa 3:1)
- Stop Loss: 0.8% (baseado em ATR x 1.5)

---

## 🔧 PERSONALIZAR

### Mudar número de posições:
```python
self.max_positions = 3  # 3 posições simultâneas
```

### Mudar score mínimo:
```python
self.min_signal_strength = 60  # Mais conservador
```

### Mudar pares monitorados:
```python
self.symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # Apenas 3 pares
```

### Mudar intervalo de monitoramento:
```python
self.monitor_interval = 30  # 30 segundos em vez de 15
```

---

## 📱 MONITORAR NA NUVEM

Quando o bot rodar no Railway:

1. Acesse seu projeto Railway
2. Aba "Logs" → Ver o bot funcionando em tempo real
3. Aba "Metrics" → Ver uso de CPU/RAM
4. O bot roda 24/7 sem parar!

---

**O bot é 100% autônomo e toma todas as decisões sozinho!** 🤖
