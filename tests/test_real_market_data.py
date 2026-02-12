import tempfile
import unittest
from pathlib import Path

from src.data.real_market_data import RealMarketDataClient


class FakeExchange:
    def fetch_ohlcv(self, symbol, timeframe="1m", since=None, limit=500):
        return [
            [1700000000000, 100.0, 101.0, 99.0, 100.5, 12.0],
            [1700000060000, 100.5, 102.0, 100.0, 101.2, 15.0],
        ][:limit]

    def fetch_order_book(self, symbol, limit=100):
        return {
            "timestamp": 1700000060000,
            "bids": [[101.1, 2.0], [101.0, 1.5]],
            "asks": [[101.2, 1.8], [101.3, 2.1]],
        }

    def fetch_trades(self, symbol, since=None, limit=200):
        return [
            {"id": "t1", "timestamp": 1700000005000, "side": "buy", "price": 100.7, "amount": 0.4, "cost": 40.28},
            {"id": "t2", "timestamp": 1700000010000, "side": "sell", "price": 100.9, "amount": 0.2, "cost": 20.18},
        ][:limit]


class TestRealMarketData(unittest.TestCase):
    def setUp(self):
        self.client = RealMarketDataClient(exchange_id="binance", exchange=FakeExchange())

    def test_fetch_klines_schema(self):
        df = self.client.fetch_klines("BTC/USDT", timeframe="1m", limit=2)
        self.assertEqual(len(df), 2)
        self.assertIn("mid_price", df.columns)
        self.assertIn("timestamp", df.columns)

    def test_fetch_order_book_schema(self):
        payload = self.client.fetch_order_book("BTC/USDT", limit=2)
        self.assertIn("bids", payload)
        self.assertIn("asks", payload)
        self.assertEqual(len(payload["bids"]), 2)
        self.assertEqual(len(payload["asks"]), 2)

    def test_fetch_trades_schema(self):
        trades = self.client.fetch_trades("BTC/USDT", limit=2)
        self.assertEqual(len(trades), 2)
        self.assertIn("price", trades.columns)
        self.assertIn("amount", trades.columns)
        self.assertIn("timestamp", trades.columns)

    def test_snapshot_and_save(self):
        snap = self.client.fetch_snapshot("BTC/USDT", timeframe="1m", kline_limit=2, order_book_limit=2, trades_limit=2)
        self.assertIn("meta", snap)
        self.assertIn("klines", snap)
        self.assertIn("order_book", snap)
        self.assertIn("trades", snap)

        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.client.save_snapshot(snap, output_dir=tmpdir, prefix="testsnap")
            self.assertTrue(Path(files.klines_path).exists())
            self.assertTrue(Path(files.order_book_bids_path).exists())
            self.assertTrue(Path(files.order_book_asks_path).exists())
            self.assertTrue(Path(files.trades_path).exists())
            self.assertTrue(Path(files.meta_path).exists())


if __name__ == "__main__":
    unittest.main()
