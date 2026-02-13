# Crypto Market Making System

Docker-first market-making MVP for research and paper trading.

## MVP Status

- Runtime, backtests, tests, and paper realtime quote loop are operational.
- Real market data ingestion (public endpoints) is operational.
- Walk-forward gate is strict (`make walk-forward` exits non-zero on failure).
- Live trading is blocked by default (`PAPER_ONLY=1`).

## Quick Start

1. Validate full stack:

```bash
make validate
```

2. Run paper realtime strategy:

```bash
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

3. Run quant gate on last month:

```bash
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
```

4. Run walk-forward stability gate:

```bash
make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
```

5. Run end-to-end MVP launch workflow:

```bash
make mvp-launch EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
```

6. Run operational reliability checks:

```bash
make daily-smoke EXCHANGE=binance SYMBOL=BTC/USDT ITERATIONS=2 POLL_SECONDS=1
make data-freshness EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m
make weekly-report
make quant-experiments EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
make realization-step EXCHANGE=binance SYMBOL=BTC/USDT SYMBOLS=BTC/USDT,ETH/USDT
make stakeholder-dashboard
```

Stakeholder dashboard output:

- `artifacts/dashboard/latest_stakeholder_dashboard.html`

## Policy

- Paper/simulation only for MVP.
- Quant failure rule: if drawdown exceeds `40%` of initial budget, run is a fail.
- `PAPER_ONLY=1` blocks:
  - `make run-live`
  - `make realtime-live`

## Documentation

- Documentation map: `docs/DOCS_INDEX.md`
- Primary technical guide: `docs/PROJECT_GUIDE.md`
- Stakeholder summary: `docs/STAKEHOLDER_MVP_BRIEF.md`
- Deployment guide: `docs/DEPLOYMENT_GUIDE.md`
- MVP plan: `docs/MVP_EXECUTION_PLAN.md`
- Team workboard: `agent_ops/WORKBOARD.md`
