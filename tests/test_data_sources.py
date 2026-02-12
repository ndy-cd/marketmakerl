import unittest

import pandas as pd

from src.data.data_processor import DataProcessor
from src.utils.market_data import OnchainDataHandler


class TestDataSources(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor(data_dir="artifacts")

    def test_simulation_and_file_roundtrip(self):
        df = self.processor.simulate_market_data(n_periods=64, initial_price=1500)
        self.assertGreater(len(df), 0)
        self.assertIn("mid_price", df.columns)
        self.assertIn("spread", df.columns)

        ok = self.processor.save_to_file(df, "tests_tmp_market_data.csv")
        self.assertTrue(ok)

        loaded = self.processor.load_from_file("tests_tmp_market_data.csv")
        self.assertGreater(len(loaded), 0)
        self.assertIn("mid_price", loaded.columns)

    def test_sync_cex_with_onchain_without_fixed_freq(self):
        cex = self.processor.simulate_market_data(n_periods=40, initial_price=2000)
        onchain = cex[["mid_price"]].copy()

        # Drop some rows so inferred frequency path is exercised.
        onchain = onchain.iloc[::2]

        merged = self.processor.sync_cex_with_onchain(cex, onchain, latency=30)
        self.assertIsInstance(merged, pd.DataFrame)
        self.assertGreater(len(merged), 0)
        self.assertIn("mid_price_cex", merged.columns)
        self.assertIn("mid_price_onchain", merged.columns)

    def test_onchain_handler_placeholder(self):
        handler = OnchainDataHandler()
        sample = handler.fetch_pool_data("0xpool")
        self.assertIn("reserves", sample)
        self.assertIn("fees", sample)
        self.assertIn("price", sample)


if __name__ == "__main__":
    unittest.main()
