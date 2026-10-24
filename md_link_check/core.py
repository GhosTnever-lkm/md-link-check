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
FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
SETEXT_RE = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
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


def _fence_transition(line: str, fence: tuple[str, int] | None) -> tuple[tuple[str, int] | None, bool]:
    """Return the active fence and whether this line is a valid fence delimiter."""
    match = FENCE_RE.match(line)
    if not match:
        return fence, False
    marker = match.group("fence")
    info = match.group("info")
    if fence is None:
        if marker[0] == "`" and "`" in info:
            return None, False
        return (marker[0], len(marker)), True
    if marker[0] == fence[0] and len(marker) >= fence[1] and not info.strip():
        return None, True
    return fence, False


def _add_anchor(slug: str, anchors: set[str], counts: dict[str, int]) -> None:
    """Allocate a heading ID without colliding with explicit or generated IDs."""
    n = counts.get(slug, 0)
    anchor = slug if n == 0 else f"{slug}-{n}"
    while anchor in anchors:
        n += 1
        anchor = f"{slug}-{n}"
    anchors.add(anchor)
    counts[slug] = n + 1


def _strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove HTML comments outside inline code and retain comment state across lines."""
    visible: list[str] = []
    index = 0
    code_ticks = 0
    while index < len(line):
        if in_comment:
            end = line.find("-->", index)
            if end == -1:
                return "".join(visible), True
            index = end + 3
            in_comment = False
            continue

        if line[index] == "`":
            end = index + 1
            while end < len(line) and line[end] == "`":
                end += 1
            run = end - index
            if code_ticks == 0:
                code_ticks = run
            elif run == code_ticks:
                code_ticks = 0
            visible.append(line[index:end])
            index = end
            continue

        if code_ticks == 0 and line.startswith("<!--", index):
            in_comment = True
            index += 4
            continue

        visible.append(line[index])
        index += 1
    return "".join(visible), in_comment


def anchors_of(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    fence: tuple[str, int] | None = None
    in_html_comment = False
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if fence is not None:
            fence, _ = _fence_transition(line, fence)
            continue
        line, in_html_comment = _strip_html_comments(line, in_html_comment)
        fence, delimiter = _fence_transition(line, None)
        if delimiter or fence is not None:
            continue

        if SETEXT_RE.match(line) and index > 0:
            title = lines[index - 1].strip()
            if title and not HEADING_RE.match(title) and not FENCE_RE.match(title):
                slug = slugify(title)
                _add_anchor(slug, anchors, counts)
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = slugify(match.group(2))
        _add_anchor(slug, anchors, counts)
    return anchors


def iter_links(text: str):
    fence: tuple[str, int] | None = None
    in_html_comment = False
    for number, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            fence, _ = _fence_transition(line, fence)
            continue
        line, in_html_comment = _strip_html_comments(line, in_html_comment)
        fence, delimiter = _fence_transition(line, None)
        if delimiter or fence is not None:
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
        # Split URL syntax before decoding escaped filename characters.
        file_part = unquote(file_part.partition("?")[0])
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


def check_repo(root: str | Path, exclude: tuple[str, ...] = ()) -> list[Problem]:
    """Check every Markdown file under root; `exclude` globs skip files by relative path."""
    import fnmatch

    base = Path(root).resolve()
    cache: dict[Path, set[str]] = {}
    problems: list[Problem] = []
    for md in sorted(base.rglob("*")):
        if not md.is_file() or md.suffix.lower() not in {".md", ".markdown"}:
            continue
        rel = md.relative_to(base)
        if any(part in {".git", "node_modules", ".venv"} for part in rel.parts):
            continue
        if any(fnmatch.fnmatch(rel.as_posix(), pat) for pat in exclude):
            continue
        problems.extend(check_file(md, base, cache))
    return problems
