# MVP Sign-Off Checklist

- [ ] `make validate` passes.
- [ ] `make campaign N=10` passes.
- [ ] `make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT` generates analysis artifacts.
- [ ] `make walk-forward EXCHANGE=binance SYMBOL=BTC/USDT DAYS=30` passes stability gate.
- [ ] Readiness checks reviewed (`positive_pnl`, `positive_sharpe`, `drawdown_below_40pct_budget`).
- [ ] `make realtime-paper ...` writes `artifacts/realtime/*.jsonl`.
- [ ] `PAPER_ONLY=1` is enabled.
- [ ] `make run-live` and `make realtime-live` are blocked.
- [ ] Documentation set is consistent and fully English.
