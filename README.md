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
make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m DAYS=30
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
make quant-experiments EXCHANGE=binance SYMBOL=BTC/USDT DAYS=60 WINDOW_DAYS=7 MAX_WINDOWS=6 BUDGETS=5000,10000,15000 VARIANTS=conservative,balanced,adaptive SEEDS=42,99 MAX_TOTAL_RETURN_PCT=0.25
make quant-experiments-1k EXCHANGE=binance SYMBOL=BTC/USDT
make quant-experiments-3k-1m EXCHANGE=binance SYMBOL=BTC/USDT
make quant-experiments-6k-1m-multisymbol EXCHANGE=binance SYMBOLS=BTC/USDT,ETH/USDT
make quant-top20-deep EXCHANGE=binance SYMBOL=BTC/USDT
make production-grade-step VERSION=e7-round1 EXCHANGE=binance SYMBOL=BTC/USDT
make production-grade-step-xl VERSION=e7-xl-round1 EXCHANGE=binance
make release-guardrails
make version-rebuild VERSION=e4
make epoch-3 EXCHANGE=binance SYMBOL=BTC/USDT
make epoch-4 VERSION=e4 EXCHANGE=binance SYMBOL=BTC/USDT
make realization-step EXCHANGE=binance SYMBOL=BTC/USDT SYMBOLS=BTC/USDT,ETH/USDT
make stakeholder-dashboard
make consistency-check
make publish-showcase
make dashboard-open
# or:
make dashboard-serve DASHBOARD_PORT=8000
```

Dashboard serving is hardened for local demos:
- no directory listing
- path traversal blocked (e.g. `/../`)
- dashboard root limited to `docs/showcase`

Stakeholder dashboard output:

- `artifacts/dashboard/latest_stakeholder_dashboard.html`
- `docs/showcase/stakeholder_dashboard.html` (committable snapshot for demos)

## Policy

- Paper/simulation only for MVP.
- Quant failure rule: if drawdown exceeds `40%` of initial budget, run is a fail.
- Quant recommendation prioritizes robust metrics (Sortino, Calmar, CVaR95, Ulcer) with plausibility filter (`MAX_TOTAL_RETURN_PCT`) over raw drawdown-only ranking.
- Release guardrails now enforce one-minute data quality (`TIMEFRAME=1m`, minimum rows, interval sanity) before promotion decisions.
- Version discipline: every new iteration/version must run `make version-rebuild VERSION=<tag>` before release/dashboard generation.
- Docker execution uses full repository mount into `/app`, so metrics always reflect latest local code after rebuild.
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
