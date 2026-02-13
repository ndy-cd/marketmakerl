# Deployment Guide

Короткий гайд по деплою paper realtime сервиса.

## Перед деплоем

```bash
make validate
make campaign N=10
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```

## Локальный smoke

```bash
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20
```

## Деплой на сервер

```bash
make deploy-server SERVER=user@host SERVER_DIR=/opt/marketmakerl
```

## Управление сервисом

```bash
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml up -d realtime-strategy"
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml logs -f realtime-strategy"
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml stop realtime-strategy"
```

## Политика

- Только paper режим.
- `PAPER_ONLY=1` должен оставаться включенным.
