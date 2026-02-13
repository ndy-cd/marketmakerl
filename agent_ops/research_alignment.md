# Deep Research Alignment

Source reviewed: `/Users/nody/codexpro/deep-research-report.md`

## Incorporated into this setup
- Enforced a single config-driven multi-agent runtime model.
- Kept safe default mode as simulation/backtest-first.
- Added explicit ownership boundaries so agents can work in parallel.
- Added quality gates and integration-first workflow.
- Added a Makefile command interface to improve reproducibility and reliability.

## Open assumptions from the report
- Exchange/venue and API credentials are not fixed yet.
- Data cadence and symbol universe are not fixed yet.
- Live execution policies and risk limits need explicit values before production use.

## Recommended merge sequence
1. A1 runtime scaffolding and config contract.
2. A2 data/signal schema hardening.
3. A3 model guards and deterministic RL behavior.
4. A4 pnl/risk accounting corrections.
5. A5 regression tests, docs, and final acceptance gate.
6. A6 documentation architecture and canonical project guide.
7. A7 quant adaptation gates on recent real-data windows.
8. A8 MVP milestone coordination and deployment readiness.
