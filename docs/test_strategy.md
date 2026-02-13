# Test Strategy

## Mandatory Commands

```bash
make validate
make campaign N=10
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
make data-freshness EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m
make weekly-report
make quant-experiments EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30
make paper-multisymbol EXCHANGE=binance SYMBOLS=BTC/USDT,ETH/USDT ITERATIONS=5 POLL_SECONDS=1
```

## What We Verify

1. Runtime reliability in Docker.
2. Regression safety for core modules.
3. Artifact generation in `artifacts/`.
4. Real-data flow with no API keys.
5. Strategy risk gate with drawdown failure threshold (`40%`).

## Pass Criteria

- Commands complete without errors.
- Expected artifacts are generated.
- Walk-forward gate is strict and must exit successfully.
- Live commands remain blocked while `PAPER_ONLY=1`.
