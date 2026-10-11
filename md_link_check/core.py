"""Offline Markdown link checker: relative file links and #anchors. No network access."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
FENCE_RE = re.compile(r"^(```|~~~)")
EXTERNAL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


@dataclass(frozen=True)
class Problem:
    file: str
    line: int
    target: str
    reason: str


def slugify(heading: str) -> str:
    """GitHub-style anchor: lowercase, drop punctuation, spaces to hyphens."""
    text = unicodedata.normalize("NFKC", heading).strip().lower()
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def anchors_of(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = slugify(match.group(2))
        n = counts.get(slug, 0)
        anchors.add(slug if n == 0 else f"{slug}-{n}")
        counts[slug] = n + 1
    return anchors


def iter_links(text: str):
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = INLINE_CODE_RE.sub("", line)
        for match in LINK_RE.finditer(line):
            yield number, match.group(1)


def check_file(path: Path, root: Path, cache: dict[Path, set[str]]) -> list[Problem]:
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[Problem] = []
    rel = str(path.relative_to(root))
    for number, target in iter_links(text):
        if EXTERNAL_RE.match(target) or target.startswith("//"):
            continue
        file_part, _, fragment = target.partition("#")
        file_part = unquote(file_part)
        if file_part == "":
            dest = path
        else:
            dest = (path.parent / file_part).resolve()
            try:
                dest.relative_to(root.resolve())
            except ValueError:
                problems.append(Problem(rel, number, target, "points outside the repository"))
                continue
            if not dest.exists():
                problems.append(Problem(rel, number, target, "target file does not exist"))
                continue
        if fragment and dest.is_file() and dest.suffix.lower() in {".md", ".markdown"}:
            if dest not in cache:
                cache[dest] = anchors_of(dest.read_text(encoding="utf-8", errors="replace"))
            if unquote(fragment).lower() not in cache[dest]:
                problems.append(Problem(rel, number, target, "anchor not found in target"))
    return problems


def check_repo(root: str | Path) -> list[Problem]:
    base = Path(root).resolve()
    cache: dict[Path, set[str]] = {}
    problems: list[Problem] = []
    for md in sorted(base.rglob("*.md")):
        if any(part in {".git", "node_modules", ".venv"} for part in md.relative_to(base).parts):
            continue
        problems.extend(check_file(md, base, cache))
    return problems
