# Project Guide

## Purpose

This guide is the single source of truth for:
- What the project does now
- How to run it
- How to test it
- How data flows through the system
- What can be extended next

It is designed for both human contributors and AI agents.

## Current Capabilities

1. Simulated market data generation and preprocessing
- `src/data/data_processor.py`

2. Signal and feature computation
- `src/utils/market_data.py`

3. Market making models
- `src/models/avellaneda_stoikov.py`
- `src/models/rl_enhanced_model.py`

4. Backtesting
- `src/backtesting/backtest_engine.py`

5. Multi-agent runtime orchestration
- `scripts/run_agents.py`
- `src/agents/base.py`
- `config/config.yaml`

6. Test and integration workflows
- `tests/test_market_data_integration.py`
- `tests/test_integration.sh`
- `scripts/integration_example.py`

## Runtime Modes

- `backtest`: safe default, simulation-only execution
- `paper`: reserved mode for paper trading paths
- `live`: requires credentials and fails fast if missing

Live mode environment requirements:
- `EXCHANGE_API_KEY`
- `EXCHANGE_API_SECRET`

## Architecture

```mermaid
flowchart LR
  C[config/config.yaml] --> R[scripts/run_agents.py]
  R --> A[src/agents/base.py]

  A --> D[Data role\nsrc/data/data_processor.py]
  A --> M[ML role\nsrc/models/* + src/utils/market_data.py]
  A --> E[Execution role\nsrc/backtesting/backtest_engine.py]
  A --> K[Risk role\nreport scaffold]

  D --> O1[artifacts/*_market_data.csv]
  E --> O2[artifacts/*_metrics.json]
  K --> O3[artifacts/*_risk_report.json]
```

## Data Flow

1. Data role produces market data
- Generates simulated OHLCV + spread + derived features.
- Writes `artifacts/<run_id>_<agent>_market_data.csv`.

2. ML role computes signals and model quotes
- Reads simulated market frame.
- Computes `volatility`, `trend_strength`, `momentum`, `mean_reversion`.
- Produces bid/ask snapshot in runtime output.

3. Execution role runs enhanced backtest
- Uses model + market features and simulates trades.
- Writes `artifacts/<run_id>_<agent>_metrics.json`.

4. Risk role writes baseline risk report
- Writes `artifacts/<run_id>_<agent>_risk_report.json`.

## How To Run

### Recommended: Docker

Preferred interface is Makefile:

```bash
make validate
```

This executes:
- `make build`
- `make run-backtest`
- `make test`
- `make live-guard`

If you need step-by-step:

1. Build image

```bash
make build
```

2. Run backtest mode

```bash
make run-backtest
```

Expected result:
- Exit code `0`
- Log event `runtime_complete` with `failures: 0`
- Files created in `artifacts/`

### Override command and mode

```bash
make run MODE=backtest MAX_WORKERS=4
```

### Live mode (guarded)

Without secrets, expected failure:

```bash
make live-guard
```

Expected error:
- `mode=live requires env vars: EXCHANGE_API_KEY, EXCHANGE_API_SECRET`

With secrets:

```bash
EXCHANGE_API_KEY=your_key EXCHANGE_API_SECRET=your_secret make run-live
```

## How To Test

### Unit tests

```bash
make test-unit
```

Expected:
- All discovered `tests/test_*.py` suites pass
- Final status `OK`

### Integration workflow

```bash
make test-integration
```

Expected:
- Unit tests pass
- Integration example runs
- Visualization images updated in `visualizations/`

### Quality gates (team contract)

Defined in `agent_ops/team.yaml`:
- `make validate`

Make and Docker-equivalent commands are above.

## What You Can Do Next

1. Connect real exchange execution paths
- Extend `DataProcessor.connect_exchange()` and execution role path.

2. Replace Gym with Gymnasium
- `src/models/rl_enhanced_model.py` currently imports `gym`.
- Runtime works, but Gym emits deprecation warnings.

3. Add strict metrics schema validation
- Validate `artifacts/*_metrics.json` against a JSON schema.

4. Add CI pipeline
- Run Docker build + test commands on each pull request.

5. Expand risk role
- Move from scaffold report to real risk controls and kill-switch behavior.

## AI Agent Onboarding

### Stable contracts

- Runtime config contract: `config/config.yaml`
- Runtime entrypoint: `scripts/run_agents.py`
- Runtime role implementations: `src/agents/base.py`
- Shared artifacts path: `artifacts/`
- Team ownership map: `agent_ops/team.yaml`

### Edit boundaries

- Runtime scaffolding: `scripts/`, `config/`, `src/agents/`
- Data/signal: `src/data/`, `src/utils/market_data.py`
- Models: `src/models/`
- Backtest/risk metrics: `src/backtesting/`
- Tests/docs: `tests/`, `README.md`, `docs/`

### Safe defaults

- Prefer `mode=backtest`
- Do not run `mode=live` without explicit user request and credentials

## Troubleshooting

1. Docker daemon permission errors
- Ensure Docker Desktop is running.
- Re-run with `docker compose build` then `docker compose run --rm agents`.

2. Missing dependency errors
- Rebuild image after dependency changes:

```bash
make build
```

3. No artifacts generated
- Check command exit code and logs for `agent_failed` events.
- Validate `config/config.yaml` has at least one agent per required role.

## Related Docs

- `README.md`: quick entrypoint
- `docs/FEATURE_CATALOG.md`: full feature inventory with implementation status
- `docs/IMPLEMENTED_CHANGES.md`: detailed record of implemented changes
- `docs/completed_enhancements.md`: MVP enhancement summary
- `docs/documentation_acceptance_checklist.md`: doc quality gate
- `Makefile`: canonical command interface for run/test/validate
- `agent_ops/research_alignment.md`: planning assumptions and merge sequencing
