# Project Guide

Canonical technical document for the MarketMakeRL MVP.

## 1) What This MVP Is

- Docker-first market making platform.
- Modes supported today:
  - `backtest` (historical simulation)
  - `paper` (real-time quoting with no order placement)
- Live order placement is blocked by policy (`PAPER_ONLY=1`).

## 2) Quick Run

```bash
make build
make validate
make campaign N=10
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

## 3) Safety Policy

- Allowed: simulation and paper execution.
- Blocked while `PAPER_ONLY=1`:
  - `make run-live`
  - `make realtime-live`
- Any strategy run with max drawdown worse than `40%` of initial budget is a failure.

## 4) Architecture

1. Data layer:
- `src/data/data_processor.py` for deterministic synthetic data.
- `src/data/real_market_data.py` for public CEX data (no keys required).

2. Strategy layer:
- `src/models/avellaneda_stoikov.py` baseline market-making model.
- `src/models/rl_enhanced_model.py` enhanced model wrapper for research.

3. Execution and risk layer:
- `src/backtesting/backtest_engine.py` with fee-aware edge filter, cooldown, soft inventory limits, and liquidation handling.
- Stability overlays:
  - volatility-targeted spread widening
  - soft/hard drawdown circuit breakers
  - adverse-move entry filter
  - risk-off inventory scaling

4. Runtime orchestration:
- `scripts/run_agents.py`, `scripts/run_realtime_strategy.py`, `Makefile`, Docker Compose.

5. Outputs:
- All artifacts under `artifacts/`.

## 5) Data Flows (Different Sources)

1. Synthetic training/smoke flow:
- `DataProcessor.simulate_market_data()`
- backtest engine
- metrics JSON artifacts.

2. Public snapshot flow (no keys):
- `scripts/fetch_real_market_data.py`
- pulls `klines`, `order_book`, and `trades`
- writes files to `data/real/`.

3. Last-month research flow (no keys):
- `scripts/analyze_last_month_strategy.py`
- fetches rolling historical klines from public endpoints
- runs budget tiers + strategy formats
- emits analysis JSON + CSV reports.

4. Real-time paper flow (no keys):
- `scripts/run_realtime_strategy.py`
- polls exchange market data
- generates quotes and logs stream to `artifacts/realtime/*.jsonl`.

## 6) Validation Gates

Mandatory before any MVP milestone:

```bash
make validate
make campaign N=10
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
make daily-smoke EXCHANGE=binance SYMBOL=BTC/USDT ITERATIONS=2 POLL_SECONDS=1
make quant-experiments EXCHANGE=binance SYMBOL=BTC/USDT DAYS=60 WINDOW_DAYS=7 MAX_WINDOWS=6 BUDGETS=5000,10000,15000 VARIANTS=conservative,balanced,adaptive SEEDS=42,99
```

Research gate checks:
- Positive PnL.
- Positive Sharpe and positive Sortino.
- `max_drawdown_pct <= 0.40`.
- Tail-risk control: `cvar_95_pct` below configured threshold.
- Walk-forward pass rate above configured threshold with no hard drawdown breaches.

## 7) Current MVP Readiness

- Platform reliability (Docker/test/runtime): operational.
- Real data ingestion (public endpoints): operational.
- Quant reliability: strict walk-forward gate currently passes with reliability preset.
- Quant exploration: new strategy lab recommends `trend_shield` as current best robust profile.
- Realization step-up: multisymbol paper shadow flow (`BTC/USDT`, `ETH/USDT`) operational.
- Decision: continue in paper-only mode.

## 8) Team Roles

- Ownership map and current status: `agent_ops/team.yaml` and `agent_ops/WORKBOARD.md`.
- Includes Quant Researcher (`A7`) and Project Manager (`A8`) roles.
