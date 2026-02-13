# Stakeholder MVP Brief

## What Works Today

1. Dockerized runtime and validation workflow.
2. Public real-market data ingestion (no API keys required).
3. Backtesting and repeated campaign execution.
4. Real-time paper quote loop.
5. Safety lock that blocks live trading.

## Risk Position

- Quant gate is strict: run fails if drawdown exceeds `40%` of budget.
- API keys are intentionally deferred until quant readiness is consistently positive.

## Decision

- MVP is operational as a paper-trading platform.
- Reliability gates are green in the latest cycle; keep paper-only until repeated weekly cycles stay green.
