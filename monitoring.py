"""
📊 MONITORAMENTO E MÉTRICAS
============================
Sistema de monitoramento com métricas e alertas.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from logging_config import get_logger, TradingLogger


# ============================================================================
= DATA CLASSES
# ============================================================================

@dataclass
class TradeMetrics:
    """Métricas de um trade específico."""
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    duration_seconds: Optional[float] = None
    reason: Optional[str] = None


@dataclass
class DailyMetrics:
    """Métricas diárias agregadas."""
    date: str
    trade_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0

    def calculate_metrics(self) -> Dict:
        """Calcular métricas derivadas."""
        if self.trade_count == 0:
            return {}

        win_rate = self.winning_trades / self.trade_count
        avg_pnl = self.total_pnl / self.trade_count

        return {
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': self.total_pnl,
            'max_win': self.max_win,
            'max_loss': self.max_loss
        }


@dataclass
class AlertConfig:
    """Configuração de alertas."""
    enabled: bool = True
    large_loss_threshold: float = -10.0  # USDT
    large_profit_threshold: float = 20.0  # USDT
    position_stuck_hours: int = 24
    api_down_minutes: int = 5
    telegram_enabled: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


# ============================================================================
= MONITOR CLASS
# ============================================================================

class TradingMonitor:
    """
    Monitor de trading com métricas e alertas.

    Acompanha:
    - Trades individuais
    - Métricas diárias
    - Posições "stuck"
    - Performance
    """

    def __init__(self, alert_config: AlertConfig = None):
        self.logger = get_logger('monitor')
        self.trading_logger = TradingLogger()
        self.alert_config = alert_config or AlertConfig()

        # Estado interno
        self._trades: List[TradeMetrics] = []
        self._daily_metrics: Dict[str, DailyMetrics] = defaultdict(
            lambda: DailyMetrics(date=datetime.now().strftime('%Y-%m-%d'))
        )
        self._position_timestamps: Dict[str, datetime] = {}
        self._api_down_since: Optional[datetime] = None

    # ========================================================================
    # REGISTRO DE EVENTOS
    # ========================================================================

    def register_trade_open(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        sl_price: float,
        tp_price: float
    ):
        """Registrar abertura de trade."""
        trade = TradeMetrics(
            symbol=symbol,
            side=side,
            entry_price=entry_price
        )
        self._trades.append(trade)
        self._position_timestamps[symbol] = datetime.now()

        self.trading_logger.trade_opened(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price
        )

    def register_trade_close(
        self,
        symbol: str,
        pnl: float,
        pnl_percent: float,
        reason: str = 'MANUAL'
    ):
        """Registrar fechamento de trade."""
        # Buscar trade aberto
        trade = next((t for t in self._trades if t.symbol == symbol and t.exit_price is None), None)

        if trade:
            trade.exit_price = trade.entry_price * (1 + pnl_percent / 100)
            trade.pnl = pnl
            trade.pnl_percent = pnl_percent
            trade.reason = reason

            # Atualizar métricas diárias
            today = datetime.now().strftime('%Y-%m-%d')
            daily = self._daily_metrics[today]
            daily.trade_count += 1
            daily.total_pnl += pnl

            if pnl > 0:
                daily.winning_trades += 1
                daily.max_win = max(daily.max_win, pnl)
            else:
                daily.losing_trades += 1
                daily.max_loss = min(daily.max_loss, pnl)

            # Remover de posições ativas
            if symbol in self._position_timestamps:
                del self._position_timestamps[symbol]

            self.trading_logger.trade_closed(symbol, pnl, pnl_percent, reason)

            # Verificar alertas
            self._check_trade_alerts(trade)

    def register_position_update(
        self,
        symbol: str,
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_percent: float
    ):
        """Registrar atualização de posição."""
        self.trading_logger.position_update(
            symbol=symbol,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent
        )

        # Verificar posição "stuck"
        if symbol in self._position_timestamps:
            duration = datetime.now() - self._position_timestamps[symbol]
            hours = duration.total_seconds() / 3600

            if hours > self.alert_config.position_stuck_hours:
                self._alert_position_stuck(symbol, hours)

    # ========================================================================
    # MÉTRICAS
    # ========================================================================

    def get_daily_metrics(self, date: str = None) -> Optional[DailyMetrics]:
        """Obter métricas diárias."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self._daily_metrics.get(date)

    def get_weekly_metrics(self) -> Dict:
        """Obter métricas semanais."""
        today = datetime.now()
        week_ago = today - timedelta(days=7)

        weekly_trades = [
            t for t in self._trades
            if t.exit_price and today - timedelta(days=7) <= week_ago
        ]

        if not weekly_trades:
            return {}

        total_pnl = sum(t.pnl for t in weekly_trades if t.pnl)
        wins = sum(1 for t in weekly_trades if t.pnl and t.pnl > 0)

        return {
            'trade_count': len(weekly_trades),
            'total_pnl': total_pnl,
            'win_rate': wins / len(weekly_trades) if weekly_trades else 0,
            'avg_pnl': total_pnl / len(weekly_trades) if weekly_trades else 0
        }

    def get_overall_metrics(self) -> Dict:
        """Obter métricas globais."""
        closed_trades = [t for t in self._trades if t.exit_price]

        if not closed_trades:
            return {'total_trades': 0}

        total_pnl = sum(t.pnl for t in closed_trades)
        wins = sum(1 for t in closed_trades if t.pnl > 0)

        return {
            'total_trades': len(closed_trades),
            'total_pnl': total_pnl,
            'win_rate': wins / len(closed_trades),
            'avg_pnl': total_pnl / len(closed_trades)
        }

    # ========================================================================
    # ALERTAS
    # ========================================================================

    def _check_trade_alerts(self, trade: TradeMetrics):
        """Verificar alertas para trade fechado."""
        if not self.alert_config.enabled:
            return

        # Perda grande
        if (trade.pnl and trade.pnl < 0 and
            trade.pnl < self.alert_config.large_loss_threshold):
            self._alert_large_loss(trade)

        # Lucro grande
        if (trade.pnl and trade.pnl > 0 and
            trade.pnl > self.alert_config.large_profit_threshold):
            self._alert_large_profit(trade)

    def _alert_large_loss(self, trade: TradeMetrics):
        """Alertar sobre perda grande."""
        self.logger.warning(
            "large_loss_alert",
            symbol=trade.symbol,
            pnl=trade.pnl,
            pnl_percent=trade.pnl_percent,
            threshold=self.alert_config.large_loss_threshold
        )

        # TODO: Enviar Telegram se configurado
        if self.alert_config.telegram_enabled:
            self._send_telegram_alert(
                f"⚠️ ALERTA: Perda grande em {trade.symbol}\n"
                f"PnL: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)\n"
                f"Threshold: ${self.alert_config.large_loss_threshold}"
            )

    def _alert_large_profit(self, trade: TradeMetrics):
        """Alertar sobre lucro grande."""
        self.logger.info(
            "large_profit_alert",
            symbol=trade.symbol,
            pnl=trade.pnl,
            pnl_percent=trade.pnl_percent,
            threshold=self.alert_config.large_profit_threshold
        )

    def _alert_position_stuck(self, symbol: str, hours: float):
        """Alertar posição aberta há muito tempo."""
        self.logger.warning(
            "position_stuck_alert",
            symbol=symbol,
            duration_hours=hours,
            message=f"Posição {symbol} aberta há {hours:.1f} horas"
        )

    def _send_telegram_alert(self, message: str):
        """Enviar alerta via Telegram."""
        if not self.alert_config.telegram_enabled:
            return

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.alert_config.telegram_token}/sendMessage"
            data = {
                'chat_id': self.alert_config.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()

        except Exception as e:
            self.logger.error("telegram_send_failed", error=str(e))

    # ========================================================================
    # REPORTS
    # ========================================================================

    def generate_daily_report(self, date: str = None) -> Dict:
        """Gerar relatório diário."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        daily = self.get_daily_metrics(date)
        if not daily or daily.trade_count == 0:
            return {'date': date, 'message': 'No trades'}

        metrics = daily.calculate_metrics()

        return {
            'date': date,
            'trade_count': daily.trade_count,
            'winning_trades': daily.winning_trades,
            'losing_trades': daily.losing_trades,
            'win_rate': metrics.get('win_rate', 0),
            'total_pnl': daily.total_pnl,
            'avg_pnl': metrics.get('avg_pnl', 0),
            'max_win': daily.max_win,
            'max_loss': daily.max_loss
        }

    def log_daily_summary(self, date: str = None):
        """Log resumo diário."""
        report = self.generate_daily_report(date)
        self.trading_logger.daily_summary(**report)


# ============================================================================
= SINGLETON
# ============================================================================

_monitor: Optional[TradingMonitor] = None


def get_monitor() -> TradingMonitor:
    """Obter instância singleton do monitor."""
    global _monitor
    if _monitor is None:
        # Ler configuração de variáveis de ambiente
        alert_config = AlertConfig(
            enabled=os.getenv('ALERTS_ENABLED', 'true').lower() == 'true',
            large_loss_threshold=float(os.getenv('ALERT_LARGE_LOSS', '-10')),
            large_profit_threshold=float(os.getenv('ALERT_LARGE_PROFIT', '20')),
            position_stuck_hours=int(os.getenv('ALERT_POSITION_STUCK_HOURS', '24')),
            telegram_enabled=os.getenv('TELEGRAM_BOT_TOKEN') is not None,
            telegram_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID')
        )

        _monitor = TradingMonitor(alert_config)
    return _monitor
