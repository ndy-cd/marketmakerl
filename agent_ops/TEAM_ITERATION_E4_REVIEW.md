# Team Iteration E4 Review (A1-A10)

Date: `2026-02-13`  
Epoch: `E4 - Version-Rebuild Discipline and Stability Upgrade`

## Team Improvement Proposals

1. `A1 Runtime Orchestrator`
- Proposal: enforce image rebuild for each versioned iteration and persist rebuild evidence artifact.

2. `A2 Data and Signal Engineer`
- Proposal: keep no-key public data path as primary and run freshness validation before each quant wave.

3. `A3 Modeling Engineer`
- Proposal: run wider-seed evaluation to reduce overfitting risk in profile ranking.

4. `A4 Backtest and Risk Engineer`
- Proposal: extend walk-forward horizon from 30 to 45 days for harder stability checks.

5. `A5 QA and Integration Engineer`
- Proposal: keep release gate chain strict (`weekly`, `guardrails`, `consistency`) in every epoch run.

6. `A6 Documentation Architect`
- Proposal: keep dashboard source metrics on one consistent scale and remove mixed legacy tables.

7. `A7 Quant Researcher`
- Proposal: increase quant sample depth (`DAYS=120`, `MAX_WINDOWS=10`, seeds=`11,21,42,77,99`).

8. `A8 Project Manager`
- Proposal: standardize a single team iteration target that always includes rebuild + experiments + gates + dashboard.

9. `A9 Dashboard Designer`
- Proposal: add uncertainty display for explored families (confidence interval, not only mean).

10. `A10 Statistical Reliability Analyst`
- Proposal: publish return uncertainty (`CI95`) in dashboard for ranking robustness interpretation.

## PM Review Decisions

1. Accepted: `A1`, `A3`, `A4`, `A5`, `A6`, `A7`, `A8`, `A9`, `A10`.
2. Accepted with scope lock: `A2` (public no-key sources only for current MVP paper phase).
3. Deferred: none for this epoch.

## Implemented in E4

1. `Makefile`: added `version-rebuild VERSION=<tag>` and integrated rebuild into epoch workflows.
2. `Makefile`: added `epoch-4` with deeper quant wave and 45-day walk-forward gate.
3. `scripts/build_stakeholder_dashboard.py`: explored table now uses current quant epoch aggregation.
4. `scripts/build_stakeholder_dashboard.py`: added `Return CI95` per family.
5. Dashboard/showcase regeneration + product consistency check required in iteration close.

## Exit Criteria for E4

1. `make epoch-4 VERSION=e4 EXCHANGE=binance SYMBOL=BTC/USDT` passes end-to-end.
2. Release guardrails remain green.
3. Dashboard and docs showcase snapshot refreshed for stakeholder review.
