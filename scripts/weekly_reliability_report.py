#!/usr/bin/env python3
import glob
import json
from datetime import datetime, timezone
from pathlib import Path


def latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def load_json(path: str | None):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    campaign_path = latest("artifacts/campaign_*/campaign_report.json")
    analysis_path = latest("artifacts/last_month_analysis/*_analysis.json")
    walk_path = latest("artifacts/walk_forward/*_walk_forward_report.json")
    realtime_path = latest("artifacts/realtime/*.jsonl")

    campaign = load_json(campaign_path)
    analysis = load_json(analysis_path)
    walk = load_json(walk_path)

    status = "pass"
    reasons = []

    if not campaign:
        status = "fail"
        reasons.append("missing_campaign_report")
    if not analysis:
        status = "fail"
        reasons.append("missing_analysis_report")
    if not walk:
        status = "fail"
        reasons.append("missing_walk_forward_report")
    if not realtime_path:
        status = "fail"
        reasons.append("missing_realtime_artifact")

    if campaign:
        mean_pnl = float(campaign.get("summary", {}).get("total_pnl", {}).get("mean", 0.0))
        if mean_pnl <= 0:
            status = "fail"
            reasons.append("campaign_mean_pnl_non_positive")

    if analysis:
        ready = bool(analysis.get("readiness", {}).get("ready_for_live_keys", False))
        if not ready:
            status = "fail"
            reasons.append("analysis_not_ready")

    if walk:
        gate_pass = bool(walk.get("gate", {}).get("pass", False))
        if not gate_pass:
            status = "fail"
            reasons.append("walk_forward_gate_failed")

    out_dir = Path("artifacts/weekly")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{stamp}_weekly_reliability_report.json"

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reasons": reasons,
        "inputs": {
            "campaign_report": campaign_path,
            "analysis_report": analysis_path,
            "walk_forward_report": walk_path,
            "realtime_artifact": realtime_path,
        },
        "summary": {
            "campaign_total_pnl_mean": (
                float(campaign.get("summary", {}).get("total_pnl", {}).get("mean", 0.0)) if campaign else None
            ),
            "analysis_ready_for_live_keys": (
                bool(analysis.get("readiness", {}).get("ready_for_live_keys", False)) if analysis else None
            ),
            "walk_forward_pass": (bool(walk.get("gate", {}).get("pass", False)) if walk else None),
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(json.dumps({"status": status, "report": str(out_path)}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
