# Test Strategy (No API Keys)

Короткая стратегия тестов MVP.

## Команды

```bash
make validate
make campaign N=10
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

## Критерии

- Команды завершаются без ошибок
- Артефакты генерируются в `artifacts/`
- Live команды остаются заблокированы при `PAPER_ONLY=1`
