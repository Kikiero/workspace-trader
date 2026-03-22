"""
Hard risk guardrails for live trading.

This module is intentionally deterministic:
- No LLM judgment required
- No silent overrides
- Clear PASS/REJECT reasons
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

# ===== Hard-coded limits (edit with extreme caution) =====
MAX_ORDER_SIZE = 10_000.0  # 单笔最大金额
DAILY_LOSS_LIMIT = -5_000.0  # 日亏损限额（<= 触发熔断）
MAX_POSITIONS = 10  # 最大持仓数量


@dataclass
class PortfolioState:
    daily_pnl: float
    open_positions: int
    trading_halted: bool = False


def default_halt_trading(portfolio: PortfolioState) -> None:
    """Hard circuit breaker: block all new orders."""
    portfolio.trading_halted = True


def validate_order(
    order: Dict[str, float],
    portfolio: PortfolioState,
    halt_trading: Optional[Callable[[PortfolioState], None]] = None,
) -> Tuple[bool, str]:
    """
    Validate a single order against hard risk rules.

    Required order fields:
    - value: order notional amount
    """
    if halt_trading is None:
        halt_trading = default_halt_trading

    if portfolio.trading_halted:
        return False, "交易已熔断，拒绝新订单"

    order_value = float(order.get("value", 0.0))
    if order_value <= 0:
        return False, "订单金额无效"

    if order_value > MAX_ORDER_SIZE:
        return False, "超出单笔最大金额"

    if portfolio.daily_pnl <= DAILY_LOSS_LIMIT:
        halt_trading(portfolio)
        return False, "日亏损限额触发熔断"

    if portfolio.open_positions >= MAX_POSITIONS:
        return False, "超过最大持仓数量"

    return True, "通过"

