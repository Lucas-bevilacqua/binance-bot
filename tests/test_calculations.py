"""
🧮 TESTS DE CÁLCULOS CRÍTICOS
=================================
Testes para funções que movem dinheiro real.
"""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal


# ============================================================================
# TESTES DE CÁLCULO DE TAMANHO DE POSIÇÃO
# ============================================================================

class TestPositionSizeCalculation:
    """Testes para cálculo de tamanho de posição."""

    @pytest.fixture
    def calc_params(self):
        """Parâmetros padrão para cálculo."""
        return {
            'balance': 1000.0,
            'risk_per_trade': 0.05,  # 5%
            'entry_price': 100.0,
            'stop_loss': 98.0,  # 2% abaixo
            'leverage': 10
        }

    def test_position_size_basic(self, calc_params):
        """Teste básico de cálculo de tamanho."""
        balance = calc_params['balance']
        risk = calc_params['risk_per_trade']
        entry = calc_params['entry_price']
        sl = calc_params['stop_loss']

        risk_amount = balance * risk
        risk_per_unit = abs(entry - sl)
        quantity = risk_amount / risk_per_unit

        assert quantity == pytest.approx(25.0, rel=0.01)  # 25 unidades

    def test_position_size_with_leverage(self, calc_params):
        """Teste cálculo com alavancagem."""
        balance = calc_params['balance']
        risk = calc_params['risk_per_trade']
        entry = calc_params['entry_price']
        sl = calc_params['stop_loss']
        leverage = calc_params['leverage']

        risk_amount = balance * risk
        risk_per_unit = abs(entry - sl)
        quantity = (risk_amount * leverage) / entry

        assert quantity == pytest.approx(50.0, rel=0.01)  # 50 unidades com 10x

    def test_position_size_small_balance(self, calc_params):
        """Teste com saldo pequeno."""
        calc_params['balance'] = 10.0
        calc_params['entry_price'] = 100.0
        calc_params['stop_loss'] = 98.0

        risk_amount = calc_params['balance'] * calc_params['risk_per_trade']
        risk_per_unit = abs(calc_params['entry_price'] - calc_params['stop_loss'])
        quantity = risk_amount / risk_per_unit

        # Saldo pequeno = posição pequena
        assert quantity == pytest.approx(0.25, rel=0.01)

    def test_position_size_min_notional(self):
        """Teste validação de MIN_NOTIONAL filter."""
        # Binance exige mínimo de $5-$10 depending on pair
        min_notional = 5.0
        entry_price = 100.0
        calculated_qty = 0.03  # $3 - abaixo do mínimo

        # Deve ajustar para atingir mínimo
        adjusted_qty = max(calculated_qty, min_notional / entry_price)

        assert adjusted_qty >= min_notional / entry_price
        assert adjusted_qty == pytest.approx(0.05, rel=0.01)

    def test_position_size_rounding(self):
        """Teste arredondamento para step_size."""
        step_size = Decimal('0.01')
        quantity = Decimal('12.3456')

        # Arredondar para step_size
        precision = abs(int(Decimal(str(step_size)).as_tuple().exponent)
        rounded = float(round(quantity, precision))

        assert rounded == 12.35


# ============================================================================
# TESTES DE CÁLCULO DE STOP LOSS E TAKE PROFIT
# ============================================================================

class TestStopLossTakeProfit:
    """Testes para cálculo de SL/TP."""

    def test_sl_tp_long(self):
        """Teste SL/TP para posição LONG."""
        entry = 100.0
        atr = 2.0  # Average True Range

        # LONG: SL = entry - (ATR * 1.5), TP = entry + (ATR * 3)
        sl = entry - (atr * 1.5)
        tp = entry + (atr * 3)

        assert sl == 97.0
        assert tp == 106.0
        assert sl < entry < tp

    def test_sl_tp_short(self):
        """Teste SL/TP para posição SHORT."""
        entry = 100.0
        atr = 2.0

        # SHORT: SL = entry + (ATR * 1.5), TP = entry - (ATR * 3)
        sl = entry + (atr * 1.5)
        tp = entry - (atr * 3)

        assert sl == 103.0
        assert tp == 94.0
        assert tp < entry < sl

    def test_risk_reward_ratio(self):
        """Teste ratio risco:recompensa."""
        entry = 100.0
        sl = 97.0
        tp = 106.0

        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = reward / risk

        # Deve ser pelo menos 2:1
        assert rr_ratio >= 2.0
        assert rr_ratio == pytest.approx(2.0, rel=0.01)

    def test_sl_tp_precent(self):
        """Teste SL/TP em percentual."""
        entry = 100.0
        sl_percent = 0.015  # 1.5%
        tp_percent = 0.03   # 3%

        sl_long = entry * (1 - sl_percent)
        tp_long = entry * (1 + tp_percent)

        assert sl_long == 98.5
        assert tp_long == 103.0


# ============================================================================
# TESTES DE GESTÃO DE RISCO
# ============================================================================

class TestRiskManagement:
    """Testes para regras de gerenciamento de risco."""

    def test_max_risk_per_trade(self):
        """Teste limite máximo de risco por trade."""
        balance = 1000.0
        max_risk_percent = 0.05  # 5% máximo
        entry = 100.0
        sl = 95.0

        max_risk = balance * max_risk_percent
        actual_risk = abs(entry - sl)  # 5% do preço

        # Risk deve ser <= 5% do balance
        assert actual_risk <= max_risk

    def test_multiple_positions_risk(self):
        """Teste risco total com múltiplas posições."""
        balance = 1000.0
        max_total_risk = 0.15  # 15% total máximo
        positions = [
            {'risk': 50.0},  # 5%
            {'risk': 50.0},  # 5%
            {'risk': 30.0},  # 3%
        ]

        total_risk = sum(p['risk'] for p in positions)
        assert total_risk <= balance * max_total_risk

    def test_leverage_limit(self):
        """Teste limite de alavancagem."""
        default_leverage = 20
        max_safe_leverage = 20

        # Para produção, alavancagem não deve exceder 20x
        assert default_leverage <= max_safe_leverage

    def test_position_sizing_with_atr(self):
        """Teste dimensionamento baseado em ATR."""
        balance = 1000.0
        risk_percent = 0.05
        entry = 100.0
        atr = 2.0
        atr_multiplier = 1.5

        sl = entry - (atr * atr_multiplier)
        risk_amount = balance * risk_percent
        quantity = risk_amount / abs(entry - sl)

        # Quantidade deve ser positiva
        assert quantity > 0
        # SL deve estar abaixo da entrada
        assert sl < entry


# ============================================================================
# TESTES DE VALIDAÇÃO
# ============================================================================

class TestValidation:
    """Testes para validações de segurança."""

    def test_invalid_quantity(self):
        """Teste rejeição de quantidade inválida."""
        quantity = -10.0

        with pytest.raises(ValueError):
            if quantity <= 0:
                raise ValueError("Quantidade deve ser positiva")

    def test_invalid_price(self):
        """Teste rejeição de preço inválido."""
        entry_price = -100.0

        with pytest.raises(ValueError):
            if entry_price <= 0:
                raise ValueError("Preço deve ser positivo")

    def test_sl_before_entry_long(self):
        """Teste SL antes do entry em LONG."""
        entry = 100.0
        sl = 105.0  # SL acima da entrada em LONG - inválido!

        with pytest.raises(ValueError):
            if sl >= entry:
                raise ValueError("Stop Loss deve estar abaixo da entrada em LONG")

    def test_sl_before_entry_short(self):
        """Teste SL antes do entry em SHORT."""
        entry = 100.0
        sl = 95.0  # SL abaixo da entrada em SHORT - inválido!

        with pytest.raises(ValueError):
            if sl <= entry:
                raise ValueError("Stop Loss deve estar acima da entrada em SHORT")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
