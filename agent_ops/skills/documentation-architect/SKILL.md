---
name: documentation-architect
description: Use when creating or revising project documentation in marketmakerl so humans and AI agents can clearly understand setup, execution, testing, data flow, capabilities, constraints, and extension paths.
---

# Documentation Architect

## Use this skill when
- README or docs are incomplete or ambiguous.
- The project needs a single source of truth for run and test workflows.
- You must explain system behavior and data flow for both engineers and AI agents.

## Project-specific workflow
1. Keep `README.md` as a short entrypoint and place deep guidance in `docs/PROJECT_GUIDE.md`.
2. Prefer Docker-first commands; include local path only as secondary.
3. For each operational command, document purpose, command, and expected result.
4. Include explicit safety behavior for `mode=live` and required env vars.
5. Map components to paths in `src/`, `scripts/`, `tests/`, `config/`, and `artifacts/`.
6. Add an architecture/data-flow section that is readable by humans and parseable by AI (clear headings, stable terminology, deterministic file references).

## Minimum acceptance checks
- `README.md` links to canonical docs.
- Documentation includes run, test, and troubleshoot sections.
- Data flow from market data generation to backtest metrics and artifact files is explicit.
- Constraints and known limitations are clearly labeled.

## Handoff requirements
- List changed files.
- Summarize documentation assumptions.
- Provide command checklist used to validate docs.
