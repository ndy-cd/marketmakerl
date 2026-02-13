# Project Guide

Канонический технический документ проекта.

## 1) Что это за MVP

- Docker-first система для market making в режиме `backtest` и `paper`.
- Поддерживает:
  - симуляцию и бэктесты
  - публичные market-data источники (без API ключей)
  - paper realtime quote loop
- Live-режим заблокирован по политике: `PAPER_ONLY=1`.

## 2) Быстрый запуск

```bash
make validate
make campaign N=10
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

## 3) Политика безопасности

- Разрешено: `backtest`, `paper`.
- Ограничено: `live`.
- При `PAPER_ONLY=1` заблокированы:
  - `make run-live`
  - `make realtime-live`

## 4) Архитектура (кратко)

1. Runtime orchestration
- `scripts/run_agents.py`
- `src/agents/base.py`
- `config/config.yaml`

2. Data
- `src/data/data_processor.py`
- `src/data/real_market_data.py`
- `scripts/fetch_real_market_data.py`

3. Models
- `src/models/avellaneda_stoikov.py`
- `src/models/rl_enhanced_model.py`

4. Backtest / metrics
- `src/backtesting/backtest_engine.py`
- артефакты в `artifacts/`

5. Realtime paper service
- `scripts/run_realtime_strategy.py`
- `docker-compose.server.yml`
- `scripts/deploy_server.sh`

## 5) Поток данных

1. Источник данных:
- simulation (`data_processor`)
- public CEX snapshots (`real_market_data`)

2. Обработка:
- сигналы и признаки (`src/utils/market_data.py`)

3. Стратегия:
- модель формирует bid/ask

4. Исполнение:
- backtest engine (или paper realtime loop)

5. Артефакты:
- `artifacts/*_metrics.json`
- `artifacts/campaign_*/campaign_report.json`
- `artifacts/last_month_analysis/*_analysis.json`
- `artifacts/realtime/*.jsonl`

## 6) Что проверяем перед любым релизом

1. Надежность:
```bash
make validate
```

2. Стабильность бэктеста:
```bash
make campaign N=10
```

3. Quant-gate за последний месяц:
```bash
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```

Ключевой флаг в отчете:
- `readiness.ready_for_live_keys`

## 7) Текущее состояние MVP

- Технически работает гладко в paper/backtest режиме.
- Realtime paper сервис развертывается и пишет поток котировок.
- `ready_for_live_keys` пока `false` (стратегия экономически не готова к live).

## 8) Следующий этап (в работе)

- execution adapter (submit/cancel/replace/reconcile)
- hard risk guards (limits, stale-data guard, kill switch)
- fee-aware quoting и снижение overtrading

## 9) Навигация по документации

- Карта документов: `docs/DOCS_INDEX.md`
- Для stakeholders: `docs/STAKEHOLDER_MVP_BRIEF.md`
- Для деплоя: `docs/DEPLOYMENT_GUIDE.md`
