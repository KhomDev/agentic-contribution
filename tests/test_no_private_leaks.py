"""This repository is public: no private term, user home path or email may be committed.

The private terms come from the gitignored overlay local/config.json (`private_terms`),
so this test is strongest on the operator's machine. On a fresh clone it still checks the
generic patterns. Run it before every push.
"""

import json
import re
import subprocess
import unittest

from _helpers import SKILL_ROOT

LOCAL = SKILL_ROOT / "local" / "config.json"

GENERIC = [
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!example\b|someone\b|jdoe\b|<)[A-Za-z0-9._-]+"),
    re.compile(r"/c/Users/(?!example\b|someone\b|jdoe\b)[A-Za-z0-9._-]+"),
    re.compile(r"[\w.+-]+@(gmail|yahoo|outlook|hotmail|proton(mail)?)\.(com|me)", re.I),
]

# Files that legitimately contain the generic patterns as data (the lint lists and their tests).
PATTERN_DATA = {"config/repos.json", "tests/test_pr_lint.py", "tests/test_no_private_leaks.py"}


def tracked_files() -> list[str]:
    """Files git would publish: tracked plus untracked-but-not-ignored."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=SKILL_ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        raise unittest.SkipTest("not a git checkout")
    return [f for f in out.stdout.splitlines() if f and not f.startswith("local/")]


class NoPrivateLeaks(unittest.TestCase):
    def test_local_overlay_is_ignored(self):
        out = subprocess.run(["git", "check-ignore", "-q", "local/config.json"], cwd=SKILL_ROOT)
        self.assertEqual(out.returncode, 0, "local/ must be gitignored")

    def test_no_private_terms(self):
        if not LOCAL.exists():
            self.skipTest("no local/config.json on this machine")
        terms = json.loads(LOCAL.read_text(encoding="utf-8")).get("private_terms", [])
        self.assertTrue(terms, "local/config.json has no private_terms; add the names that must never leak")
        hits = []
        for rel in tracked_files():
            try:
                text = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            for term in terms:
                if term.lower() in text.lower():
                    hits.append(f"{rel}: {term!r}")
        self.assertEqual(hits, [], "private terms in publishable files")

    def test_no_home_paths_or_emails(self):
        hits = []
        for rel in tracked_files():
            if rel in PATTERN_DATA:
                continue
            try:
                text = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
            for rx in GENERIC:
                m = rx.search(text)
                if m:
                    hits.append(f"{rel}: {m.group(0)!r}")
        self.assertEqual(hits, [], "home paths or personal emails in publishable files")


if __name__ == "__main__":
    unittest.main()
