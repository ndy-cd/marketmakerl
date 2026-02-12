# Test Strategy (No API Keys)

## Goal
Validate all project flows that do not require exchange credentials and stress backtest stability with repeated runs.

## Scope
- Docker image build and compose configuration
- Backtest runtime orchestration (`mode=backtest`)
- Unit and integration test suites
- Live-mode safety guard (expected failure without keys)

## Command Plan
1. `make build`
2. `make test`
3. `make live-guard` (must fail with expected env-var error)
4. Backtest campaign: run `make campaign N=10` and collect aggregated metrics from campaign report

## Acceptance Criteria
- All non-live commands succeed with exit code 0
- Live guard fails for the correct reason
- 10+ backtests complete and produce parsable metrics
- Campaign report includes min/mean/max for key metrics (total_pnl, sharpe_ratio, max_drawdown)
