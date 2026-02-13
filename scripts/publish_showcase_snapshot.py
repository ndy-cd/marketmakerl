#!/usr/bin/env python3
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def latest(pattern: str) -> Optional[str]:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def copy_text(src: str, dst: Path) -> None:
    dst.write_text(Path(src).read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    dashboard_html = latest("artifacts/dashboard/*_stakeholder_dashboard.html")
    dashboard_json = latest("artifacts/dashboard/*_stakeholder_dashboard.json")
    quant_json = latest("artifacts/quant_experiments/*_quant_experiments.json")
    weekly_json = latest("artifacts/weekly/*_weekly_reliability_report.json")

    if not dashboard_html or not dashboard_json:
        raise SystemExit("Dashboard artifacts missing. Run make stakeholder-dashboard first")

    out_dir = Path("docs/showcase")
    out_dir.mkdir(parents=True, exist_ok=True)

    copy_text(dashboard_html, out_dir / "stakeholder_dashboard.html")
    copy_text(dashboard_json, out_dir / "stakeholder_dashboard.json")

    quant = json.loads(Path(quant_json).read_text(encoding="utf-8")) if quant_json else {}
    weekly = json.loads(Path(weekly_json).read_text(encoding="utf-8")) if weekly_json else {}
    rec = quant.get("recommendation", {})

    md = f"""# Stakeholder Showcase Snapshot (MarketMakeRL)

Generated: {datetime.now(timezone.utc).isoformat()}

## Dashboard

- HTML: `docs/showcase/stakeholder_dashboard.html`
- JSON: `docs/showcase/stakeholder_dashboard.json`

## Headline Metrics

- Weekly reliability status: `{weekly.get('status', 'n/a')}`
- Recommended strategy: `{rec.get('strategy', 'n/a')}`
- Recommended budget: `{rec.get('budget', 'n/a')}`
- Recommended robustness score: `{rec.get('robustness_score', 'n/a')}`
- Recommended Sortino ratio: `{rec.get('sortino_ratio', 'n/a')}`
- Recommended CVaR95 %: `{rec.get('cvar_95_pct', 'n/a')}`

## Source Artifacts

- Quant experiments: `{quant_json}`
- Weekly report: `{weekly_json}`
- Dashboard (artifact): `{dashboard_html}`
"""
    (out_dir / "README.md").write_text(md, encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "showcase_dir": str(out_dir),
        "files": [
            str(out_dir / "stakeholder_dashboard.html"),
            str(out_dir / "stakeholder_dashboard.json"),
            str(out_dir / "README.md"),
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
