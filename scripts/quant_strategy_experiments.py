#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.data.real_market_data import RealMarketDataClient
from src.models.avellaneda_stoikov import AvellanedaStoikovModel


@dataclass
class StrategySpec:
    name: str
    backtest_mode: str
    risk_aversion: float
    time_horizon: float
    max_inventory: int
    spread_constraint_bps: float
    transaction_fee: float
    min_edge_bps: float
    cooldown_steps: int
    inventory_soft_limit_ratio: float
    target_volatility: float
    vol_spread_scale: float
    soft_drawdown_risk_pct: float
    hard_drawdown_stop_pct: float
    adverse_return_bps: float
    risk_off_inventory_scale: float


@dataclass
class ExperimentResult:
    strategy: str
    budget: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    n_trades: float
    pass_rate: float
    hard_fail_windows: int
    robustness_score: float
    gate_pass: bool


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Quant strategy experiments with robustness ranking")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--batch-limit", type=int, default=1000)
    p.add_argument("--window-days", type=int, default=5)
    p.add_argument("--budgets", default="5000,10000")
    p.add_argument("--drawdown-fail-pct", type=float, default=0.40)
    p.add_argument("--output-dir", default="artifacts/quant_experiments")
    return p.parse_args()


def parse_budgets(raw: str) -> List[float]:
    out = []
    for t in raw.split(","):
        t = t.strip()
        if not t:
            continue
        v = float(t)
        if v > 0:
            out.append(v)
    return sorted(set(out))


def fetch_klines(exchange: str, symbol: str, timeframe: str, days: int, batch_limit: int) -> pd.DataFrame:
    client = RealMarketDataClient(exchange_id=exchange, market_type="spot")
    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(days=days)
    since_ms = int(since_dt.timestamp() * 1000)
    until_ms = int(now.timestamp() * 1000)

    frames: List[pd.DataFrame] = []
    cursor = since_ms
    while cursor < until_ms:
        batch = client.fetch_klines(symbol=symbol, timeframe=timeframe, since=cursor, limit=batch_limit)
        if batch.empty:
            break
        frames.append(batch)
        last_ts_ms = int(batch["timestamp"].iloc[-1].timestamp() * 1000)
        nxt = last_ts_ms + 1
        if nxt <= cursor:
            break
        cursor = nxt
        if len(batch) < batch_limit:
            break

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return df.reset_index(drop=True)


def split_windows(df: pd.DataFrame, window_days: int) -> List[pd.DataFrame]:
    if df.empty:
        return []
    start = df["timestamp"].min()
    end = df["timestamp"].max()
    out = []
    cursor = start
    while cursor < end:
        right = cursor + pd.Timedelta(days=window_days)
        w = df[(df["timestamp"] >= cursor) & (df["timestamp"] < right)].copy()
        if len(w) >= 200:
            out.append(w)
        cursor = right
    return out


def build_specs() -> List[StrategySpec]:
    return [
        StrategySpec("defensive_core", "standard", 1.8, 0.5, 4, 40.0, 0.0002, 2.5, 4, 0.40, 0.0032, 1.5, 0.14, 0.40, 12.0, 0.35),
        StrategySpec("inventory_tight", "standard", 2.0, 0.5, 3, 42.0, 0.0002, 2.8, 5, 0.35, 0.0030, 1.6, 0.13, 0.40, 10.0, 0.30),
        StrategySpec("spread_capture", "standard", 1.4, 0.75, 5, 34.0, 0.0002, 2.2, 3, 0.45, 0.0038, 1.3, 0.16, 0.40, 14.0, 0.40),
        StrategySpec("trend_shield", "standard", 1.6, 0.75, 4, 39.0, 0.0002, 2.4, 4, 0.40, 0.0034, 1.5, 0.15, 0.40, 11.0, 0.33),
        StrategySpec("volatility_brake", "standard", 1.9, 0.50, 3, 45.0, 0.0002, 3.0, 5, 0.35, 0.0029, 1.8, 0.12, 0.40, 9.0, 0.28),
        StrategySpec("enhanced_signal_guarded", "enhanced", 0.9, 0.75, 5, 36.0, 0.0002, 2.3, 4, 0.45, 0.0035, 1.4, 0.15, 0.40, 13.0, 0.38),
    ]


def prep_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["returns"] = data["mid_price"].pct_change()
    data["volatility"] = data["returns"].rolling(window=20).std().fillna(0.01)
    return data.set_index("timestamp")


def run_single(data: pd.DataFrame, spec: StrategySpec, budget: float) -> Dict:
    model = AvellanedaStoikovModel(risk_aversion=spec.risk_aversion, time_horizon=spec.time_horizon)
    engine = BacktestEngine(
        market_data=data,
        initial_capital=budget,
        transaction_fee=spec.transaction_fee,
        random_seed=42,
        min_edge_bps=spec.min_edge_bps,
        cooldown_steps=spec.cooldown_steps,
    )
    params = {
        "spread_constraint_bps": spec.spread_constraint_bps,
        "min_edge_bps": spec.min_edge_bps,
        "cooldown_steps": spec.cooldown_steps,
        "inventory_soft_limit_ratio": spec.inventory_soft_limit_ratio,
        "target_volatility": spec.target_volatility,
        "vol_spread_scale": spec.vol_spread_scale,
        "soft_drawdown_risk_pct": spec.soft_drawdown_risk_pct,
        "hard_drawdown_stop_pct": spec.hard_drawdown_stop_pct,
        "adverse_return_bps": spec.adverse_return_bps,
        "risk_off_inventory_scale": spec.risk_off_inventory_scale,
    }
    if spec.backtest_mode == "enhanced":
        out = engine.run_backtest_enhanced(
            model=model,
            params=params,
            max_inventory=spec.max_inventory,
            volatility_window=20,
            use_signals=True,
        )
    else:
        out = engine.run_backtest(
            model=model,
            params=params,
            max_inventory=spec.max_inventory,
            volatility_window=20,
        )
    return out["metrics"]


def evaluate(args: argparse.Namespace, df_raw: pd.DataFrame) -> List[ExperimentResult]:
    specs = build_specs()
    budgets = parse_budgets(args.budgets)
    windows = split_windows(df_raw, args.window_days)
    results: List[ExperimentResult] = []

    for budget in budgets:
        for spec in specs:
            print(f"[quant] strategy={spec.name} budget={budget:.0f}", flush=True)
            full_metrics = run_single(prep_data(df_raw), spec, budget)

            pass_windows = 0
            hard_fails = 0
            for w in windows:
                m = run_single(prep_data(w), spec, budget)
                dd_pct = float(m.get("max_drawdown", 0.0)) / max(1e-9, budget)
                pnl = float(m.get("total_pnl", 0.0))
                sharpe = float(m.get("sharpe_ratio", 0.0))
                if dd_pct <= args.drawdown_fail_pct and pnl >= 0 and sharpe >= 0:
                    pass_windows += 1
                if dd_pct > args.drawdown_fail_pct:
                    hard_fails += 1

            pass_rate = (pass_windows / len(windows)) if windows else 0.0
            total_pnl = float(full_metrics.get("total_pnl", 0.0))
            sharpe = float(full_metrics.get("sharpe_ratio", 0.0))
            max_dd = float(full_metrics.get("max_drawdown", 0.0))
            dd_pct = max_dd / max(1e-9, budget)
            gate_pass = bool(total_pnl > 0 and sharpe > 0 and dd_pct <= args.drawdown_fail_pct and hard_fails == 0)

            robustness = (
                (2.0 * sharpe)
                + (2.0 * pass_rate)
                + (total_pnl / max(1.0, budget))
                - (3.0 * dd_pct)
                - (2.5 * hard_fails)
            )

            results.append(
                ExperimentResult(
                    strategy=spec.name,
                    budget=budget,
                    total_pnl=total_pnl,
                    sharpe_ratio=sharpe,
                    max_drawdown=max_dd,
                    max_drawdown_pct=dd_pct,
                    n_trades=float(full_metrics.get("n_trades", 0.0)),
                    pass_rate=pass_rate,
                    hard_fail_windows=hard_fails,
                    robustness_score=robustness,
                    gate_pass=gate_pass,
                )
            )
    return results


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    raw = fetch_klines(args.exchange, args.symbol, args.timeframe, args.days, args.batch_limit)
    if raw.empty:
        raise SystemExit("No data fetched")

    results = evaluate(args, raw)
    df = pd.DataFrame([asdict(r) for r in results]).sort_values("robustness_score", ascending=False)

    passed = df[df["gate_pass"] == True].copy()  # noqa: E712
    recommended = (passed.iloc[0] if not passed.empty else df.iloc[0]).to_dict()

    known_strategy_families = [
        "inventory_defensive",
        "trend_shield",
        "volatility_brake",
        "spread_capture",
        "enhanced_signal_guarded",
        "inventory_tight",
        "conservative_mm",
        "balanced_mm",
        "cross_exchange_arb",
        "latency_arb",
        "options_hedged_mm",
        "funding_basis_mm",
    ]
    tested_families = [
        "inventory_defensive",
        "trend_shield",
        "volatility_brake",
        "spread_capture",
        "enhanced_signal_guarded",
        "inventory_tight",
        "conservative_mm",
        "balanced_mm",
    ]
    untested_families = [x for x in known_strategy_families if x not in tested_families]

    report = {
        "meta": {
            "exchange": args.exchange,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "days": args.days,
            "window_days": args.window_days,
            "budgets": parse_budgets(args.budgets),
            "rows": int(len(raw)),
            "strategies": [s.name for s in build_specs()],
        },
        "recommendation": recommended,
        "coverage": {
            "known_families_total": len(known_strategy_families),
            "tested_families_count": len(tested_families),
            "coverage_pct": (len(tested_families) / len(known_strategy_families)) * 100.0,
            "tested_families": tested_families,
            "untested_families": untested_families,
            "note": "MVP paper phase focuses on market-making families; non-MM families remain future work.",
        },
        "gate_pass_count": int(df["gate_pass"].sum()),
        "total_cases": int(len(df)),
        "top_10": df.head(10).to_dict(orient="records"),
    }

    csv_path = out_dir / f"{stamp}_quant_experiments.csv"
    json_path = out_dir / f"{stamp}_quant_experiments.json"
    df.to_csv(csv_path, index=False)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({**report, "files": {"csv": str(csv_path), "report": str(json_path)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
