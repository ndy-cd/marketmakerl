import unittest

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine


class TestBacktestLiquidationAccounting(unittest.TestCase):
    def setUp(self):
        market_data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2026-01-01", periods=2, freq="min", tz="UTC"),
                "mid_price": [100.0, 100.0],
            }
        ).set_index("timestamp")
        self.engine = BacktestEngine(market_data=market_data, initial_capital=1000.0, transaction_fee=0.001)

    def test_run_backtest_passes_spread_constraint_to_model(self):
        class StubModel:
            def __init__(self):
                self.constraints = []

            def update_inventory(self, inventory):
                return None

            def set_parameters(self, **kwargs):
                return None

            def calculate_optimal_quotes(self, mid_price, spread_constraint=None):
                self.constraints.append(spread_constraint)
                return mid_price * 0.999, mid_price * 1.001

        model = StubModel()
        self.engine.run_backtest(model=model, params={"spread_constraint": 0.003}, max_inventory=100)
        self.assertGreater(len(model.constraints), 0)
        self.assertTrue(all(c == 0.003 for c in model.constraints))

    def test_liquidation_of_long_inventory_increases_capital(self):
        self.engine.capital = 500.0
        self.engine.inventory = 5

        self.engine._process_trade(
            timestamp=self.engine.market_data.index[0],
            side="LIQUIDATION",
            price=100.0,
            quantity=5,
            mid_price=100.0,
        )

        expected_fee = 100.0 * 5 * 0.001
        self.assertAlmostEqual(self.engine.capital, 500.0 + 500.0 - expected_fee, places=6)
        self.assertEqual(self.engine.inventory, 0)

    def test_liquidation_of_short_inventory_decreases_capital(self):
        self.engine.capital = 1500.0
        self.engine.inventory = -3

        self.engine._process_trade(
            timestamp=self.engine.market_data.index[0],
            side="LIQUIDATION",
            price=100.0,
            quantity=-3,
            mid_price=100.0,
        )

        expected_fee = 100.0 * 3 * 0.001
        self.assertAlmostEqual(self.engine.capital, 1500.0 - 300.0 - expected_fee, places=6)
        self.assertEqual(self.engine.inventory, 0)


if __name__ == "__main__":
    unittest.main()
