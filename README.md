# 🚀 BINANCE FUTURES TRADING AGENT

Agente especializado em trading de futuros da Binance com múltiplas skills de análise técnica.

## ⚠️ AVISO IMPORTANTE

**TRADING ENVOLVE RISCOS SIGNIFICATIVOS.** Este agente foi criado para fins educacionais. Use por sua própria conta e risco. Comece com valores pequenos em conta testnet antes de usar capital real.

## 📋 RECURSOS

### Skills do Agente

1. **Análise Técnica Avançada**
   - EMA's (9, 21, 50)
   - RSI (14)
   - MACD
   - Bollinger Bands
   - ATR para Stop Loss dinâmico
   - Análise de Volume

2. **Escaneamento de Oportunidades**
   - Varredura automática de 12 pares principais
   - Filtragem por força de sinal (score 0-100)
   - Identificação de setups de alta probabilidade

3. **Gerenciamento de Posições**
   - Cálculo automático de tamanho de posição
   - Stop Loss e Take Profit baseados em ATR
   - Gestão de risco por operação

4. **Monitoramento em Tempo Real**
   - Acompanhamento de posições abertas
   - Fechamento automático em TP/SL
   - Alertas de mudança de preço

5. **Stream de Preços**
   - WebSocket para preços em tempo real
   - Atualização contínua de cotações

## 🛠️ INSTALAÇÃO

### Windows
```bash
# Execute o instalador automático
INSTALL.bat
```

### Manual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ CONFIGURAÇÃO

1. **Obter API Keys da Binance:**
   - Acesse: https://www.binance.com/en/my/settings/api-management
   - Crie uma nova API Key
   - Habilite permissão de "Futures Trading"
   - **NUNCA habilite "Withdrawal"**

2. **Configurar arquivo `.env`:**
   ```env
   BINANCE_API_KEY=sua_chave_aqui
   BINANCE_API_SECRET=seu_secreto_aqui

   CAPITAL_INICIAL=100
   RISCO_MAXIMO_POR_OPERACAO=0.05  # 5% do capital
   ALAVANCAGEM_PADRAO=20
   STOP_LOSS_PERCENTUAL=0.015  # 1.5%
   TAKE_PROFIT_PERCENTUAL=0.03  # 3%
   ```

3. **Testar na Testnet (Recomendado primeiro):**
   - Testnet: https://testnet.binancefuture.com
   - Use credenciais de teste antes de capital real

## 🎮 COMO USAR

```bash
# Ativar ambiente virtual
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Executar agente
python binance_futures_agent.py
```

### Menu Interativo

```
[1] 💡 Pedir entrada/sinal agora
    -> Análise instantânea de um par ou scan automático

[2] 🔬 Escanear oportunidades (auto)
    -> Busca setups com força >= 60/100 em 12 pares

[3] 📊 Análise completa de par específico
    -> Análise técnica detalhada com timeframe customizável

[4] 📡 Stream de preços em tempo real
    -> Monitoramento ao vivo de um par

[5] 👀 Monitorar posições abertas
    -> Acompanhar e gerenciar posições

[6] ❌ Fechar posição
    -> Fechar posição manualmente

[7] 💰 Ver saldo da conta
    -> Informações da conta futures

[8] ⚙️  Configurações
    -> Ajustar alavancagem, risco, SL/TP
```

## 📊 ESTRATÉGIAS UTILIZADAS

### Sinais de Compra (LONG)
- EMA 9 > EMA 21 > EMA 50 (tendência bullish)
- RSI < 30 (oversold) ou cruzando para cima de 50
- MACD positivo e histograma crescendo
- Preço tocando ou abaixo Bollinger Band inferior
- Volume acima da média

### Sinais de Venda (SHORT)
- EMA 9 < EMA 21 < EMA 50 (tendência bearish)
- RSI > 70 (overbought) ou cruzando para baixo de 50
- MACD negativo e histograma caindo
- Preço tocando ou acima Bollinger Band superior
- Volume acima da média

### Sistema de Score
- **0-40**: Ignorar (sem sinal claro)
- **40-60**: Fraco (esperar confirmação)
- **60-80**: Moderado (considerar entrada)
- **80-100**: Forte (entrada recomendada)

## 🎯 EXEMPLO DE USO

```
1. Execute o bot: python binance_futures_agent.py

2. Escolha [1] - Pedir entrada

3. Digite "BTCUSDT" ou ENTER para scan automático

4. Analise o sinal apresentado:
   🚀 BTCUSDT - LONG (Força: 75/100)
   💰 Preço de entrada: $43250.00
   🎯 Targets:
      TP1: $43800.00
      TP2: $44100.00
      TP3: $44700.00
   🛑 Invalidation (SL): $42800.00

5. Confirme se deseja abrir posição

6. O bot calcula tamanho, abre ordem, define SL/TP
```

## 📌 PARES SUPORTADOS

Principais criptomoedas com maior liquidez:
- BTC, ETH, BNB, SOL, XRP
- ADA, DOGE, AVAX, MATIC, DOT
- LINK, ATOM, e outros pares USDT

## 🛡️ GESTÃO DE RISCO

### Regras de Ouro
1. **Nunca arrisque mais que 5% por operação**
2. **Sempre use Stop Loss**
3. **Não faça overtrading (muitas operações)**
4. **Respeite os níveis de invalidação**
5. **Comece com alavancagem baixa (5-10x)**

### Fórmula de Tamanho de Posição
```
Quantidade = (Saldo × Risco) / (Entry - Stop Loss)

Exemplo:
- Saldo: $100
- Risco: 5% ($5)
- Entry: $43000
- SL: $42800
- Quantidade = $5 / $200 = 0.025 BTC
```

## 📱 TELEGRAM (FUTURO)

O bot pode ser integrado com Telegram para:
- Receber sinais remotamente
- Confirmar operações
- Alertas de TP/SL

Configure no `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

## ⚠️ ERROS COMUNS

### Erro: "Invalid API-key"
- Verifique se a API Key está correta
- Confirme se habilitou "Futures Trading"

### Erro: "Lot size filter"
- O lote mínimo/máximo foi calculado automaticamente
- Ajuste o risco ou capital

### TA-Lib não instala (Windows)
- O bot funciona sem TA-Lib
- Indicadores básicos ainda funcionam

## 🔧 SOLUÇÃO DE PROBLEMAS

1. **Dependências não instalam:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

2. **Conexão recusada:**
   - Verifique sua internet
   - Confirme se a Binance está online
   - Tente usar VPN

3. **Erro de permissão:**
   - Verifique as permissões da API Key
   - IP whitelist configurado corretamente

## 📚 MELHORIAS FUTURAS

- [ ] Integração com Telegram
- [ ] Backtesting de estratégias
- [ ] Machine Learning para previsões
- [ ] Estratégias de grid trading
- [ ] Arbitragem de funding rate
- [ ] Dashboard web

## 📝 DISCLAIMER

```
ESTE SOFTWARE É FORNECIDO "COMO ESTÁ", SEM GARANTIAS.
TRADING DE CRIPTOMOEDAS ENVOLVE RISCO SIGNIFICATIVO.
VOCÊ PODE PERDER TODO OU PARTE DO SEU INVESTIMENTO.

O AUTOR NÃO É RESPONSÁVEL POR QUALQUER PERDA FINANCEIRA.
USE POR SUA CONTA E RISCO.
```

## 📄 LICENÇA

Este projeto é de código aberto e pode ser usado/modificado livremente.

---

**Feito com Python e ❤️ para a comunidade crypto**

*Lucas - 2026*
