#!/usr/bin/env python3
import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.models.avellaneda_stoikov import AvellanedaStoikovModel
from src.data.real_market_data import RealMarketDataClient


@dataclass
class StrategyResult:
    risk_aversion: float
    time_horizon: float
    max_inventory: int
    spread_constraint: float
    transaction_fee: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
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


def build_param_grid(max_combinations: int) -> List[Dict]:
    grid: List[Dict] = []
    for risk_aversion in (0.5, 1.0, 1.5):
        for time_horizon in (0.5, 1.0):
            for max_inventory in (10, 20):
                for spread_constraint in (0.001, 0.002, 0.003):
                    grid.append(
                        {
                            "risk_aversion": risk_aversion,
                            "time_horizon": time_horizon,
                            "max_inventory": max_inventory,
                            "spread_constraint": spread_constraint,
                            "transaction_fee": 0.001,
                        }
                    )
    return grid[: max(1, int(max_combinations))]


def run_strategy_sweep(data: pd.DataFrame, initial_capital: float, max_combinations: int) -> List[StrategyResult]:
    results: List[StrategyResult] = []
    grid = build_param_grid(max_combinations=max_combinations)
    total = len(grid)
    for idx, cfg in enumerate(grid, start=1):
        print(
            f"[analysis] strategy {idx}/{total} "
            f"gamma={cfg['risk_aversion']} horizon={cfg['time_horizon']} "
            f"max_inv={cfg['max_inventory']} spread={cfg['spread_constraint']}",
            flush=True,
        )
        model = AvellanedaStoikovModel(
            risk_aversion=cfg["risk_aversion"],
            time_horizon=cfg["time_horizon"],
        )
        engine = BacktestEngine(
            market_data=data.copy(),
            initial_capital=initial_capital,
            transaction_fee=cfg["transaction_fee"],
        )
        out = engine.run_backtest(
            model=model,
            params={"spread_constraint": cfg["spread_constraint"]},
            max_inventory=cfg["max_inventory"],
            volatility_window=20,
        )
        m = out["metrics"]
        results.append(
            StrategyResult(
                risk_aversion=cfg["risk_aversion"],
                time_horizon=cfg["time_horizon"],
                max_inventory=cfg["max_inventory"],
                spread_constraint=cfg["spread_constraint"],
                transaction_fee=cfg["transaction_fee"],
                total_pnl=float(m.get("total_pnl", 0.0)),
                sharpe_ratio=float(m.get("sharpe_ratio", 0.0)),
                max_drawdown=float(m.get("max_drawdown", 0.0)),
                n_trades=float(m.get("n_trades", 0.0)),
                win_rate=float(m.get("win_rate", 0.0)),
            )
        )
    return results


def pick_best(results: List[StrategyResult]) -> StrategyResult:
    # Primary objective: maximize Sharpe; secondary: maximize PnL; tertiary: minimize drawdown.
    return sorted(
        results,
        key=lambda r: (r.sharpe_ratio, r.total_pnl, -r.max_drawdown),
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
        initial_capital=args.initial_capital,
        max_combinations=args.max_combinations,
    )
    best = pick_best(strategy_results)

    runs_df = pd.DataFrame([asdict(r) for r in strategy_results])
    runs_df = runs_df.sort_values(["sharpe_ratio", "total_pnl"], ascending=[False, False]).reset_index(drop=True)

    raw_path = output_dir / f"{stamp}_klines.csv"
    runs_path = output_dir / f"{stamp}_strategy_runs.csv"
    report_path = output_dir / f"{stamp}_analysis.json"

    klines.to_csv(raw_path, index=False)
    runs_df.to_csv(runs_path, index=False)

    readiness = {
        "ready_for_live_keys": bool(best.total_pnl > 0 and best.sharpe_ratio > 0 and best.max_drawdown < args.initial_capital),
        "checks": {
            "positive_pnl": bool(best.total_pnl > 0),
            "positive_sharpe": bool(best.sharpe_ratio > 0),
            "drawdown_below_initial_capital": bool(best.max_drawdown < args.initial_capital),
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
        },
        "best_strategy": asdict(best),
        "readiness": readiness,
        "top_5": runs_df.head(5).to_dict(orient="records"),
        "files": {
            "klines": str(raw_path),
            "strategy_runs": str(runs_path),
        },
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({**report, "files": {**report["files"], "analysis": str(report_path)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
