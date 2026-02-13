#!/usr/bin/env python3
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data.real_market_data import RealMarketDataClient
from src.models.avellaneda_stoikov import AvellanedaStoikovModel


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run real-time market-making quote loop on public CEX data")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--iterations", type=int, default=20)
    p.add_argument("--poll-seconds", type=float, default=5.0)
    p.add_argument("--kline-limit", type=int, default=200)
    p.add_argument("--order-book-limit", type=int, default=20)
    p.add_argument("--trades-limit", type=int, default=50)
    p.add_argument("--risk-aversion", type=float, default=1.0)
    p.add_argument("--time-horizon", type=float, default=1.0)
    p.add_argument("--spread-constraint", type=float, default=0.001)
    p.add_argument("--disable-regime-switch", action="store_true")
    p.add_argument("--initial-inventory", type=float, default=0.0)
    p.add_argument("--output-dir", default="artifacts/realtime")
    p.add_argument("--require-keys", action="store_true")
    return p.parse_args()


def require_live_secrets() -> None:
    paper_only = str(os.getenv("PAPER_ONLY", "0")).lower() in {"1", "true", "yes"}
    if paper_only:
        raise ValueError("live realtime mode is disabled while PAPER_ONLY=1")
    required = ("EXCHANGE_API_KEY", "EXCHANGE_API_SECRET")
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")


def compute_mid(snapshot: dict) -> float:
    bids = snapshot["order_book"]["bids"]
    asks = snapshot["order_book"]["asks"]
    if not bids.empty and not asks.empty:
        return float((bids.iloc[0]["price"] + asks.iloc[0]["price"]) / 2.0)
    klines = snapshot["klines"]
    if klines.empty:
        raise ValueError("No data available to compute mid price")
    return float(klines.iloc[-1]["mid_price"])


def compute_volatility(klines: pd.DataFrame) -> float:
    if klines.empty or len(klines) < 20:
        return 0.01
    rets = klines["mid_price"].pct_change().dropna()
    if rets.empty:
        return 0.01
    return float(max(1e-8, rets.rolling(window=20).std().iloc[-1] if len(rets) >= 20 else rets.std()))


def detect_regime(klines: pd.DataFrame, volatility: float) -> str:
    if klines.empty or len(klines) < 30:
        return "neutral"
    short = float(klines["mid_price"].iloc[-1])
    long = float(klines["mid_price"].iloc[-30])
    trend = (short - long) / max(1e-9, long)
    if volatility > 0.0045:
        return "volatile"
    if trend > 0.003:
        return "trend_up"
    if trend < -0.003:
        return "trend_down"
    return "range"


def regime_spread_multiplier(regime: str) -> float:
    if regime == "volatile":
        return 1.35
    if regime in {"trend_up", "trend_down"}:
        return 1.15
    if regime == "range":
        return 0.95
    return 1.0


def main() -> int:
    args = parse_args()
    if args.require_keys:
        require_live_secrets()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = output_dir / f"{token}_{args.exchange.replace('/', '_')}_{args.symbol.replace('/', '_')}.jsonl"

    client = RealMarketDataClient(exchange_id=args.exchange)
    model = AvellanedaStoikovModel(
        risk_aversion=float(args.risk_aversion),
        time_horizon=float(args.time_horizon),
        volatility=0.01,
    )
    inventory = float(args.initial_inventory)

    total_iterations = int(args.iterations)
    if total_iterations <= 0:
        total_iterations = 10**12

    with out_path.open("w", encoding="utf-8") as fh:
        for i in range(total_iterations):
            snapshot = client.fetch_snapshot(
                symbol=args.symbol,
                timeframe=args.timeframe,
                kline_limit=args.kline_limit,
                order_book_limit=args.order_book_limit,
                trades_limit=args.trades_limit,
            )
            mid = compute_mid(snapshot)
            klines = snapshot["klines"]
            vol = compute_volatility(klines)
            regime = detect_regime(klines, vol)
            model.update_inventory(inventory)
            model.set_parameters(volatility=vol)
            spread_constraint = float(args.spread_constraint)
            if not args.disable_regime_switch:
                spread_constraint *= regime_spread_multiplier(regime)
            bid, ask = model.calculate_optimal_quotes(mid, spread_constraint=spread_constraint)

            payload = {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "iteration": i + 1,
                "exchange": args.exchange,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "mid_price": mid,
                "volatility": vol,
                "inventory": inventory,
                "bid": float(bid),
                "ask": float(ask),
                "spread": float(ask - bid),
                "spread_constraint": float(spread_constraint),
                "regime": regime,
                "top_bid_levels": int(len(snapshot["order_book"]["bids"])),
                "top_ask_levels": int(len(snapshot["order_book"]["asks"])),
                "recent_trades": int(len(snapshot["trades"])),
            }
            fh.write(json.dumps(payload) + "\n")
            fh.flush()
            print(json.dumps(payload), flush=True)
            if i < total_iterations - 1:
                time.sleep(max(0.0, args.poll_seconds))

    print(json.dumps({"status": "ok", "output": str(out_path), "iterations": args.iterations}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
