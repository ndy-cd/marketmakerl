# Implemented Changes

Краткий журнал внедренных блоков.

## Что внедрено

1. Runtime и orchestration
- Docker-first запуск и `Makefile`
- Multi-agent runtime (`data/ml/execution/risk`)

2. Data и стратегии
- Public CEX data snapshots
- Last-month quant analysis
- Realtime paper quote loop

3. Качество и тесты
- Unit + integration + campaign
- Исправления liquidation/backtest accounting
- Миграция `gym` -> `gymnasium`

4. Управление и документация
- Расширена команда ролей (A1-A8)
- Добавлен stakeholder пакет и чеклисты
- Включен paper-only lock (`PAPER_ONLY=1`)

## Где смотреть детали

- Каноника: `docs/PROJECT_GUIDE.md`
- План MVP: `docs/MVP_EXECUTION_PLAN.md`
- Бриф для стейкхолдеров: `docs/STAKEHOLDER_MVP_BRIEF.md`
