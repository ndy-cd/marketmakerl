#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DOC_FILES = [
    Path("README.md"),
    Path("docs/PROJECT_GUIDE.md"),
    Path("docs/test_strategy.md"),
    Path("docs/MVP_EXECUTION_PLAN.md"),
]


def extract_make_commands(text: str) -> list[str]:
    cmds = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("make "):
            cmds.append(s)
    return cmds


def target_exists(makefile_text: str, cmd: str) -> bool:
    parts = cmd.split()
    if len(parts) < 2:
        return True
    target = parts[1]
    pattern = rf"^\s*{re.escape(target)}\s*:"
    return re.search(pattern, makefile_text, flags=re.MULTILINE) is not None


def main() -> int:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    problems = []
    checks = []

    for doc in DOC_FILES:
        text = doc.read_text(encoding="utf-8")
        cmds = extract_make_commands(text)
        for c in cmds:
            ok = target_exists(makefile, c)
            checks.append({"doc": str(doc), "command": c, "ok": ok})
            if not ok:
                problems.append({"doc": str(doc), "command": c, "issue": "target_missing_in_makefile"})

    required_docs = [
        Path("agent_ops/TEAM_ACTION_PLAN_STRICT.md"),
        Path("agent_ops/TEAM_MEMBER_REPORTS.md"),
        Path("agent_ops/TEAM_SYSTEM_CHECK_REPORT.md"),
    ]
    for p in required_docs:
        exists = p.exists()
        checks.append({"doc": str(p), "command": "exists", "ok": exists})
        if not exists:
            problems.append({"doc": str(p), "command": "exists", "issue": "required_doc_missing"})

    out_dir = Path("artifacts/consistency")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not problems else "fail",
        "checks": checks,
        "problems": problems,
    }
    out_path = out_dir / f"{stamp}_product_consistency.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(json.dumps({"status": out["status"], "report": str(out_path), "problem_count": len(problems)}, indent=2))
    return 0 if not problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
