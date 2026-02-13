# Weekly Gate Review Template

## Week

- Week start (UTC):
- Week end (UTC):

## Gate Results

1. `make validate`: pass/fail
2. `make campaign N=10`: pass/fail
3. `make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT`: pass/fail
4. `make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30`: pass/fail
5. `make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20`: pass/fail

## Reliability Summary

- Campaign mean PnL:
- Campaign max drawdown mean:
- Walk-forward pass:
- Hard fail windows:
- Latest realtime artifact:

## Decisions

- Go/No-Go for continued paper operations:
- Rollback required: yes/no
- Priority work for next week:

## Sign-Off

- A5 (QA):
- A6 (Docs):
- A7 (Quant):
- A8 (PM):
