---
name: dashboard-designer
description: Use when building or revising stakeholder dashboards so quant decisions are easy to interpret without hiding risk or data-quality issues.
---

# Dashboard Designer

## Use this skill when
- KPI hierarchy, readability, or visual clarity must be improved.
- Strategy/reliability evidence needs stakeholder-friendly framing.
- Missing data or stale artifacts must be rendered explicitly.

## Project-specific workflow
1. Build from latest quant, walk-forward, campaign, and weekly artifacts.
2. Keep decision KPIs and blockers in first viewport.
3. Render tiny risk metrics with explicit units (`bps` where needed).
4. Never show missing data as misleading `0`; use `n/a` and annotate source gaps.
5. Keep dashboard mobile-safe and demo-ready.

## Minimum acceptance checks
- Recommendation, risk, and blocker status are readable in under 30 seconds.
- Team verification and artifact sources are visible.
- Dashboard output is regenerated through `make stakeholder-dashboard`.

## Handoff requirements
- Updated dashboard artifact paths.
- Mapping note from dashboard cards to source artifact fields.
- Known visualization limitations.
