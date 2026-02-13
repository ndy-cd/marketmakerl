# PM Process Review (Market Entry Prep)

Date: `2026-02-13`
Owner: `A8 Project Manager`

## Problem Statement

Previous experimentation cycles accepted outputs with implausible profitability magnitudes.
Root cause: process allowed headline metrics before plausibility and execution-model checks were enforced.

## Process Gaps Found

1. Model realism gate was not a hard precondition for quant ranking.
2. Recommendation pipeline accepted outlier return regimes without explicit plausibility threshold.
3. Dashboard emphasized top-line outcomes without enough reliability context.
4. Team review checklist did not include a statistical sanity checkpoint.

## Corrective Actions (Enforced)

1. Add execution realism controls in backtest engine:
- cash-constrained buys
- explicit position sizing
- quantity-aware realized PnL accounting

2. Add quant plausibility controls:
- robust metrics as primary ranking basis
- max total return threshold gate for recommendation eligibility
- anomaly penalty in robustness score

3. Add dashboard reliability-first framing:
- robustness, Sortino, CVaR95, pass-rate focus
- return shown as contextual %, not standalone claim

4. Expand team roles for governance:
- `A9 Dashboard Designer`
- `A10 Statistical Reliability Analyst`

## Updated PM Weekly Checklist

1. Verify execution realism assumptions before reading PnL.
2. Verify quant report gate thresholds are present and green.
3. Verify dashboard metrics match latest quant artifact schema.
4. Reject release if any plausibility/anomaly checks fail.

## Exit Criteria Before Key Onboarding

1. Three consecutive weekly cycles with green strict gates.
2. No implausible-return flags in quant recommendation.
3. Stable walk-forward pass with drawdown and tail-risk controls.
