import importlib.util
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


def _load_module(name: str, rel_path: str):
    root = Path(__file__).resolve().parents[1]
    module_path = root / rel_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


serve_mod = _load_module("serve_dashboard_secure", "scripts/serve_dashboard_secure.py")
dash_mod = _load_module("build_stakeholder_dashboard", "scripts/build_stakeholder_dashboard.py")


class TestSecureDashboardServer(unittest.TestCase):
    def test_safe_join_blocks_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            self.assertEqual(serve_mod._safe_join(base, "/%2e%2e/").name, "__forbidden__")
            self.assertEqual(serve_mod._safe_join(base, "/../").name, "__forbidden__")

    def test_server_disables_listing_and_blocks_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "stakeholder_dashboard.html").write_text("<h1>ok</h1>", encoding="utf-8")
            (base / "subdir").mkdir()
            handler = serve_mod.build_handler(base.resolve(), "stakeholder_dashboard.html")
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                with urlopen(f"http://127.0.0.1:{port}/stakeholder_dashboard.html") as resp:
                    self.assertEqual(resp.status, 200)

                with self.assertRaises(HTTPError) as err:
                    urlopen(f"http://127.0.0.1:{port}/subdir/")
                self.assertEqual(err.exception.code, 403)

                with self.assertRaises(HTTPError) as err:
                    urlopen(f"http://127.0.0.1:{port}/%2e%2e/")
                self.assertEqual(err.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()


class TestDashboardEscaping(unittest.TestCase):
    def test_build_html_escapes_strategy_strings(self):
        payload = {
            "generated_utc": "2026-02-15T00:00:00Z",
            "cards": {
                "overall_status": "READY",
                "walk_forward_pass": "PASS",
                "campaign_mean_pnl": 1.0,
                "campaign_mean_sharpe": 1.0,
                "total_cases": 1,
                "gate_pass_ratio": 1.0,
                "quant_strategy": "<script>alert(1)</script>",
                "robustness_score": 1.0,
                "sortino_ratio": 1.0,
                "total_return_pct": 0.01,
                "cvar_95_pct": 0.0,
            },
            "quant_top": [
                {
                    "strategy": "<img src=x onerror=alert(1)>",
                    "budget": 1000,
                    "total_return_pct": 0.01,
                    "sortino_ratio": 1.0,
                    "calmar_ratio": 1.0,
                    "cvar_95_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "pass_rate": 1.0,
                }
            ],
            "robustness_snapshot": {
                "cases": 1,
                "dd_min_pct": 0.0,
                "dd_mean_pct": 0.0,
                "dd_p95_pct": 0.0,
                "dd_max_pct": 0.0,
                "cvar_mean_pct": 0.0,
                "cvar_p95_pct": 0.0,
                "cvar_max_pct": 0.0,
                "return_min_pct": 0.0,
                "return_mean_pct": 0.01,
                "return_p95_pct": 0.01,
                "return_max_pct": 0.01,
                "negative_return_cases": 0.0,
            },
            "execution_snapshot": {
                "cases": 1,
                "fill_ratio_mean": 0.5,
                "fill_ratio_p05": 0.4,
                "fill_ratio_p95": 0.6,
                "execution_cost_bps_mean": 1.0,
                "execution_cost_bps_p95": 2.0,
                "realized_edge_bps_mean": 0.1,
                "execution_quality_mean": 60.0,
                "slippage_cost_mean": 1.0,
                "latency_cost_mean": 1.0,
                "impact_cost_mean": 1.0,
                "adverse_selection_cost_mean": 1.0,
            },
            "data_profile": {
                "rows": 100,
                "start_utc": "2026-01-01T00:00:00+00:00",
                "end_utc": "2026-01-01T01:39:00+00:00",
                "interval_seconds_median": 60.0,
                "interval_seconds_p05": 60.0,
                "interval_seconds_p95": 60.0,
            },
            "explored_strategies": [
                {
                    "strategy_format": "<b>bad</b>",
                    "cases": 1,
                    "mean_total_return_pct": 0.01,
                    "return_ci95_pct": 0.001,
                    "mean_sortino": 1.0,
                    "mean_sharpe": 1.0,
                    "mean_drawdown_pct": 0.0,
                    "mean_cvar_95_pct": 0.0,
                    "gate_pass_rate": 1.0,
                }
            ],
            "capabilities": ["ok"],
            "limitations": ["paper only"],
            "strategic_profitability_path": ["<script>x</script>"],
            "selection_gates": {"max_cvar95_pct": "0.03"},
            "files": {
                "campaign": "<x>",
                "analysis": "<y>",
                "walk_forward": "<z>",
                "weekly": "<w>",
                "quant_recommendation_source": "<q1>",
                "quant_coverage_source": "<q2>",
            },
        }
        html_out = dash_mod.build_html(payload)
        self.assertNotIn("<script>alert(1)</script>", html_out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_out)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", html_out)


if __name__ == "__main__":
    unittest.main()
