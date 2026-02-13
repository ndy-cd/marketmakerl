# Team Action Plan (Strict) - A1 to A8

Planning window: `2026-02-13` to `2026-03-13`

## Objective

Keep MVP reliably green in paper mode for repeated weekly cycles, with strict gates and no documentation/runtime drift.

## Global Non-Negotiable Gates

1. `make validate` must pass.
2. `make campaign N=10` must stay profitable on average.
3. `make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT` must produce readiness artifacts.
4. `make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30` must pass in strict mode.
5. `PAPER_ONLY=1` must remain enabled.

## Team Plan by Agent

1. `A1 Runtime Orchestrator`
- Priority: `P0`
- Scope: pipeline reliability and deterministic runtime behavior.
- Deliverables:
  - add one-command daily smoke target in `Makefile` (`validate + walk-forward strict + short realtime-paper`)
  - ensure artifact timestamps and naming stay deterministic and parseable
- KPI:
  - smoke command success rate >= `95%` weekly
- Done criteria:
  - smoke command documented and used in weekly ops review

2. `A2 Data and Signal Engineer`
- Priority: `P0`
- Scope: robustness of public no-key market data ingestion.
- Deliverables:
  - fallback/retry policy for transient exchange failures
  - data freshness checks for klines/orderbook/trades
- KPI:
  - ingestion failure rate <= `2%` weekly
- Done criteria:
  - failures auto-recover without manual restart in test runs

3. `A3 Modeling Engineer`
- Priority: `P1`
- Scope: reduce regime sensitivity of quote behavior.
- Deliverables:
  - conservative regime switch logic (range/trend/volatile)
  - parameter guardrails to prevent over-aggressive quoting
- KPI:
  - no single walk-forward window with drawdown > `35%`
- Done criteria:
  - regime switch logic documented and validated in backtest reports

4. `A4 Backtest and Risk Engineer`
- Priority: `P0`
- Scope: downside containment and execution realism.
- Deliverables:
  - extend slippage/fill calibration scenarios
  - maintain strict risk overlays as default runtime profile
- KPI:
  - `hard_fail_windows = 0` in weekly walk-forward
- Done criteria:
  - updated risk benchmark attached to weekly report

5. `A5 QA and Integration Engineer`
- Priority: `P0`
- Scope: regression safety and gate enforcement.
- Deliverables:
  - automated weekly gate run checklist and artifact verification
  - failure triage template for red gates
- KPI:
  - mean time to diagnose gate failure <= `30 min`
- Done criteria:
  - checklist used for two consecutive weekly cycles

6. `A6 Documentation Architect` (Owner)
- Priority: `P0`
- Scope: strict documentation governance for humans and AI.
- Deliverables:
  - keep `README.md`, `docs/`, and `agent_ops/` synchronized with runtime defaults
  - remove duplicated or conflicting statements immediately
- KPI:
  - docs/runtime mismatch count = `0`
- Done criteria:
  - all documentation acceptance checklist items remain green each week

7. `A7 Quant Researcher`
- Priority: `P0`
- Scope: rolling reliability evaluation and recommendation.
- Deliverables:
  - weekly 30-day rolling research summary
  - explicit go/no-go note for live-key readiness
- KPI:
  - weekly report published on time (`100%` cadence)
- Done criteria:
  - each report references latest campaign + walk-forward artifacts

8. `A8 Project Manager`
- Priority: `P0`
- Scope: coordination, SLA, and decision control.
- Deliverables:
  - weekly release gate review
  - enforce rollback criteria on any red gate
- KPI:
  - unresolved P0 action items older than `7 days` = `0`
- Done criteria:
  - stakeholder update published weekly with current gate status

## Risks and Mitigations

1. Exchange API instability
- Mitigation: A2 retry/fallback + A5 failure triage.

2. Strategy drift in volatile regimes
- Mitigation: A3 regime logic + A4 drawdown-first constraints.

3. Documentation drift
- Mitigation: A6 owner-only docs governance with A5/A8 mandatory review.

## Weekly Cadence

1. Monday: run full gates and publish artifact links.
2. Wednesday: review drift and adjust risk/model parameters.
3. Friday: publish go/no-go status and next-week priorities.

## Implementation Snapshot (Current)

Date: `2026-02-13`

1. `A1`: `daily-smoke` implemented and passing.
2. `A2`: data freshness check implemented (`make data-freshness`) and passing.
3. `A3`: regime-aware spread adjustment added to paper realtime strategy.
4. `A4`: risk calibration scenario sweep implemented (`make risk-calibration`).
5. `A5`: failure triage and weekly gate review templates added.
6. `A6`: strict docs governance reflected in team and workboard docs.
7. `A7`: weekly reliability summary generator implemented (`make weekly-report`).
8. `A8`: strict team execution plan and role accountability documented.

## Next Realization Step (Implemented)

1. Quant exploration module added: `make quant-experiments`.
2. New robust profile selected from experiments: `trend_shield` (budget 10k, gate pass).
3. Runtime and walk-forward preset updated to quant-selected profile.
4. Multisymbol paper shadow flow activated: `make paper-multisymbol SYMBOLS=BTC/USDT,ETH/USDT`.
5. Combined step-up command added: `make realization-step`.
