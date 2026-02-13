import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd

try:
    import ccxt

    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

logger = logging.getLogger(__name__)


def _to_millis(since: Optional[Union[int, datetime]]) -> Optional[int]:
    if since is None:
        return None
    if isinstance(since, datetime):
        return int(since.timestamp() * 1000)
    return int(since)


@dataclass
class SnapshotFiles:
    klines_path: str
    order_book_bids_path: str
    order_book_asks_path: str
    trades_path: str
    meta_path: str


class RealMarketDataClient:
    """Lightweight market-data client for public CEX data using ccxt."""

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout_ms: int = 10000,
        market_type: str = "spot",
        load_markets_retries: int = 3,
        exchange: Optional[Any] = None,
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout_ms = timeout_ms
        self.market_type = market_type
        self.load_markets_retries = max(1, int(load_markets_retries))
        self._exchange = exchange or self._build_exchange()

    def _build_exchange(self) -> Any:
        if not CCXT_AVAILABLE:
            raise ImportError("ccxt is required for real market data collection")
        if self.exchange_id not in ccxt.exchanges:
            raise ValueError(f"Unsupported exchange: {self.exchange_id}")
        exchange_class = getattr(ccxt, self.exchange_id)
        ex = exchange_class(
            {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
                "timeout": self.timeout_ms,
                "options": {
                    "defaultType": self.market_type,
                    "fetchMarkets": {"types": [self.market_type]},
                },
            }
        )
        last_error = None
        for attempt in range(1, self.load_markets_retries + 1):
            try:
                ex.load_markets()
                last_error = None
                break
            except Exception as err:
                last_error = err
                logger.warning(
                    "load_markets failed for %s (type=%s), attempt %d/%d: %s",
                    self.exchange_id,
                    self.market_type,
                    attempt,
                    self.load_markets_retries,
                    err,
                )
                if attempt < self.load_markets_retries:
                    time.sleep(min(3.0, 0.5 * attempt))
        if last_error is not None:
            raise last_error
        return ex

    @property
    def exchange(self) -> Any:
        return self._exchange

    def fetch_klines(
        self,
        symbol: str,
        timeframe: str = "1m",
        since: Optional[Union[int, datetime]] = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=_to_millis(since), limit=int(limit))
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df["mid_price"] = (df["high"] + df["low"]) / 2.0
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, pd.DataFrame]:
        payload = self.exchange.fetch_order_book(symbol, limit=int(limit))
        timestamp = payload.get("timestamp")
        ts = pd.to_datetime(timestamp, unit="ms", utc=True) if timestamp else pd.Timestamp.utcnow()

        bids = pd.DataFrame(payload.get("bids", []), columns=["price", "amount"])
        asks = pd.DataFrame(payload.get("asks", []), columns=["price", "amount"])
        for frame in (bids, asks):
            if not frame.empty:
                frame["timestamp"] = ts
        return {"bids": bids, "asks": asks, "timestamp": ts}

    def fetch_trades(
        self,
        symbol: str,
        since: Optional[Union[int, datetime]] = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        raw = self.exchange.fetch_trades(symbol, since=_to_millis(since), limit=int(limit))
        if not raw:
            return pd.DataFrame(columns=["id", "timestamp", "side", "price", "amount", "cost"])

        rows = []
        for t in raw:
            rows.append(
                {
                    "id": t.get("id"),
                    "timestamp": pd.to_datetime(t.get("timestamp"), unit="ms", utc=True) if t.get("timestamp") else pd.NaT,
                    "side": t.get("side"),
                    "price": t.get("price"),
                    "amount": t.get("amount"),
                    "cost": t.get("cost"),
                }
            )
        df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
        return df

    def fetch_snapshot(
        self,
        symbol: str,
        timeframe: str = "1m",
        kline_limit: int = 500,
        order_book_limit: int = 100,
        trades_limit: int = 200,
    ) -> Dict[str, Any]:
        klines = self.fetch_klines(symbol=symbol, timeframe=timeframe, limit=kline_limit)
        order_book = self.fetch_order_book(symbol=symbol, limit=order_book_limit)
        trades = self.fetch_trades(symbol=symbol, limit=trades_limit)
        meta = {
            "exchange": self.exchange_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
            "kline_rows": int(len(klines)),
            "bid_levels": int(len(order_book["bids"])),
            "ask_levels": int(len(order_book["asks"])),
            "trade_rows": int(len(trades)),
        }
        return {"meta": meta, "klines": klines, "order_book": order_book, "trades": trades}

    def save_snapshot(
        self,
        snapshot: Dict[str, Any],
        output_dir: Union[str, Path] = "data/real",
        prefix: Optional[str] = None,
    ) -> SnapshotFiles:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        token = prefix or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        klines_path = output / f"{token}_klines.csv"
        bids_path = output / f"{token}_orderbook_bids.csv"
        asks_path = output / f"{token}_orderbook_asks.csv"
        trades_path = output / f"{token}_trades.csv"
        meta_path = output / f"{token}_meta.json"

        snapshot["klines"].to_csv(klines_path, index=False)
        snapshot["order_book"]["bids"].to_csv(bids_path, index=False)
        snapshot["order_book"]["asks"].to_csv(asks_path, index=False)
        snapshot["trades"].to_csv(trades_path, index=False)
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(snapshot["meta"], fh, indent=2)

        return SnapshotFiles(
            klines_path=str(klines_path),
            order_book_bids_path=str(bids_path),
            order_book_asks_path=str(asks_path),
            trades_path=str(trades_path),
            meta_path=str(meta_path),
        )
