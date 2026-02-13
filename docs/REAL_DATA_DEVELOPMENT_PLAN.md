# Real Data Development Plan

Краткий план развития real-data части.

## Текущий статус

- Public market data ingestion: `Implemented`
- Realtime paper quote loop: `Implemented`
- Quant gate по последнему месяцу: `Implemented`
- Live onboarding: `Not allowed now` (paper-only policy)

## Фазы

1. Data reliability
- schema checks
- dedup/order guarantees

2. Strategy economics
- fee-aware logic
- inventory/risk guard tuning

3. Execution readiness
- execution adapter + reconciliation
- kill switch + risk limits

4. Live readiness gate
- `readiness.ready_for_live_keys=true`
- только после этого рассматривать API keys

## Команды контроля

```bash
make real-data-fetch EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```
