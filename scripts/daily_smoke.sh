#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

EXCHANGE="${EXCHANGE:-binance}"
SYMBOL="${SYMBOL:-BTC/USDT}"
DAYS="${DAYS:-30}"
ITERATIONS="${ITERATIONS:-5}"
POLL_SECONDS="${POLL_SECONDS:-1}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="artifacts/smoke"
mkdir -p "$OUT_DIR"
REPORT_PATH="$OUT_DIR/${STAMP}_daily_smoke_report.json"
LOG_DIR="$OUT_DIR/${STAMP}_logs"
mkdir -p "$LOG_DIR"

run_step() {
  local name="$1"
  local log_file="$2"
  shift
  shift
  local start_ts end_ts
  start_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if "$@" >"$log_file" 2>&1; then
    status="pass"
  else
    status="fail"
  fi
  end_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"name":"%s","status":"%s","start_utc":"%s","end_utc":"%s","log":"%s"}' "$name" "$status" "$start_ts" "$end_ts" "$log_file"
  return $([ "$status" = "pass" ] && echo 0 || echo 1)
}

steps_json="[]"
overall=0

append_step() {
  local step_json="$1"
  steps_json="$(printf '%s' "$steps_json" | python3 -c 'import json,sys; arr=json.load(sys.stdin); arr.append(json.loads(sys.argv[1])); print(json.dumps(arr))' "$step_json")"
}

if step="$(run_step validate "$LOG_DIR/validate.log" make validate)"; then
  append_step "$step"
else
  append_step "$step"
  overall=1
fi

if step="$(run_step walk_forward "$LOG_DIR/walk_forward.log" make walk-forward EXCHANGE="$EXCHANGE" SYMBOL="$SYMBOL" DAYS="$DAYS")"; then
  append_step "$step"
else
  append_step "$step"
  overall=1
fi

if step="$(run_step realtime_paper "$LOG_DIR/realtime_paper.log" make realtime-paper EXCHANGE="$EXCHANGE" SYMBOL="$SYMBOL" TIMEFRAME=1m ITERATIONS="$ITERATIONS" POLL_SECONDS="$POLL_SECONDS")"; then
  append_step "$step"
else
  append_step "$step"
  overall=1
fi

python3 - <<PY
import json
from datetime import datetime, timezone
report = {
  "timestamp_utc": datetime.now(timezone.utc).isoformat(),
  "exchange": "${EXCHANGE}",
  "symbol": "${SYMBOL}",
  "status": "pass" if ${overall} == 0 else "fail",
  "steps": json.loads('''${steps_json}''')
}
with open("${REPORT_PATH}", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(json.dumps({"status": report["status"], "report": "${REPORT_PATH}"}, indent=2))
PY

exit "$overall"
