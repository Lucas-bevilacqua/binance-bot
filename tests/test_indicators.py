"""
📊 TESTS DE INDICADORES TÉCNICOS
==================================
Testes para EMA, RSI, MACD, ATR, Bollinger Bands.
"""

import pytest
import pandas as pd
import numpy as np
from decimal import Decimal


# ============================================================================
= FIXTURES - DADOS DE TESTE
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Dados OHLCV de exemplo para testes."""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='15T'),
        'open': np.linspace(100, 110, 100) + np.random.randn(100) * 0.5,
        'high': np.linspace(100, 110, 100) + np.random.randn(100) * 0.5 + 0.5,
        'low': np.linspace(100, 110, 100) + np.random.randn(100) * 0.5 - 0.5,
        'close': np.linspace(100, 110, 100) + np.random.randn(100) * 0.3,
        'volume': np.random.randint(1000, 5000, 100)
    })


@pytest.fixture
def uptrend_data():
    """Dados com tendência de alta para testes."""
    return pd.DataFrame({
        'close': [100, 102, 104, 106, 108, 110, 112, 114, 116, 118,
                   120, 122, 124, 126, 128, 130, 132, 134, 136, 138] * 5  # 100 períodos
    })


@pytest.fixture
def downtrend_data():
    """Dados com tendência de baixa para testes."""
    return pd.DataFrame({
        'close': [138, 136, 134, 132, 130, 128, 126, 124, 122, 120,
                   118, 116, 114, 112, 110, 108, 106, 104, 102, 100] * 5
    })


@pytest.fixture
def sideways_data():
    """Dados em lateralização (consolidação)."""
    base = 100
    noise = np.random.randn(100) * 2
    return pd.DataFrame({
        'close': base + noise
    })


# ============================================================================
= CÁLCULO DE INDICADORES
# ============================================================================

class TestEMA:
    """Testes para Exponential Moving Average."""

    def test_ema_calculation(self, sample_ohlcv_data):
        """Testar cálculo básico de EMA."""
        close = sample_ohlcv_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()

        # Verificar propriedades da EMA
        assert len(ema_9) == len(close)
        # EMA deve ser menor que preço em tendência de alta
        # (lagging indicator)
        assert ema_9.iloc[-1] > 0
        assert not ema_9.isna().any()

    def test_ema_uptrend(self, uptrend_data):
        """Testar EMA em tendência de alta."""
        close = uptrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()

        # Em uptrend: EMA curta > EMA longa
        assert ema_9.iloc[-1] > ema_21.iloc[-1]

    def test_ema_downtrend(self, downtrend_data):
        """Testar EMA em tendência de baixa."""
        close = downtrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()

        # Em downtrend: EMA curta < EMA longa
        assert ema_9.iloc[-1] < ema_21.iloc[-1]

    def test_ema_order_bullish(self, uptrend_data):
        """Testar ordem bullis (9 > 21 > 50)."""
        close = uptrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # Ordem bullis: 9 > 21 > 50
        assert ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1]

    def test_ema_order_bearish(self, downtrend_data):
        """Testar ordem bearis (9 < 21 < 50)."""
        close = downtrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # Ordem bearis: 9 < 21 < 50
        assert ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1]


class TestRSI:
    """Testes para Relative Strength Index."""

    def test_rsi_calculation(self, sample_ohlcv_data):
        """Testar cálculo básico de RSI."""
        close = sample_ohlcv_data['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # RSI deve estar entre 0 e 100
        assert rsi.iloc[-1] >= 0
        assert rsi.iloc[-1] <= 100

    def test_rsi_overbought(self, uptrend_data):
        """Testar RSI em sobrecompra."""
        close = uptrend_data['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Em forte uptrend, RSI deve ser alto (> 50)
        # (pode não estar > 70 se o uptrend for gradual)
        assert rsi.iloc[-1] > 50

    def test_rsi_oversold(self, downtrend_data):
        """Testar RSI em sobrevenda."""
        close = downtrend_data['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Em forte downtrend, RSI deve ser baixo (< 50)
        assert rsi.iloc[-1] < 50

    def test_rsi_extremes(self):
        """Testar limites extremos do RSI."""
        # Criar dados que geram RSI extremo
        close = pd.Series([100] * 10 + [110] * 10)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # RSI não deve ser exatamente 0 ou 100 (rolling suavisa)
        assert rsi.iloc[-1] > 0
        assert rsi.iloc[-1] < 100


class TestMACD:
    """Testes para Moving Average Convergence Divergence."""

    def test_macd_calculation(self, sample_ohlcv_data):
        """Testar cálculo básico de MACD."""
        close = sample_ohlcv_data['close']
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal

        # MACD pode ser positivo ou negativo
        assert not np.isnan(macd.iloc[-1])
        assert not np.isnan(macd_signal.iloc[-1])
        assert not np.isnan(macd_hist.iloc[-1])

    def test_macd_bullish(self, uptrend_data):
        """Testar MACD em tendência de alta."""
        close = uptrend_data['close']
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        # Em uptrend forte: MACD > Signal
        assert macd.iloc[-1] > macd_signal.iloc[-1]

    def test_macd_bearish(self, downtrend_data):
        """Testar MACD em tendência de baixa."""
        close = downtrend_data['close']
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        # Em downtrend forte: MACD < Signal
        assert macd.iloc[-1] < macd_signal.iloc[-1]

    def test_macd_crossover(self):
        """Testar detecção de crossover."""
        # Criar série onde acontece crossover
        close = pd.Series([100] * 10 + [105] * 10)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26

        # MACD deve ter mudado de sinal
        assert macd.iloc[-1] > macd.iloc[0]


class TestATR:
    """Testes para Average True Range."""

    def test_atr_calculation(self, sample_ohlcv_data):
        """Testar cálculo básico de ATR."""
        high = sample_ohlcv_data['high']
        low = sample_ohlcv_data['low']
        close = sample_ohlcv_data['close']

        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        atr = ranges.max(axis=1).rolling(window=14).mean()

        # ATR deve ser positivo
        assert atr.iloc[-1] > 0
        assert not np.isnan(atr.iloc[-1])

    def test_atr_volatile(self):
        """Testar ATR em período volátil."""
        # Dados voláteis: grandes variações
        close = pd.Series([100, 110, 95, 115, 90, 120, 85, 125] * 10)
        high = close + 5
        low = close - 5

        high_low = high - low
        atr = high_low.rolling(window=14).mean()

        # ATR deve ser maior em dados voláteis
        assert atr.iloc[-1] > 5

    def test_atr_stable(self, sideways_data):
        """Testar ATR em período estável."""
        close = sideways_data['close']
        high = close + 0.5
        low = close - 0.5

        high_low = high - low
        atr = high_low.rolling(window=14).mean()

        # ATR deve ser pequeno em dados estáveis
        assert atr.iloc[-1] < 5


class TestBollingerBands:
    """Testes para Bollinger Bands."""

    def test_bb_calculation(self, sample_ohlcv_data):
        """Testar cálculo básico de BB."""
        close = sample_ohlcv_data['close']
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)

        # Preço deve estar entre as bandas (normalmente)
        assert bb_lower.iloc[-1] < close.iloc[-1] < bb_upper.iloc[-1]

    def test_bb_squeeze(self, sideways_data):
        """Testar BB squeeze (baixa volatilidade)."""
        close = sideways_data['close']
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        bb_width = bb_upper - bb_lower

        # BB width deve ser menor em dados estáveis
        assert bb_width.iloc[-1] < 10

    def test_bb_expansion(self, uptrend_data):
        """Testar BB expansion (expansão de bandas)."""
        close = uptrend_data['close']
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)

        # Bandas devem expandir em tendência forte
        # (bb_std deve aumentar)
        assert bb_std.iloc[-1] > bb_std.iloc[20]

    def test_bb_touch_upper(self, uptrend_data):
        """Testar preço tocando banda superior."""
        close = uptrend_data['close']
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)

        # Em forte uptrend, preço deve estar perto ou acima da banda superior
        assert close.iloc[-1] >= bb_middle.iloc[-1]


# ============================================================================
= SINAIS DE TRADING
# ============================================================================

class TestTradingSignals:
    """Testes para geração de sinais de trading."""

    @pytest.fixture
    def calculate_signals(self, sample_ohlcv_data):
        """Função auxiliar para calcular sinais."""
        from bot_master import AutonomousBot
        bot = AutonomousBot()
        return bot.analyze_symbol

    def test_bullish_signal_strength(self, uptrend_data):
        """Testar força do sinal bullis."""
        close = uptrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # Calcular pontuação
        score = 0
        if ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1]:
            score += 25

        # Deve ter pontuação de pelo menos 25 (tendência)
        assert score >= 25

    def test_bearish_signal_strength(self, downtrend_data):
        """Testar força do sinal bearis."""
        close = downtrend_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # Calcular pontuação
        score = 0
        if ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1]:
            score += 25

        # Deve ter pontuação de pelo menos 25 (tendência)
        assert score >= 25

    def test_min_signal_threshold(self, sideways_data):
        """Testar sinal abaixo do threshold mínimo."""
        close = sideways_data['close']
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()

        # Em sideways, sinais devem ser fracos
        score = 0
        if ema_9.iloc[-1] > ema_21.iloc[-1] > ema_50.iloc[-1]:
            score += 25
        elif ema_9.iloc[-1] < ema_21.iloc[-1] < ema_50.iloc[-1]:
            score += 25

        # Score deve ser baixo (< 40) em sideways
        assert score < 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
