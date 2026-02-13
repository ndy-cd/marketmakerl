# Agent Workboard (A1-A8)

Единая рабочая доска команды.  
Обновляется при каждом заметном изменении MVP.

## Sprint Goal

Стабильный paper-only MVP с понятной документацией для команды и стейкхолдеров.

## Status by Agent

1. `A1 Runtime Orchestrator` - `Done`
- Область: runtime orchestration, `Makefile`, safety policy.
- Результат: paper-only lock (`PAPER_ONLY=1`), live-команды блокируются.

2. `A2 Data and Signal Engineer` - `Done`
- Область: data ingestion/signal path.
- Результат: public CEX snapshots + стабильный no-key data flow.

3. `A3 Modeling Engineer` - `In Progress`
- Область: модель и котирование.
- Текущий фокус: fee-aware adjustments и снижение overtrading.

4. `A4 Backtest and Risk Engineer` - `In Progress`
- Область: backtest realism, risk controls.
- Текущий фокус: execution adapter contract + hard risk guards.

5. `A5 QA and Integration Engineer` - `Done`
- Область: тесты/интеграция.
- Результат: стабильные команды `make validate`, `make campaign`, `make test`.

6. `A6 Documentation Architect` - `Done`
- Область: документация.
- Результат: единая упрощенная структура docs без удаления файлов.

7. `A7 Quant Researcher` - `In Progress`
- Область: quant gate.
- Результат: `analyze-last-month` + readiness verdict.
- Статус: `ready_for_live_keys=false`.

8. `A8 Project Manager` - `Done`
- Область: MVP план и координация.
- Результат: единые gate-правила и roadmap следующей фазы.

## Hard Gates

```bash
make validate
make campaign N=10
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```

## Current Decision

- MVP идет в `paper-only` режиме.
- API keys не подключаем до `readiness.ready_for_live_keys=true`.
