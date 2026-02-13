# Real-Data Development Plan

## Current Baseline

- Real market data ingestion from public exchange endpoints is available.
- Paper real-time strategy loop is available.
- Last-month quant research is available with budget tiers and format comparisons.

## Next Steps

1. Improve strategy economics:
- reduce overtrading
- improve fee-adjusted edge quality
- stabilize drawdown behavior

2. Strengthen execution realism:
- better fill probability calibration
- slippage/latency sensitivity tests

3. Quant gate target:
- positive PnL
- positive Sharpe
- max drawdown not worse than `40%` of budget

4. Live-key onboarding prerequisites:
- all gates green in repeated runs
- operational runbooks complete
- explicit approval to move from paper to live

## Control Commands

```bash
make real-data-fetch EXCHANGE=binance SYMBOL=BTC/USDT
make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT
```
