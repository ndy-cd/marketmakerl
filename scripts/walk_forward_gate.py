#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.backtesting.backtest_engine import BacktestEngine
from src.data.real_market_data import RealMarketDataClient
from src.models.avellaneda_stoikov import AvellanedaStoikovModel


@dataclass
class WindowResult:
    window_id: int
    start_utc: str
    end_utc: str
    rows: int
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    n_trades: float
    pass_window: bool


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Walk-forward stability gate on recent real market data")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--window-days", type=int, default=5)
    p.add_argument("--batch-limit", type=int, default=1000)
    p.add_argument("--initial-capital", type=float, default=10000.0)
    p.add_argument("--drawdown-fail-pct", type=float, default=0.40)
    p.add_argument("--min-pass-rate", type=float, default=0.60)
    p.add_argument("--strict", action="store_true", help="Exit non-zero when gate does not pass")
    p.add_argument("--output-dir", default="artifacts/walk_forward")
    return p.parse_args()


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


def build_runtime_params() -> Dict:
    # Quant-selected trend-shield preset for reliability and stronger risk-adjusted returns.
    return {
        "risk_aversion": 1.6,
        "time_horizon": 0.75,
        "max_inventory": 4,
        "transaction_fee": 0.0002,
        "spread_constraint_bps": 39.0,
        "min_edge_bps": 2.4,
        "cooldown_steps": 4,
        "inventory_soft_limit_ratio": 0.4,
        "target_volatility": 0.0034,
        "vol_spread_scale": 1.5,
        "soft_drawdown_risk_pct": 0.15,
        "hard_drawdown_stop_pct": 0.40,
        "adverse_return_bps": 11.0,
        "risk_off_inventory_scale": 0.33,
        "volatility_window": 20,
        "random_seed": 42,
    }


def run_window(df: pd.DataFrame, capital: float, drawdown_fail_pct: float, params: Dict, window_id: int) -> WindowResult:
    data = df.copy()
    data["returns"] = data["mid_price"].pct_change()
    data["volatility"] = data["returns"].rolling(window=20).std().fillna(0.01)
    data = data.set_index("timestamp")

    model = AvellanedaStoikovModel(
        risk_aversion=float(params["risk_aversion"]),
        time_horizon=float(params["time_horizon"]),
    )
    engine = BacktestEngine(
        market_data=data,
        initial_capital=capital,
        transaction_fee=float(params["transaction_fee"]),
        random_seed=int(params["random_seed"]),
        min_edge_bps=float(params["min_edge_bps"]),
        cooldown_steps=int(params["cooldown_steps"]),
    )

    out = engine.run_backtest(
        model=model,
        params={
            "spread_constraint_bps": float(params["spread_constraint_bps"]),
            "min_edge_bps": float(params["min_edge_bps"]),
            "cooldown_steps": int(params["cooldown_steps"]),
            "inventory_soft_limit_ratio": float(params["inventory_soft_limit_ratio"]),
            "target_volatility": float(params["target_volatility"]),
            "vol_spread_scale": float(params["vol_spread_scale"]),
            "soft_drawdown_risk_pct": float(params["soft_drawdown_risk_pct"]),
            "hard_drawdown_stop_pct": float(params["hard_drawdown_stop_pct"]),
            "adverse_return_bps": float(params["adverse_return_bps"]),
            "risk_off_inventory_scale": float(params["risk_off_inventory_scale"]),
        },
        max_inventory=int(params["max_inventory"]),
        volatility_window=int(params["volatility_window"]),
    )
    m = out["metrics"]
    max_dd = float(m.get("max_drawdown", 0.0))
    dd_pct = max_dd / max(1e-9, capital)
    pnl = float(m.get("total_pnl", 0.0))
    sharpe = float(m.get("sharpe_ratio", 0.0))
    pass_window = bool(dd_pct <= drawdown_fail_pct and pnl >= 0 and sharpe >= 0)

    return WindowResult(
        window_id=window_id,
        start_utc=df["timestamp"].min().isoformat(),
        end_utc=df["timestamp"].max().isoformat(),
        rows=int(len(df)),
        total_pnl=pnl,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        max_drawdown_pct=dd_pct,
        n_trades=float(m.get("n_trades", 0.0)),
        pass_window=pass_window,
    )


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    klines = fetch_klines(args.exchange, args.symbol, args.timeframe, args.days, args.batch_limit)
    if klines.empty:
        raise SystemExit("No klines fetched")

    windows = split_windows(klines, window_days=args.window_days)
    if not windows:
        raise SystemExit("No valid windows produced")

    params = build_runtime_params()
    window_results = [
        run_window(w, capital=args.initial_capital, drawdown_fail_pct=args.drawdown_fail_pct, params=params, window_id=i + 1)
        for i, w in enumerate(windows)
    ]

    df = pd.DataFrame([asdict(w) for w in window_results])
    pass_rate = float(df["pass_window"].mean())
    hard_fail_windows = int((df["max_drawdown_pct"] > args.drawdown_fail_pct).sum())
    median_sharpe = float(df["sharpe_ratio"].median())
    total_pnl = float(df["total_pnl"].sum())

    gate = {
        "pass": bool(pass_rate >= args.min_pass_rate and hard_fail_windows == 0 and median_sharpe >= 0),
        "checks": {
            "pass_rate": pass_rate,
            "min_pass_rate": float(args.min_pass_rate),
            "hard_fail_windows": hard_fail_windows,
            "median_sharpe": median_sharpe,
            "total_pnl": total_pnl,
        },
    }

    report = {
        "meta": {
            "exchange": args.exchange,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "days": args.days,
            "window_days": args.window_days,
            "initial_capital": args.initial_capital,
            "drawdown_fail_pct": args.drawdown_fail_pct,
            "windows": int(len(df)),
        },
        "runtime_preset": params,
        "gate": gate,
        "windows": df.to_dict(orient="records"),
    }

    runs_path = out_dir / f"{stamp}_walk_forward_windows.csv"
    report_path = out_dir / f"{stamp}_walk_forward_report.json"
    df.to_csv(runs_path, index=False)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({**report, "files": {"windows": str(runs_path), "report": str(report_path)}}, indent=2))
    if args.strict and not gate["pass"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
