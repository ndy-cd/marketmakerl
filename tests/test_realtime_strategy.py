import unittest

import pandas as pd

from scripts.run_realtime_strategy import compute_mid, compute_volatility


class TestRealtimeStrategyHelpers(unittest.TestCase):
    def test_compute_mid_from_order_book(self):
        snap = {
            "order_book": {
                "bids": pd.DataFrame([{"price": 99.0, "amount": 1.0}]),
                "asks": pd.DataFrame([{"price": 101.0, "amount": 1.0}]),
            },
            "klines": pd.DataFrame([{"mid_price": 100.0}]),
        }
        self.assertEqual(compute_mid(snap), 100.0)

    def test_compute_mid_fallback_to_klines(self):
        snap = {
            "order_book": {"bids": pd.DataFrame(), "asks": pd.DataFrame()},
            "klines": pd.DataFrame([{"mid_price": 123.45}]),
        }
        self.assertEqual(compute_mid(snap), 123.45)

    def test_compute_volatility_non_negative(self):
        klines = pd.DataFrame({"mid_price": [100.0 + i * 0.1 for i in range(30)]})
        vol = compute_volatility(klines)
        self.assertGreaterEqual(vol, 0.0)


if __name__ == "__main__":
    unittest.main()
