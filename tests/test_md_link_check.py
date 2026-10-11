import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from md_link_check.cli import main
from md_link_check.core import anchors_of, check_repo, slugify


def repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


class SlugTests(unittest.TestCase):
    def test_github_style_slugs(self):
        self.assertEqual(slugify("Quick Start!"), "quick-start")
        self.assertEqual(slugify("`code` & more"), "code--more")

    def test_duplicate_headings_get_suffix(self):
        self.assertEqual(anchors_of("# A\n# A\n"), {"a", "a-1"})

    def test_headings_inside_code_fences_ignored(self):
        self.assertEqual(anchors_of("```\n# not a heading\n```\n"), set())


class CheckTests(unittest.TestCase):
    def test_valid_links_pass(self):
        root = repo({"README.md": "[d](docs/a.md) [s](docs/a.md#intro)\n", "docs/a.md": "# Intro\n"})
        self.assertEqual(check_repo(root), [])

    def test_missing_file_reported(self):
        root = repo({"README.md": "[x](nope.md)\n"})
        problems = check_repo(root)
        self.assertEqual([p.reason for p in problems], ["target file does not exist"])

    def test_missing_anchor_reported(self):
        root = repo({"README.md": "[x](a.md#missing)\n", "a.md": "# Real\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["anchor not found in target"])

    def test_same_page_anchor(self):
        root = repo({"README.md": "# Top\n[ok](#top) [bad](#nope)\n"})
        problems = check_repo(root)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].target, "#nope")

    def test_external_links_are_skipped(self):
        root = repo({"README.md": "[w](https://example.com/x) [m](mailto:a@b.c)\n"})
        self.assertEqual(check_repo(root), [])

    def test_link_inside_fence_is_skipped(self):
        root = repo({"README.md": "```\n[x](missing.md)\n```\n"})
        self.assertEqual(check_repo(root), [])

    def test_link_inside_inline_code_is_skipped(self):
        root = repo({"README.md": "Пример: `[x](missing.md)` — не ссылка.\n"})
        self.assertEqual(check_repo(root), [])

    def test_path_escape_reported(self):
        root = repo({"README.md": "[x](../../etc/passwd)\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["points outside the repository"])

    def test_percent_encoded_path(self):
        root = repo({"README.md": "[x](my%20doc.md)\n", "my doc.md": "hi\n"})
        self.assertEqual(check_repo(root), [])


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_clean_exit_zero(self):
        code, out = self.run_cli([str(repo({"a.md": "# T\n"}))])
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_broken_exit_one_and_json(self):
        root = repo({"a.md": "[x](gone.md)\n"})
        code, out = self.run_cli(["--json", str(root)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)[0]["target"], "gone.md")

    def test_bad_path_exit_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.run_cli(["/no/such/dir"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
