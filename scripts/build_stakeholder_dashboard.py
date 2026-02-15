#!/usr/bin/env python3
import csv
import glob
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def latest(pattern: str) -> Optional[str]:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def read_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def pct_or_bps(value: float) -> str:
    pct_value = value * 100.0
    if abs(pct_value) < 0.01:
        bps = value * 10000.0
        return f"{bps:.2f} bps"
    return f"{pct_value:.2f}%"


def safe(v: Any, default: Any = "n/a") -> Any:
    return default if v is None else v


def h(v: Any) -> str:
    return html.escape(str(v), quote=True)


def dedupe_quant_rows(rows: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    best_by_strategy: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("strategy", "unknown"))
        cur = best_by_strategy.get(key)
        score = float(row.get("robustness_score", 0.0))
        if cur is None or score > float(cur.get("robustness_score", 0.0)):
            best_by_strategy[key] = row
    deduped = sorted(
        best_by_strategy.values(),
        key=lambda r: float(r.get("robustness_score", 0.0)),
        reverse=True,
    )
    return deduped[:limit]


def build_explored_from_quant_csv(quant_json_path: Optional[str]) -> List[Dict[str, Any]]:
    if not quant_json_path:
        return []

    csv_path = quant_json_path.replace("_quant_experiments.json", "_quant_experiments.csv")
    if not Path(csv_path).exists():
        return []

    buckets: Dict[str, Dict[str, Any]] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            family = (row.get("family") or "unknown").strip()
            b = buckets.setdefault(
                family,
                {
                    "strategy_format": family,
                    "cases": 0,
                    "sum_return": 0.0,
                    "sum_sharpe": 0.0,
                    "sum_sortino": 0.0,
                    "sum_drawdown_pct": 0.0,
                    "sum_cvar_95_pct": 0.0,
                    "gate_pass_cases": 0,
                },
            )
            b["cases"] += 1
            b["sum_return"] += float(row.get("total_return_pct") or 0.0)
            b["sum_return_sq"] = b.get("sum_return_sq", 0.0) + (float(row.get("total_return_pct") or 0.0) ** 2)
            b["sum_sharpe"] += float(row.get("sharpe_ratio") or 0.0)
            b["sum_sortino"] += float(row.get("sortino_ratio") or 0.0)
            b["sum_drawdown_pct"] += float(row.get("max_drawdown_pct") or 0.0)
            b["sum_cvar_95_pct"] += float(row.get("cvar_95_pct") or 0.0)
            gate_pass_raw = str(row.get("gate_pass", "")).strip().lower()
            if gate_pass_raw in {"true", "1", "yes"}:
                b["gate_pass_cases"] += 1

    out: List[Dict[str, Any]] = []
    for family, b in buckets.items():
        n = max(1, int(b["cases"]))
        out.append(
            {
                "strategy_format": family,
                "cases": b["cases"],
                "mean_total_return_pct": b["sum_return"] / n,
                "std_total_return_pct": math.sqrt(max(0.0, (b.get("sum_return_sq", 0.0) / n) - ((b["sum_return"] / n) ** 2))),
                "mean_sharpe": b["sum_sharpe"] / n,
                "mean_sortino": b["sum_sortino"] / n,
                "mean_drawdown_pct": b["sum_drawdown_pct"] / n,
                "mean_cvar_95_pct": b["sum_cvar_95_pct"] / n,
                "gate_pass_rate": b["gate_pass_cases"] / n,
            }
        )

    for row in out:
        n = max(1, int(row["cases"]))
        sem = row["std_total_return_pct"] / math.sqrt(n)
        row["return_ci95_pct"] = 1.96 * sem

    out.sort(key=lambda x: (x["gate_pass_rate"], x["mean_sortino"]), reverse=True)
    return out


def build_robustness_snapshot_from_quant_csv(quant_json_path: Optional[str]) -> Dict[str, float]:
    if not quant_json_path:
        return {
            "cases": 0,
            "dd_min_pct": 0.0,
            "dd_mean_pct": 0.0,
            "dd_p95_pct": 0.0,
            "dd_max_pct": 0.0,
            "cvar_mean_pct": 0.0,
            "cvar_p95_pct": 0.0,
            "cvar_max_pct": 0.0,
            "return_min_pct": 0.0,
            "return_mean_pct": 0.0,
            "return_p95_pct": 0.0,
            "return_max_pct": 0.0,
            "negative_return_cases": 0.0,
        }
    csv_path = quant_json_path.replace("_quant_experiments.json", "_quant_experiments.csv")
    if not Path(csv_path).exists():
        return {
            "cases": 0,
            "dd_min_pct": 0.0,
            "dd_mean_pct": 0.0,
            "dd_p95_pct": 0.0,
            "dd_max_pct": 0.0,
            "cvar_mean_pct": 0.0,
            "cvar_p95_pct": 0.0,
            "cvar_max_pct": 0.0,
            "return_min_pct": 0.0,
            "return_mean_pct": 0.0,
            "return_p95_pct": 0.0,
            "return_max_pct": 0.0,
            "negative_return_cases": 0.0,
        }

    dd_vals: List[float] = []
    cvar_vals: List[float] = []
    ret_vals: List[float] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dd_vals.append(float(row.get("max_drawdown_pct") or 0.0))
            cvar_vals.append(float(row.get("cvar_95_pct") or 0.0))
            ret_vals.append(float(row.get("total_return_pct") or 0.0))

    if not dd_vals:
        return {
            "cases": 0,
            "dd_min_pct": 0.0,
            "dd_mean_pct": 0.0,
            "dd_p95_pct": 0.0,
            "dd_max_pct": 0.0,
            "cvar_mean_pct": 0.0,
            "cvar_p95_pct": 0.0,
            "cvar_max_pct": 0.0,
            "return_min_pct": 0.0,
            "return_mean_pct": 0.0,
            "return_p95_pct": 0.0,
            "return_max_pct": 0.0,
            "negative_return_cases": 0.0,
        }

    dd_sorted = sorted(dd_vals)
    cvar_sorted = sorted(cvar_vals)
    ret_sorted = sorted(ret_vals)
    n = len(dd_sorted)
    p95_idx = max(0, min(n - 1, int(0.95 * (n - 1))))
    return {
        "cases": float(n),
        "dd_min_pct": float(dd_sorted[0]),
        "dd_mean_pct": float(sum(dd_sorted) / n),
        "dd_p95_pct": float(dd_sorted[p95_idx]),
        "dd_max_pct": float(dd_sorted[-1]),
        "cvar_mean_pct": float(sum(cvar_sorted) / n),
        "cvar_p95_pct": float(cvar_sorted[p95_idx]),
        "cvar_max_pct": float(cvar_sorted[-1]),
        "return_min_pct": float(ret_sorted[0]),
        "return_mean_pct": float(sum(ret_sorted) / n),
        "return_p95_pct": float(ret_sorted[p95_idx]),
        "return_max_pct": float(ret_sorted[-1]),
        "negative_return_cases": float(sum(1 for x in ret_vals if x < 0.0)),
    }


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    data = sorted(values)
    idx = max(0, min(len(data) - 1, int(p * (len(data) - 1))))
    return float(data[idx])


def build_execution_snapshot_from_quant_csv(quant_json_path: Optional[str]) -> Dict[str, float]:
    base = {
        "cases": 0.0,
        "fill_ratio_mean": 0.0,
        "fill_ratio_p05": 0.0,
        "fill_ratio_p95": 0.0,
        "execution_cost_bps_mean": 0.0,
        "execution_cost_bps_p95": 0.0,
        "realized_edge_bps_mean": 0.0,
        "execution_quality_mean": 0.0,
        "slippage_cost_mean": 0.0,
        "latency_cost_mean": 0.0,
        "impact_cost_mean": 0.0,
        "adverse_selection_cost_mean": 0.0,
    }
    if not quant_json_path:
        return base

    csv_path = quant_json_path.replace("_quant_experiments.json", "_quant_experiments.csv")
    if not Path(csv_path).exists():
        return base

    fill_vals: List[float] = []
    cost_bps_vals: List[float] = []
    edge_vals: List[float] = []
    quality_vals: List[float] = []
    slip_vals: List[float] = []
    lat_vals: List[float] = []
    impact_vals: List[float] = []
    adverse_vals: List[float] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fill_vals.append(float(row.get("fill_ratio") or 0.0))
            cost_bps_vals.append(float(row.get("execution_cost_bps") or 0.0))
            edge_vals.append(float(row.get("realized_edge_bps") or 0.0))
            quality_vals.append(float(row.get("execution_quality_score") or 0.0))
            slip_vals.append(float(row.get("slippage_cost") or 0.0))
            lat_vals.append(float(row.get("latency_cost") or 0.0))
            impact_vals.append(float(row.get("impact_cost") or 0.0))
            adverse_vals.append(float(row.get("adverse_selection_cost") or 0.0))

    if not fill_vals:
        return base

    n = len(fill_vals)
    return {
        "cases": float(n),
        "fill_ratio_mean": float(sum(fill_vals) / n),
        "fill_ratio_p05": _percentile(fill_vals, 0.05),
        "fill_ratio_p95": _percentile(fill_vals, 0.95),
        "execution_cost_bps_mean": float(sum(cost_bps_vals) / n),
        "execution_cost_bps_p95": _percentile(cost_bps_vals, 0.95),
        "realized_edge_bps_mean": float(sum(edge_vals) / n),
        "execution_quality_mean": float(sum(quality_vals) / n),
        "slippage_cost_mean": float(sum(slip_vals) / n),
        "latency_cost_mean": float(sum(lat_vals) / n),
        "impact_cost_mean": float(sum(impact_vals) / n),
        "adverse_selection_cost_mean": float(sum(adverse_vals) / n),
    }


def build_html(payload: Dict[str, Any]) -> str:
    c = payload["cards"]
    r = payload["robustness_snapshot"]
    x = payload["execution_snapshot"]
    d = payload["data_profile"]
    g = payload["selection_gates"]
    gate_ratio_class = "good" if float(c.get("gate_pass_ratio", 0.0)) >= 0.95 else "warn"
    exec_quality_class = "good" if float(x.get("execution_quality_mean", 0.0)) >= 55.0 else "warn"
    quant_top = payload["quant_top"]
    explored = payload["explored_strategies"]
    capabilities = payload["capabilities"]
    limitations = payload["limitations"]
    strategic = payload["strategic_profitability_path"]
    files = payload["files"]

    rows = "".join(
        f"<tr><td>{h(r['strategy'])}</td><td>{r['budget']}</td><td>{pct(r.get('total_return_pct', 0.0))}</td><td>{r['sortino_ratio']:.3f}</td><td>{r['calmar_ratio']:.3f}</td><td>{pct_or_bps(r['cvar_95_pct'])}</td><td>{pct_or_bps(r['max_drawdown_pct'])}</td><td>{r['pass_rate']:.2f}</td><td>{pct(r.get('fill_ratio', 0.0))}</td><td>{r.get('execution_cost_bps', 0.0):.2f}</td><td>{r.get('execution_quality_score', 0.0):.1f}</td></tr>"
        for r in quant_top
    )

    explored_rows = "".join(
        f"<tr><td>{h(r['strategy_format'])}</td><td>{r['cases']}</td><td>{pct(r['mean_total_return_pct'])}</td><td>{pct(r['return_ci95_pct'])}</td><td>{r['mean_sortino']:.3f}</td><td>{r['mean_sharpe']:.3f}</td><td>{pct(r['mean_drawdown_pct'])}</td><td>{pct_or_bps(r['mean_cvar_95_pct'])}</td><td>{r['gate_pass_rate']:.2f}</td></tr>"
        for r in explored
    )

    cap_list = "".join(f"<li>{h(x)}</li>" for x in capabilities)
    limit_list = "".join(f"<li>{h(x)}</li>" for x in limitations)
    strategic_list = "".join(f"<li>{h(x)}</li>" for x in strategic)
    selection_list = "".join(
        f"<li>{h(k)}: {h(v)}</li>" for k, v in g.items()
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MarketMakeRL MVP Dashboard</title>
  <style>
    :root {{
      --bg0: #f2f7fb;
      --bg1: #e5f1ff;
      --ink: #0f2338;
      --muted: #4d6277;
      --card: rgba(255, 255, 255, 0.9);
      --line: #c7d7ea;
      --accent: #0f6abf;
      --good: #0d7f46;
      --warn: #b65a0f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 4%, rgba(15, 106, 191, 0.18), transparent 24%),
        radial-gradient(circle at 86% 8%, rgba(13, 127, 70, 0.13), transparent 22%),
        linear-gradient(180deg, var(--bg1), var(--bg0));
    }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 20px 16px 28px; }}
    .hero {{
      background: linear-gradient(132deg, rgba(255, 255, 255, 0.92), rgba(230, 241, 255, 0.95));
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 10px 26px rgba(8, 32, 58, 0.08);
    }}
    h1 {{ margin: 0 0 6px; font-size: clamp(24px, 3vw, 34px); letter-spacing: -0.02em; }}
    .sub {{ color: var(--muted); margin: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; margin-top: 12px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      backdrop-filter: blur(4px);
    }}
    .k {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }}
    .v {{ font-size: clamp(20px, 2.4vw, 28px); font-weight: 700; margin-top: 6px; overflow-wrap: anywhere; }}
    .v-code {{ font-family: "IBM Plex Mono", "Menlo", monospace; font-size: clamp(16px, 2vw, 22px); line-height: 1.15; word-break: break-word; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .section {{ margin-top: 14px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; }}
    h2 {{ margin: 0 0 10px; font-size: clamp(17px, 1.8vw, 24px); letter-spacing: -0.01em; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); text-align: left; padding: 8px 6px; }}
    th {{ color: var(--muted); font-weight: 600; }}
    ul {{ margin: 0; padding-left: 18px; }}
    .small {{ font-size: 12px; color: var(--muted); }}
    .pill {{ display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; margin-right: 6px; margin-bottom: 6px; font-size: 12px; }}
    @media (max-width: 700px) {{
      .wrap {{ padding: 14px 10px 22px; }}
      th, td {{ font-size: 12px; padding: 6px 4px; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>MarketMakeRL MVP: Stakeholder Analytics Dashboard</h1>
      <p class=\"sub\">Paper-only research platform focused on robust backtests and reliability evidence. Not approved for real-money trading.</p>
      <p class=\"small\">Generated: {h(payload['generated_utc'])}</p>
    </div>

    <div class=\"section\">
      <h2>System Capabilities (Current Research Scope)</h2>
      <ul>{cap_list}</ul>
    </div>

    <div class=\"section\">
      <h2>Known Limits (Do Not Ignore)</h2>
      <ul>{limit_list}</ul>
    </div>

    <div class=\"section\">
      <h2>Robust Backtest Reliability (Primary)</h2>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"k\">Total Cases Evaluated</div><div class=\"v\">{int(c['total_cases'])}</div></div>
        <div class=\"card\"><div class=\"k\">Quant Gate Pass Ratio</div><div class=\"v {gate_ratio_class}\">{pct(c['gate_pass_ratio'])}</div></div>
        <div class=\"card\"><div class=\"k\">Worst Drawdown</div><div class=\"v warn\">{pct_or_bps(r['dd_max_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">P95 Drawdown</div><div class=\"v\">{pct_or_bps(r['dd_p95_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Drawdown</div><div class=\"v\">{pct_or_bps(r['dd_mean_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Min Drawdown</div><div class=\"v\">{pct_or_bps(r['dd_min_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">P95 CVaR</div><div class=\"v\">{pct_or_bps(r['cvar_p95_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Max CVaR</div><div class=\"v warn\">{pct_or_bps(r['cvar_max_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Worst Return Case</div><div class=\"v warn\">{pct(r['return_min_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Negative Return Cases</div><div class=\"v\">{int(r['negative_return_cases'])}</div></div>
        <div class=\"card\"><div class=\"k\">Recommended Strategy</div><div class=\"v v-code\" title=\"{h(c['quant_strategy'])}\">{h(c['quant_strategy'])}</div></div>
        <div class=\"card\"><div class=\"k\">Robustness Score</div><div class=\"v\">{c['robustness_score']:.3f}</div></div>
        <div class=\"card\"><div class=\"k\">Recommended Return</div><div class=\"v\">{pct(c['total_return_pct'])}</div></div>
        <div class=\"card\"><div class=\"k\">Sortino Ratio</div><div class=\"v\">{c['sortino_ratio']:.3f}</div></div>
      </div>
    </div>

    <div class=\"section\">
      <h2>Execution Gate Status (Secondary)</h2>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"k\">Research Status</div><div class=\"v good\">{h(c['overall_status'])}</div></div>
        <div class=\"card\"><div class=\"k\">Walk-Forward Gate</div><div class=\"v good\">{h(c['walk_forward_pass'])}</div></div>
        <div class=\"card\"><div class=\"k\">Campaign Mean PnL</div><div class=\"v\">{c['campaign_mean_pnl']:.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Campaign Mean Sharpe</div><div class=\"v\">{c['campaign_mean_sharpe']:.3f}</div></div>
      </div>
    </div>

    <div class=\"section\">
      <h2>Minute Data Coverage and Intervals</h2>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"k\">Rows</div><div class=\"v\">{int(d.get('rows', 0) or 0)}</div></div>
        <div class=\"card\"><div class=\"k\">Start UTC</div><div class=\"v\" style=\"font-size:15px\">{h(d.get('start_utc', 'n/a'))}</div></div>
        <div class=\"card\"><div class=\"k\">End UTC</div><div class=\"v\" style=\"font-size:15px\">{h(d.get('end_utc', 'n/a'))}</div></div>
        <div class=\"card\"><div class=\"k\">Median Interval (s)</div><div class=\"v\">{float(d.get('interval_seconds_median', 0.0)):.1f}</div></div>
        <div class=\"card\"><div class=\"k\">P05 Interval (s)</div><div class=\"v\">{float(d.get('interval_seconds_p05', 0.0)):.1f}</div></div>
        <div class=\"card\"><div class=\"k\">P95 Interval (s)</div><div class=\"v\">{float(d.get('interval_seconds_p95', 0.0)):.1f}</div></div>
      </div>
    </div>

    <div class=\"section\">
      <h2>Execution Realism Snapshot</h2>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"k\">Mean Fill Ratio</div><div class=\"v\">{pct(float(x.get('fill_ratio_mean', 0.0)))}</div></div>
        <div class=\"card\"><div class=\"k\">Fill Ratio P05</div><div class=\"v\">{pct(float(x.get('fill_ratio_p05', 0.0)))}</div></div>
        <div class=\"card\"><div class=\"k\">Fill Ratio P95</div><div class=\"v\">{pct(float(x.get('fill_ratio_p95', 0.0)))}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Exec Cost (bps)</div><div class=\"v warn\">{float(x.get('execution_cost_bps_mean', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">P95 Exec Cost (bps)</div><div class=\"v warn\">{float(x.get('execution_cost_bps_p95', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Realized Edge (bps)</div><div class=\"v\">{float(x.get('realized_edge_bps_mean', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Execution Quality</div><div class=\"v {exec_quality_class}\">{float(x.get('execution_quality_mean', 0.0)):.1f}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Slippage Cost</div><div class=\"v\">{float(x.get('slippage_cost_mean', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Latency Cost</div><div class=\"v\">{float(x.get('latency_cost_mean', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Impact Cost</div><div class=\"v\">{float(x.get('impact_cost_mean', 0.0)):.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Mean Adverse Cost</div><div class=\"v\">{float(x.get('adverse_selection_cost_mean', 0.0)):.2f}</div></div>
      </div>
      <p class=\"small\">Execution realism now includes slippage, latency, market impact, and adverse-selection penalties in each simulated fill.</p>
    </div>

    <div class=\"section\">
      <h2>Top Strategy Profiles (Deduplicated)</h2>
      <table>
        <thead><tr><th>Strategy</th><th>Budget</th><th>Total Return</th><th>Sortino</th><th>Calmar</th><th>CVaR95</th><th>Max DD %</th><th>Pass Rate</th><th>Fill Ratio</th><th>Exec Cost bps</th><th>Exec Quality</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class=\"small\">Deduplicated by strategy (best robustness per profile) from latest quant experiment epoch. Drawdown is conservative worst-case across full and rolling windows.</p>
    </div>

    <div class=\"section\">
      <h2>Explored Ways (Current Epoch Quant Families)</h2>
      <table>
        <thead><tr><th>Family</th><th>Cases</th><th>Mean Return</th><th>Return CI95</th><th>Mean Sortino</th><th>Mean Sharpe</th><th>Mean DD %</th><th>Mean CVaR95</th><th>Gate Pass Rate</th></tr></thead>
        <tbody>{explored_rows}</tbody>
      </table>
      <p class=\"small\">This table is aggregated from the same quant experiment epoch CSV used for recommendation.</p>
    </div>

    <div class=\"section\">
      <h2>Strategic Way to Increase Profitability</h2>
      <ul>{strategic_list}</ul>
    </div>

    <div class=\"section\">
      <h2>How Strategies Are Chosen</h2>
      <ul>{selection_list}</ul>
      <p class=\"small\">Selection is reliability-first: a strategy is promoted only if all gates pass, then ranked by robustness score with instability penalties.</p>
    </div>

    <div class=\"section\">
      <h2>Team Verification and Evidence</h2>
      <div>
        <span class=\"pill\">A1 Runtime Check</span>
        <span class=\"pill\">A2 Data Freshness Check</span>
        <span class=\"pill\">A3 Strategy Exploration</span>
        <span class=\"pill\">A4 Risk Calibration</span>
        <span class=\"pill\">A5 QA Templates + Gates</span>
        <span class=\"pill\">A6 Docs Governance</span>
        <span class=\"pill\">A7 Quant Weekly Report</span>
        <span class=\"pill\">A8 PM Sign-Off</span>
        <span class=\"pill\">A9 Dashboard Designer</span>
        <span class=\"pill\">A10 Statistical Reliability</span>
        <span class=\"pill\">A11 Cybersecurity Review</span>
      </div>
      <p class=\"small\">Artifacts used:</p>
      <ul>
        <li>{h(files['campaign'])}</li>
        <li>{h(files['analysis'])}</li>
        <li>{h(files['walk_forward'])}</li>
        <li>{h(files['weekly'])}</li>
        <li>{h(files['quant_recommendation_source'])}</li>
        <li>{h(files['quant_coverage_source'])}</li>
      </ul>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    out_dir = Path("artifacts/dashboard")
    out_dir.mkdir(parents=True, exist_ok=True)

    campaign_path = latest("artifacts/campaign_*/campaign_report.json")
    walk_path = latest("artifacts/walk_forward/*_walk_forward_report.json")
    weekly_path = latest("artifacts/weekly/*_weekly_reliability_report.json")
    quant_path = latest("artifacts/quant_experiments/*_quant_experiments.json")
    quant_candidates = sorted(glob.glob("artifacts/quant_experiments/*_quant_experiments.json"))
    quant_source_path = quant_path or (quant_candidates[-1] if quant_candidates else None)

    campaign = read_json(campaign_path) or {}
    walk = read_json(walk_path) or {}
    weekly = read_json(weekly_path) or {}
    quant = read_json(quant_source_path) or {}
    quant_anchor = quant

    campaign_mean_pnl = float(campaign.get("summary", {}).get("total_pnl", {}).get("mean", 0.0))
    campaign_mean_sharpe = float(campaign.get("summary", {}).get("sharpe_ratio", {}).get("mean", 0.0))
    walk_pass = bool(walk.get("gate", {}).get("pass", False))
    overall_status = "PAPER RESEARCH READY" if (walk_pass and campaign_mean_pnl > 0 and weekly.get("status") == "pass") else "RESEARCH NEEDS TUNING"

    recommendation = quant.get("recommendation", {})
    quant_top = dedupe_quant_rows(quant.get("top_10", []), limit=8)
    explored = build_explored_from_quant_csv(quant_source_path)
    robustness_snapshot = build_robustness_snapshot_from_quant_csv(quant_source_path)
    execution_snapshot = build_execution_snapshot_from_quant_csv(quant_source_path)
    data_profile = (quant_anchor.get("meta", {}) or {}).get("data_profile", {})
    total_cases = int(quant_anchor.get("total_cases", 0) or 0)
    gate_pass_count = int(quant_anchor.get("gate_pass_count", 0) or 0)
    gate_pass_ratio = (gate_pass_count / total_cases) if total_cases > 0 else 0.0

    best_family = explored[0] if explored else {}
    avg_family_return = (
        (sum(float(x.get("mean_total_return_pct", 0.0)) for x in explored) / len(explored))
        if explored
        else 0.0
    )
    ret_lead = float(recommendation.get("total_return_pct", 0.0)) - avg_family_return
    rec_max_dd = float(recommendation.get("max_drawdown_pct", 0.0))
    rec_cvar = float(recommendation.get("cvar_95_pct", 0.0))
    top_pass_rate = (
        sum(float(x.get("pass_rate", 0.0)) for x in quant_top) / len(quant_top)
        if quant_top
        else 0.0
    )
    worst_seed_return = float(recommendation.get("worst_seed_return_pct", 0.0))
    worst_seed_dd = float(recommendation.get("worst_seed_drawdown_pct", recommendation.get("max_drawdown_pct", 0.0)))
    seed_return_std = float(recommendation.get("seed_return_std_pct", 0.0))
    selection_gates = quant.get("gates", {})

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cards": {
            "overall_status": overall_status,
            "walk_forward_pass": "PASS" if walk_pass else "FAIL",
            "campaign_mean_pnl": campaign_mean_pnl,
            "campaign_mean_sharpe": campaign_mean_sharpe,
            "total_cases": total_cases,
            "gate_pass_ratio": gate_pass_ratio,
            "quant_strategy": safe(recommendation.get("strategy"), "n/a"),
            "robustness_score": float(recommendation.get("robustness_score", 0.0)),
            "sortino_ratio": float(recommendation.get("sortino_ratio", 0.0)),
            "total_return_pct": float(recommendation.get("total_return_pct", 0.0)),
            "cvar_95_pct": float(recommendation.get("cvar_95_pct", 0.0)),
            "fill_ratio": float(recommendation.get("fill_ratio", 0.0)),
            "execution_cost_bps": float(recommendation.get("execution_cost_bps", 0.0)),
            "execution_quality_score": float(recommendation.get("execution_quality_score", 0.0)),
        },
        "quant_top": quant_top,
        "robustness_snapshot": robustness_snapshot,
        "execution_snapshot": execution_snapshot,
        "data_profile": data_profile,
        "explored_strategies": explored,
        "capabilities": [
            "Docker-first orchestration with repeatable reliability gates",
            "Paper-only realtime quoting with public market data (no API keys)",
            "Backtest + walk-forward risk gating with strict drawdown controls",
            "Quant strategy laboratory with robust risk metrics (Sortino, Calmar, CVaR, Ulcer)",
            "Multisymbol paper shadow operation for rollout rehearsal",
            "Operational cadence: daily smoke, weekly reliability report, failure triage",
            "Not live-trading ready: current results are backtest/paper evidence only",
        ],
        "limitations": [
            "Execution realism is improved, but live venue queue dynamics and hidden liquidity are still not fully modeled.",
            "No real order placement yet; this remains paper/research evidence rather than production fill telemetry.",
            "Current recommendation is for paper research only, not capital deployment.",
            "Deep validation uses selected windows; broader regime coverage still required.",
        ],
        "strategic_profitability_path": [
            f"Current recommendation is {safe(recommendation.get('strategy'), 'n/a')} with {pct(float(recommendation.get('total_return_pct', 0.0)))} return, Sortino {float(recommendation.get('sortino_ratio', 0.0)):.3f}, CVaR95 {pct_or_bps(rec_cvar)}, and max drawdown {pct_or_bps(rec_max_dd)}.",
            f"Seed stability check: worst-seed return {pct(worst_seed_return)}, worst-seed drawdown {pct_or_bps(worst_seed_dd)}, return dispersion (std) {pct(seed_return_std)}.",
            f"Best explored family now is {safe(best_family.get('strategy_format'), 'n/a')} ({int(best_family.get('cases', 0) or 0)} cases, mean return {pct(float(best_family.get('mean_total_return_pct', 0.0)))}, mean Sortino {float(best_family.get('mean_sortino', 0.0)):.3f}).",
            f"Recommendation edge over explored-family average return is {pct(ret_lead)}; keep promotion gates tied to this edge plus risk constraints.",
            f"Top-profile gate stability is {top_pass_rate:.2f} pass rate across deduplicated leaders; keep replacement policy strict if this falls below 0.95.",
            f"Keep capital allocation risk-first: scale only profiles that maintain CVaR95 <= 5 bps and max drawdown <= 0.20% in walk-forward windows.",
            "Run weekly rolling re-optimization; promote a new profile only when Sortino, Calmar, and gate-pass remain green on out-of-sample windows.",
            "Increase profitability via execution quality: tighten quote skew, monitor adverse selection, and reduce slippage before increasing aggressiveness.",
        ],
        "selection_gates": selection_gates,
        "files": {
            "campaign": campaign_path,
            "analysis": "n/a (replaced by quant CSV aggregation for consistent scale)",
            "walk_forward": walk_path,
            "weekly": weekly_path,
            "quant_recommendation_source": quant_source_path,
            "quant_coverage_source": quant_source_path,
        },
    }

    html = build_html(payload)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    html_path = out_dir / f"{stamp}_stakeholder_dashboard.html"
    json_path = out_dir / f"{stamp}_stakeholder_dashboard.json"

    html_path.write_text(html, encoding="utf-8")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    latest_html = out_dir / "latest_stakeholder_dashboard.html"
    latest_json = out_dir / "latest_stakeholder_dashboard.json"
    latest_html.write_text(html, encoding="utf-8")
    with latest_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(json.dumps({
        "status": "ok",
        "dashboard_html": str(html_path),
        "dashboard_json": str(json_path),
        "latest_html": str(latest_html),
        "latest_json": str(latest_json),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
