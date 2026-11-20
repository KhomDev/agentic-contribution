"""census, signed_check, ci and rules_drift, driven through a fake `gh`."""

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _helpers import FakeGh, quota

import census
import ci
import rules_drift
import signed_check
from _common import EXAMPLE_LOCAL_PATH, Gh, QuotaTooLow, load_config

CONFIG = load_config(local=EXAMPLE_LOCAL_PATH)


def pr(repo, number, draft=False):
    return {"repository": {"nameWithOwner": repo}, "number": number, "title": f"t{number}", "isDraft": draft,
            "url": f"https://github.com/{repo}/pull/{number}", "updatedAt": "2026-11-20T00:00:00Z"}


class Census(unittest.TestCase):
    def test_tally_budget_and_untracked(self):
        prs = [pr("near/mpc", 1), pr("near/mpc", 2), pr("near/mpc", 3), pr("near/mpc", 4),
               pr("x402-foundation/x402", 10, draft=True), pr("someone/else", 99)]
        result = census.tally(prs, CONFIG)
        rows = {r["repo"]: r for r in result["repos"]}
        self.assertEqual(rows["mpc"]["open"], 4)
        self.assertEqual(rows["mpc"]["free"], 0)
        self.assertEqual(rows["mpc"]["over"], 1)
        self.assertEqual(rows["x402"]["free"], 2)
        self.assertTrue(rows["x402"]["prs"][0]["draft"])
        self.assertEqual(rows["agave"]["open"], 0)
        self.assertEqual(len(result["untracked"]), 1)
        text = census.render(result)
        self.assertIn("OVER BUDGET", text)
        self.assertIn("someone/else", text)
        self.assertIn("#10 (draft)", text)

    def test_single_search_call(self):
        fake = FakeGh().add(("gh", "search", "prs"), [pr("near/docs", 5)])
        prs = census.fetch_open_prs(Gh(runner=fake), "KhomDev")
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("--author", fake.calls[0])
        self.assertEqual(prs[0]["number"], 5)

    def test_from_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "prs.json"
            p.write_text(json.dumps([pr("near/nearcore", 7)]), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(census.main(["--from-file", str(p), "--json"]), 0)
            rows = {r["repo"]: r for r in json.loads(out.getvalue())["repos"]}
            self.assertEqual(rows["nearcore"]["open"], 1)


class QuotaGuard(unittest.TestCase):
    def test_guard_raises_below_floor(self):
        gh = Gh(runner=FakeGh().add(("gh", "api", "rate_limit"), quota(120)), min_quota=300)
        with self.assertRaises(QuotaTooLow):
            gh.guard()

    def test_guard_passes(self):
        gh = Gh(runner=FakeGh().add(("gh", "api", "rate_limit"), quota(4000)), min_quota=300)
        self.assertEqual(gh.guard(), 4000)


def commit_payload(sha, verified=True, email="KhomDev@users.noreply.github.com", reason="valid"):
    return {"sha": sha, "commit": {"verification": {"verified": verified, "reason": reason},
                                   "author": {"email": email}, "message": "fix: thing\n\nbody"}}


class SignedCheck(unittest.TestCase):
    def test_problems(self):
        self.assertEqual(signed_check.problems({"verified": True, "reason": "valid", "email": "khomdev@users.noreply.github.com"}), [])
        issues = signed_check.problems({"verified": False, "reason": "unsigned", "email": "x@y.z"})
        self.assertEqual(len(issues), 2)

    def test_lookup_falls_back_to_upstream(self):
        fake = (FakeGh()
                .add(("gh", "api", "repos/KhomDev/x402/commits/abc"), "", 1)
                .add(("gh", "api", "repos/x402-foundation/x402/commits/abc"), commit_payload("abc123")))
        info = signed_check.commit_info(Gh(runner=fake), ["KhomDev/x402", "x402-foundation/x402"], "abc")
        self.assertEqual(info["repo"], "x402-foundation/x402")
        self.assertTrue(info["verified"])

    def test_pr_commits(self):
        fake = FakeGh().add(("gh", "pr", "view"), {"commits": [{"oid": "a1"}, {"oid": "b2"}]})
        self.assertEqual(signed_check.pr_commits(Gh(runner=fake), "near/mpc", 5260), ["a1", "b2"])


class Ci(unittest.TestCase):
    def ns(self, **kw):
        base = dict(target="KhomDev/x402", ref="verify/1-x", toolchain="node", command="pnpm test",
                    label="green", apt="", node_version="")
        base.update(kw)
        return argparse.Namespace(**base)

    def test_dispatch_args(self):
        args = ci.dispatch_args("KhomDev/oss-ci", self.ns(apt="clang cmake", node_version="20"))
        self.assertEqual(args[:5], ["workflow", "run", "fork-branch-verify.yml", "-R", "KhomDev/oss-ci"])
        self.assertIn("command=pnpm test", args)
        self.assertIn("apt=clang cmake", args)
        self.assertIn("node_version=20", args)
        self.assertNotIn("apt=", ci.dispatch_args("KhomDev/oss-ci", self.ns()))

    def test_no_watch_subcommand(self):
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                ci.build_parser().parse_args(["watch", "1"])

    def test_dispatch_refuses_on_low_quota(self):
        fake = FakeGh().add(("gh", "api", "rate_limit"), quota(10))
        with self.assertRaises(QuotaTooLow):
            ci.main(["dispatch", "--target", "KhomDev/x402", "--ref", "r", "--toolchain", "node",
                     "--command", "c", "--label", "l"], gh=Gh(runner=fake, min_quota=300))
        self.assertFalse(any(c[1:3] == ["workflow", "run"] for c in fake.calls))

    def test_dispatch_finds_run_by_title(self):
        runs = [{"databaseId": 2, "displayTitle": "KhomDev/x402@other: l", "createdAt": "", "status": "queued", "url": "u2"},
                {"databaseId": 1, "displayTitle": "KhomDev/x402@r: l", "createdAt": "", "status": "queued", "url": "u1"}]
        fake = (FakeGh().add(("gh", "api", "rate_limit"), quota(4000))
                .add(("gh", "workflow", "run"), "")
                .add(("gh", "run", "list"), runs))
        out = io.StringIO()
        with redirect_stdout(out):
            ci.main(["dispatch", "--target", "KhomDev/x402", "--ref", "r", "--toolchain", "node",
                     "--command", "c", "--label", "l"], gh=Gh(runner=fake, min_quota=300))
        self.assertIn("run 1 u1", out.getvalue())

    def test_grep_on_running_job_is_friendly(self):
        import subprocess

        gh = Gh(runner=lambda args: subprocess.CompletedProcess(
            args, 1, "", "run 7 is still in progress; logs will be available when it is complete"))
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(ci.main(["grep", "7", "x"], gh=gh), 3)
        self.assertIn("still in progress", out.getvalue())

    def test_grep_strips_ansi(self):
        log = "job\tstep\t\x1b[32mRESULT [PASS]\x1b[0m\nnoise\n"
        fake = FakeGh().add(("gh", "run", "view"), log)
        out = io.StringIO()
        with redirect_stdout(out):
            ci.main(["grep", "5", "RESULT"], gh=Gh(runner=fake))
        self.assertIn("RESULT [PASS]", out.getvalue())
        self.assertNotIn("\x1b", out.getvalue())
        self.assertIn("1 matching line(s)", out.getvalue())


class Drift(unittest.TestCase):
    def test_compare(self):
        current = {"a:x": "1", "a:y": "2", "a:z": None, "a:new": "4"}
        snapshot = {"a:x": "1", "a:y": "OLD", "a:z": "3", "a:gone": "5"}
        lines = rules_drift.compare(current, snapshot)
        self.assertEqual(sorted(l.split()[0] for l in lines), ["CHANGED", "DROPPED", "MISSING", "NEW"])

    def test_sources_include_extra(self):
        pairs = rules_drift.sources_for(CONFIG["repos"]["rust-sdk"])
        self.assertIn(("modelcontextprotocol/modelcontextprotocol", "AI_POLICY.md"), pairs)

    def test_main_reports_change_and_update_writes(self):
        fake = FakeGh().add(("gh", "api", "rate_limit"), quota(4000)).add(("gh", "api"), "new content")
        with tempfile.TemporaryDirectory() as d:
            snap = Path(d) / "snap.json"
            snap.write_text(json.dumps({"files": {"near/docs:CONTRIBUTING.md": "stale"}}), encoding="utf-8")
            with mock.patch.object(rules_drift, "SNAPSHOT", snap), redirect_stdout(io.StringIO()) as out:
                self.assertEqual(rules_drift.main(["--repo", "docs"], gh=Gh(runner=fake)), 1)
                self.assertIn("CHANGED  near/docs:CONTRIBUTING.md", out.getvalue())
                self.assertEqual(rules_drift.main(["--repo", "docs", "--update"], gh=Gh(runner=fake)), 0)
                self.assertEqual(rules_drift.main(["--repo", "docs"], gh=Gh(runner=fake)), 0)
            stored = json.loads(snap.read_text(encoding="utf-8"))
            self.assertEqual(stored["files"]["near/docs:CONTRIBUTING.md"], rules_drift.digest("new content"))


if __name__ == "__main__":
    unittest.main()
