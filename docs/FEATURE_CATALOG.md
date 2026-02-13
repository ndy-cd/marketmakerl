# Feature Catalog

This file documents all current features and their implementation status.

## Legend
- `Implemented`: usable now and covered by tests/workflows
- `Partial`: usable with constraints
- `Placeholder`: interface exists, production behavior not yet implemented

## Runtime and Orchestration

1. Dockerized runtime execution (`Implemented`)
- Files: `Dockerfile`, `docker-compose.yml`, `docker/requirements.runtime.txt`
- Command surface: `Makefile`
- Notes: Docker is the canonical runtime path.

2. Multi-agent orchestration (`Implemented`)
- Files: `scripts/run_agents.py`, `src/agents/base.py`, `config/config.yaml`
- Roles: `data`, `ml`, `execution`, `risk`
- Outputs: artifacts under `artifacts/`.

3. Runtime mode safety (`Implemented`)
- Modes: `backtest`, `paper`, `live`
- Live guard requires: `EXCHANGE_API_KEY`, `EXCHANGE_API_SECRET`

## Data Layer

1. Simulated market data generation (`Implemented`)
- File: `src/data/data_processor.py`
- Function: `simulate_market_data`
- Output includes: OHLCV, spread, technical features.

2. File-based ingest/export (`Implemented`)
- File: `src/data/data_processor.py`
- Functions: `load_from_file`, `save_to_file`
- Formats: CSV, PKL, JSON.

3. CEX public market data (`Implemented`)
- File: `src/data/data_processor.py`
- Functions: `connect_exchange`, `fetch_historical_data`
- Notes: public market data can be fetched without private API keys for supported venues.

4. Real snapshot collector module (`Implemented`)
- File: `src/data/real_market_data.py`
- Functions: `fetch_klines`, `fetch_order_book`, `fetch_trades`, `fetch_snapshot`, `save_snapshot`
- Script: `scripts/fetch_real_market_data.py`
- Notes: optimized for lightweight snapshot polling and storage.

5. Realtime quote strategy loop (`Implemented`)
- Script: `scripts/run_realtime_strategy.py`
- Data source: public CEX market data via ccxt
- Outputs: JSONL quote stream under `artifacts/realtime/`

5. CEX-onchain synchronization (`Implemented`)
- File: `src/data/data_processor.py`
- Function: `sync_cex_with_onchain`
- Notes: fixed frequency-inference and mixed-dtype resampling issues.

6. Onchain data handler (`Placeholder`)
- File: `src/utils/market_data.py`
- Class: `OnchainDataHandler`
- Notes: returns stub pool payload; no real RPC/indexer integration yet.

## Signal and Modeling

1. Signal computation (`Implemented`)
- File: `src/utils/market_data.py`
- Function: `calculate_signals`
- Signals: volatility, trend strength, momentum, mean reversion, spread/volume derivatives.

2. Baseline market making model (`Implemented`)
- File: `src/models/avellaneda_stoikov.py`
- Core: reservation price + spread logic, inventory awareness, quote bounds.

3. RL-enhanced model and env (`Implemented`)
- File: `src/models/rl_enhanced_model.py`
- Notes: uses `gymnasium` environment interface.

## Backtesting

1. Standard and enhanced backtests (`Implemented`)
- File: `src/backtesting/backtest_engine.py`
- Functions: `run_backtest`, `run_backtest_enhanced`
- Outputs: metrics/trades/positions.
- Supports strategy parameter passthrough (including `spread_constraint`) from backtest params.

2. Latency and signal-influenced behavior (`Implemented`)
- File: `src/backtesting/backtest_engine.py`
- Notes: enhanced mode uses signals and short-term move proxy.

## Testing and Quality Gates

1. Unit tests (`Implemented`)
- Command: `make test-unit`
- Mechanism: `python -m unittest discover -s tests -p "test_*.py"`
- Current scope: data sources, baseline algorithm, runtime config, integration-level market data tests.

2. Integration test (`Implemented`)
- Command: `make test-integration`
- Script: `tests/test_integration.sh`
- Includes integration example + visualization generation.

3. Reliability pipeline (`Implemented`)
- Command: `make validate`
- Pipeline: build -> run-backtest -> test -> live-guard.

4. Backtest campaign (`Implemented`)
- Command: `make campaign N=10`
- Script: `scripts/run_backtest_campaign.sh`
- Output: `artifacts/campaign_<timestamp>/campaign_report.json`

5. Last-month quant adaptation gate (`Implemented`)
- Command: `make analyze-last-month ...`
- Script: `scripts/analyze_last_month_strategy.py`
- Output: ranked strategies + readiness verdict under `artifacts/last_month_analysis/`

## Documentation and Agent Ops

1. Canonical project guide (`Implemented`)
- File: `docs/PROJECT_GUIDE.md`

2. Test strategy (`Implemented`)
- File: `docs/test_strategy.md`

3. Documentation acceptance checklist (`Implemented`)
- File: `docs/documentation_acceptance_checklist.md`

4. Parallel agent plan, prompts, skills (`Implemented`)
- Files: `agent_ops/team.yaml`, `agent_ops/prompts/*`, `agent_ops/skills/*`

5. Server deployment workflow (`Implemented`)
- Files: `docker-compose.server.yml`, `scripts/deploy_server.sh`, `docs/DEPLOYMENT_GUIDE.md`

6. Stakeholder MVP package (`Implemented`)
- Files: `docs/STAKEHOLDER_MVP_BRIEF.md`, `docs/MVP_SIGNOFF_CHECKLIST.md`, `docs/MVP_EXECUTION_PLAN.md`
