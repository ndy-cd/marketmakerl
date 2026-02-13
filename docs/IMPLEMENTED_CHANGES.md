# Implemented Changes

## Runtime and Reliability

1. Docker-first execution path.
2. `Makefile` targets for build, validation, campaign, research, and paper runtime.
3. Live-mode guardrail via `PAPER_ONLY=1`.

## Data and Strategy

1. Public no-key data ingestion module.
2. Last-month research script with:
- budget tiers
- strategy-format comparisons
- readiness report artifacts
3. Baseline and enhanced strategy execution support.

## Risk and Backtest

1. Fee-aware execution edge filter.
2. Cooldown control to reduce overtrading churn.
3. Soft inventory limit controls before hard liquidation.
4. Deterministic random seed in backtest execution simulation.
5. Volatility-targeted spread scaling and adverse-move blocking.
6. Soft/hard drawdown circuit breakers for capital preservation.
7. Drawdown failure rule standardized at `40%` of initial budget.

## Team and Delivery

1. Agent team expanded with Quant Researcher (A7) and Project Manager (A8).
2. Simplified docs package aligned with MVP gates.
