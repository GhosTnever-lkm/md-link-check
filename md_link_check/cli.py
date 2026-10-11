"""md-link-check [PATH] [--json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import check_repo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="md-link-check", description="Check relative links and anchors in Markdown files (offline).")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--json", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    if not Path(args.path).is_dir():
        print(f"md-link-check: not a directory: {args.path}", file=sys.stderr)
        return 2
    problems = check_repo(args.path)
    if args.json:
        print(json.dumps([p.__dict__ for p in problems], indent=2, ensure_ascii=False))
    elif not problems:
        print("OK: all relative links and anchors resolve")
    else:
        for pr in problems:
            print(f"{pr.file}:{pr.line}: {pr.reason}: {pr.target}")
        print(f"{len(problems)} problem(s) found")
    return 1 if problems else 0
