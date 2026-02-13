# Team Review and Action Plan (A1-A8)

## Objective

Deliver a launch-ready paper-trading MVP with stable operations and controlled risk, without requiring high profitability.

## Team Strengths and Weaknesses

1. `A1 Runtime Orchestrator`
- Strengths: consistent Docker/Make workflow, clear mode guardrails, reproducible entrypoints.
- Weaknesses: baseline runtime metrics are still sensitive to strategy preset quality.

2. `A2 Data and Signal Engineer`
- Strengths: no-key market-data flows for klines/orderbook/trades are operational.
- Weaknesses: external exchange API behavior can change; requires resilient fallbacks and retries.

3. `A3 Modeling Engineer`
- Strengths: robust risk-aware quote presets identified in quant research.
- Weaknesses: model still regime-sensitive and can underperform in broad random campaigns.

4. `A4 Backtest and Risk Engineer`
- Strengths: realistic execution probabilities and risk overlays are implemented.
- Weaknesses: campaign-level PnL distribution remains volatile; more robustness tuning is needed.

5. `A5 QA and Integration Engineer`
- Strengths: validation pipeline is repeatable and catches regressions quickly.
- Weaknesses: needs explicit weekly walk-forward monitoring as a mandatory KPI.

6. `A6 Documentation Architect`
- Strengths: docs are now compact, English-only, and linked to executable commands.
- Weaknesses: requires regular synchronization with runtime defaults after each quant update.

7. `A7 Quant Researcher`
- Strengths: budget/format sweep and walk-forward gate provide practical launch criteria.
- Weaknesses: risk passing depends on selected preset; broad universality not guaranteed yet.

8. `A8 Project Manager`
- Strengths: clear gate-based MVP launch workflow and ownership model.
- Weaknesses: needs tighter cadence for reviewing drift between campaign and walk-forward outcomes.

## Cross-Team Risks

1. External exchange API instability (network/endpoint changes).
2. Performance drift under changing volatility regimes.
3. Divergence between "best preset" research and runtime defaults.

## Action Plan (Next Cycle)

1. `A1 + A8`: enforce `make mvp-launch` as default pre-release workflow.
- Done when: last run artifacts exist for validate/campaign/research/walk-forward/realtime.

2. `A2`: add market-data fallback policy and monitor error-rate in ingestion logs.
- Done when: no-key flows recover from transient API errors without manual intervention.

3. `A3 + A4`: tune preset for lower downside variance, prioritize drawdown stability over return.
- Done when: walk-forward passes and campaign loss-tail is reduced.

4. `A5`: add recurring operational check (`daily smoke`) for paper loop and artifact freshness.
- Done when: one-command health check reports green status.

5. `A6`: update docs after every preset or gate change in the same commit.
- Done when: no docs/runtime mismatch in review.

6. `A7`: maintain rolling 30-day adaptation and weekly walk-forward report.
- Done when: latest report includes pass/fail verdict and reasoned recommendation.

7. `A8`: run weekly team review and publish go/no-go summary.
- Done when: stakeholder sign-off references latest artifact set only.

## Launch Decision Rule (Paper MVP)

Proceed with paper launch when all are true:

1. `make validate` passes.
2. `make research-budgets` indicates a viable preset.
3. `make walk-forward` gate passes.
4. `PAPER_ONLY=1` remains enabled.
5. Realtime paper stream writes fresh artifacts.
