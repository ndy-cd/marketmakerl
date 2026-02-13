# MVP Execution Plan

План MVP в одном месте.

## Статус фаз

1. Runtime + tests: `Done`
2. Real data ingestion: `Done`
3. Backtest campaign: `Done`
4. Quant gate: `Done` (но verdict пока negative)
5. Realtime paper deployment: `Done`
6. Paper-only lock: `Done`
7. Execution/risk/fee-aware redesign: `In Progress`

## Release gate (обязательный)

- `make validate`
- `make campaign N=10`
- `make analyze-last-month ...`
- в отчете: `readiness.ready_for_live_keys=true`

## Текущее решение

- Сейчас `ready_for_live_keys=false`.
- Работаем только в paper режиме (`PAPER_ONLY=1`).
- Статус по агентам: `agent_ops/WORKBOARD.md`
