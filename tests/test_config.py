import re
import unittest

from _helpers import SKILL_ROOT

from _common import EXAMPLE_LOCAL_PATH, load_config, repo_by_upstream

REQUIRED = {
    "upstream", "fork", "default_branch", "budget", "process", "title", "commit_subject_enforcement",
    "ai_disclosure", "pr_body", "changelog", "sources", "card", "examples", "body_sections",
    "oss_dir", "knowledge",
}


class ConfigShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(local=EXAMPLE_LOCAL_PATH)

    def test_fifteen_repos(self):
        self.assertEqual(len(self.config["repos"]), 15)

    def test_every_repo_has_required_fields(self):
        for key, repo in self.config["repos"].items():
            with self.subTest(repo=key):
                self.assertEqual(REQUIRED - set(repo), set(), "missing fields")

    def test_enums(self):
        for key, repo in self.config["repos"].items():
            with self.subTest(repo=key):
                self.assertIn(repo["ai_disclosure"], {"required", "none"})
                self.assertIn(repo["pr_body"], {"template", "prose"})
                self.assertIn(repo["title"]["enforcement"], {"error", "warn"})
                self.assertIn(repo["commit_subject_enforcement"], {"error", "warn"})
                self.assertIn(repo["default_branch"], {"main", "master"})
                self.assertGreaterEqual(repo["budget"], 1)
                self.assertEqual(set(repo["process"]), {"issue_first", "draft_first", "cla", "signed_commits"})

    def test_fork_is_khomdev_or_null(self):
        for key, repo in self.config["repos"].items():
            with self.subTest(repo=key):
                fork = repo["fork"]
                self.assertTrue(fork is None or fork.startswith("KhomDev/"), fork)

    def test_card_exists(self):
        for key, repo in self.config["repos"].items():
            with self.subTest(repo=key):
                self.assertTrue((SKILL_ROOT / repo["card"]).is_file(), repo["card"])

    def test_upstreams_unique_and_lookup(self):
        ups = [r["upstream"].lower() for r in self.config["repos"].values()]
        self.assertEqual(len(ups), len(set(ups)))
        self.assertEqual(repo_by_upstream(self.config, "NEAR/MPC"), "mpc")
        self.assertIsNone(repo_by_upstream(self.config, "someone/else"))

    def test_mcp_repos_require_disclosure(self):
        for key, repo in self.config["repos"].items():
            if repo["upstream"].startswith("modelcontextprotocol/"):
                self.assertEqual(repo["ai_disclosure"], "required", key)

    def test_patterns_compile(self):
        for p in self.config["public_text"]["error_patterns"] + self.config["public_text"]["warn_patterns"]:
            re.compile(p)
        re.compile(self.config["co_author_pattern"])


class TitleExamples(unittest.TestCase):
    """Each repo's title regex accepts its real merged titles and rejects the bad ones."""

    def test_examples(self):
        config = load_config(local=EXAMPLE_LOCAL_PATH)
        for key, repo in config["repos"].items():
            rx = re.compile(repo["title"]["regex"])
            self.assertTrue(repo["examples"]["good"], f"{key}: no good examples")
            self.assertTrue(repo["examples"]["bad"], f"{key}: no bad examples")
            for title in repo["examples"]["good"]:
                with self.subTest(repo=key, good=title):
                    self.assertRegex(title, rx)
            for title in repo["examples"]["bad"]:
                with self.subTest(repo=key, bad=title):
                    bad = rx.match(title) is None or title.endswith(".") or len(title) > repo["title"]["max_len"]
                    self.assertTrue(bad, f"{key} accepts a title it should reject: {title!r}")


if __name__ == "__main__":
    unittest.main()
