---
name: data-signal-engineer
description: Use when modifying market data ingestion, preprocessing, or feature/signal generation in marketmakerl while preserving deterministic simulation behavior and stable schemas.
---

# Data and Signal Engineer

## Use this skill when
- Editing `src/data/data_processor.py` or `src/utils/market_data.py`.
- Introducing new features used by models or backtests.
- Hardening input validation for data sources.

## Project-specific workflow
1. Keep data IO and feature generation separate.
2. Define one canonical feature schema used by models/backtests.
3. Handle malformed or missing columns with explicit validation errors.
4. Preserve simulation mode behavior used by tests and docs.
5. Avoid hidden state; pass settings as function arguments.

## Feature schema contract
- Required core price key: `mid_price` or derivable equivalent.
- Volatility feature: non-negative float.
- Directional features (momentum/trend): bounded and documented.
- Missing optional features must degrade gracefully.

## Minimum acceptance checks
- Existing integration tests still pass.
- New edge-case test data is added for malformed inputs.
- Callers can detect schema errors early.

## Handoff requirements
- Enumerate schema keys and value ranges.
- Note any signature changes.
- Provide commands that reproduce results.
