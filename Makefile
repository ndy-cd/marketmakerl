SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

COMPOSE ?= docker compose
CONFIG ?= config/config.yaml
MODE ?= backtest
MAX_WORKERS ?= 4
EXCHANGE ?= binance
SYMBOL ?= BTC/USDT
TIMEFRAME ?= 1m
KLINE_LIMIT ?= 200
ORDER_BOOK_LIMIT ?= 50
TRADES_LIMIT ?= 200
OUTPUT_DIR ?= data/real
DAYS ?= 30
BATCH_LIMIT ?= 1000
MAX_COMBINATIONS ?= 12
ITERATIONS ?= 20
POLL_SECONDS ?= 5
SPREAD_CONSTRAINT ?= 0.001
SERVER ?=
SERVER_DIR ?= /opt/marketmakerl
PAPER_ONLY ?= 1

.PHONY: help build run run-backtest run-live test test-unit test-integration validate live-guard compose-config campaign real-data-fetch analyze-last-month research-budgets walk-forward mvp-launch realtime-paper realtime-live deploy-server

help:
	@echo "Targets:"
	@echo "  make build             - Build runtime image"
	@echo "  make run               - Run agents with MODE=$(MODE)"
	@echo "  make run-backtest      - Run agents in backtest mode"
	@echo "  make run-live          - Run agents in live mode (requires API env vars)"
	@echo "                          disabled while PAPER_ONLY=1"
	@echo "  make test-unit         - Run unittest suite in Docker"
	@echo "  make test-integration  - Run integration script in Docker"
	@echo "  make test              - Run unit + integration tests"
	@echo "  make live-guard        - Validate that live mode fails without secrets"
	@echo "  make validate          - Full reliability validation pipeline"
	@echo "  make campaign N=10     - Run N backtests and aggregate metrics"
	@echo "  make real-data-fetch   - Fetch real market snapshot (klines/orderbook/trades)"
	@echo "  make analyze-last-month - Run real-data strategy analysis and parameter sweep"
	@echo "  make research-budgets   - Run budget/strategy-format research over last month"
	@echo "  make walk-forward      - Run walk-forward stability gate on recent real data"
	@echo "  make mvp-launch        - Full MVP readiness workflow (validate+campaign+research+walk-forward+paper)"
	@echo "  make realtime-paper     - Run realtime quote strategy (public data, no keys)"
	@echo "  make realtime-live      - Run realtime strategy with key guard"
	@echo "                           disabled while PAPER_ONLY=1"
	@echo "  make deploy-server SERVER=user@host [SERVER_DIR=/opt/marketmakerl]"
	@echo "  make compose-config    - Validate compose config"

compose-config:
	$(COMPOSE) config >/dev/null

build: compose-config
	$(COMPOSE) build

run:
	$(COMPOSE) run --rm -e PAPER_ONLY=$(PAPER_ONLY) agents python3 scripts/run_agents.py --config $(CONFIG) --mode $(MODE) --max-workers $(MAX_WORKERS)

run-backtest:
	$(MAKE) run MODE=backtest

run-live:
	@if [ "$(PAPER_ONLY)" = "1" ]; then echo "run-live is blocked: PAPER_ONLY=1"; exit 1; fi
	@test -n "$${EXCHANGE_API_KEY:-}" || (echo "EXCHANGE_API_KEY is required" && exit 1)
	@test -n "$${EXCHANGE_API_SECRET:-}" || (echo "EXCHANGE_API_SECRET is required" && exit 1)
	$(MAKE) run MODE=live

test-unit:
	$(COMPOSE) run --rm agents python3 -m unittest discover -s tests -p "test_*.py"

test-integration:
	$(COMPOSE) run --rm agents bash tests/test_integration.sh

test: test-unit test-integration

live-guard:
	@set +e; \
	out="$$( $(COMPOSE) run --rm -e PAPER_ONLY=$(PAPER_ONLY) agents python3 scripts/run_agents.py --config $(CONFIG) --mode live --max-workers 2 2>&1 )"; \
	code=$$?; \
	set -e; \
	echo "$$out"; \
	if [ $$code -eq 0 ]; then \
		echo "Expected live mode to fail without secrets, but it succeeded"; \
		exit 1; \
	fi; \
	echo "$$out" | grep -Eq "mode=live requires env vars|mode=live is disabled while PAPER_ONLY=1" || (echo "Unexpected live-guard failure message" && exit 1)

validate: build run-backtest test live-guard

campaign:
	./scripts/run_backtest_campaign.sh $(N)

real-data-fetch:
	$(COMPOSE) run --rm agents python3 scripts/fetch_real_market_data.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe $(TIMEFRAME) --kline-limit $(KLINE_LIMIT) --order-book-limit $(ORDER_BOOK_LIMIT) --trades-limit $(TRADES_LIMIT) --output-dir $(OUTPUT_DIR)

analyze-last-month:
	$(COMPOSE) run --rm agents python3 scripts/analyze_last_month_strategy.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe $(TIMEFRAME) --days $(DAYS) --batch-limit $(BATCH_LIMIT) --initial-capital 10000 --budget-tiers 2500,5000,10000 --drawdown-fail-pct 0.40 --max-combinations $(MAX_COMBINATIONS)

research-budgets:
	$(MAKE) analyze-last-month TIMEFRAME=15m DAYS=30 MAX_COMBINATIONS=24

walk-forward:
	$(COMPOSE) run --rm agents python3 scripts/walk_forward_gate.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe 15m --days $(DAYS)

mvp-launch:
	$(MAKE) validate
	$(MAKE) campaign N=10
	$(MAKE) research-budgets EXCHANGE=$(EXCHANGE) SYMBOL=$(SYMBOL)
	$(MAKE) walk-forward EXCHANGE=$(EXCHANGE) SYMBOL=$(SYMBOL) DAYS=$(DAYS)
	$(MAKE) realtime-paper EXCHANGE=$(EXCHANGE) SYMBOL=$(SYMBOL) TIMEFRAME=1m ITERATIONS=20 POLL_SECONDS=2

realtime-paper:
	$(COMPOSE) run --rm -e PAPER_ONLY=$(PAPER_ONLY) agents python3 scripts/run_realtime_strategy.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe $(TIMEFRAME) --iterations $(ITERATIONS) --poll-seconds $(POLL_SECONDS) --spread-constraint $(SPREAD_CONSTRAINT)

realtime-live:
	@if [ "$(PAPER_ONLY)" = "1" ]; then echo "realtime-live is blocked: PAPER_ONLY=1"; exit 1; fi
	@test -n "$${EXCHANGE_API_KEY:-}" || (echo "EXCHANGE_API_KEY is required" && exit 1)
	@test -n "$${EXCHANGE_API_SECRET:-}" || (echo "EXCHANGE_API_SECRET is required" && exit 1)
	$(COMPOSE) run --rm -e EXCHANGE_API_KEY -e EXCHANGE_API_SECRET -e PAPER_ONLY=$(PAPER_ONLY) agents python3 scripts/run_realtime_strategy.py --exchange $(EXCHANGE) --symbol $(SYMBOL) --timeframe $(TIMEFRAME) --iterations $(ITERATIONS) --poll-seconds $(POLL_SECONDS) --spread-constraint $(SPREAD_CONSTRAINT) --require-keys

deploy-server:
	@test -n "$(SERVER)" || (echo "SERVER is required, e.g. make deploy-server SERVER=user@host" && exit 1)
	bash scripts/deploy_server.sh $(SERVER) $(SERVER_DIR)
