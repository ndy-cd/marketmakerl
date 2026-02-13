#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_processor import DataProcessor
from src.models.avellaneda_stoikov import AvellanedaStoikovModel


SCENARIOS = [
    {"name": "base", "min_edge_bps": 2.5, "cooldown_steps": 4, "spread_bps": 40.0, "max_inventory": 4},
    {"name": "tight_spread", "min_edge_bps": 2.0, "cooldown_steps": 3, "spread_bps": 35.0, "max_inventory": 4},
    {"name": "high_cooldown", "min_edge_bps": 2.5, "cooldown_steps": 6, "spread_bps": 40.0, "max_inventory": 3},
    {"name": "risk_off", "min_edge_bps": 3.0, "cooldown_steps": 5, "spread_bps": 45.0, "max_inventory": 3},
]


def run_scenario(frame: pd.DataFrame, scenario: dict) -> dict:
    model = AvellanedaStoikovModel(risk_aversion=1.8, time_horizon=0.5)
    engine = BacktestEngine(
        market_data=frame.copy(),
        initial_capital=10000.0,
        transaction_fee=0.0002,
        random_seed=42,
        min_edge_bps=float(scenario["min_edge_bps"]),
        cooldown_steps=int(scenario["cooldown_steps"]),
    )
    out = engine.run_backtest(
        model=model,
        params={
            "spread_constraint_bps": float(scenario["spread_bps"]),
            "min_edge_bps": float(scenario["min_edge_bps"]),
            "cooldown_steps": int(scenario["cooldown_steps"]),
            "inventory_soft_limit_ratio": 0.4,
            "target_volatility": 0.0032,
            "vol_spread_scale": 1.5,
            "soft_drawdown_risk_pct": 0.14,
            "hard_drawdown_stop_pct": 0.40,
            "adverse_return_bps": 12.0,
            "risk_off_inventory_scale": 0.35,
        },
        max_inventory=int(scenario["max_inventory"]),
        volatility_window=20,
    )
    m = out["metrics"]
    return {
        "scenario": scenario["name"],
        "total_pnl": float(m.get("total_pnl", 0.0)),
        "sharpe_ratio": float(m.get("sharpe_ratio", 0.0)),
        "max_drawdown": float(m.get("max_drawdown", 0.0)),
        "n_trades": float(m.get("n_trades", 0.0)),
        "win_rate": float(m.get("win_rate", 0.0)),
    }


def main() -> int:
    processor = DataProcessor(data_dir="./data")
    frame = processor.simulate_market_data(n_periods=1000, initial_price=2000, volatility=0.01, mean_reversion=0.1)

    rows = [run_scenario(frame, s) for s in SCENARIOS]
    df = pd.DataFrame(rows)

    out_dir = Path("artifacts/risk_calibration")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = out_dir / f"{stamp}_risk_calibration.csv"
    json_path = out_dir / f"{stamp}_risk_calibration.json"

    best = df.sort_values(["max_drawdown", "sharpe_ratio", "total_pnl"], ascending=[True, False, False]).iloc[0].to_dict()

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "best_scenario": best,
        "rows": rows,
        "files": {"csv": str(csv_path), "json": str(json_path)},
    }

    df.to_csv(csv_path, index=False)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
