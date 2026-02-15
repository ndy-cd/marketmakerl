#!/usr/bin/env python3
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

THRESHOLDS = {
    "campaign_mean_pnl_min": 0.0,
    "campaign_mean_sharpe_min": 0.50,
    "walk_forward_pass_required": True,
    "walk_forward_hard_fail_windows_max": 0,
    "walk_forward_pass_rate_min": 0.60,
    "weekly_status_required": "pass",
    "quant_gate_pass_required": True,
    "quant_max_drawdown_pct_max": 0.40,
    "quant_max_cvar95_pct_max": 0.03,
    "quant_min_sortino": 0.20,
    "quant_min_pass_rate": 0.65,
    "quant_max_total_return_pct": 0.25,
    "quant_min_fill_ratio": 0.20,
    "quant_max_execution_cost_bps": 5.0,
    "quant_max_realized_edge_bps": 12.0,
    "quant_max_sharpe": 4.0,
    "quant_max_sortino": 6.0,
    "quant_max_calmar": 50.0,
    "quant_gate_pass_ratio_max": 0.90,
}


def latest(pattern: str) -> Optional[str]:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def read_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dashboard_security_checks() -> Dict[str, Any]:
    makefile_path = Path("Makefile")
    secure_server_path = Path("scripts/serve_dashboard_secure.py")
    out = {
        "secure_server_script_exists": secure_server_path.exists(),
        "makefile_uses_secure_server": False,
        "makefile_binds_loopback": False,
        "makefile_avoids_python_http_server": False,
    }
    if not makefile_path.exists():
        return out
    text = makefile_path.read_text(encoding="utf-8")
    out["makefile_uses_secure_server"] = "scripts/serve_dashboard_secure.py" in text
    out["makefile_binds_loopback"] = "--host 127.0.0.1" in text
    out["makefile_avoids_python_http_server"] = "python3 -m http.server" not in text
    return out


def main() -> int:
    campaign_path = latest("artifacts/campaign_*/campaign_report.json")
    walk_path = latest("artifacts/walk_forward/*_walk_forward_report.json")
    weekly_path = latest("artifacts/weekly/*_weekly_reliability_report.json")
    quant_path = latest("artifacts/quant_experiments/*_quant_experiments.json")

    campaign = read_json(campaign_path)
    walk = read_json(walk_path)
    weekly = read_json(weekly_path)
    quant = read_json(quant_path)

    campaign_mean_pnl = float(campaign.get("summary", {}).get("total_pnl", {}).get("mean", 0.0))
    campaign_mean_sharpe = float(campaign.get("summary", {}).get("sharpe_ratio", {}).get("mean", 0.0))

    walk_gate = walk.get("gate", {})
    walk_checks = walk_gate.get("checks", {})
    walk_pass = bool(walk_gate.get("pass", False))
    walk_hard_fails = int(walk_checks.get("hard_fail_windows", 999))
    walk_pass_rate = float(walk_checks.get("pass_rate", 0.0))

    weekly_status = str(weekly.get("status", "fail")).lower()

    rec = quant.get("recommendation", {})
    quant_gate_pass = bool(rec.get("gate_pass", False))
    quant_dd = float(rec.get("max_drawdown_pct", 1.0))
    quant_cvar = float(rec.get("cvar_95_pct", 1.0))
    quant_sortino = float(rec.get("sortino_ratio", 0.0))
    quant_sharpe = float(rec.get("sharpe_ratio", 0.0))
    quant_calmar = float(rec.get("calmar_ratio", 999.0))
    quant_pass_rate = float(rec.get("pass_rate", 0.0))
    quant_total_return = float(rec.get("total_return_pct", 999.0))
    quant_fill_ratio = float(rec.get("fill_ratio", 0.0))
    quant_execution_cost_bps = float(rec.get("execution_cost_bps", 999.0))
    quant_realized_edge_bps = float(rec.get("realized_edge_bps", 999.0))
    quant_total_cases = int(quant.get("total_cases", 0) or 0)
    quant_gate_pass_count = int(quant.get("gate_pass_count", 0) or 0)
    quant_gate_pass_ratio = (
        quant_gate_pass_count / quant_total_cases
        if quant_total_cases > 0
        else 0.0
    )
    dashboard_security = dashboard_security_checks()

    checks = [
        ("campaign_mean_pnl", campaign_mean_pnl >= THRESHOLDS["campaign_mean_pnl_min"], campaign_mean_pnl),
        ("campaign_mean_sharpe", campaign_mean_sharpe >= THRESHOLDS["campaign_mean_sharpe_min"], campaign_mean_sharpe),
        ("walk_forward_pass", walk_pass is THRESHOLDS["walk_forward_pass_required"], walk_pass),
        (
            "walk_forward_hard_fail_windows",
            walk_hard_fails <= THRESHOLDS["walk_forward_hard_fail_windows_max"],
            walk_hard_fails,
        ),
        ("walk_forward_pass_rate", walk_pass_rate >= THRESHOLDS["walk_forward_pass_rate_min"], walk_pass_rate),
        ("weekly_status", weekly_status == THRESHOLDS["weekly_status_required"], weekly_status),
        ("quant_gate_pass", quant_gate_pass is THRESHOLDS["quant_gate_pass_required"], quant_gate_pass),
        ("quant_max_drawdown_pct", quant_dd <= THRESHOLDS["quant_max_drawdown_pct_max"], quant_dd),
        ("quant_cvar95_pct", quant_cvar <= THRESHOLDS["quant_max_cvar95_pct_max"], quant_cvar),
        ("quant_sortino", quant_sortino >= THRESHOLDS["quant_min_sortino"], quant_sortino),
        ("quant_sharpe_max", quant_sharpe <= THRESHOLDS["quant_max_sharpe"], quant_sharpe),
        ("quant_sortino_max", quant_sortino <= THRESHOLDS["quant_max_sortino"], quant_sortino),
        ("quant_calmar_max", quant_calmar <= THRESHOLDS["quant_max_calmar"], quant_calmar),
        ("quant_pass_rate", quant_pass_rate >= THRESHOLDS["quant_min_pass_rate"], quant_pass_rate),
        ("quant_fill_ratio", quant_fill_ratio >= THRESHOLDS["quant_min_fill_ratio"], quant_fill_ratio),
        (
            "quant_execution_cost_bps",
            quant_execution_cost_bps <= THRESHOLDS["quant_max_execution_cost_bps"],
            quant_execution_cost_bps,
        ),
        (
            "quant_realized_edge_bps",
            quant_realized_edge_bps <= THRESHOLDS["quant_max_realized_edge_bps"],
            quant_realized_edge_bps,
        ),
        (
            "quant_gate_pass_ratio",
            quant_gate_pass_ratio <= THRESHOLDS["quant_gate_pass_ratio_max"],
            quant_gate_pass_ratio,
        ),
        (
            "quant_total_return_pct",
            quant_total_return <= THRESHOLDS["quant_max_total_return_pct"],
            quant_total_return,
        ),
        ("dashboard_secure_server_script_exists", bool(dashboard_security["secure_server_script_exists"]), dashboard_security["secure_server_script_exists"]),
        ("dashboard_makefile_uses_secure_server", bool(dashboard_security["makefile_uses_secure_server"]), dashboard_security["makefile_uses_secure_server"]),
        ("dashboard_makefile_binds_loopback", bool(dashboard_security["makefile_binds_loopback"]), dashboard_security["makefile_binds_loopback"]),
        (
            "dashboard_makefile_avoids_python_http_server",
            bool(dashboard_security["makefile_avoids_python_http_server"]),
            dashboard_security["makefile_avoids_python_http_server"],
        ),
    ]

    failed = [name for name, ok, _ in checks if not ok]
    status = "pass" if not failed else "fail"

    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "thresholds": THRESHOLDS,
        "artifacts": {
            "campaign": campaign_path,
            "walk_forward": walk_path,
            "weekly": weekly_path,
            "quant": quant_path,
        },
        "checks": [{"name": n, "ok": ok, "value": v} for n, ok, v in checks],
        "dashboard_security": dashboard_security,
        "failed_checks": failed,
    }

    out_dir = Path("artifacts/guardrails")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{stamp}_release_guardrails.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(json.dumps({"status": status, "report": str(out_path), "failed_checks": failed}, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
