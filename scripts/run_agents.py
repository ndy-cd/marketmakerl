#!/usr/bin/env python3
import argparse
import json
import sys

from src.agents.base import ALLOWED_MODES, AgentRuntime, load_runtime_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run marketmakerl multi-role agent runtime")
    parser.add_argument("--config", default="config/config.yaml", help="Path to runtime config yaml")
    parser.add_argument("--mode", choices=sorted(ALLOWED_MODES), help="Override config mode")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum concurrent worker threads")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cfg = load_runtime_config(args.config)
        if args.mode:
            cfg["mode"] = args.mode
        runtime = AgentRuntime(cfg)
        results = runtime.run_all(max_workers=args.max_workers)
        print(json.dumps({"status": "ok", "results": results}, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
