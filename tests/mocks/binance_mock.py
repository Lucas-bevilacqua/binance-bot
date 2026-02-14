"""
🎭 MOCK BINANCE CLIENT
=====================
Mock completo da API da Binance para testes isolados.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from unittest.mock import AsyncMock
import asyncio


class MockBinanceAPIException(Exception):
    """Exception simulando BinanceAPIException."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[-{code}] {message}")


class MockBinanceClient:
    """
    Mock completo do cliente Binance para testes.

    Simula:
    - Account information
    - Position information
    - Order creation/cancellation
    - Klines (candlestick data)
    - Rate limiting
    """

    def __init__(self):
        # Estado interno
        self.positions: Dict[str, Dict] = {}
        self.orders: Dict[int, Dict] = {}
        self.balance: float = 1000.0
        self.leverage: int = 20

        # Controle de rate limiting
        self.request_count: int = 0
        self.rate_limit_triggered: bool = False
        self.rate_limit_threshold: int = 1200  # Binance padrão

        # Order ID counter
        self._order_id_counter: int = 1000

        # Preços mock para símbolos comuns
        self._prices: Dict[str, float] = {
            'BTCUSDT': 43000.0,
            'ETHUSDT': 2300.0,
            'BNBUSDT': 320.0,
            'SOLUSDT': 95.0,
            'XRPUSDT': 0.55,
            'ADAUSDT': 0.50,
            'DOGEUSDT': 0.08,
            'AVAXUSDT': 35.0,
            'MATICUSDT': 0.85,
            'DOTUSDT': 7.5,
            'LINKUSDT': 14.5,
            'ATOMUSDT': 10.0,
            'NEARUSDT': 5.5,
            'APTUSDT': 9.0,
            'ARBUSDT': 1.8,
            'OPUSDT': 2.0,
            'INJUSDT': 22.0,
            'SUIUSDT': 1.5,
            'PEPEUSDT': 0.000001
        }

        # Filtros de símbolo
        self._symbol_filters: Dict[str, Dict] = {
            'BTCUSDT': {'tick_size': 0.01, 'lot_size': 0.001, 'min_notional': 5.0},
            'ETHUSDT': {'tick_size': 0.01, 'lot_size': 0.001, 'min_notional': 5.0},
            'BNBUSDT': {'tick_size': 0.01, 'lot_size': 0.001, 'min_notional': 5.0},
            'SOLUSDT': {'tick_size': 0.001, 'lot_size': 0.01, 'min_notional': 5.0},
            'XRPUSDT': {'tick_size': 0.0001, 'lot_size': 1, 'min_notional': 5.0},
            'ADAUSDT': {'tick_size': 0.0001, 'lot_size': 1, 'min_notional': 5.0},
            'DOGEUSDT': {'tick_size': 0.00001, 'lot_size': 1, 'min_notional': 5.0},
            'AVAXUSDT': {'tick_size': 0.001, 'lot_size': 0.01, 'min_notional': 5.0},
            'MATICUSDT': {'tick_size': 0.0001, 'lot_size': 1, 'min_notional': 5.0},
            'DOTUSDT': {'tick_size': 0.001, 'lot_size': 0.01, 'min_notional': 5.0},
        }

    # ========================================================================
    # ACCOUNT METHODS
    # ========================================================================

    async def futures_account(self) -> Dict:
        """
        Simula GET /fapi/v2/account.

        Returns:
            Dict com informações da conta
        """
        self.request_count += 1

        if self.rate_limit_triggered and self.request_count % 100 == 0:
            raise MockBinanceAPIException(-1003, "Too many requests")

        return {
            'totalWalletBalance': self.balance,
            'availableBalance': self.balance * 0.95,
            'maxWithdrawAmount': self.balance * 0.9
        }

    async def futures_position_information(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Simula GET /fapi/v2/positionRisk.

        Args:
            symbol: Símbolo específico ou None para todos

        Returns:
            Lista de posições
        """
        if symbol:
            if symbol in self.positions:
                pos = self.positions[symbol]
                return [{
                    'symbol': symbol,
                    'positionAmt': pos['amount'],
                    'entryPrice': pos['entry_price'],
                    'markPrice': pos.get('current_price', pos['entry_price']),
                    'unRealizedProfit': pos.get('pnl', 0.0)
                }]
            else:
                return [{
                    'symbol': symbol,
                    'positionAmt': 0,
                    'entryPrice': 0,
                    'markPrice': self._get_price(symbol),
                    'unRealizedProfit': 0
                }]
        else:
            result = []
            for sym, pos in self.positions.items():
                result.append({
                    'symbol': sym,
                    'positionAmt': pos['amount'],
                    'entryPrice': pos['entry_price'],
                    'markPrice': pos.get('current_price', pos['entry_price']),
                    'unRealizedProfit': pos.get('pnl', 0.0)
                })
            return result

    async def futures_change_leverage(self, symbol: str, leverage: int) -> Dict:
        """Simula POST /fapi/v1/leverage."""
        self.leverage = leverage
        return {'symbol': symbol, 'leverage': leverage, 'maxNotionalValue': '1000000'}

    # ========================================================================
    # ORDER METHODS
    # ========================================================================

    async def futures_create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        stopPrice: Optional[float] = None,
        **kwargs
    ) -> Dict:
        """
        Simula POST /fapi/v1/order.

        Args:
            symbol: Par de trading
            side: 'BUY' ou 'SELL'
            type: 'MARKET', 'LIMIT', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT'
            quantity: Quantidade
            price: Preço (para ordens limit)
            stopPrice: Preço de gatilho (para stop orders)

        Returns:
            Dict com ordem criada
        """
        self.request_count += 1

        # Verificar MIN_NOTIONAL
        if quantity and price:
            notional = quantity * price
            min_notional = self._get_min_notional(symbol)
            if notional < min_notional:
                raise MockBinanceAPIException(-4060, "Order would violate MIN_NOTIONAL filter")

        # Criar ordem
        order_id = self._order_id_counter
        self._order_id_counter += 1

        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': type,
            'status': 'FILLED',
            'origQty': str(quantity) if quantity else '0',
            'executedQty': str(quantity) if quantity else '0'
        }

        if price:
            order['price'] = str(price)
        if stopPrice:
            order['stopPrice'] = str(stopPrice)

        self.orders[order_id] = order

        # Atualizar posição
        if type == 'MARKET':
            self._update_position(symbol, side, quantity)

        return order

    async def futures_cancel_all_open_orders(self, symbol: str) -> Dict:
        """Simula DELETE /fapi/v1/allOpenOrders."""
        canceled = 0
        for order_id, order in list(self.orders.items()):
            if order['symbol'] == symbol and order['status'] != 'FILLED':
                order['status'] = 'CANCELED'
                canceled += 1
        return {'symbol': symbol, 'canceled': canceled}

    async def futures_get_open_orders(self, symbol: str) -> List[Dict]:
        """Simula GET /fapi/v1/openOrders."""
        return [
            order for order_id, order in self.orders.items()
            if order['symbol'] == symbol and order['status'] not in ['FILLED', 'CANCELED', 'EXPIRED']
        ]

    # ========================================================================
    # MARKET DATA METHODS
    # ========================================================================

    async def futures_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> List[List]:
        """
        Simula GET /fapi/v1/klines.

        Returns dados mock de candlestick.
        """
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta

        # Gerar dados mock
        base_price = self._get_price(symbol)
        timestamps = pd.date_range(
            end=pd.Timestamp.now(),
            periods=limit,
            freq=self._interval_to_freq(interval)
        )

        klines = []
        for ts in timestamps:
            close = base_price + (np.random.randn() * base_price * 0.001)
            high = close * (1 + abs(np.random.randn() * 0.002))
            low = close * (1 - abs(np.random.randn() * 0.002))
            open_ = close + (np.random.randn() * base_price * 0.0005)

            klines.append([
                int(ts.timestamp() * 1000),
                str(open_),
                str(high),
                str(low),
                str(close),
                str(np.random.randint(100, 1000)),
                str(int(ts.timestamp() * 1000) + 900000),
                str(np.random.randint(100, 500)),
                str(np.random.randint(50, 200)),
                str(np.random.randint(50, 150)),
                '0'
            ])

        return klines

    async def futures_symbol_ticker(self, symbol: str) -> Dict:
        """Simula 24hr ticker."""
        price = self._get_price(symbol)
        return {
            'symbol': symbol,
            'price': str(price),
            'volume': str(np.random.randint(1000000, 10000000))
        }

    # ========================================================================
    # TRADE HISTORY METHODS
    # ========================================================================

    async def futures_account_trades(
        self,
        symbol: str,
        limit: int = 1000,
        **kwargs
    ) -> List[Dict]:
        """Simula GET /fapi/v1/userTrades."""
        # Retornar trades mock
        return [
            {
                'symbol': symbol,
                'orderId': i,
                'price': str(self._get_price(symbol)),
                'qty': str(np.random.randint(1, 100)),
                'time': int(pd.Timestamp.now().timestamp() * 1000) - i * 1000,
                'commission': '0.001',
                'realizedPnl': str(np.random.randn() * 10)
            }
            for i in range(min(limit, 10))
        ]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_price(self, symbol: str) -> float:
        """Obter preço mock para símbolo."""
        return self._prices.get(symbol, 100.0)

    def _get_min_notional(self, symbol: str) -> float:
        """Obter MIN_NOTIONAL para símbolo."""
        filters = self._symbol_filters.get(symbol, {})
        return filters.get('min_notional', 5.0)

    def _update_position(self, symbol: str, side: str, quantity: float):
        """Atualizar posição após ordem preenchida."""
        price = self._get_price(symbol)

        if symbol not in self.positions:
            self.positions[symbol] = {
                'amount': 0.0,
                'entry_price': price,
                'current_price': price,
                'pnl': 0.0
            }

        # Atualizar quantidade
        if side == 'BUY':
            self.positions[symbol]['amount'] += quantity
        else:
            self.positions[symbol]['amount'] -= quantity

        # Atualizar preço médio de entrada
        pos = self.positions[symbol]
        if abs(pos['amount']) > 0:
            total_cost = pos['entry_price'] * abs(pos['amount']) + (price * quantity)
            new_amount = abs(pos['amount']) + quantity
            pos['entry_price'] = total_cost / new_amount

    # ========================================================================
    # TEST CONTROL METHODS
    # ========================================================================

    def set_balance(self, balance: float):
        """Definir saldo da conta."""
        self.balance = balance

    def set_price(self, symbol: str, price: float):
        """Definir preço mock para símbolo."""
        self._prices[symbol] = price

    def trigger_rate_limit(self, trigger: bool = True):
        """Ativar/desativar rate limit."""
        self.rate_limit_triggered = trigger

    def reset(self):
        """Resetar estado."""
        self.positions.clear()
        self.orders.clear()
        self.request_count = 0
        self.rate_limit_triggered = False
        self._order_id_counter = 1000

    @staticmethod
    def _interval_to_freq(interval: str) -> str:
        """Converter interval Binance para freq pandas."""
        mapping = {
            '1m': '1T', '3m': '3T', '5m': '5T', '15m': '15T',
            '30m': '30T', '1h': '1H', '2h': '2H', '4h': '4H',
            '6h': '6H', '8h': '8H', '12h': '12H', '1d': '1D',
            '3d': '3D', '1w': '1W', '1M': '1M'
        }
        return mapping.get(interval, '15T')


# ============================================================================
= PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_binance():
    """Fixture para uso em testes."""
    mock = MockBinanceClient()
    yield mock
    mock.reset()


@pytest.fixture
def mock_binance_with_positions():
    """Fixture com posições abertas."""
    mock = MockBinanceClient()
    mock.positions = {
        'BTCUSDT': {
            'amount': 0.1,
            'entry_price': 42000.0,
            'current_price': 42500.0,
            'pnl': 50.0
        }
    }
    yield mock
    mock.reset()


@pytest.fixture
async def async_binance_client():
    """Fixture assíncrona para testes."""
    mock = MockBinanceClient()
    yield mock
    mock.reset()


if __name__ == "__main__":
    # Testar o mock
    async def test():
        mock = MockBinanceClient()
        print("📊 Testando MockBinanceClient...")

        # Testar account
        account = await mock.futures_account()
        print(f"💰 Saldo: {account['totalWalletBalance']}")

        # Testar ordem
        order = await mock.futures_create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='MARKET',
            quantity=0.1
        )
        print(f"✅ Ordem criada: {order}")

        # Testar posições
        positions = await mock.futures_position_information()
        print(f"📈 Posições: {positions}")

        print("✅ Mock funcionando!")

    asyncio.run(test())
