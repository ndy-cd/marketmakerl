# Documentation Acceptance Checklist

Use this checklist before merging documentation updates.

## Clarity

- [ ] README is a short entrypoint and links to `docs/PROJECT_GUIDE.md`.
- [ ] `docs/PROJECT_GUIDE.md` explains purpose, capabilities, and current constraints.
- [ ] Terms are consistent across README, docs, and agent specs.

## Operability

- [ ] Docker build command is documented and runnable.
- [ ] Backtest runtime command is documented and runnable.
- [ ] Unit and integration test commands are documented and runnable.
- [ ] Makefile targets (`make validate`, `make test`, `make run-backtest`) are documented and runnable.
- [ ] Expected outputs and artifact paths are described.

## Safety

- [ ] Live mode requirements are explicit (`EXCHANGE_API_KEY`, `EXCHANGE_API_SECRET`).
- [ ] Docs state expected failure behavior when live secrets are missing.

## AI-Agent Readability

- [ ] Stable contracts and file paths are explicitly listed.
- [ ] Team ownership and edit boundaries are documented.
- [ ] Data flow is described step-by-step.

## Scope and Integrity

- [ ] Documentation distinguishes implemented behavior vs future possibilities.
- [ ] No docs claim behavior that code does not support.
- [ ] Related docs are cross-linked.
