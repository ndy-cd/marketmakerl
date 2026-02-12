# Real Data Development Plan

## Objective
Move from simulation-first to real market data ingestion for a lightweight trading app, while keeping API-key usage optional until all non-live functionality is validated.

## Current Status
- Implemented real market data module: `src/data/real_market_data.py`
- Supports public CEX endpoints for:
  - klines (`fetch_klines`)
  - order book (`fetch_order_book`)
  - trades (`fetch_trades`)
- Snapshot persistence implemented via `save_snapshot`
- CLI fetch script: `scripts/fetch_real_market_data.py`
- Make target: `make real-data-fetch`

## Step-by-Step Delivery Plan

### Step 1: Public data ingestion (no keys)
- Use public exchange endpoints for historical and near-real-time snapshots.
- Validate schemas and persistence.
- Done when:
  - `make test-unit` passes new real-data tests
  - `make real-data-fetch` writes snapshot files to `data/real`

### Step 2: Data quality and normalization
- Add validation rules for missing/invalid values.
- Enforce timestamp ordering and deduplication.
- Add schema checks for each dataset.

### Step 3: Incremental polling loop
- Add short-interval polling service for lightweight operation.
- Save append-only records (CSV/JSONL) for klines/orderbook/trades.
- Add restart-safe checkpointing for last timestamps.

### Step 4: Strategy wiring
- Feed real snapshots into baseline Avellaneda pipeline in paper mode.
- Keep execution disabled until risk controls are complete.
- Compare against simulation baseline metrics.

### Step 5: API-key onboarding (after full validation)
- Introduce private endpoints only for execution/account context.
- Keep data ingestion paths working without private keys.
- Add strict secret management and startup guards.

## Testing Plan

1. Unit tests (offline)
- `tests/test_real_market_data.py` with mocked exchange client.
- Expected: deterministic, no network dependency.

2. Integration tests (Docker)
- `make validate`
- Expected: runtime + discovered tests + integration script pass.

3. Real-data smoke (network, no keys)
- `make real-data-fetch EXCHANGE=binance SYMBOL=BTC/USDT`
- Expected: files in `data/real/` and metadata json printed.

4. Campaign stability
- `make campaign N=10`
- Expected: campaign report with aggregated metrics.

## Lightweight App Principles
- Keep dependencies minimal (`ccxt`, `pandas`, standard library).
- Prefer polling snapshots over heavy stream infra for MVP.
- Use flat files and deterministic schemas first; move to DB only when needed.
- Keep runtime safe-by-default (`mode=backtest`, guarded `mode=live`).
