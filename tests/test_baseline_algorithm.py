import unittest

from src.models.avellaneda_stoikov import AvellanedaStoikovModel


class TestBaselineAlgorithm(unittest.TestCase):
    def setUp(self):
        self.model = AvellanedaStoikovModel(risk_aversion=1.0, time_horizon=1.0, volatility=0.01)

    def test_quotes_are_ordered(self):
        bid, ask = self.model.calculate_optimal_quotes(mid_price=2000.0)
        self.assertLess(bid, ask)

    def test_inventory_pushes_reservation_price_directionally(self):
        mid = 2000.0
        self.model.update_inventory(20)
        bid_long, ask_long = self.model.calculate_optimal_quotes(mid)

        self.model.update_inventory(-20)
        bid_short, ask_short = self.model.calculate_optimal_quotes(mid)

        self.assertLess((bid_long + ask_long) / 2, (bid_short + ask_short) / 2)

    def test_spread_constraint_is_respected(self):
        mid = 2000.0
        spread_constraint = 10.0
        bid, ask = self.model.calculate_optimal_quotes(mid_price=mid, spread_constraint=spread_constraint)
        self.assertGreaterEqual(ask - bid, spread_constraint)

    def test_expected_pnl_is_finite(self):
        mid = 2000.0
        bid, ask = self.model.calculate_optimal_quotes(mid)
        pnl = self.model.expected_pnl(mid, bid, ask)
        self.assertTrue(float("-inf") < float(pnl) < float("inf"))


if __name__ == "__main__":
    unittest.main()
