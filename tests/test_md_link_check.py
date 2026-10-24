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

    def test_explicit_suffix_after_duplicate_gets_unique_anchor(self):
        self.assertEqual(anchors_of("# A\n# A\n# A-1\n"), {"a", "a-1", "a-1-1"})

    def test_explicit_suffix_before_duplicate_is_not_overwritten(self):
        self.assertEqual(anchors_of("# A-1\n# A\n# A\n"), {"a-1", "a", "a-2"})

    def test_generated_suffix_collisions_keep_incrementing(self):
        text = "# A\n# A\n# A-1\n# A-1\n# A\n"
        self.assertEqual(anchors_of(text), {"a", "a-1", "a-1-1", "a-1-2", "a-2"})

    def test_setext_and_atx_headings_share_unique_namespace(self):
        text = "A\n===\n# A\nA-1\n---\n"
        self.assertEqual(anchors_of(text), {"a", "a-1", "a-1-1"})

    def test_headings_inside_code_fences_ignored(self):
        self.assertEqual(anchors_of("```\n# not a heading\n```\n"), set())

    def test_headings_inside_multiline_html_comments_are_ignored(self):
        self.assertEqual(anchors_of("<!--\n# Hidden\n-->\n# Visible\n"), {"visible"})

    def test_long_fence_is_not_closed_by_shorter_fence(self):
        text = "````markdown\n```\n# hidden\n```\n````\n# visible\n"
        self.assertEqual(anchors_of(text), {"visible"})

    def test_setext_heading_creates_anchor(self):
        self.assertEqual(anchors_of("Quick Start\n===========\n"), {"quick-start"})


class CheckTests(unittest.TestCase):
    def test_valid_links_pass(self):
        root = repo({"README.md": "[d](docs/a.md) [s](docs/a.md#intro)\n", "docs/a.md": "# Intro\n"})
        self.assertEqual(check_repo(root), [])

    def test_balanced_parentheses_in_link_destination(self):
        root = repo({
            "README.md": "[manual](docs/setup_(windows).md#quick-start)\n",
            "docs/setup_(windows).md": "# Quick Start\n",
        })
        self.assertEqual(check_repo(root), [])

    def test_multiple_parenthetical_segments_in_link_destination(self):
        root = repo({
            "README.md": "[manual](docs/setup_(windows)_(steam).md)\n",
            "docs/setup_(windows)_(steam).md": "# Setup\n",
        })
        self.assertEqual(check_repo(root), [])

    def test_missing_file_reported(self):
        root = repo({"README.md": "[x](nope.md)\n"})
        problems = check_repo(root)
        self.assertEqual([p.reason for p in problems], ["target file does not exist"])

    def test_missing_anchor_reported(self):
        root = repo({"README.md": "[x](a.md#missing)\n", "a.md": "# Real\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["anchor not found in target"])

    def test_links_to_collision_resolved_anchors_pass(self):
        root = repo({"README.md": "# A-1\n# A\n# A\n[x](#a-2)\n"})
        self.assertEqual(check_repo(root), [])

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

    def test_links_inside_multiline_html_comments_are_skipped(self):
        root = repo({"README.md": "<!-- start\n[x](missing.md)\n-->\n[y](also-missing.md)\n"})
        problems = check_repo(root)
        self.assertEqual([problem.target for problem in problems], ["also-missing.md"])

    def test_html_comment_markers_inside_fences_do_not_hide_later_links(self):
        root = repo({"README.md": "```\n<!--\n```\n[x](missing.md)\n"})
        self.assertEqual([problem.target for problem in check_repo(root)], ["missing.md"])

    def test_html_comment_markers_inside_inline_code_are_ignored(self):
        root = repo({"README.md": "`<!-- [x](ignored.md) -->` [y](missing.md)\n"})
        self.assertEqual([problem.target for problem in check_repo(root)], ["missing.md"])

    def test_link_inside_inline_code_is_skipped(self):
        root = repo({"README.md": "Пример: `[x](missing.md)` — не ссылка.\n"})
        self.assertEqual(check_repo(root), [])

    def test_path_escape_reported(self):
        root = repo({"README.md": "[x](../../etc/passwd)\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["points outside the repository"])

    def test_relative_link_query_is_not_part_of_filename(self):
        root = repo({"README.md": "[guide](guide.md?plain=1#intro)\n", "guide.md": "# Intro\n"})
        self.assertEqual(check_repo(root), [])

    def test_query_does_not_hide_missing_anchor(self):
        root = repo({"README.md": "[guide](guide.md?plain=1#missing)\n", "guide.md": "# Intro\n"})
        problems = check_repo(root)
        self.assertEqual([p.reason for p in problems], ["anchor not found in target"])
        self.assertEqual(problems[0].target, "guide.md?plain=1#missing")

    def test_query_only_link_uses_current_document(self):
        root = repo({"README.md": "# Top\n[guide](?plain=1#top)\n[view](?plain=1)\n"})
        self.assertEqual(check_repo(root), [])

    def test_encoded_question_mark_remains_in_filename(self):
        import os

        if os.name == "nt":
            self.skipTest("Windows does not allow question marks in filenames")
        root = repo({"README.md": "[guide](guide%3Fdraft.md?plain=1#intro)\n", "guide?draft.md": "# Intro\n"})
        self.assertEqual(check_repo(root), [])

    def test_encoded_hash_remains_in_filename(self):
        root = repo({"README.md": "[guide](guide%23draft.md?plain=1#intro)\n", "guide#draft.md": "# Intro\n"})
        self.assertEqual(check_repo(root), [])

    def test_query_separator_in_fragment_is_not_a_path_query(self):
        root = repo({"README.md": "[guide](guide.md#intro?plain=1)\n", "guide.md": "# Intro\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["anchor not found in target"])

    def test_query_does_not_hide_missing_file(self):
        root = repo({"README.md": "[guide](missing.md?plain=1#intro)\n"})
        self.assertEqual([p.reason for p in check_repo(root)], ["target file does not exist"])

    def test_percent_encoded_path(self):
        root = repo({"README.md": "[x](my%20doc.md)\n", "my doc.md": "hi\n"})
        self.assertEqual(check_repo(root), [])

    def test_markdown_extension_and_setext_target_are_scanned(self):
        root = repo({"README.md": "[guide](guide.markdown#quick-start)\n", "guide.markdown": "Quick Start\n===========\n"})
        self.assertEqual(check_repo(root), [])

    def test_links_inside_long_fence_are_skipped(self):
        root = repo({
            "README.md": "````markdown\n```\n[x](missing.md)\n```\n````\n[ok](exists.md)\n",
            "exists.md": "# Exists\n",
        })
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

    def test_version_matches_package_metadata(self):
        from md_link_check import __version__

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as raised:
            main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(buf.getvalue().strip(), __version__)


if __name__ == "__main__":
    unittest.main()
