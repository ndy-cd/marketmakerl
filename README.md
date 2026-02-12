# Crypto Market Making System

Market making research and simulation framework with:
- Avellaneda-Stoikov quoting
- RL-enhanced market making environment
- Backtesting engine with market-signal integration
- Dockerized multi-agent runtime orchestration

## Start Here

- Canonical guide: `docs/PROJECT_GUIDE.md`
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
