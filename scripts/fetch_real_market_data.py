#!/usr/bin/env python3
import argparse
import json

from src.data.real_market_data import RealMarketDataClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch real market data snapshot (klines/orderbook/trades)")
    p.add_argument("--exchange", default="binance")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--kline-limit", type=int, default=200)
    p.add_argument("--order-book-limit", type=int, default=50)
    p.add_argument("--trades-limit", type=int, default=200)
    p.add_argument("--output-dir", default="data/real")
    p.add_argument("--prefix", default="")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    client = RealMarketDataClient(exchange_id=args.exchange)
    snapshot = client.fetch_snapshot(
        symbol=args.symbol,
        timeframe=args.timeframe,
        kline_limit=args.kline_limit,
        order_book_limit=args.order_book_limit,
        trades_limit=args.trades_limit,
    )
    files = client.save_snapshot(snapshot, output_dir=args.output_dir, prefix=args.prefix or None)

    payload = {
        "meta": snapshot["meta"],
        "files": {
            "klines": files.klines_path,
            "order_book_bids": files.order_book_bids_path,
            "order_book_asks": files.order_book_asks_path,
            "trades": files.trades_path,
            "meta": files.meta_path,
        },
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
