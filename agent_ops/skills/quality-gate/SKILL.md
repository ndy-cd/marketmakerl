---
name: quality-gate
description: Use when building or enforcing tests, smoke checks, and release-readiness documentation for marketmakerl after parallel agent changes are merged.
---

# QA and Integration Engineer

## Use this skill when
- Editing `tests/`, `README.md`, or `docs/` for validation workflows.
- Integrating outputs from multiple agent branches.
- Defining merge gates for release candidates.

## Project-specific workflow
1. Keep a fast smoke path and a deeper integration path.
2. Ensure tests run in simulation mode without exchange keys.
3. Add regression tests for each fixed defect.
4. Update docs with exact commands and expected pass/fail behavior.
5. Report residual risk explicitly.

## Default quality gates
- `make validate`
- `make test`
- Any new targeted regression tests introduced by other agents.

## Minimum acceptance checks
- Test commands are reproducible from a clean virtual environment.
- Failures are actionable and point to broken contracts.
- Documentation reflects current commands and file paths.

## Handoff requirements
- Test matrix with status.
- Known gaps not covered by tests.
- Recommended follow-up checks for live-readiness.
