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
- Weaknesses: regime classification is still static and not auto-adaptive yet.

4. `A4 Backtest and Risk Engineer`
- Strengths: realistic execution probabilities, risk overlays, and strict walk-forward gate are implemented.
- Weaknesses: needs periodic retuning as volatility regimes drift month-to-month.

5. `A5 QA and Integration Engineer`
- Strengths: validation pipeline is repeatable and catches regressions quickly.
- Weaknesses: needs explicit weekly walk-forward monitoring as a mandatory KPI.

6. `A6 Documentation Architect`
- Strengths: single documentation owner with end-to-end view for humans and AI.
- Weaknesses: becomes bottleneck if review SLA is not enforced.

7. `A7 Quant Researcher`
- Strengths: budget/format sweep and walk-forward gate provide practical launch criteria.
- Weaknesses: passing profile still concentrated in defensive formats for smaller budgets.

8. `A8 Project Manager`
- Strengths: clear gate-based MVP launch workflow and ownership model.
- Weaknesses: requires weekly cadence enforcement and explicit rollback criteria.

## Documentation Responsibility (Strict)

1. Owner: `A6 Documentation Architect`.
2. Mandatory reviewers: `A5` (test accuracy) and `A8` (scope/governance).
3. Hard rules:
- every runtime or strategy preset change must update docs in the same commit;
- duplicate or conflicting docs are prohibited;
- commands in docs must be runnable exactly as written;
- docs language is English-only.
4. Rejection criteria (automatic fail):
- outdated command examples;
- mismatch between `Makefile`/runtime defaults and docs;
- missing data-flow, test-flow, or run-flow section after feature change.

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
- Status: done in current cycle.
- Evidence: strict walk-forward pass with `hard_fail_windows=0`; 10-run campaign remained profitable with reduced drawdown tail.

4. `A5`: add recurring operational check (`daily smoke`) for paper loop and artifact freshness.
- Done when: one-command health check reports green status.

5. `A6`: update docs after every preset or gate change in the same commit.
- Done when: strict documentation rejection criteria are all green.

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

## Latest Cycle Snapshot

Date: `2026-02-13`

1. `validate`: pass
2. `campaign (N=10)`: pass, all runs positive
3. `research-budgets`: best reliability preset moved to `inventory_defensive_mm`
4. `walk-forward --strict`: pass (`pass_rate=1.0`, `hard_fail_windows=0`)
5. `realtime-paper`: pass (20 iterations, fresh artifact written)
6. per-agent reports published: `agent_ops/TEAM_MEMBER_REPORTS.md`
