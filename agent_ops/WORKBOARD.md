# Agent Workboard (A1-A10)

Single shared board for MVP execution status.

## Sprint Goal

Stable paper-only MVP with clear technical and stakeholder documentation.

## Documentation Ownership (Strict)

- Owner: `A6 Documentation Architect` (single owner).
- Mandatory reviewers: `A5 QA and Integration Engineer`, `A8 Project Manager`.
- Rule: no docs PR/commit is accepted without owner approval and reviewer sign-off.
- Scope: `README.md`, `docs/`, `agent_ops/` project-facing docs.

## Status by Agent

1. `A1 Runtime Orchestrator` - `Done`
- Scope: runtime orchestration, Makefile, safety policy.
- Result: paper-only lock enabled (`PAPER_ONLY=1`), live commands blocked.

2. `A2 Data and Signal Engineer` - `Done`
- Scope: data ingestion and signal path.
- Result: stable no-key flow for public CEX snapshots and klines.

3. `A3 Modeling Engineer` - `In Progress`
- Scope: quote model behavior.
- Focus: reliability-first preset tuning and regime adaptation.

4. `A4 Backtest and Risk Engineer` - `Done`
- Scope: backtest realism and risk controls.
- Result: strict walk-forward gate + reduced drawdown tail under reliability preset.

5. `A5 QA and Integration Engineer` - `Done`
- Scope: tests and integration.
- Result: stable `make validate`, `make campaign`, `make test` workflows.

6. `A6 Documentation Architect` - `Done`
- Scope: docs structure and readability.
- Result: strict docs ownership, compact English set, and gate-aligned guidance.

7. `A7 Quant Researcher` - `Done`
- Scope: quant readiness gate.
- Result: budget-tier/strategy-format research, walk-forward gate, and readiness verdict.
- Current result: reliability preset selected (`inventory_defensive_mm`) with strict gate pass.

8. `A8 Project Manager` - `Done`
- Scope: MVP milestone governance.
- Focus: lock launch workflow and sign-off criteria.

9. `A9 Dashboard Designer` - `Done`
- Scope: stakeholder dashboard readability and narrative quality.
- Result: dashboard refocused on robust statistics and decision-friendly KPI cards.

10. `A10 Statistical Reliability Analyst` - `Done`
- Scope: quant metric reliability and plausibility controls.
- Result: experiment gates include robust risk metrics plus implausible-return filter.

## Hard Gates

```bash
make validate
make campaign N=10
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
make daily-smoke EXCHANGE=binance SYMBOL=BTC/USDT
```

## Current Decision

- MVP remains `paper-only`.
- Paper launch can proceed with the reliability preset and strict walk-forward gate.
- Do not connect exchange API keys until paper operations remain stable in repeated cycles.
- Active strict execution plan: `agent_ops/TEAM_ACTION_PLAN_STRICT.md`.
- Active per-agent report set: `agent_ops/TEAM_MEMBER_REPORTS.md`.
