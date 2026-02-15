# Team Action Plan (Strict) - A1 to A11

Planning window: `2026-02-15` to `2026-03-15`

## Objective

Move from demo-grade quant evidence to production-grade paper trading readiness under strict one-minute data and execution realism controls.

## Global Non-Negotiable Gates

1. `make validate` must pass.
2. `make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m DAYS=30` must pass.
3. `make release-guardrails` must pass.
4. `make consistency-check` must pass.
5. `PAPER_ONLY=1` must remain enabled.

## Strict Metric Contract (Release Guardrails)

Command:

```bash
make release-guardrails
```

Hard thresholds:

1. Campaign:
- mean `total_pnl >= 0`
- mean `sharpe_ratio >= 0.50`

2. Walk-forward:
- `gate.pass = true`
- `hard_fail_windows = 0`
- `pass_rate >= 0.60`

3. Weekly reliability:
- `status = pass`

4. Quant recommendation:
- `gate_pass = true`
- `max_drawdown_pct <= 0.40`
- `cvar_95_pct <= 0.03`
- `sortino_ratio >= 0.20`
- `pass_rate >= 0.65`
- `fill_ratio >= 0.20`
- `execution_cost_bps <= 5.0`
- `realized_edge_bps <= 12.0`
- `total_return_pct <= 0.25`

5. One-minute data quality:
- quant `meta.timeframe == 1m`
- `data_profile.rows >= 10000`
- `interval_seconds_median` in `[50.0, 70.0]`
- `start_utc` and `end_utc` must be present

6. Dashboard security posture:
- secure serving script exists
- Makefile uses secure server path
- bind host remains loopback-only
- `python3 -m http.server` is not used for dashboard serving

Policy:

- Any red guardrail is release-blocking.
- PM (`A8`) owns stop/go decision.
- Statistical interpretation ownership: `A10`.
- Artifact integrity ownership: `A5`.

## Team Plan by Agent

1. `A1 Runtime Orchestrator` (`P0`)
- Maintain deterministic Docker execution and image-rebuild discipline.
- Deliverable: stable `make production-grade-step` flow.

2. `A2 Data and Signal Engineer` (`P0`)
- Enforce one-minute freshness checks before quant runs.
- Deliverable: no stale data profile in quant artifacts.

3. `A3 Modeling Engineer` (`P1`)
- Keep strategy bounds realistic for 1m microstructure.
- Deliverable: parameter bound note for expanded profile generation.

4. `A4 Backtest and Risk Engineer` (`P0`)
- Audit slippage, latency, impact, and adverse-selection penalties.
- Deliverable: risk note on execution realism and liquidation behavior.

5. `A5 QA and Integration Engineer` (`P0`)
- Run blocker checks on every phase handoff.
- Deliverable: green guardrail + consistency report pair.

6. `A6 Documentation Architect` (`P0`, owner)
- Keep README/docs/agent_ops synchronized with E7 commands and policy.
- Deliverable: no command drift across docs.

7. `A7 Quant Researcher` (`P0`)
- Run deep top-20 validation on 1m data and compare stability metrics.
- Deliverable: promoted candidate only if full deep pass.

8. `A8 Project Manager` (`P0`)
- Enforce no-skip phase gates.
- Deliverable: explicit go/no-go note per phase.

9. `A9 Dashboard Designer` (`P1`)
- Keep dashboard modern, readable, and honest about missing data.
- Deliverable: `n/a` rendering for missing coverage/execution sources.

10. `A10 Statistical Reliability Analyst` (`P0`)
- Own plausibility and statistical defensibility interpretation.
- Deliverable: reject over-optimistic candidates even when raw return is high.

11. `A11 Cybersecurity and Platform Security Engineer` (`P0`)
- Guard local/demo serving exposure paths.
- Deliverable: periodic serving hardening review note.

## E7 Production Bridge Workflow

Use this command chain:

1. `make version-rebuild VERSION=e7-round1`
2. `make data-freshness EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m`
3. `make quant-experiments-1m EXCHANGE=binance SYMBOL=BTC/USDT DAYS=14 WINDOW_DAYS=2 MAX_WINDOWS=6 BUDGETS=5000,10000 VARIANTS=conservative,balanced,adaptive SEEDS=21,42,99 MAX_TOTAL_RETURN_PCT=0.25`
4. `make quant-top20-deep-1m EXCHANGE=binance SYMBOL=BTC/USDT`
5. `make release-guardrails`
6. `make consistency-check`
7. `make stakeholder-dashboard`
8. `make publish-showcase`

Equivalent one-command target:

```bash
make production-grade-step VERSION=e7-round1 EXCHANGE=binance SYMBOL=BTC/USDT
```

## E7 Acceptance

1. One-minute data coverage and interval checks pass in guardrails.
2. Deep validation passes for all selected top-20 strategies.
3. No dashboard security regression.
4. Docs and command contract remain consistent.
5. Dashboard is regenerated from latest artifacts.

## Strategy Selection Policy (Reliability First)

1. Hard reject if any gate fails.
2. Rank surviving candidates by robustness and stability, not raw return.
3. Use raw return only as a tiebreaker after risk and stability checks.
4. Keep strategy recommendation in paper-only mode until repeated E7 cycles remain green.
