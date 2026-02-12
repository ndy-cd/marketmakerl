SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

COMPOSE ?= docker compose
CONFIG ?= config/config.yaml
MODE ?= backtest
MAX_WORKERS ?= 4

.PHONY: help build run run-backtest run-live test test-unit test-integration validate live-guard compose-config campaign

help:
	@echo "Targets:"
	@echo "  make build             - Build runtime image"
	@echo "  make run               - Run agents with MODE=$(MODE)"
	@echo "  make run-backtest      - Run agents in backtest mode"
	@echo "  make run-live          - Run agents in live mode (requires API env vars)"
	@echo "  make test-unit         - Run unittest suite in Docker"
	@echo "  make test-integration  - Run integration script in Docker"
	@echo "  make test              - Run unit + integration tests"
	@echo "  make live-guard        - Validate that live mode fails without secrets"
	@echo "  make validate          - Full reliability validation pipeline"
	@echo "  make campaign N=10     - Run N backtests and aggregate metrics"
	@echo "  make compose-config    - Validate compose config"

compose-config:
	$(COMPOSE) config >/dev/null

build: compose-config
	$(COMPOSE) build

run:
	$(COMPOSE) run --rm agents python3 scripts/run_agents.py --config $(CONFIG) --mode $(MODE) --max-workers $(MAX_WORKERS)

run-backtest:
	$(MAKE) run MODE=backtest

run-live:
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
	out="$$( $(COMPOSE) run --rm agents python3 scripts/run_agents.py --config $(CONFIG) --mode live --max-workers 2 2>&1 )"; \
	code=$$?; \
	set -e; \
	echo "$$out"; \
	if [ $$code -eq 0 ]; then \
		echo "Expected live mode to fail without secrets, but it succeeded"; \
		exit 1; \
	fi; \
	echo "$$out" | grep -q "mode=live requires env vars" || (echo "Unexpected live-guard failure message" && exit 1)

validate: build run-backtest test live-guard

campaign:
	./scripts/run_backtest_campaign.sh $(N)
