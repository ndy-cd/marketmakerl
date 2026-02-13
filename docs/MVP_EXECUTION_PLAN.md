# MVP Execution Plan

## Goal

Deliver a stable, stakeholder-ready paper-trading MVP with explicit risk gates.

## Phase Status

1. Runtime and Docker workflow: `Done`
2. Public data ingestion (no keys): `Done`
3. Strategy/backtest baseline: `Done`
4. Quant research gate: `Done (paper launch preset selected)`
5. Documentation and stakeholder package: `Done`

## Hard Gates

```bash
make validate
make campaign N=10
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
```

Release gate criteria:

1. Pipeline commands succeed.
2. Strategy report includes readiness checks.
3. Drawdown rule enforced: failure if drawdown exceeds `40%` of initial budget.
4. Tail-risk rule enforced: CVaR95 and Sortino thresholds must pass in quant experiments.
5. Plausibility rule enforced: recommendation must satisfy total-return cap.
6. `PAPER_ONLY=1` remains enabled until quant gate passes.
7. Walk-forward gate passes (`make walk-forward ...`).

## Current Decision

- Continue paper-only operation.
- Use reliability runtime preset (`inventory_defensive_mm`) and `make mvp-launch` workflow for paper rollout.
- Keep strict walk-forward gate enabled (`make walk-forward` fails the pipeline when gate is red).
- Do not onboard exchange API keys until repeated paper cycles remain stable.
