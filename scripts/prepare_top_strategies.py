#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prepare top-N unique strategy names from quant CSV")
    p.add_argument("--quant-csv", required=True)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--output-file", required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.quant_csv)
    out_path = Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    if df.empty:
        raise SystemExit("quant CSV is empty")

    ranked = (
        df.sort_values("robustness_score", ascending=False)
        .drop_duplicates(subset=["strategy"], keep="first")
        .head(max(1, args.top_n))
    )
    strategies = ranked["strategy"].astype(str).tolist()
    out_path.write_text("\n".join(strategies) + "\n", encoding="utf-8")
    print(
        {
            "status": "ok",
            "input_csv": str(csv_path),
            "selected_count": len(strategies),
            "output_file": str(out_path),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
