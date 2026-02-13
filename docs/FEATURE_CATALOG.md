# Feature Catalog

Краткий каталог фич проекта.
Подробности и запуск: `docs/PROJECT_GUIDE.md`.

## Runtime

- Docker runtime и Make-команды: `Implemented`
- Multi-agent orchestration (`data/ml/execution/risk`): `Implemented`
- Paper-only lock (`PAPER_ONLY=1`): `Implemented`

## Data

- Simulation data pipeline: `Implemented`
- Public CEX snapshot collection: `Implemented`
- Realtime quote loop on public data: `Implemented`
- Onchain handler: `Placeholder`

## Models

- Avellaneda-Stoikov: `Implemented`
- RL-enhanced (gymnasium): `Implemented`

## Backtesting

- Standard + enhanced backtest: `Implemented`
- Campaign run (`N=10`): `Implemented`
- Last-month quant gate: `Implemented`

## Quality Gates

- `make validate`: `Implemented`
- `make test-unit`: `Implemented`
- `make test-integration`: `Implemented`

## Deployment

- Paper realtime service via `docker-compose.server.yml`: `Implemented`
- Remote deploy script: `Implemented`
