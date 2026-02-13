---
name: project-manager
description: Use when coordinating MVP phases, ownership, acceptance gates, and deployment readiness for marketmakerl.
---

# Project Manager

## Use this skill when
- The team needs a phased MVP execution plan with owners.
- Multiple agent outputs must be integrated under explicit quality gates.
- Deployment steps and rollback policy must be documented.

## Project-specific workflow
1. Define milestone phases and map each to owner agents.
2. Attach verification commands and expected outputs to each milestone.
3. Track blockers and residual risks in docs.
4. Keep release and deployment steps reproducible.

## Minimum acceptance checks
- MVP plan includes status and validation command per phase.
- Delivery gate includes: `make validate`, campaign, and real-data analysis.
- Deployment and rollback procedures are documented.

## Handoff requirements
- Current milestone status board
- Gate results snapshot
- Outstanding blockers and owner assignments
