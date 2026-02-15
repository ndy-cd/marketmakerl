# Agent Workboard (A1-A11)

Single shared board for active execution and release blockers.

## Sprint Goal

Move from MVP research/demo posture to production-grade paper trading readiness with strict 1m data-quality gates.

## Current Round: E7 Production Bridge

- Status: `In Progress`
- Why files were uncommitted:
  - prior push intentionally scoped to runtime/backtest/dashboard implementation commit
  - team/docs artifacts were left in working tree for coordinated cleanup
- Canonical run command:
  - `make production-grade-step VERSION=e7-round1 EXCHANGE=binance SYMBOL=BTC/USDT`

## Release-Blocking Conditions (No-Go if any fail)

1. `make release-guardrails` must pass.
2. `make consistency-check` must pass.
3. Quant report must be `TIMEFRAME=1m`, with:
- `rows >= 10000`
- `median interval in [50s, 70s]`
4. Dashboard serving security checks must pass:
- loopback bind only
- no directory listing
- no path traversal

## E7 Execution Sequence

1. `make version-rebuild VERSION=e7-round1`
2. `make data-freshness EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m`
3. `make quant-experiments-1m EXCHANGE=binance SYMBOL=BTC/USDT DAYS=14 WINDOW_DAYS=2 MAX_WINDOWS=6 BUDGETS=5000,10000 VARIANTS=conservative,balanced,adaptive SEEDS=21,42,99 MAX_TOTAL_RETURN_PCT=0.25`
4. `make quant-top20-deep-1m EXCHANGE=binance SYMBOL=BTC/USDT`
5. `make release-guardrails`
6. `make consistency-check`
7. `make stakeholder-dashboard && make publish-showcase`

## Ownership Snapshot

1. `A1 Runtime Orchestrator` - Docker determinism and version rebuild discipline.
2. `A2 Data and Signal Engineer` - one-minute freshness and schema health.
3. `A3 Modeling Engineer` - safe parameter bounds for 1m runs.
4. `A4 Backtest and Risk Engineer` - execution realism and liquidation behavior.
5. `A5 QA and Integration Engineer` - guardrails and consistency gates.
6. `A6 Documentation Architect` - command/docs contract and cleanup.
7. `A7 Quant Researcher` - top-20 deep validation and strategy comparison.
8. `A8 Project Manager` - stop/go control and blocker enforcement.
9. `A9 Dashboard Designer` - readable KPI hierarchy with explicit missing-data handling.
10. `A10 Statistical Reliability Analyst` - plausibility and statistical defensibility.
11. `A11 Cybersecurity Engineer` - serving hardening and exposure checks.

## Current Decision

- System remains `paper-only`.
- No promotion toward live trading until E7 release blockers are green for repeated cycles.
