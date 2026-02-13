# Crypto Market Making System

Docker-first market-making MVP for research and paper trading.

## MVP Status

- Runtime, backtests, tests, and paper realtime quote loop are operational.
- Real market data ingestion (public endpoints) is operational.
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
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```

## Policy

- Paper/simulation only for MVP.
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
