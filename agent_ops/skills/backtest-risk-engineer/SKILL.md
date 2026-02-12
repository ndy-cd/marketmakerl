---
name: backtest-risk-engineer
description: Use when modifying backtesting logic or risk metrics in marketmakerl, including pnl accounting, drawdown/win-rate metrics, and realism knobs like slippage and latency.
---

# Backtest and Risk Engineer

## Use this skill when
- Editing `src/backtesting/backtest_engine.py`.
- Updating metrics definitions or execution simulation logic.
- Adding regression performance comparisons.

## Project-specific workflow
1. Preserve return payload keys: `metrics`, `trades`, `positions`.
2. Keep accounting internally consistent between cash, inventory, and portfolio value.
3. Add configurable realism knobs (slippage, latency, partial fills).
4. Separate execution simulation from metrics calculations where possible.
5. Document any metric definition change in docs/test notes.

## Metrics guardrails
- `total_pnl = final_value - initial_capital` must match position series.
- Win-rate computation must avoid lossy type conversions.
- Drawdown is computed from cumulative peak of total value.

## Minimum acceptance checks
- Deterministic fixture run produces stable metrics.
- No regressions in existing integration flow.
- Added knobs default to prior behavior when disabled.

## Handoff requirements
- Before/after metric table.
- Changed assumptions in execution model.
- Verification commands and expected output shape.
