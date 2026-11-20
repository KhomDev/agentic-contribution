import unittest

from _helpers import SKILL_ROOT  # noqa: F401  (sets sys.path)

import pr_lint
from _common import EXAMPLE_LOCAL_PATH, load_config

CONFIG = load_config(local=EXAMPLE_LOCAL_PATH)
FOOTER = CONFIG["footer"]
TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def errors(findings):
    return [f for f in findings if f.level == "error"]


def body(text, footer=True):
    return text.strip() + ("\n\n" + FOOTER + "\n" if footer else "\n")


X402_BODY = body(
    """## Description
Closes #4300. The settlement cache never evicted expired entries.

## Tests
`pnpm --filter @x402/near test`: 71 passed.

## Checklist
- [x] I have formatted and linted my code

## AI assistance
Most of this change was written with Claude Code; I reviewed every line.
"""
)


class Titles(unittest.TestCase):
    def test_good_x402_title(self):
        self.assertEqual(errors(pr_lint.lint("x402", "fix(near): evict expired settlement entries", None, [], CONFIG)), [])

    def test_trailing_period_is_error(self):
        f = pr_lint.lint("x402", "fix(near): evict expired entries.", None, [], CONFIG)
        self.assertTrue(any("period" in x.message for x in errors(f)))

    def test_too_long(self):
        f = pr_lint.lint("x402", "fix(near): " + "x" * 80, None, [], CONFIG)
        self.assertTrue(any("limit" in x.message for x in errors(f)))

    def test_nearcore_doc_not_docs(self):
        self.assertTrue(errors(pr_lint.lint("nearcore", "docs: update readme", None, [], CONFIG)))
        self.assertEqual(errors(pr_lint.lint("nearcore", "doc: update readme", None, [], CONFIG)), [])

    def test_foundry_soft_length_warns(self):
        f = pr_lint.lint("foundry", "fix(config): use slashes in the scoped alias warning target path", None, [], CONFIG)
        self.assertEqual(errors(f), [])
        self.assertTrue(any(x.level == "warn" and "prefers" in x.message for x in f))

    def test_warn_enforcement_does_not_error(self):
        f = pr_lint.lint("near-sdk-rs", "Centralize dependencies", None, [], CONFIG)
        self.assertEqual(errors(f), [])
        self.assertTrue(f)

    def test_private_term_in_title(self):
        self.assertTrue(errors(pr_lint.lint("docs", "Fix gas examples found in example-secret-project", None, [], CONFIG)))


class Bodies(unittest.TestCase):
    def test_clean_x402_body(self):
        self.assertEqual(errors(pr_lint.lint_body(X402_BODY, CONFIG["repos"]["x402"], CONFIG)), [])

    def test_missing_footer(self):
        f = pr_lint.lint_body(X402_BODY.replace(FOOTER, ""), CONFIG["repos"]["x402"], CONFIG)
        self.assertTrue(any("footer" in x.message for x in errors(f)))

    def test_footer_alone_is_not_disclosure(self):
        section = "## AI assistance\nMost of this change was written with Claude Code; I reviewed every line.\n"
        self.assertIn(section, X402_BODY)
        text = X402_BODY.replace(section, "")
        f = pr_lint.lint_body(text, CONFIG["repos"]["x402"], CONFIG)
        self.assertTrue(any("disclosure" in x.message for x in errors(f)))

    def test_rust_sdk_disclosure_variants(self):
        repo = CONFIG["repos"]["rust-sdk"]
        for sentence in (
            "This PR was written primarily by Claude Code.",
            "AI assistance: Claude Code generated the first draft; I reviewed it.",
            "I used AI (Claude) to draft the test.",
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(errors(pr_lint.lint_body(body("Fixes #12.\n\n" + sentence), repo, CONFIG)), [])

    def test_missing_template_section(self):
        text = X402_BODY.replace("## Tests", "## Testing")
        f = pr_lint.lint_body(text, CONFIG["repos"]["x402"], CONFIG)
        self.assertTrue(any("Tests" in x.message for x in errors(f)))

    def test_private_terms_are_errors(self):
        repo = CONFIG["repos"]["docs"]
        for leak in (
            "I found this while working on example-secret-project.",
            "A Haiku agent drafted this.",
            "Log at C:\\Users\\jdoe\\Desktop\\x.log",
            "see /c/Users/someone/notes",
            "mail me at someone.private@gmail.com",
            "the orchestrator verified it",
        ):
            with self.subTest(leak=leak):
                self.assertTrue(errors(pr_lint.lint_body(body(leak), repo, CONFIG)), leak)

    def test_warn_terms_are_only_warnings(self):
        f = pr_lint.lint_body(body("The review agent's commands now run in a sandbox."), CONFIG["repos"]["mpc"], CONFIG)
        self.assertEqual(errors(f), [])
        self.assertTrue(any(x.level == "warn" for x in f))

    def test_foundry_wants_prose(self):
        repo = CONFIG["repos"]["foundry"]
        f = pr_lint.lint_body(body("## Motivation\n- Tested with cargo test"), repo, CONFIG)
        self.assertTrue(any("prose" in x.message for x in f))
        clean = pr_lint.lint_body(body("Loading two Ledger signers failed because the second one reused the first's path."), repo, CONFIG)
        self.assertFalse(any("prose" in x.message for x in clean))

    def test_issue_first_wants_issue_link(self):
        f = pr_lint.lint_body(body("Change without a link."), CONFIG["repos"]["openzeppelin"], CONFIG)
        self.assertTrue(any("issue" in x.message for x in f))

    def test_comment_mode_skips_pr_template(self):
        reply = body("Thanks. Fixed in 8896b98: the test now says why the row is orphaned.")
        self.assertEqual(errors(pr_lint.lint_body(reply, CONFIG["repos"]["x402"], CONFIG, comment=True)), [])
        self.assertTrue(errors(pr_lint.lint_body(reply, CONFIG["repos"]["x402"], CONFIG)))

    def test_comment_mode_keeps_leak_scan_and_footer(self):
        repo = CONFIG["repos"]["x402"]
        self.assertTrue(errors(pr_lint.lint_body(body("Fixed; the haiku agent checked it."), repo, CONFIG, comment=True)))
        self.assertTrue(errors(pr_lint.lint_body("Fixed in abc.", repo, CONFIG, comment=True)))

    def test_issue_title_skips_pr_format_but_not_leaks(self):
        title = "createAccount treats any name ending in the parent's account ID as a sub-account"
        self.assertEqual(errors(pr_lint.lint("near-api-js", title, None, [], CONFIG, comment=True)), [])
        self.assertTrue(errors(pr_lint.lint("near-api-js", title, None, [], CONFIG)))
        self.assertTrue(errors(pr_lint.lint("near-api-js", "Bug found for jdoe", None, [], CONFIG, comment=True)))

    def test_mcp_comments_need_disclosure(self):
        repo = CONFIG["repos"]["rust-sdk"]
        self.assertTrue(errors(pr_lint.lint_body(body("Fixed in abc."), repo, CONFIG, comment=True)))
        ok = body("Fixed in abc. This reply was drafted with Claude Code and checked by me.")
        self.assertEqual(errors(pr_lint.lint_body(ok, repo, CONFIG, comment=True)), [])

    def test_empty_body(self):
        self.assertTrue(errors(pr_lint.lint_body("  \n", CONFIG["repos"]["docs"], CONFIG)))


class Commits(unittest.TestCase):
    def msg(self, subject="fix(near): evict expired settlement entries", extra=""):
        return f"{subject}\n\nThe cache grew without bound.\n{extra}\n{TRAILER}\n"

    def test_clean_commit(self):
        self.assertEqual(errors(pr_lint.lint_commit(self.msg(), CONFIG["repos"]["x402"], CONFIG, "c")), [])

    def test_missing_trailer(self):
        f = pr_lint.lint_commit("fix(near): x\n\nwhy\n", CONFIG["repos"]["x402"], CONFIG, "c")
        self.assertTrue(any("trailer" in x.message for x in errors(f)))

    def test_two_claude_trailers(self):
        m = self.msg(extra="Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>")
        f = pr_lint.lint_commit(m, CONFIG["repos"]["x402"], CONFIG, "c")
        self.assertTrue(any("exactly one" in x.message for x in errors(f)))

    def test_fable_trailer_accepted(self):
        m = "fix(near): x\n\nwhy\n\nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\n"
        self.assertEqual(errors(pr_lint.lint_commit(m, CONFIG["repos"]["x402"], CONFIG, "c")), [])

    def test_second_line_must_be_blank(self):
        f = pr_lint.lint_commit(f"fix(near): x\nbody\n{TRAILER}\n", CONFIG["repos"]["x402"], CONFIG, "c")
        self.assertTrue(any("blank" in x.message for x in errors(f)))

    def test_subject_format_enforcement(self):
        bad = self.msg(subject="Evict expired entries")
        self.assertTrue(errors(pr_lint.lint_commit(bad, CONFIG["repos"]["rust-sdk"], CONFIG, "c")))
        self.assertEqual(errors(pr_lint.lint_commit(bad, CONFIG["repos"]["mpc"], CONFIG, "c")), [])

    def test_rust_sdk_body_line_limit(self):
        m = self.msg(subject="fix(client): keep scope", extra="x" * 101)
        f = pr_lint.lint_commit(m, CONFIG["repos"]["rust-sdk"], CONFIG, "c")
        self.assertTrue(any("over 100" in x.message for x in errors(f)))

    def test_private_term_in_commit_body(self):
        m = self.msg(extra="Found while reviewing for jdoe.")
        self.assertTrue(errors(pr_lint.lint_commit(m, CONFIG["repos"]["x402"], CONFIG, "c")))


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        import tempfile, os

        with tempfile.TemporaryDirectory() as d:
            good = os.path.join(d, "b.md")
            with open(good, "w", encoding="utf-8") as fh:
                fh.write(X402_BODY)
            import io
            from contextlib import redirect_stdout

            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(pr_lint.main(["--repo", "x402", "--title", "fix(near): evict expired entries", "--body-file", good]), 0)
                self.assertEqual(pr_lint.main(["--repo", "x402", "--title", "Evict expired entries", "--body-file", good]), 1)
            self.assertIn("x402: 1 error(s)", out.getvalue())


if __name__ == "__main__":
    unittest.main()
