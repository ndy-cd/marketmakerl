#!/usr/bin/env python3
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def read_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def safe(v: Any, default: Any = "n/a") -> Any:
    return default if v is None else v


def build_html(payload: dict[str, Any]) -> str:
    c = payload["cards"]
    quant_top = payload["quant_top"]
    explored = payload["explored_strategies"]
    capabilities = payload["capabilities"]
    strategic = payload["strategic_profitability_path"]
    files = payload["files"]

    rows = "".join(
        f"<tr><td>{r['strategy']}</td><td>{r['budget']}</td><td>{r['total_pnl']:.2f}</td><td>{r['sharpe_ratio']:.3f}</td><td>{pct(r['max_drawdown_pct'])}</td><td>{r['pass_rate']:.2f}</td><td>{r['hard_fail_windows']}</td></tr>"
        for r in quant_top
    )

    explored_rows = "".join(
        f"<tr><td>{r['strategy_format']}</td><td>{r['mean_pnl']:.2f}</td><td>{r['mean_sharpe']:.3f}</td><td>{pct(r['mean_drawdown_pct'])}</td><td>{r['pass_rate_40pct_dd']:.2f}</td></tr>"
        for r in explored
    )

    cap_list = "".join(f"<li>{x}</li>" for x in capabilities)
    strategic_list = "".join(f"<li>{x}</li>" for x in strategic)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MarketMakerL MVP Dashboard</title>
  <style>
    :root {{
      --bg: #f6f8fb;
      --ink: #152238;
      --muted: #5b6b83;
      --card: #ffffff;
      --line: #d9e1ee;
      --accent: #0059b2;
      --good: #0b7a3d;
      --warn: #b26a00;
    }}
    body {{ margin: 0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .hero {{ background: linear-gradient(120deg, #dcecff, #f5fbff); border: 1px solid var(--line); border-radius: 16px; padding: 20px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; }}
    .sub {{ color: var(--muted); margin: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-top: 16px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 14px; }}
    .k {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .v {{ font-size: 26px; font-weight: 700; margin-top: 6px; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .section {{ margin-top: 20px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }}
    h2 {{ margin: 0 0 12px; font-size: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); text-align: left; padding: 8px 6px; }}
    th {{ color: var(--muted); font-weight: 600; }}
    ul {{ margin: 0; padding-left: 18px; }}
    .small {{ font-size: 12px; color: var(--muted); }}
    .pill {{ display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; margin-right: 6px; margin-bottom: 6px; font-size: 12px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>MarketMakerL MVP: Stakeholder Analytics Dashboard</h1>
      <p class=\"sub\">Paper-only quant market-making platform with strict risk gates and live-ready operational discipline.</p>
      <p class=\"small\">Generated: {payload['generated_utc']}</p>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"k\">Overall Status</div><div class=\"v good\">{c['overall_status']}</div></div>
        <div class=\"card\"><div class=\"k\">Walk-Forward Gate</div><div class=\"v good\">{c['walk_forward_pass']}</div></div>
        <div class=\"card\"><div class=\"k\">Campaign Mean PnL</div><div class=\"v\">{c['campaign_mean_pnl']:.2f}</div></div>
        <div class=\"card\"><div class=\"k\">Campaign Mean Sharpe</div><div class=\"v\">{c['campaign_mean_sharpe']:.3f}</div></div>
        <div class=\"card\"><div class=\"k\">Quant Recommended Strategy</div><div class=\"v\">{c['quant_strategy']}</div></div>
        <div class=\"card\"><div class=\"k\">Recommended Drawdown</div><div class=\"v\">{pct(c['quant_dd_pct'])}</div></div>
      </div>
    </div>

    <div class=\"section\">
      <h2>What System Can Do Right Now</h2>
      <ul>{cap_list}</ul>
    </div>

    <div class=\"section\">
      <h2>Strategies Explored: Robustness Ranking</h2>
      <table>
        <thead><tr><th>Strategy</th><th>Budget</th><th>Total PnL</th><th>Sharpe</th><th>Max DD %</th><th>Pass Rate</th><th>Hard Fail Windows</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class=\"small\">Top table is from latest quant experiments artifact.</p>
    </div>

    <div class=\"section\">
      <h2>Explored Ways (Last-Month Research Formats)</h2>
      <table>
        <thead><tr><th>Format</th><th>Mean PnL</th><th>Mean Sharpe</th><th>Mean DD %</th><th>40% DD Pass Rate</th></tr></thead>
        <tbody>{explored_rows}</tbody>
      </table>
    </div>

    <div class=\"section\">
      <h2>Strategic Way to Increase Profitability</h2>
      <ul>{strategic_list}</ul>
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
      </div>
      <p class=\"small\">Artifacts used:</p>
      <ul>
        <li>{files['campaign']}</li>
        <li>{files['analysis']}</li>
        <li>{files['walk_forward']}</li>
        <li>{files['weekly']}</li>
        <li>{files['quant']}</li>
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
    analysis_path = latest("artifacts/last_month_analysis/*_analysis.json")
    walk_path = latest("artifacts/walk_forward/*_walk_forward_report.json")
    weekly_path = latest("artifacts/weekly/*_weekly_reliability_report.json")
    quant_path = latest("artifacts/quant_experiments/*_quant_experiments.json")

    campaign = read_json(campaign_path) or {}
    analysis = read_json(analysis_path) or {}
    walk = read_json(walk_path) or {}
    weekly = read_json(weekly_path) or {}
    quant = read_json(quant_path) or {}

    campaign_mean_pnl = float(campaign.get("summary", {}).get("total_pnl", {}).get("mean", 0.0))
    campaign_mean_sharpe = float(campaign.get("summary", {}).get("sharpe_ratio", {}).get("mean", 0.0))
    walk_pass = bool(walk.get("gate", {}).get("pass", False))
    overall_status = "READY FOR MVP SHOWCASE" if (walk_pass and campaign_mean_pnl > 0 and weekly.get("status") == "pass") else "NEEDS TUNING"

    recommendation = quant.get("recommendation", {})

    explored = analysis.get("strategy_format_summary", [])

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cards": {
            "overall_status": overall_status,
            "walk_forward_pass": "PASS" if walk_pass else "FAIL",
            "campaign_mean_pnl": campaign_mean_pnl,
            "campaign_mean_sharpe": campaign_mean_sharpe,
            "quant_strategy": safe(recommendation.get("strategy"), "n/a"),
            "quant_dd_pct": float(recommendation.get("max_drawdown_pct", 0.0)),
        },
        "quant_top": quant.get("top_10", [])[:8],
        "explored_strategies": explored,
        "capabilities": [
            "Docker-first orchestration with repeatable reliability gates",
            "Paper-only realtime quoting with public market data (no API keys)",
            "Backtest + walk-forward risk gating with strict drawdown controls",
            "Quant strategy laboratory with robustness ranking and recommendation",
            "Multisymbol paper shadow operation for rollout rehearsal",
            "Operational cadence: daily smoke, weekly reliability report, failure triage",
        ],
        "strategic_profitability_path": [
            "Exploit regime-adaptive profiles: keep trend-shield as primary and inventory-tight as backup",
            "Allocate capital by robustness score and drawdown efficiency, not by raw PnL",
            "Run weekly rolling re-optimization and replace profile only when strict gates remain green",
            "Improve execution quality (fill/slippage calibration) before increasing strategy aggressiveness",
            "Scale symbols gradually via shadow paper expansion, then promote only stable symbols",
        ],
        "files": {
            "campaign": campaign_path,
            "analysis": analysis_path,
            "walk_forward": walk_path,
            "weekly": weekly_path,
            "quant": quant_path,
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
