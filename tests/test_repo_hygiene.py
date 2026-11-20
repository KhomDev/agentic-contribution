"""Repository hygiene: every publishable text file uses LF line endings."""

import subprocess
import unittest

from _helpers import SKILL_ROOT


class LineEndings(unittest.TestCase):
    def test_no_crlf_in_publishable_files(self):
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=SKILL_ROOT, capture_output=True, text=True, encoding="utf-8",
        )
        if out.returncode != 0:
            self.skipTest("not a git checkout")
        crlf = [
            rel for rel in out.stdout.splitlines()
            if rel and not rel.startswith("local/") and b"\r\n" in (SKILL_ROOT / rel).read_bytes()
        ]
        self.assertEqual(crlf, [], "files with CRLF line endings (Windows tools wrote them)")

    def test_gitattributes_forces_lf(self):
        text = (SKILL_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("eol=lf", text)


if __name__ == "__main__":
    unittest.main()
