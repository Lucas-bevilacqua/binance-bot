"""
📋 STRUCTLOG CONFIGURATION
==========================
Logging estruturado para Binance Bot.
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)


# ============================================================================
= LOG LEVELS
# ============================================================================

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


# ============================================================================
= CUSTOM FORMATTERS
# ============================================================================

def add_color(logger, method_name, event_dict):
    """Adicionar cores aos logs baseado no level."""
    level = event_dict.get('level', 'INFO')
    message = event_dict.get('event', '')

    if level == 'DEBUG':
        event_dict['color'] = Fore.CYAN
    elif level == 'INFO':
        event_dict['color'] = Fore.GREEN
    elif level == 'WARNING':
        event_dict['color'] = Fore.YELLOW
    elif level == 'ERROR':
        event_dict['color'] = Fore.RED
    elif level == 'CRITICAL':
        event_dict['color'] = Fore.RED + Style.BRIGHT

    return event_dict


def format_timestamp(logger, method_name, event_dict):
    """Formatar timestamp de forma legível."""
    timestamp = event_dict.get('timestamp')
    if timestamp:
        event_dict['timestamp'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return event_dict


def trade_events_formatter(logger, method_name, event_dict):
    """Formatador especial para eventos de trading."""
    event = event_dict.get('event', '')

    # Emojis para eventos específicos
    if 'trade_opened' in event:
        event_dict['emoji'] = '🚀'
    elif 'trade_closed' in event:
        event_dict['emoji'] = '✅'
    elif 'stop_loss' in event:
        event_dict['emoji'] = '🛑'
    elif 'take_profit' in event:
        event_dict['emoji'] = '🎯'
    elif 'error' in event.lower():
        event_dict['emoji'] = '❌'
    elif 'warning' in event.lower():
        event_dict['emoji'] = '⚠️'
    else:
        event_dict['emoji'] = '📊'

    return event_dict


# ============================================================================
= CONFIGURAÇÃO
# ============================================================================

def configure_logging(log_level: str = 'INFO', log_file: str = None):
    """
    Configurar structlog para o bot.

    Args:
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Arquivo para salvar logs (opcional)
    """
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)

    # Configurar logging padrão
    logging.basicConfig(
        format="%(message)s",
        level=level,
        stream=sys.stdout
    )

    # Processadores de logs
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_color,
        trade_events_formatter,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Renderer baseado em se tem terminal
    if sys.stdout.isatty():
        # Terminal colorido
        processors.append(structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback
        ))
    else:
        # JSON para logs em arquivo
        processors.append(structlog.processors.JSONRenderer())

    # Configurar structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Adicionar file handler se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)

        # Criar logger específico para arquivo
        file_logger = logging.getLogger('file_logger')
        file_logger.addHandler(file_handler)
        file_logger.setLevel(level)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Obter logger configurado.

    Args:
        name: Nome do logger

    Returns:
        Logger configurado com structlog
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# ============================================================================
= LOGGER ESPECIALIZADOS
# ============================================================================

class TradingLogger:
    """Logger especializado para eventos de trading."""

    def __init__(self, name: str = 'binance_bot'):
        self.logger = get_logger(name)
        self._trade_count = 0
        self._profit_count = 0
        self._loss_count = 0

    def trade_opened(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        sl_price: float,
        tp_price: float
    ):
        """Log quando trade é aberto."""
        self._trade_count += 1
        self.logger.info(
            "trade_opened",
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            trade_count=self._trade_count
        )

    def trade_closed(
        self,
        symbol: str,
        pnl: float,
        pnl_percent: float,
        reason: str = 'MANUAL'
    ):
        """Log quando trade é fechado."""
        if pnl > 0:
            self._profit_count += 1
        else:
            self._loss_count += 1

        self.logger.info(
            "trade_closed",
            symbol=symbol,
            pnl=pnl,
            pnl_percent=pnl_percent,
            reason=reason,
            profit_count=self._profit_count,
            loss_count=self._loss_count,
            win_rate=self._profit_count / self._trade_count if self._trade_count > 0 else 0
        )

    def position_update(
        self,
        symbol: str,
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_percent: float
    ):
        """Log atualização de posição."""
        self.logger.debug(
            "position_update",
            symbol=symbol,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent
        )

    def stop_loss_hit(self, symbol: str, price: float, pnl: float):
        """Log quando SL é atingido."""
        self.logger.warning(
            "stop_loss_hit",
            symbol=symbol,
            price=price,
            pnl=pnl,
            pnl_color='red' if pnl < 0 else 'green'
        )

    def take_profit_hit(self, symbol: str, price: float, pnl: float):
        """Log quando TP é atingido."""
        self.logger.info(
            "take_profit_hit",
            symbol=symbol,
            price=price,
            pnl=pnl,
            pnl_color='green' if pnl > 0 else 'red'
        )

    def signal_detected(self, symbol: str, trend: str, strength: int):
        """Log quando sinal é detectado."""
        self.logger.info(
            "signal_detected",
            symbol=symbol,
            trend=trend,
            strength=strength,
            strength_level='high' if strength >= 80 else 'medium' if strength >= 60 else 'low'
        )

    def api_error(self, endpoint: str, error_code: int, message: str):
        """Log erro de API."""
        self.logger.error(
            "api_error",
            endpoint=endpoint,
            error_code=error_code,
            message=message,
            error_severity='high' if error_code < -1000 else 'medium'
        )

    def risk_warning(self, message: str, **kwargs):
        """Log aviso de risco."""
        self.logger.warning(
            "risk_warning",
            message=message,
            **kwargs
        )

    def daily_summary(self, date: str, metrics: Dict):
        """Log resumo diário."""
        self.logger.info(
            "daily_summary",
            date=date,
            **metrics
        )


# ============================================================================
= FUNÇÕES DE AJUDA
# ============================================================================

def log_startup(config: Dict):
    """Log informações de startup."""
    logger = get_logger('startup')
    logger.info(
        "bot_starting",
        leverage=config.get('leverage'),
        max_positions=config.get('max_positions'),
        risk_per_trade=config.get('risk_per_trade'),
        symbols_count=len(config.get('symbols', []))
    )


def log_shutdown(reason: str = 'user_interrupt'):
    """Log informações de shutdown."""
    logger = get_logger('shutdown')
    logger.info(
        "bot_stopping",
        reason=reason,
        timestamp=datetime.now().isoformat()
    )


def log_exception(logger: structlog.stdlib.BoundLogger, exc: Exception, **context):
    """Log exception com contexto."""
    logger.exception(
        "exception_occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        **context
    )


# ============================================================================
= INICIALIZAÇÃO PADRÃO
# ============================================================================

# Configurar logging ao importar
configure_logging()

# Logger padrão
logger = get_logger('binance_bot')
trading_logger = TradingLogger()
