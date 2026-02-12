import tempfile
import unittest
from pathlib import Path

import yaml

from src.agents.base import load_runtime_config


class TestRuntimeConfig(unittest.TestCase):
    def _write_cfg(self, data):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        with tmp as fh:
            yaml.safe_dump(data, fh)
        return Path(tmp.name)

    def test_load_runtime_config_defaults(self):
        cfg_path = self._write_cfg(
            {
                "mode": "backtest",
                "agents": [{"name": "a", "role": "data", "params": {}}],
            }
        )
        cfg = load_runtime_config(str(cfg_path))
        self.assertEqual(cfg["mode"], "backtest")
        self.assertIn("run_id", cfg)
        self.assertIn("paths", cfg)
        self.assertIn("artifacts_dir", cfg["paths"])

    def test_invalid_mode_raises(self):
        cfg_path = self._write_cfg(
            {
                "mode": "invalid",
                "agents": [{"name": "a", "role": "data", "params": {}}],
            }
        )
        with self.assertRaises(ValueError):
            load_runtime_config(str(cfg_path))

    def test_agents_required(self):
        cfg_path = self._write_cfg({"mode": "backtest", "agents": []})
        with self.assertRaises(ValueError):
            load_runtime_config(str(cfg_path))


if __name__ == "__main__":
    unittest.main()
