#!/usr/bin/env python3
import argparse
import html
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Serve dashboard files with directory listing disabled.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--directory", default="docs/showcase")
    p.add_argument("--index", default="stakeholder_dashboard.html")
    return p.parse_args()


def _safe_join(base_dir: Path, url_path: str) -> Path:
    parsed = urlparse(url_path)
    raw_path = unquote(parsed.path)
    if raw_path in {"", "/"}:
        raw_path = ""
    rel = Path(raw_path.lstrip("/"))
    candidate = (base_dir / rel).resolve()
    try:
        candidate.relative_to(base_dir)
    except ValueError:
        return base_dir / "__forbidden__"
    return candidate


def build_handler(base_dir: Path, index_name: str):
    class SecureDashboardHandler(SimpleHTTPRequestHandler):
        server_version = "MarketMakeRLDashboard/1.0"
        sys_version = ""

        def translate_path(self, path: str) -> str:
            target = _safe_join(base_dir, path)
            if target.name == "__forbidden__":
                return str(target)
            if target.is_dir():
                index_path = target / index_name
                if index_path.exists():
                    return str(index_path)
            return str(target)

        def list_directory(self, path):  # noqa: ANN001
            self.send_error(403, "Directory listing is disabled")
            return None

        def send_head(self):  # noqa: D401
            fs_path = Path(self.translate_path(self.path))
            if fs_path.name == "__forbidden__":
                self.send_error(403, "Forbidden path")
                return None
            if fs_path.is_dir():
                self.send_error(403, "Directory listing is disabled")
                return None
            if not fs_path.exists():
                self.send_error(404, f"File not found: {html.escape(self.path)}")
                return None
            return super().send_head()

        def end_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            super().log_message(format, *args)

    return SecureDashboardHandler


def main() -> int:
    args = parse_args()
    base_dir = Path(args.directory).resolve()
    if not base_dir.exists():
        raise SystemExit(f"Dashboard directory does not exist: {base_dir}")

    os.chdir(str(base_dir))
    handler = build_handler(base_dir=base_dir, index_name=args.index)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving dashboard securely on http://{args.host}:{args.port}/{args.index}")
    print(f"Directory listing: disabled, root: {base_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
