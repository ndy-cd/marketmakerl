#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone

import pandas as pd

from src.data.real_market_data import RealMarketDataClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check real market data freshness and structural health")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--kline-limit", type=int, default=200)
    p.add_argument("--order-book-limit", type=int, default=20)
    p.add_argument("--trades-limit", type=int, default=50)
    p.add_argument("--max-kline-age-minutes", type=float, default=15.0)
    p.add_argument("--max-trade-age-minutes", type=float, default=15.0)
    return p.parse_args()


def age_minutes(ts: pd.Timestamp) -> float:
    now = pd.Timestamp(datetime.now(timezone.utc))
    return float((now - ts).total_seconds() / 60.0)


def main() -> int:
    args = parse_args()
    client = RealMarketDataClient(exchange_id=args.exchange)
    snap = client.fetch_snapshot(
        symbol=args.symbol,
        timeframe=args.timeframe,
        kline_limit=args.kline_limit,
        order_book_limit=args.order_book_limit,
        trades_limit=args.trades_limit,
    )

    klines = snap["klines"]
    bids = snap["order_book"]["bids"]
    asks = snap["order_book"]["asks"]
    trades = snap["trades"]

    checks = {
        "klines_non_empty": bool(not klines.empty),
        "bids_non_empty": bool(not bids.empty),
        "asks_non_empty": bool(not asks.empty),
        "trades_non_empty": bool(not trades.empty),
    }

    kline_age = None
    trade_age = None
    if not klines.empty:
        kline_age = age_minutes(pd.Timestamp(klines["timestamp"].iloc[-1]))
        checks["kline_fresh"] = bool(kline_age <= args.max_kline_age_minutes)
    else:
        checks["kline_fresh"] = False

    if not trades.empty:
        trade_age = age_minutes(pd.Timestamp(trades["timestamp"].iloc[-1]))
        checks["trade_fresh"] = bool(trade_age <= args.max_trade_age_minutes)
    else:
        checks["trade_fresh"] = False

    top_bid = float(bids.iloc[0]["price"]) if not bids.empty else None
    top_ask = float(asks.iloc[0]["price"]) if not asks.empty else None
    checks["book_spread_positive"] = bool(
        top_bid is not None and top_ask is not None and top_ask > top_bid
    )

    status = "pass" if all(checks.values()) else "fail"
    payload = {
        "status": status,
        "exchange": args.exchange,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "checks": checks,
        "metrics": {
            "kline_age_minutes": kline_age,
            "trade_age_minutes": trade_age,
            "top_bid": top_bid,
            "top_ask": top_ask,
            "klines_rows": int(len(klines)),
            "bids_rows": int(len(bids)),
            "asks_rows": int(len(asks)),
            "trades_rows": int(len(trades)),
        },
    }
    print(json.dumps(payload, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
