# Stakeholder MVP Brief

Коротко для стейкхолдеров.

## Где мы сейчас

- MVP стабильно работает в Docker.
- Realtime работает в paper режиме.
- Live intentionally disabled (`PAPER_ONLY=1`).

## Что доказано

- Reliability: `make validate`
- Backtest stability: `make campaign N=10`
- Quant gate: `make analyze-last-month ...`
- Realtime stream: `make realtime-paper ...`

## Ключевой вывод

- В текущем отчете `ready_for_live_keys=false`.
- Значит API keys не подключаем, продолжаем paper-only.

## Следующий шаг

- execution/risk/fee-aware redesign до положительного quant gate.
