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
make quant-experiments EXCHANGE=binance SYMBOL=BTC/USDT DAYS=60 WINDOW_DAYS=7 MAX_WINDOWS=6 BUDGETS=5000,10000,15000 VARIANTS=conservative,balanced,adaptive SEEDS=42,99 MAX_TOTAL_RETURN_PCT=1.0
make paper-multisymbol EXCHANGE=binance SYMBOLS=BTC/USDT,ETH/USDT ITERATIONS=5 POLL_SECONDS=1
```

## What We Verify

1. Runtime reliability in Docker.
2. Regression safety for core modules.
3. Artifact generation in `artifacts/`.
4. Real-data flow with no API keys.
5. Strategy risk gate with drawdown failure threshold (`40%`), tail-risk controls (Sortino/CVaR95), and plausibility cap on total return.

## Pass Criteria

- Commands complete without errors.
- Expected artifacts are generated.
- Walk-forward gate is strict and must exit successfully.
- Live commands remain blocked while `PAPER_ONLY=1`.
