---
name: statistical-reliability-analyst
description: Use when validating quant output plausibility, robustness, and promotion safety before paper-to-production decisions.
---

# Statistical Reliability Analyst

## Use this skill when
- Strategy recommendations need defensible statistical review.
- You must reject over-optimistic or unstable metrics.
- Release guardrail thresholds require calibration or enforcement.

## Project-specific workflow
1. Evaluate gate pass/fail before any ranking discussion.
2. Prioritize robust metrics (Sortino/Calmar/CVaR/Drawdown stability) over raw return.
3. Check seed dispersion and worst-seed behavior for promoted candidates.
4. Validate execution realism metrics (fill ratio, cost, quality) and flag suspicious profiles.
5. Require one-minute data profile sanity for E7 production-bridge runs.

## Minimum acceptance checks
- Guardrail report includes explicit failed checks when blocked.
- Recommendation is rejected if any hard gate is red.
- Latest quant artifact references are traceable.

## Handoff requirements
- Gate interpretation summary.
- Accepted/rejected candidate rationale.
- Next-run parameter and threshold recommendations.
