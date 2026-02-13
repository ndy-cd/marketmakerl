# Deployment Guide

## 1) Local Docker Deployment

```bash
make build
make validate
```

Run paper real-time service:

```bash
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=100 POLL_SECONDS=5
```

## 2) Server Deployment

```bash
make deploy-server SERVER=user@host SERVER_DIR=/opt/marketmakerl
```

After deploy, run on server:

```bash
cd /opt/marketmakerl
make build
make validate
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT
```

## 3) Operations

- Rebuild service image: `make build`
- Full regression check: `make validate`
- Quant/budget research: `make research-budgets EXCHANGE=binance SYMBOL=BTC/USDT`

## 4) Policy

- MVP is paper-only by default.
- Keep `PAPER_ONLY=1` until quant gate passes.
