"""The documentation is part of the product: check its shape, links and the prompt builder."""

import re
import unittest

from _helpers import SKILL_ROOT

import brief
from _common import EXAMPLE_LOCAL_PATH, load_config

CONFIG = load_config(local=EXAMPLE_LOCAL_PATH)
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")
MD_FILES = sorted(p for p in SKILL_ROOT.rglob("*.md") if "tests" not in p.parts)


class SkillFrontmatter(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"^---\nname: (\S+)\ndescription: (.+?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(m, "SKILL.md must start with name/description frontmatter")
        self.assertEqual(m.group(1), "oss-contrib")
        self.assertEqual(m.group(1), SKILL_ROOT.name)
        self.assertLess(len(m.group(2)), 1024)

    def test_skill_md_is_short(self):
        self.assertLess(len((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()), 500)

    def test_skill_md_lists_every_card(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for repo in CONFIG["repos"].values():
            self.assertIn(f"({repo['card']})", text)


class Links(unittest.TestCase):
    def test_relative_links_resolve(self):
        for md in MD_FILES:
            for target, _ in LINK.findall(md.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(file=md.relative_to(SKILL_ROOT).as_posix(), link=target):
                    self.assertTrue((md.parent / target).exists())

    def test_backticked_reference_files_exist(self):
        names = {p.name for p in (SKILL_ROOT / "references").glob("*.md")}
        for md in MD_FILES:
            for name in re.findall(r"`([a-z0-9-]+\.md)`", md.read_text(encoding="utf-8")):
                if name in {"RESEARCH.md", "PR-DRAFTS.md", "WORKBOARD.md", "CHANGELOG.md",
                            "PRIVATE-SECURITY-NOTE.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "README.md",
                            "GUIDELINES.md", "AI_POLICY.md", "CLA.md", "SKILL.md", "body.md"}:
                    continue
                if name.endswith(".md") and not name.startswith("R"):
                    with self.subTest(file=md.name, ref=name):
                        self.assertTrue(name in names or name.startswith(("oss-contributions",)), name)


class Cards(unittest.TestCase):
    def test_every_card_has_rules_block_and_notes(self):
        for key, repo in CONFIG["repos"].items():
            text = (SKILL_ROOT / repo["card"]).read_text(encoding="utf-8")
            with self.subTest(repo=key):
                self.assertIn(f"`{repo['upstream']}`", text.splitlines()[0])
                blocks = brief.text_blocks(text, "Agent rules block")
                self.assertTrue(blocks)
                self.assertIn("## Orchestrator notes", text)
                self.assertRegex(text, r"read\s+2026-\d\d-\d\d")

    def test_x402_block_is_upstream_sample(self):
        text = (SKILL_ROOT / "repos" / "x402.md").read_text(encoding="utf-8")
        first = brief.text_blocks(text, "Agent rules block")[0]
        self.assertTrue(first.startswith("You are contributing to x402, an open protocol for internet-native payments."))
        self.assertEqual(len(re.findall(r"^\d+\. [A-Z]", first, re.MULTILINE)), 9)

    def test_rules_blocks_are_numbered(self):
        for key, repo in CONFIG["repos"].items():
            text = (SKILL_ROOT / repo["card"]).read_text(encoding="utf-8")
            for block in brief.text_blocks(text, "Agent rules block"):
                with self.subTest(repo=key):
                    self.assertGreaterEqual(len(re.findall(r"^\d+\. ", block, re.MULTILINE)), 4)


class Brief(unittest.TestCase):
    def test_build_every_repo(self):
        for key in CONFIG["repos"]:
            with self.subTest(repo=key):
                prompt = brief.build(key, "Find one docs fix.", CONFIG)
                self.assertNotRegex(prompt, r"<(UPSTREAM|FORK|OSS_ROOT|OSS_DIR|SKILL_ROOT|WORKSPACE_ROOT|KNOWLEDGE_PATHS|DEFAULT_BRANCH)>")
                self.assertIn(CONFIG["repos"][key]["upstream"], prompt)
                self.assertIn("REPO RULES", prompt)
                card = (SKILL_ROOT / CONFIG["repos"][key]["card"]).read_text(encoding="utf-8")
                for block in brief.text_blocks(card, "Agent rules block"):
                    self.assertIn(block, prompt)
                self.assertTrue(prompt.rstrip().endswith("Find one docs fix."))
                self.assertIn(CONFIG["knowledge_search"], prompt)
                self.assertNotIn("DISCOVERY PLAYBOOK", prompt)

    def test_discover_mode_adds_playbook_before_task(self):
        prompt = brief.build("near-api-js", "Surface: account builders.", CONFIG, discover=True)
        self.assertIn("DISCOVERY PLAYBOOK", prompt)
        self.assertIn("SECURITY-RELEVANT", prompt)
        self.assertLess(prompt.index("REPO RULES"), prompt.index("DISCOVERY PLAYBOOK"))
        self.assertLess(prompt.index("DISCOVERY PLAYBOOK"), prompt.index("TASK"))

    def test_private_rules_only_where_configured(self):
        self.assertIn("PRIVATE REPO NOTES", brief.build("outlayer", "t", CONFIG))
        self.assertNotIn("PRIVATE REPO NOTES", brief.build("foundry", "t", CONFIG))

    def test_merge_overlay(self):
        from _common import merge

        merged = merge({"a": {"x": 1}, "l": ["p"], "s": 1}, {"a": {"y": 2}, "l": ["q", "p"], "s": 2})
        self.assertEqual(merged, {"a": {"x": 1, "y": 2}, "l": ["p", "q"], "s": 2})

    def test_footer_and_disclosure_reach_the_agent(self):
        self.assertIn(CONFIG["footer"], brief.build("docs", "t", CONFIG))
        self.assertIn("--repo docs", brief.build("docs", "t", CONFIG))
        self.assertIn("REQUIRED", brief.build("rust-sdk", "t", CONFIG))
        self.assertNotIn("REQUIRED. Add one plain sentence", brief.build("docs", "t", CONFIG))

    def test_missing_fork_is_explained(self):
        prompt = brief.build("cargo-near", "t", CONFIG)
        self.assertIn("none yet", prompt)

    def test_knowledge_paths_are_absolute(self):
        prompt = brief.build("mpc", "t", CONFIG)
        self.assertIn(CONFIG["workspace_root"] + "/notes/mpc", prompt)
        self.assertIn("PRIVATE REPO NOTES", prompt)
        self.assertIn("notes/mpc/exclusions.md", prompt)

    def test_section_errors(self):
        with self.assertRaises(ValueError):
            brief.section("# nothing here", "Agent rules block")


if __name__ == "__main__":
    unittest.main()
