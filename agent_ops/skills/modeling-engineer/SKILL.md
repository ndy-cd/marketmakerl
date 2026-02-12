---
name: modeling-engineer
description: Use when improving Avellaneda-Stoikov or RL model behavior in marketmakerl, including parameter guards, quote stability, and deterministic simulation behavior.
---

# Modeling Engineer

## Use this skill when
- Editing `src/models/avellaneda_stoikov.py` or `src/models/rl_enhanced_model.py`.
- Changing quote logic, reservation price logic, or RL environment transitions.
- Adding model-level safeguards.

## Project-specific workflow
1. Preserve public interfaces used by tests and backtesting.
2. Add parameter guards (risk aversion, volatility, horizon, inventory bounds).
3. Keep bid/ask ordering valid under all edge cases.
4. Clamp extreme feature influence to prevent unstable quotes.
5. Add deterministic controls for any stochastic RL behavior.

## Numerical safety rules
- Validate denominators and log/exp inputs before use.
- Avoid silent NaN propagation.
- Use explicit fallback quotes when model math fails.

## Minimum acceptance checks
- Quote calculation does not crash on invalid inputs.
- Stress scenarios maintain bounded quotes.
- Existing and new model tests pass.

## Handoff requirements
- Describe math changes and assumptions.
- Provide deterministic reproduction commands.
- List compatibility impacts to backtesting.
