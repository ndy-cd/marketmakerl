# MVP Signoff Checklist

Use this checklist for stakeholder readiness and internal signoff.

## Product and Operations

- [ ] `make validate` passes.
- [ ] `make campaign N=10` passes and report is generated.
- [ ] `make analyze-last-month ...` report exists with explicit readiness verdict.
- [ ] `make realtime-paper ...` produces JSONL output under `artifacts/realtime/`.
- [ ] `docker-compose.server.yml` service starts successfully.

## Safety and Policy

- [ ] `PAPER_ONLY=1` is active by default.
- [ ] `make run-live` is blocked while `PAPER_ONLY=1`.
- [ ] `make realtime-live` is blocked while `PAPER_ONLY=1`.
- [ ] Live-key onboarding criteria are documented in `docs/MVP_EXECUTION_PLAN.md`.

## Documentation Package

- [ ] `README.md` links to stakeholder and operations docs.
- [ ] `docs/PROJECT_GUIDE.md` reflects current implemented behavior.
- [ ] `docs/STAKEHOLDER_MVP_BRIEF.md` is up to date with latest evidence artifacts.
- [ ] `docs/DEPLOYMENT_GUIDE.md` includes deployment and rollback steps.
- [ ] `docs/MVP_EXECUTION_PLAN.md` includes in-progress and blocked items.

## Agent Coverage

- [ ] `agent_ops/team.yaml` includes A1-A8.
- [ ] Prompt files exist for each role under `agent_ops/prompts/`.
- [ ] Skill files exist for each role under `agent_ops/skills/`.
