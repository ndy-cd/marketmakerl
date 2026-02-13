# MVP Execution Plan

Date: 2026-02-12

## Milestones

1. Runtime and Safety Gates (`Owner: A1, A5`) - `Completed`
- Commands: `make validate`, `make live-guard`
- Acceptance: Docker runtime stable; live mode blocked without secrets.

2. Real Data Module (`Owner: A2`) - `Completed`
- Commands: `make real-data-fetch EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m`
- Acceptance: klines/order book/trades snapshots saved under `data/real/`.

3. Baseline Strategy + Backtests (`Owner: A3, A4`) - `Completed`
- Commands: `make campaign N=10`
- Acceptance: campaign report generated under `artifacts/campaign_<timestamp>/campaign_report.json`.

4. Quant Research Gate (`Owner: A7`) - `Completed`
- Commands: `make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24`
- Acceptance: ranked strategies + readiness verdict written to `artifacts/last_month_analysis/`.

5. Server Deployment Path (`Owner: A1, A8`) - `Implemented`
- Commands:
  - `make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20`
  - `make deploy-server SERVER=user@host SERVER_DIR=/opt/marketmakerl`
- Acceptance: real-time quote strategy service is deployable with Docker Compose server profile.

6. Paper-only runtime lock (`Owner: A1, A8`) - `Completed`
- Commands: `make run-live`, `make realtime-live`
- Acceptance: both commands are blocked while `PAPER_ONLY=1`.

7. Execution/risk/fee-aware redesign (`Owner: A3, A4, A7`) - `In Progress`
- Scope:
  - add execution adapter contract (submit/cancel/replace/reconcile stubs)
  - add hard risk guards (max position/notional, kill switch, stale data guard)
  - add fee-aware quoting and trade filtering to reduce overtrading
- Acceptance:
  - deterministic tests for execution/risk state transitions
  - improved quant-gate economics on last-month analysis

## Release Gate

Required before enabling exchange keys:
- `make validate` passes.
- `make campaign N=10` passes.
- `make analyze-last-month ...` produces `readiness.ready_for_live_keys=true`.

Current status:
- Last quant report marks `ready_for_live_keys=false`.
- Runtime policy is paper-only (`PAPER_ONLY=1`).
- Stakeholder package is published:
  - `docs/STAKEHOLDER_MVP_BRIEF.md`
  - `docs/MVP_SIGNOFF_CHECKLIST.md`

## Blockers

1. Strategy remains unprofitable on last-month real-data gate.
2. No production order execution module exists yet (current live path is quote-loop and key-gated runtime).
