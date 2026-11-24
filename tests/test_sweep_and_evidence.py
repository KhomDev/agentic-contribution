"""sweep, refcheck, verify_draft, outcomes and the brief's placeholder guard, through a fake `gh`."""

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from _helpers import FakeGh, quota

import brief
import outcomes
import refcheck
import sweep
import verify_draft
from _common import EXAMPLE_LOCAL_PATH, Gh, load_config

CONFIG = load_config(local=EXAMPLE_LOCAL_PATH)
SINCE = "2026-11-22T12:00:00Z"
CI = CONFIG["ci_repo"]


def row(repo, number, updated, state="open", is_pr=False, closed=None):
    return {"repository": {"nameWithOwner": repo}, "number": number, "url": f"https://github.com/{repo}/{number}",
            "updatedAt": updated, "title": f"t{number}", "state": state, "isPullRequest": is_pr, "closedAt": closed}


def comment(login, at, typ="User"):
    return {"user": {"login": login, "type": typ}, "created_at": at, "html_url": f"https://c/{login}/{at}"}


def review(login, at, state="APPROVED"):
    return {"user": {"login": login, "type": "User"}, "submitted_at": at, "state": state, "html_url": "https://r"}


class Sweep(unittest.TestCase):
    def fake(self):
        f = FakeGh()
        f.add(("gh", "api", "rate_limit"), quota(4000))
        f.add(("gh", "search", "prs"), [row("near/mpc", 5257, "2026-11-23T08:15:46Z", is_pr=True),
                                        row("near/docs", 3190, "2026-11-20T18:48:05Z", is_pr=True)])
        f.add(("gh", "search", "issues", "--author"), [
            row("foundry-rs/foundry", 18664, "2026-11-23T14:59:48Z", state="closed", closed="2026-11-23T14:59:49Z"),
            row("near/mpc", 5257, "2026-11-23T08:15:46Z", is_pr=True)])
        f.add(("gh", "search", "issues", "--commenter"), [row("near/mpc", 1852, "2026-11-24T16:00:00Z"),
                                                           row("someone/else", 1, "2026-11-23T00:00:00Z")])
        mpc = "repos/near/mpc"
        f.add(("gh", "api", f"{mpc}/issues/5257/comments?since={SINCE}&per_page=100"),
              [comment("SimonRastikian", "2026-11-23T08:15:46Z")])
        f.add(("gh", "api", f"{mpc}/pulls/5257/reviews?per_page=100"),
              [review("kevindeforth", "2026-11-22T14:36:32Z"), review("old", "2026-11-01T00:00:00Z")])
        f.add(("gh", "api", f"{mpc}/pulls/5257/comments?since={SINCE}&per_page=100"), [])
        f.add(("gh", "api", f"{mpc}/issues/1852/comments?since={SINCE}&per_page=100"),
              [comment("AmHelm", "2026-11-23T08:35:29Z"), comment("KhomDev", "2026-11-24T15:55:00Z")])
        f.add(("gh", "api", f"repos/foundry-rs/foundry/issues/18664/comments?since={SINCE}&per_page=100"), [])
        f.add(("gh", "api", f"repos/someone/else/issues/1/comments?since={SINCE}&per_page=100"),
              [comment("greptile-apps", "2026-11-23T00:00:00Z", typ="Bot")])
        f.add(("gh", "pr", "view", "5257"), {"statusCheckRollup": [
            {"name": "Extra CI checks", "conclusion": "FAILURE"}, {"name": "lint", "conclusion": "SUCCESS"},
            {"context": "Vercel", "state": "ERROR"}], "mergeStateStatus": "BLOCKED", "reviewDecision": "REVIEW_REQUIRED"})
        f.add(("gh", "pr", "view", "3190"), {"statusCheckRollup": [], "mergeStateStatus": "BLOCKED"})
        return f

    def test_classification(self):
        fake = self.fake()
        results = {f"{r['repo']}#{r['number']}": r for r in sweep.sweep(Gh(runner=fake), CONFIG, SINCE)}
        self.assertEqual(results["near/mpc#5257"]["verdict"], "OWED")
        self.assertEqual([h["login"] for h in results["near/mpc#5257"]["humans"]],
                         ["kevindeforth", "SimonRastikian"], "old review before SINCE is ignored")
        self.assertEqual(results["near/mpc#5257"]["failed_checks"], ["Extra CI checks", "Vercel"])
        self.assertEqual(results["near/mpc#1852"]["verdict"], "QUIET", "our reply came after AmHelm's")
        self.assertEqual(results["foundry-rs/foundry#18664"]["verdict"], "STATE")
        self.assertEqual(results["someone/else#1"]["verdict"], "BOT")
        self.assertIsNone(results["someone/else#1"]["program"])
        self.assertEqual(results["near/docs#3190"]["verdict"], "QUIET")
        # deduplication: 5257 came from two searches but was fetched once
        self.assertEqual(sum(1 for c in fake.calls if c[:3] == ["gh", "api", "repos/near/mpc/pulls/5257/reviews?per_page=100"]), 1)
        # items not updated since SINCE are not fetched
        self.assertFalse(any("3190/comments" in " ".join(c) for c in fake.calls))
        order = [r["verdict"] for r in sweep.sweep(Gh(runner=self.fake()), CONFIG, SINCE)]
        self.assertEqual(order, sorted(order, key=sweep.VERDICT_ORDER.get), "OWED first")

    def test_no_ci_skips_pr_view(self):
        fake = self.fake()
        sweep.sweep(Gh(runner=fake), CONFIG, SINCE, with_ci=False)
        self.assertFalse(any(c[:3] == ["gh", "pr", "view"] for c in fake.calls))

    def test_quota_guard_runs_first(self):
        fake = FakeGh().add(("gh", "api", "rate_limit"), quota(10))
        with self.assertRaises(Exception):
            sweep.sweep(Gh(runner=fake, min_quota=300), CONFIG, SINCE)
        self.assertEqual(len(fake.calls), 1)

    def test_classify_ignores_our_own_and_earlier_events(self):
        item = {"repo": "a/b", "number": 1, "state": "open", "closed_at": None}
        evts = [{"login": "mike", "at": "2026-11-23T00:00:00Z", "what": "comment"},
                {"login": "khomdev", "at": "2026-11-23T01:00:00Z", "what": "comment"}]
        self.assertEqual(sweep.classify(item, evts, "KhomDev", SINCE, CONFIG)["verdict"], "QUIET")
        evts.append({"login": "mike", "at": "2026-11-23T02:00:00Z", "what": "comment"})
        self.assertEqual(sweep.classify(item, evts, "KhomDev", SINCE, CONFIG)["verdict"], "OWED")
        closed = {**item, "state": "closed", "closed_at": "2026-11-01T00:00:00Z"}
        self.assertEqual(sweep.classify(closed, [], "KhomDev", SINCE, CONFIG)["verdict"], "QUIET",
                         "closed before the window is old news")

    def test_render(self):
        results = sweep.sweep(Gh(runner=self.fake()), CONFIG, SINCE)
        text = sweep.render(results, SINCE)
        self.assertIn("1 owed", text)
        self.assertIn("red: Extra CI checks, Vercel", text)
        self.assertIn("now closed", text)
        self.assertIn("outside the program", text)
        self.assertIn("bots: greptile-apps", text)


class RefCheck(unittest.TestCase):
    TREE = {"tree": [{"path": "docs/TASKS.md", "type": "blob"}, {"path": "VAULTS.md", "type": "blob"},
                     {"path": "a/x.rs", "type": "blob"}, {"path": "b/x.rs", "type": "blob"},
                     {"path": "docs", "type": "tree"}]}

    def fake(self):
        f = FakeGh().add(("gh", "api", "repos/o/r/git/trees/main?recursive=1"), self.TREE)
        f.add(("gh", "api", "-H", "Accept: application/vnd.github.raw", "repos/o/r/contents/docs/TASKS.md?ref=main"),
              "\n".join(f"line {n}" for n in range(1, 511)) + "\nwallet id\nGET /wallet/v1/webhook-keys\n")
        f.add(("gh", "api", "-H", "Accept: application/vnd.github.raw", "repos/o/r/contents/VAULTS.md?ref=main"),
              "one\ntwo\n")
        return f

    def test_find_refs(self):
        text = ("See docs/TASKS.md:511 and `VAULTS.md:341`, src/a.rs:10-12, src/a.rs:12-10, again docs/TASKS.md:511. "
                "Not https://host.io:8443/x, not v0.31.1:5, not 12:30, not a.b:c.")
        specs = [r.spec for r in refcheck.find_refs(text)]
        self.assertEqual(specs, ["docs/TASKS.md:511", "VAULTS.md:341", "src/a.rs:10-12"])

    def test_check_statuses(self):
        src = refcheck.Source(Gh(runner=self.fake()), "o/r", "main")
        refs = refcheck.find_refs("TASKS.md:512 VAULTS.md:341 x.rs:1 nope.md:1 docs/TASKS.md:511")
        refs[-1].expect = "webhook-keys"
        got = {r.spec: (r.status, r.resolved) for r in refcheck.check(src, refs)}
        self.assertEqual(got["TASKS.md:512"], ("OK", "docs/TASKS.md"), "unique suffix resolves")
        self.assertEqual(got["VAULTS.md:341"][0], "OUT_OF_RANGE")
        self.assertEqual(got["x.rs:1"][0], "MISSING", "ambiguous name is not guessed")
        self.assertEqual(got["nope.md:1"][0], "MISSING")
        self.assertEqual(got["docs/TASKS.md:511"][0], "MOVED")
        moved = [r for r in refs if r.spec == "docs/TASKS.md:511"][0]
        self.assertIn("512", moved.detail)

    def test_tree_and_file_fetched_once(self):
        fake = self.fake()
        src = refcheck.Source(Gh(runner=fake), "o/r", "main")
        refcheck.check(src, refcheck.find_refs("docs/TASKS.md:1 docs/TASKS.md:2 TASKS.md:3"))
        self.assertEqual(sum("git/trees" in " ".join(c) for c in fake.calls), 1)
        self.assertEqual(sum("contents/docs/TASKS.md" in " ".join(c) for c in fake.calls), 1)

    def test_render(self):
        src = refcheck.Source(Gh(runner=self.fake()), "o/r", "main")
        text = refcheck.render(refcheck.check(src, refcheck.find_refs("TASKS.md:512")), "o/r", "main")
        self.assertIn("OK           TASKS.md:512 -> docs/TASKS.md", text)
        self.assertIn("  512 | GET /wallet/v1/webhook-keys", text)


def header(**over):
    base = {"repo": "alloy", "verdict": "READY", "kind": "pr", "base": {"ref": "main", "sha": "4ca81a06"},
            "claims": [{"id": "C1", "kind": "behaviour", "text": "0x+2a parses", "evidence": ["red run"]}],
            "ci_runs": [{"id": 11, "role": "red", "expect": "failure"}, {"id": 12, "role": "green", "expect": "success"}],
            "prior_art": {"queries": ["a", "b", "c"], "related": []}, "precedent": ["#4488"],
            "line_refs": [{"path": "src/index.rs", "line": 2, "text": "from_str_radix"}], "not_run": []}
    base.update(over)
    return "<!-- oss-draft\n" + json.dumps(base) + "\n-->\n# Draft\n\n## Draft body\n\nSee src/index.rs:2.\n"


class VerifyDraft(unittest.TestCase):
    def fake(self, red="failure", green="success", line2="    usize::from_str_radix(val, 16)"):
        f = FakeGh()
        f.add(("gh", "run", "view", "11", "-R", CI), {"status": "completed", "conclusion": red})
        f.add(("gh", "run", "view", "12", "-R", CI), {"status": "completed", "conclusion": green})
        f.add(("gh", "api", "repos/alloy-rs/alloy/git/trees/4ca81a06?recursive=1"),
              {"tree": [{"path": "src/index.rs", "type": "blob"}]})
        f.add(("gh", "api", "-H"), f"line one\n{line2}\n")
        return f

    def check(self, text, fake=None, offline=False):
        return verify_draft.verify(text, CONFIG, None if offline else Gh(runner=fake or self.fake()))

    def test_good_draft_passes(self):
        result = self.check(header())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["warnings"], [], "body ref is declared in line_refs")

    def test_missing_or_broken_header(self):
        self.assertIn("no `<!-- oss-draft", self.check("# just text", offline=True)["errors"][0])
        self.assertIn("not valid JSON", self.check("<!-- oss-draft\n{bad}\n-->", offline=True)["errors"][0])
        self.assertIn("missing", self.check("<!-- oss-draft\n{\"repo\": \"alloy\"}\n-->", offline=True)["errors"][0])

    def test_static_rules(self):
        cases = {
            "unknown repo": header(repo="nope"),
            "verdict must": header(verdict="MAYBE"),
            "base.sha": header(base={"ref": "main", "sha": "main"}),
            "at least one claim": header(claims=[]),
            "no evidence": header(claims=[{"id": "C1", "kind": "behaviour", "text": "x", "evidence": []}]),
            "absence claim must list": header(claims=[{"id": "C1", "kind": "absence", "text": "no flag",
                                                       "evidence": ["--help"], "searched": ["check --help"]}]),
            "red run": header(ci_runs=[{"id": 12, "role": "green", "expect": "success"}]),
            "green run": header(ci_runs=[{"id": 11, "role": "red", "expect": "failure"}]),
            "integer run id": header(ci_runs=[{"id": "45", "role": "red", "expect": "failure"},
                                              {"id": 12, "role": "green", "expect": "success"}]),
            "three searches": header(prior_art={"queries": ["one"]}),
        }
        for needle, text in cases.items():
            with self.subTest(needle=needle):
                errors = self.check(text, offline=True)["errors"]
                self.assertTrue(any(needle in e for e in errors), errors)

    def test_absence_claim_with_scope_passes(self):
        text = header(claims=[{"id": "C1", "kind": "absence", "text": "no flag", "evidence": ["rg"],
                               "searched": ["every subcommand's args struct", "--help of all subcommands"]}])
        self.assertEqual(self.check(text, offline=True)["errors"], [])

    def test_nothing_draft_is_light(self):
        text = header(verdict="NOTHING", kind="none", claims=[], ci_runs=[], prior_art={"queries": []},
                      precedent=[], line_refs=[])
        self.assertEqual(self.check(text, offline=True)["errors"], [])

    def test_precedent_warning(self):
        self.assertTrue(any("precedent" in w for w in self.check(header(precedent=[]), offline=True)["warnings"]))

    def test_ci_conclusion_mismatch(self):
        errors = self.check(header(), fake=self.fake(red="success"))["errors"]
        self.assertTrue(any("concluded success, the draft says failure" in e for e in errors), errors)

    def test_ci_missing_and_in_progress(self):
        f = FakeGh().add(("gh", "run", "view", "11"), "", returncode=1)
        f.add(("gh", "run", "view", "12"), {"status": "in_progress", "conclusion": None})
        f.add(("gh", "api", "repos/alloy-rs/alloy/git/trees/4ca81a06?recursive=1"),
              {"tree": [{"path": "src/index.rs", "type": "blob"}]})
        f.add(("gh", "api", "-H"), "a\nfrom_str_radix\n")
        errors = self.check(header(), fake=f)["errors"]
        self.assertTrue(any("not found" in e for e in errors), errors)
        self.assertTrue(any("still in_progress" in e for e in errors), errors)

    def test_line_ref_moved(self):
        errors = self.check(header(), fake=self.fake(line2="something else"))["errors"]
        self.assertTrue(any("MOVED" in e for e in errors), errors)

    def test_undeclared_body_ref_warns(self):
        text = header(line_refs=[])
        result = self.check(text)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("not in line_refs" in w for w in result["warnings"]))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d) / "good.md", Path(d) / "bad.md"
            good.write_text(header(), encoding="utf-8")
            bad.write_text(header(claims=[]), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(verify_draft.main([str(good), "--offline"]), 0)
                self.assertEqual(verify_draft.main([str(bad), "--offline"]), 1)


class Outcomes(unittest.TestCase):
    def node(self, typ, repo, number, state, created="2026-11-19T00:00:00Z", closed=None, **kw):
        return {"__typename": typ, "number": number, "url": "u", "repository": {"nameWithOwner": repo},
                "state": state, "createdAt": created, "closedAt": closed, **kw}

    def test_outcome(self):
        self.assertEqual(outcomes.outcome(self.node("PullRequest", "a/b", 1, "MERGED", merged=True)), "merged")
        self.assertEqual(outcomes.outcome(self.node("PullRequest", "a/b", 1, "CLOSED", merged=False)), "closed")
        self.assertEqual(outcomes.outcome(self.node("PullRequest", "a/b", 1, "OPEN", merged=False)), "open")
        self.assertEqual(outcomes.outcome(self.node("Issue", "a/b", 1, "CLOSED", stateReason="COMPLETED")), "fixed")
        self.assertEqual(outcomes.outcome(self.node("Issue", "a/b", 1, "CLOSED", stateReason="NOT_PLANNED")),
                         "not_planned")
        self.assertEqual(outcomes.outcome(self.node("Issue", "a/b", 1, "CLOSED", stateReason="DUPLICATE")), "duplicate")
        self.assertEqual(outcomes.outcome(self.node("Issue", "a/b", 1, "CLOSED", stateReason=None)), "fixed")
        self.assertEqual(outcomes.outcome(self.node("Issue", "a/b", 1, "OPEN")), "open")

    def test_tally(self):
        nodes = [
            self.node("Issue", "foundry-rs/foundry", 18664, "CLOSED", "2026-11-22T17:00:00Z", "2026-11-23T14:59:49Z",
                      stateReason="COMPLETED"),
            self.node("Issue", "wevm/viem", 5638, "CLOSED", closed="2026-11-22T21:01:00Z", stateReason="NOT_PLANNED"),
            self.node("PullRequest", "near/mpc", 1, "MERGED", "2026-11-19T00:00:00Z", "2026-11-20T00:00:00Z", merged=True),
            self.node("PullRequest", "near/mpc", 2, "CLOSED", merged=False),
            self.node("PullRequest", "near/mpc", 3, "OPEN", merged=False),
            self.node("PullRequest", "someone/else", 9, "OPEN", merged=False),
        ]
        rows = {r["repo"]: r for r in outcomes.tally(nodes, CONFIG)}
        self.assertNotIn("someone/else", rows)
        self.assertEqual(rows["foundry"]["acceptance"], 1.0)
        self.assertEqual(rows["foundry"]["median_days_to_land"], 0.9)
        self.assertEqual(rows["viem"]["acceptance"], 0.0)
        self.assertEqual(rows["mpc"]["acceptance"], 0.5)
        self.assertEqual(rows["mpc"]["open"], 1)
        self.assertIn("someone/else", {r["repo"] for r in outcomes.tally(nodes, CONFIG, include_all=True)})
        text = outcomes.render(outcomes.tally(nodes, CONFIG), "2026-11-01")
        self.assertIn("100%", text)

    def test_fetch_paginates(self):
        pages = [
            {"data": {"search": {"pageInfo": {"hasNextPage": True, "endCursor": "C1"},
                                 "nodes": [self.node("Issue", "a/b", 1, "OPEN"), None]}}},
            {"data": {"search": {"pageInfo": {"hasNextPage": False, "endCursor": None},
                                 "nodes": [self.node("Issue", "a/b", 2, "OPEN")]}}},
        ]
        calls = []

        def runner(args):
            calls.append(list(args))
            return subprocess.CompletedProcess(args, 0, json.dumps(pages[len(calls) - 1]), "")

        nodes = outcomes.fetch(Gh(runner=runner), "KhomDev", "2026-11-01")
        self.assertEqual([n["number"] for n in nodes], [1, 2], "null nodes dropped")
        self.assertNotIn("after=C1", " ".join(calls[0]))
        self.assertIn("after=C1", " ".join(calls[1]))
        self.assertIn("q=author:KhomDev created:>=2026-11-01", calls[0])


class BriefPlaceholders(unittest.TestCase):
    def test_task_placeholders_are_filled(self):
        prompt = brief.build("alloy", "Write to <OSS_ROOT>/<OSS_DIR>/drafts/x.md", CONFIG, discover=True)
        self.assertIn(f"Write to {CONFIG['oss_root']}/{CONFIG['repos']['alloy']['oss_dir']}/drafts/x.md", prompt)
        self.assertNotIn("<OSS_ROOT>", prompt)

    def test_unknown_placeholder_refused(self):
        with self.assertRaisesRegex(ValueError, "NOT_A_KEY"):
            brief.build("alloy", "x <NOT_A_KEY>", CONFIG)

    def test_lowercase_slots_are_allowed(self):
        brief.build("alloy", "Output: drafts/<YYYY-MM-DD>-<slug>.md", CONFIG)

    def test_every_repo_builds(self):
        for key in CONFIG["repos"]:
            for discover in (False, True):
                with self.subTest(repo=key, discover=discover):
                    self.assertIn("TASK", brief.build(key, "t", CONFIG, discover=discover))


if __name__ == "__main__":
    unittest.main()
