---
name: quant-researcher
description: Use when evaluating and adapting trading strategy parameters from recent real market data before enabling live API keys.
---

# Quant Researcher

## Use this skill when
- Defining parameter sweeps and objective functions for backtests.
- Running last-month strategy analysis on public market data.
- Producing readiness criteria for live key onboarding.

## Project-specific workflow
1. Use `make analyze-last-month` as canonical no-key research command.
2. Evaluate by Sharpe, PnL, drawdown, trade count, and win-rate.
3. Emit explicit readiness decision in report output.
4. Keep strategy adaptation decisions reproducible and documented.

## Minimum acceptance checks
- Analysis artifacts generated under `artifacts/last_month_analysis/`.
- Report contains best strategy, top-N alternatives, and readiness verdict.
- Commands and thresholds are documented in docs.

## Handoff requirements
- Parameter grid used
- Best candidate and rejected candidates summary
- Gate decision and next experiment suggestions
