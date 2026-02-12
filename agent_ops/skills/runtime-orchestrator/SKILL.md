---
name: runtime-orchestrator
description: Use when adding or refactoring runtime orchestration for marketmakerl, including multi-agent launchers, config loading, run modes (backtest/paper/live), and structured logging.
---

# Runtime Orchestrator

## Use this skill when
- The task requires a central run command.
- You need to wire multiple role agents in one process manager or script.
- Configuration and safety gates by run mode must be enforced.

## Project-specific workflow
1. Keep orchestration logic in `scripts/` and shared runtime base in `src/agents/`.
2. Read settings from `config/config.yaml` and validate required keys before starting workers.
3. Enforce mode safety:
- `backtest` and `paper` can run without secrets.
- `live` must fail fast unless required credentials are explicitly present.
4. Emit structured logs with `run_id`, `agent_id`, `symbol`, and `mode` fields.
5. Ensure process exit code is non-zero on startup or worker failure.
6. Keep Docker entrypoints mirrored in `Makefile` targets for stable operations.

## Minimum acceptance checks
- `scripts/run_agents.py --config config/config.yaml --mode backtest` starts cleanly.
- Invalid config fails with actionable messages.
- Existing backtest paths are not broken.

## Handoff requirements
- List new CLI arguments.
- List config keys added/changed.
- Include exact verification commands.
