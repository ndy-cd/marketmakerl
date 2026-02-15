import unittest

import numpy as np
import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine


class _StubModel:
    def update_inventory(self, inventory):
        return None

    def set_parameters(self, **kwargs):
        return None

    def calculate_optimal_quotes(self, mid_price, spread_constraint=None):
        return mid_price * 0.9995, mid_price * 1.0005


def _build_market_data(n: int = 240) -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=n, freq="min", tz="UTC")
    mid = 100.0 + np.sin(np.linspace(0.0, 10.0, n)) * 0.8
    low = mid * 0.999
    high = mid * 1.001
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "mid_price": mid,
            "low": low,
            "high": high,
            "volume": np.full(n, 200.0),
        }
    )
    df["returns"] = df["mid_price"].pct_change().fillna(0.0)
    df["volatility"] = df["returns"].rolling(window=20).std().fillna(0.001)
    return df.set_index("timestamp")


class TestExecutionRealism(unittest.TestCase):
    def setUp(self):
        self.market_data = _build_market_data()
        self.model = _StubModel()
        self.run_params = {
            "spread_constraint_bps": 18.0,
            "min_edge_bps": 0.0,
            "cooldown_steps": 0,
            "inventory_soft_limit_ratio": 0.8,
            "order_notional_pct": 0.01,
            "min_order_qty": 0.01,
            "max_order_qty": 2.0,
        }

    def _run(self, **engine_kwargs):
        engine = BacktestEngine(
            market_data=self.market_data,
            initial_capital=10_000.0,
            transaction_fee=0.0002,
            random_seed=123,
            **engine_kwargs,
        )
        return engine.run_backtest(
            model=self.model,
            params=self.run_params,
            max_inventory=10,
            volatility_window=20,
        )["metrics"]

    def test_execution_metrics_bounds_and_presence(self):
        m = self._run()
        self.assertIn("fill_ratio", m)
        self.assertIn("execution_cost_bps", m)
        self.assertIn("execution_quality_score", m)
        self.assertGreaterEqual(m["fill_ratio"], 0.0)
        self.assertLessEqual(m["fill_ratio"], 1.0)
        self.assertGreaterEqual(m["fills_attempted"], m["fills_completed"])
        self.assertAlmostEqual(
            m["execution_cost"],
            m["slippage_cost"] + m["latency_cost"] + m["impact_cost"] + m["adverse_selection_cost"],
            places=6,
        )

    def test_latency_penalty_increases_execution_cost(self):
        low_latency = self._run(latency_ms=10.0)
        high_latency = self._run(latency_ms=600.0)
        self.assertGreaterEqual(high_latency["execution_cost_bps"], low_latency["execution_cost_bps"])

    def test_slippage_penalty_increases_execution_cost(self):
        low_slip = self._run(base_slippage_bps=0.2)
        high_slip = self._run(base_slippage_bps=4.0)
        self.assertGreaterEqual(high_slip["execution_cost_bps"], low_slip["execution_cost_bps"])

    def test_seed_determinism(self):
        a = self._run(latency_ms=120.0, base_slippage_bps=1.5)
        b = self._run(latency_ms=120.0, base_slippage_bps=1.5)
        self.assertAlmostEqual(a["total_pnl"], b["total_pnl"], places=8)
        self.assertAlmostEqual(a["fill_ratio"], b["fill_ratio"], places=8)
        self.assertAlmostEqual(a["execution_cost_bps"], b["execution_cost_bps"], places=8)


if __name__ == "__main__":
    unittest.main()
