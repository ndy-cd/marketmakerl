#!/usr/bin/env bash
set -euo pipefail

RUNS="${1:-10}"
if ! [[ "$RUNS" =~ ^[0-9]+$ ]] || [ "$RUNS" -lt 1 ]; then
  echo "Usage: $0 <positive-integer-runs>" >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="artifacts/campaign_${STAMP}"
mkdir -p "$OUT_DIR"

for i in $(seq 1 "$RUNS"); do
  echo "[campaign] run ${i}/${RUNS}"
  make run-backtest >/tmp/marketmakerl_campaign_run_${i}.log
  cp artifacts/local_bootstrap_exec_agent_1_metrics.json "$OUT_DIR/run_${i}_metrics.json"
  cp /tmp/marketmakerl_campaign_run_${i}.log "$OUT_DIR/run_${i}.log"
done

python3 - "$OUT_DIR" "$RUNS" <<'PY'
import json
import pathlib
import statistics
import sys

out_dir = pathlib.Path(sys.argv[1])
runs = int(sys.argv[2])
metrics = []
for i in range(1, runs + 1):
    p = out_dir / f"run_{i}_metrics.json"
    with p.open() as f:
        metrics.append(json.load(f))

def summarize(key):
    vals = [float(m.get(key, 0.0)) for m in metrics]
    return {
        "min": min(vals),
        "mean": statistics.fmean(vals),
        "max": max(vals),
    }

report = {
    "runs": runs,
    "summary": {
        "total_pnl": summarize("total_pnl"),
        "sharpe_ratio": summarize("sharpe_ratio"),
        "max_drawdown": summarize("max_drawdown"),
        "n_trades": summarize("n_trades"),
    },
    "files": [str((out_dir / f"run_{i}_metrics.json")) for i in range(1, runs + 1)],
}

report_path = out_dir / "campaign_report.json"
with report_path.open("w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
PY

echo "[campaign] report written to ${OUT_DIR}/campaign_report.json"
