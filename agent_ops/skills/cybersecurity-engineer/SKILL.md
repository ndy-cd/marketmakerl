---
name: cybersecurity-engineer
description: Use when hardening local/demo serving paths, secret handling, and platform exposure controls for marketmakerl.
---

# Cybersecurity Engineer

## Use this skill when
- Dashboard/docs serving behavior may expose files or paths.
- Runtime commands need security posture review.
- Release blockers must include security checks.

## Project-specific workflow
1. Enforce secure serving via `scripts/serve_dashboard_secure.py`.
2. Verify loopback-only defaults for local demo hosting.
3. Block directory listing and path traversal attempts.
4. Check logs/reports for accidental secret leakage.
5. Keep security checks wired into release guardrails.

## Minimum acceptance checks
- Secure server script exists and is used by Makefile targets.
- Dashboard serving path does not allow listing/traversal.
- No fallback to unsafe `python -m http.server` demo path.

## Handoff requirements
- Security findings (severity + mitigation).
- Verified commands and checks run.
- Remaining risk notes before stakeholder demo.
