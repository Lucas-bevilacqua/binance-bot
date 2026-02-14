"""
🗄️ DATABASE PACKAGE
====================
Persistência PostgreSQL para Binance Bot.
"""

from .repositories import (
    DatabaseRepository,
    TradeRepository,
    PositionRepository,
    get_trade_repo,
    get_position_repo,
    close_repos
)

from .db_integration import (
    BotWithPersistence,
    main_with_persistence,
    get_dashboard_data_from_db
)

__all__ = [
    'DatabaseRepository',
    'TradeRepository',
    'PositionRepository',
    'get_trade_repo',
    'get_position_repo',
    'close_repos',
    'BotWithPersistence',
    'main_with_persistence',
    'get_dashboard_data_from_db'
]
