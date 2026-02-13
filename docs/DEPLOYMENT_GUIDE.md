# Deployment Guide

## Scope

This guide covers deployment of the real-time strategy quote loop to a remote server using Docker.
It does not place exchange orders yet; it runs real market data strategy quoting.
Default runtime is paper-only (`PAPER_ONLY=1`).

## Prerequisites

- Remote Linux server with Docker and Docker Compose.
- SSH access: `user@host`.
- Optional exchange keys for guarded live mode:
  - `EXCHANGE_API_KEY`
  - `EXCHANGE_API_SECRET`

## Local Pre-Deploy Checks

```bash
make validate
make campaign N=10
make analyze-last-month EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24
```

## Realtime Strategy (local smoke)

```bash
make realtime-paper EXCHANGE=binance SYMBOL=BTC/USDT TIMEFRAME=1m ITERATIONS=20 POLL_SECONDS=5
```

Expected output:
- JSON lines per iteration.
- Artifact file in `artifacts/realtime/`.

## Server Deploy

```bash
make deploy-server SERVER=user@host SERVER_DIR=/opt/marketmakerl
```

This performs:
1. Creates remote directory.
2. Syncs repository files via `rsync`.
3. Builds and starts `realtime-strategy` service using `docker-compose.server.yml`.

## Server Operations

Start or restart:

```bash
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml up -d realtime-strategy"
```

Logs:

```bash
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml logs -f realtime-strategy"
```

Stop:

```bash
ssh user@host "cd /opt/marketmakerl && docker compose -f docker-compose.server.yml stop realtime-strategy"
```

Paper-only policy:
- `PAPER_ONLY=1` blocks live-mode commands by design.
- Keep this enabled until `ready_for_live_keys=true` in quant gate output.

## Rollback

1. On server, checkout previous known-good commit.
2. Rebuild and restart service:

```bash
ssh user@host "cd /opt/marketmakerl && git checkout <commit> && docker compose -f docker-compose.server.yml build && docker compose -f docker-compose.server.yml up -d realtime-strategy"
```
