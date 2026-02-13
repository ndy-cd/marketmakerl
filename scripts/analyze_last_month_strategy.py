#!/usr/bin/env python3
import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.data.real_market_data import RealMarketDataClient


@dataclass
class StrategyResult:
    budget: float
    strategy_format: str
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
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    n_trades: float
    win_rate: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run last-month real-data strategy analysis (no API keys)")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--batch-limit", type=int, default=1000)
    p.add_argument("--initial-capital", type=float, default=10000.0)
    p.add_argument("--budget-tiers", default="2500,5000,10000")
    p.add_argument("--drawdown-fail-pct", type=float, default=0.40)
    p.add_argument("--max-combinations", type=int, default=12)
    p.add_argument("--output-dir", default="artifacts/last_month_analysis")
    return p.parse_args()


def fetch_last_month_klines(
    exchange: str,
    symbol: str,
    timeframe: str,
    days: int,
    batch_limit: int,
) -> pd.DataFrame:
    client = RealMarketDataClient(exchange_id=exchange)
    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(days=days)
    since_ms = int(since_dt.timestamp() * 1000)
    until_ms = int(now.timestamp() * 1000)

    frames: List[pd.DataFrame] = []
    cursor = since_ms
    while cursor < until_ms:
        batch = client.fetch_klines(
            symbol=symbol,
            timeframe=timeframe,
            since=cursor,
            limit=batch_limit,
        )
        if batch.empty:
            break
        frames.append(batch)
        last_ts_ms = int(batch["timestamp"].iloc[-1].timestamp() * 1000)
        next_cursor = last_ts_ms + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if len(batch) < batch_limit:
            break

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df[df["timestamp"] >= pd.Timestamp(since_dt)]
    return df


def parse_budget_tiers(raw: str) -> List[float]:
    out: List[float] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        value = float(token)
        if value <= 0:
            continue
        out.append(value)
    return sorted(set(out))


def build_strategy_formats() -> Dict[str, Dict]:
    return {
        "conservative_mm": {
            "backtest_mode": "standard",
            "risk_aversion": 1.5,
            "time_horizon": 1.0,
            "max_inventory": 6,
            "spread_constraint_bps": 34.0,
            "transaction_fee": 0.0002,
            "min_edge_bps": 2.0,
            "cooldown_steps": 3,
            "inventory_soft_limit_ratio": 0.55,
            "target_volatility": 0.0040,
            "vol_spread_scale": 1.1,
            "soft_drawdown_risk_pct": 0.18,
            "hard_drawdown_stop_pct": 0.40,
            "adverse_return_bps": 20.0,
        },
        "balanced_mm": {
            "backtest_mode": "standard",
            "risk_aversion": 1.0,
            "time_horizon": 1.0,
            "max_inventory": 8,
            "spread_constraint_bps": 30.0,
            "transaction_fee": 0.0002,
            "min_edge_bps": 1.5,
            "cooldown_steps": 2,
            "inventory_soft_limit_ratio": 0.60,
            "target_volatility": 0.0040,
            "vol_spread_scale": 1.0,
            "soft_drawdown_risk_pct": 0.20,
            "hard_drawdown_stop_pct": 0.40,
            "adverse_return_bps": 22.0,
        },
        "enhanced_signal_mm": {
            "backtest_mode": "enhanced",
            "risk_aversion": 0.8,
            "time_horizon": 0.75,
            "max_inventory": 7,
            "spread_constraint_bps": 32.0,
            "transaction_fee": 0.0002,
            "min_edge_bps": 2.0,
            "cooldown_steps": 3,
            "inventory_soft_limit_ratio": 0.50,
            "target_volatility": 0.0038,
            "vol_spread_scale": 1.2,
            "soft_drawdown_risk_pct": 0.16,
            "hard_drawdown_stop_pct": 0.40,
            "adverse_return_bps": 18.0,
        },
        "inventory_defensive_mm": {
            "backtest_mode": "standard",
            "risk_aversion": 1.8,
            "time_horizon": 0.5,
            "max_inventory": 5,
            "spread_constraint_bps": 38.0,
            "transaction_fee": 0.0002,
            "min_edge_bps": 2.5,
            "cooldown_steps": 3,
            "inventory_soft_limit_ratio": 0.50,
            "target_volatility": 0.0035,
            "vol_spread_scale": 1.3,
            "soft_drawdown_risk_pct": 0.15,
            "hard_drawdown_stop_pct": 0.40,
            "adverse_return_bps": 16.0,
        },
    }


def build_param_grid(max_combinations: int) -> List[Tuple[str, Dict]]:
    formats = build_strategy_formats()
    variants = []
    for format_name, cfg in formats.items():
        variants.append((format_name, cfg))
        relaxed = {**cfg}
        relaxed["spread_constraint_bps"] = max(20.0, cfg["spread_constraint_bps"] - 3.0)
        relaxed["min_edge_bps"] = max(1.0, cfg["min_edge_bps"] - 0.5)
        relaxed["soft_drawdown_risk_pct"] = min(0.25, cfg["soft_drawdown_risk_pct"] + 0.02)
        relaxed["adverse_return_bps"] = max(12.0, cfg["adverse_return_bps"] - 2.0)
        variants.append((f"{format_name}_relaxed", relaxed))
    return variants[: max(1, int(max_combinations))]


def run_strategy_sweep(
    data: pd.DataFrame,
    budget_tiers: List[float],
    max_combinations: int,
) -> List[StrategyResult]:
    results: List[StrategyResult] = []
    grid = build_param_grid(max_combinations=max_combinations)
    total = len(grid) * len(budget_tiers)
    case_idx = 0

    for budget in budget_tiers:
        for format_name, cfg in grid:
            case_idx += 1
            print(
                f"[analysis] case {case_idx}/{total} budget={budget:.2f} format={format_name} "
                f"gamma={cfg['risk_aversion']} horizon={cfg['time_horizon']} "
                f"max_inv={cfg['max_inventory']} spread_bps={cfg['spread_constraint_bps']}",
                flush=True,
            )
            model = AvellanedaStoikovModel(
                risk_aversion=cfg["risk_aversion"],
                time_horizon=cfg["time_horizon"],
            )
            engine = BacktestEngine(
                market_data=data.copy(),
                initial_capital=budget,
                transaction_fee=cfg["transaction_fee"],
                random_seed=42,
            )
            run_params = {
                "spread_constraint_bps": cfg["spread_constraint_bps"],
                "min_edge_bps": cfg["min_edge_bps"],
                "cooldown_steps": cfg["cooldown_steps"],
                "inventory_soft_limit_ratio": cfg["inventory_soft_limit_ratio"],
                "target_volatility": cfg["target_volatility"],
                "vol_spread_scale": cfg["vol_spread_scale"],
                "soft_drawdown_risk_pct": cfg["soft_drawdown_risk_pct"],
                "hard_drawdown_stop_pct": cfg["hard_drawdown_stop_pct"],
                "adverse_return_bps": cfg["adverse_return_bps"],
            }
            if cfg["backtest_mode"] == "enhanced":
                out = engine.run_backtest_enhanced(
                    model=model,
                    params=run_params,
                    max_inventory=cfg["max_inventory"],
                    volatility_window=20,
                    use_signals=True,
                )
            else:
                out = engine.run_backtest(
                    model=model,
                    params=run_params,
                    max_inventory=cfg["max_inventory"],
                    volatility_window=20,
                )
            m = out["metrics"]
            max_drawdown = float(m.get("max_drawdown", 0.0))
            results.append(
                StrategyResult(
                    budget=float(budget),
                    strategy_format=format_name,
                    backtest_mode=cfg["backtest_mode"],
                    risk_aversion=cfg["risk_aversion"],
                    time_horizon=cfg["time_horizon"],
                    max_inventory=cfg["max_inventory"],
                    spread_constraint_bps=cfg["spread_constraint_bps"],
                    transaction_fee=cfg["transaction_fee"],
                    min_edge_bps=cfg["min_edge_bps"],
                    cooldown_steps=cfg["cooldown_steps"],
                    inventory_soft_limit_ratio=cfg["inventory_soft_limit_ratio"],
                    target_volatility=cfg["target_volatility"],
                    vol_spread_scale=cfg["vol_spread_scale"],
                    soft_drawdown_risk_pct=cfg["soft_drawdown_risk_pct"],
                    hard_drawdown_stop_pct=cfg["hard_drawdown_stop_pct"],
                    adverse_return_bps=cfg["adverse_return_bps"],
                    total_pnl=float(m.get("total_pnl", 0.0)),
                    sharpe_ratio=float(m.get("sharpe_ratio", 0.0)),
                    max_drawdown=max_drawdown,
                    max_drawdown_pct=float(max_drawdown / max(1e-9, budget)),
                    n_trades=float(m.get("n_trades", 0.0)),
                    win_rate=float(m.get("win_rate", 0.0)),
                )
            )
    return results


def pick_best(results: List[StrategyResult], drawdown_fail_pct: float) -> StrategyResult:
    # Primary objective: pass drawdown rule, then maximize Sharpe/PnL.
    return sorted(
        results,
        key=lambda r: (
            r.max_drawdown_pct <= drawdown_fail_pct,
            r.sharpe_ratio,
            r.total_pnl,
            -r.max_drawdown_pct,
        ),
        reverse=True,
    )[0]


def main() -> int:
    logging.getLogger("src.backtesting.backtest_engine").setLevel(logging.ERROR)
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    klines = fetch_last_month_klines(
        exchange=args.exchange,
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
        batch_limit=args.batch_limit,
    )
    if klines.empty:
        raise SystemExit("No klines fetched for requested period")

    market_data = klines.copy()
    market_data["returns"] = market_data["mid_price"].pct_change()
    market_data["volatility"] = market_data["returns"].rolling(window=20).std().fillna(0.01)
    market_data = market_data.set_index("timestamp")

    strategy_results = run_strategy_sweep(
        market_data,
        budget_tiers=parse_budget_tiers(args.budget_tiers),
        max_combinations=args.max_combinations,
    )
    if not strategy_results:
        raise SystemExit("No strategy results generated")
    best = pick_best(strategy_results, drawdown_fail_pct=args.drawdown_fail_pct)

    runs_df = pd.DataFrame([asdict(r) for r in strategy_results])
    runs_df = runs_df.sort_values(
        ["budget", "max_drawdown_pct", "sharpe_ratio", "total_pnl"],
        ascending=[True, True, False, False],
    ).reset_index(drop=True)

    budget_summary = (
        runs_df.groupby("budget")
        .apply(
            lambda g: pd.Series(
                {
                    "cases": int(len(g)),
                    "best_pnl": float(g["total_pnl"].max()),
                    "best_sharpe": float(g["sharpe_ratio"].max()),
                    "best_drawdown_pct": float(g["max_drawdown_pct"].min()),
                    "pass_rate_40pct_dd": float((g["max_drawdown_pct"] <= args.drawdown_fail_pct).mean()),
                }
            )
        )
        .reset_index()
    )
    format_summary = (
        runs_df.groupby("strategy_format")
        .apply(
            lambda g: pd.Series(
                {
                    "cases": int(len(g)),
                    "mean_pnl": float(g["total_pnl"].mean()),
                    "mean_sharpe": float(g["sharpe_ratio"].mean()),
                    "mean_drawdown_pct": float(g["max_drawdown_pct"].mean()),
                    "pass_rate_40pct_dd": float((g["max_drawdown_pct"] <= args.drawdown_fail_pct).mean()),
                }
            )
        )
        .reset_index()
    )

    raw_path = output_dir / f"{stamp}_klines.csv"
    runs_path = output_dir / f"{stamp}_strategy_runs.csv"
    budget_summary_path = output_dir / f"{stamp}_budget_summary.csv"
    format_summary_path = output_dir / f"{stamp}_format_summary.csv"
    report_path = output_dir / f"{stamp}_analysis.json"

    klines.to_csv(raw_path, index=False)
    runs_df.to_csv(runs_path, index=False)
    budget_summary.to_csv(budget_summary_path, index=False)
    format_summary.to_csv(format_summary_path, index=False)

    dd_threshold_value = best.budget * args.drawdown_fail_pct

    readiness = {
        "ready_for_live_keys": bool(
            best.total_pnl > 0
            and best.sharpe_ratio > 0
            and best.max_drawdown_pct <= args.drawdown_fail_pct
        ),
        "checks": {
            "positive_pnl": bool(best.total_pnl > 0),
            "positive_sharpe": bool(best.sharpe_ratio > 0),
            "drawdown_below_40pct_budget": bool(best.max_drawdown_pct <= args.drawdown_fail_pct),
        },
        "rules": {
            "drawdown_fail_pct": float(args.drawdown_fail_pct),
            "drawdown_fail_abs_for_best_budget": float(dd_threshold_value),
        },
    }

    report = {
        "meta": {
            "exchange": args.exchange,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "days": args.days,
            "batch_limit": args.batch_limit,
            "rows": int(len(klines)),
            "start_utc": klines["timestamp"].min().isoformat(),
            "end_utc": klines["timestamp"].max().isoformat(),
            "budget_tiers": parse_budget_tiers(args.budget_tiers),
            "max_combinations": args.max_combinations,
        },
        "best_strategy": asdict(best),
        "readiness": readiness,
        "budget_summary": budget_summary.to_dict(orient="records"),
        "strategy_format_summary": format_summary.to_dict(orient="records"),
        "top_10": runs_df.head(10).to_dict(orient="records"),
        "files": {
            "klines": str(raw_path),
            "strategy_runs": str(runs_path),
            "budget_summary": str(budget_summary_path),
            "format_summary": str(format_summary_path),
        },
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({**report, "files": {**report["files"], "analysis": str(report_path)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
