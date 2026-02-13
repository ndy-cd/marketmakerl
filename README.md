# Crypto Market Making System

Market making research and simulation framework with:
- Avellaneda-Stoikov quoting
- RL-enhanced market making environment
- Backtesting engine with market-signal integration
- Dockerized multi-agent runtime orchestration

## Start Here

- Canonical guide: `docs/PROJECT_GUIDE.md`
- Feature catalog: `docs/FEATURE_CATALOG.md`
- Implemented change log: `docs/IMPLEMENTED_CHANGES.md`
- Real data roadmap: `docs/REAL_DATA_DEVELOPMENT_PLAN.md`
- MVP execution plan: `docs/MVP_EXECUTION_PLAN.md`
- Stakeholder brief: `docs/STAKEHOLDER_MVP_BRIEF.md`
- MVP signoff checklist: `docs/MVP_SIGNOFF_CHECKLIST.md`
- Server deployment guide: `docs/DEPLOYMENT_GUIDE.md`
- Multi-agent team spec: `agent_ops/team.yaml`
- Runtime config: `config/config.yaml`

## Quick Run (Docker, Recommended)

```bash
make validate
```

`make validate` runs the reliability pipeline:

```bash
make build
make run-backtest
make test
make live-guard
```

Artifacts are written to `artifacts/` during run/test steps.

## Quick Test (Docker)

```bash
make test
```

## Real Data Snapshot (No API Keys)

```bash
make real-data-fetch EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m
```

This fetches real public market data and writes snapshot files under `data/real/`.

## Last-Month Strategy Analysis (No API Keys)

```bash
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=5m DAYS=30 MAX_COMBINATIONS=12
```

This runs a parameter sweep on the last-month public klines and writes analysis artifacts to `artifacts/last_month_analysis/`.

## Realtime Strategy (Server-ready)

```bash
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

Paper-only lock is enabled by default:
- `PAPER_ONLY=1` blocks all live paths (`make run-live`, `make realtime-live`)
- This project currently runs in paper/simulation mode only

Remote deploy:

```bash
make deploy-server SERVER=user@host SERVER_DIR=/opt/marketmakerl
```

## Live Mode Safety

Live mode is intentionally blocked unless secrets are provided:

- `EXCHANGE_API_KEY`
- `EXCHANGE_API_SECRET`

Example:

```bash
EXCHANGE_API_KEY=your_key EXCHANGE_API_SECRET=your_secret make run-live
```

Equivalent raw Docker command:

```bash
docker compose run --rm \
  -e EXCHANGE_API_KEY=your_key \
  -e EXCHANGE_API_SECRET=your_secret \
  agents python3 scripts/run_agents.py --config config/config.yaml --mode live --max-workers 4
```
