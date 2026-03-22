import unittest

from risk_controls import (
    DAILY_LOSS_LIMIT,
    MAX_ORDER_SIZE,
    MAX_POSITIONS,
    PortfolioState,
    validate_order,
)


class TestRiskControls(unittest.TestCase):
    def test_reject_order_exceeding_max_size(self) -> None:
        portfolio = PortfolioState(daily_pnl=0.0, open_positions=0)
        order = {"value": MAX_ORDER_SIZE + 1}

        ok, reason = validate_order(order, portfolio)

        self.assertFalse(ok)
        self.assertEqual(reason, "超出单笔最大金额")

    def test_daily_loss_limit_triggers_halt(self) -> None:
        portfolio = PortfolioState(daily_pnl=DAILY_LOSS_LIMIT, open_positions=0)
        order = {"value": 1000}

        ok, reason = validate_order(order, portfolio)

        self.assertFalse(ok)
        self.assertEqual(reason, "日亏损限额触发熔断")
        self.assertTrue(portfolio.trading_halted)

    def test_reject_when_max_positions_reached(self) -> None:
        portfolio = PortfolioState(daily_pnl=0.0, open_positions=MAX_POSITIONS)
        order = {"value": 1000}

        ok, reason = validate_order(order, portfolio)

        self.assertFalse(ok)
        self.assertEqual(reason, "超过最大持仓数量")

    def test_pass_for_valid_order(self) -> None:
        portfolio = PortfolioState(daily_pnl=100.0, open_positions=MAX_POSITIONS - 1)
        order = {"value": 1000}

        ok, reason = validate_order(order, portfolio)

        self.assertTrue(ok)
        self.assertEqual(reason, "通过")
        self.assertFalse(portfolio.trading_halted)

    def test_reject_non_positive_order_value(self) -> None:
        portfolio = PortfolioState(daily_pnl=0.0, open_positions=0)

        ok_zero, reason_zero = validate_order({"value": 0}, portfolio)
        ok_negative, reason_negative = validate_order({"value": -10}, portfolio)

        self.assertFalse(ok_zero)
        self.assertEqual(reason_zero, "订单金额无效")
        self.assertFalse(ok_negative)
        self.assertEqual(reason_negative, "订单金额无效")

    def test_reject_when_trading_already_halted(self) -> None:
        portfolio = PortfolioState(daily_pnl=100.0, open_positions=0, trading_halted=True)
        order = {"value": 1000}

        ok, reason = validate_order(order, portfolio)

        self.assertFalse(ok)
        self.assertEqual(reason, "交易已熔断，拒绝新订单")


if __name__ == "__main__":
    unittest.main()

