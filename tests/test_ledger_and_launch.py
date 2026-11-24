"""ledger.py (the actionable state) and launch.py (launch discipline), fully offline."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from _helpers import SKILL_ROOT  # noqa: F401  (sets the import path)

import launch
import ledger
from _common import EXAMPLE_LOCAL_PATH, is_bot, ledger_path, load_config

CONFIG = load_config(local=EXAMPLE_LOCAL_PATH)
NOW = datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc)


def run(main, argv, **kw):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv, **kw)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class TempLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"

    def tearDown(self):
        self.tmp.cleanup()


class Common(unittest.TestCase):
    def test_is_bot(self):
        self.assertTrue(is_bot("greptile-apps", CONFIG))
        self.assertTrue(is_bot("GREPTILE-APPS", CONFIG), "case-insensitive")
        self.assertTrue(is_bot("renovate[bot]", CONFIG))
        self.assertTrue(is_bot("someone", CONFIG, user_type="Bot"))
        self.assertTrue(is_bot(None, CONFIG), "a deleted account is never owed a reply")
        self.assertFalse(is_bot("mikedotexe", CONFIG))
        self.assertFalse(is_bot("claudette", CONFIG), "no substring matching")

    def test_ledger_path(self):
        self.assertEqual(ledger_path(CONFIG), Path(CONFIG["oss_root"]) / "state.json")
        self.assertEqual(ledger_path({**CONFIG, "ledger_file": "C:/x/l.json"}), Path("C:/x/l.json"))

    def test_launch_limits_configured(self):
        self.assertEqual(set(CONFIG["launch"]), {"min_free_mb", "spacing_s", "max_agents"})
        self.assertGreaterEqual(CONFIG["launch"]["min_free_mb"], 1024)


class LedgerModel(unittest.TestCase):
    def test_add_requires_next_action_for_open_items(self):
        data = ledger.empty()
        with self.assertRaises(ValueError):
            ledger.add(data, "x#1", "pr", "waiting", "   ")
        ledger.add(data, "x#2", "pr", "done", "")  # a done item needs none

    def test_add_rejects_duplicates_bad_kind_status_date(self):
        data = ledger.empty()
        ledger.add(data, "x#1", "pr", "waiting", "wait")
        for kwargs in ({"item_id": "x#1"}, {"item_id": "y", "kind": "nope"}, {"item_id": "y", "status": "nope"},
                       {"item_id": "y", "due": "23 Nov"}):
            args = {"item_id": "y", "kind": "pr", "status": "waiting", "next_action": "n", **kwargs}
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ledger.add(data, args.pop("item_id"), **args)

    def test_update_and_notes(self):
        data = ledger.empty()
        ledger.add(data, "x#1", "pr", "waiting", "ping", due="2026-11-23", stamp="2026-11-22T10:00:00Z")
        item = ledger.update(data, "x#1", note="pinged", due="2026-11-27", stamp="2026-11-24T10:00:00Z")
        self.assertEqual(item["due"], "2026-11-27")
        self.assertEqual(item["notes"], ["2026-11-24: pinged"])
        self.assertEqual(item["updated"], "2026-11-24T10:00:00Z")
        ledger.update(data, "x#1", due="none")
        self.assertIsNone(item["due"])
        ledger.update(data, "x#1", due="keep")  # the default leaves it alone
        self.assertIsNone(item["due"])
        with self.assertRaises(KeyError):
            ledger.update(data, "missing")
        with self.assertRaises(ValueError):
            ledger.update(data, "x#1", next_action="")

    def test_due_items_skip_done_and_undated(self):
        data = ledger.empty()
        ledger.add(data, "late", "pr", "waiting", "a", due="2026-11-23")
        ledger.add(data, "today", "issue", "open", "b", due="2026-11-24")
        ledger.add(data, "later", "issue", "open", "c", due="2026-11-30")
        ledger.add(data, "undated", "issue", "held", "d")
        ledger.add(data, "finished", "pr", "done", "", due="2026-11-01")
        overdue, today = ledger.due_items(data, date(2026, 11, 24))
        self.assertEqual([i["id"] for i in overdue], ["late"])
        self.assertEqual([i["id"] for i in today], ["today"])

    def test_render_and_splice(self):
        data = ledger.empty()
        ledger.add(data, "a|b", "pr", "waiting", "line1\nline2", url="https://x/1", due="2026-11-20")
        ledger.add(data, "gone", "pr", "done", "")
        table = ledger.render(data, date(2026, 11, 24))
        self.assertIn("[a\\|b](https://x/1)", table, "pipes are escaped")
        self.assertIn("line1 line2", table)
        self.assertIn("**2026-11-20 DUE**", table)
        self.assertNotIn("gone", table)
        self.assertIn("gone", ledger.render(data, date(2026, 11, 24), include_done=True))
        self.assertIn("nothing open", ledger.render(ledger.empty(), date(2026, 11, 24)))

        doc = "# Board\n\nintro\n\n## Log\n"
        once = ledger.splice(doc, "T1")
        self.assertEqual(once.count(ledger.START), 1)
        self.assertTrue(once.index("## Ledger") < once.index("## Log"))
        twice = ledger.splice(once, "T2")
        self.assertEqual(twice.count(ledger.START), 1, "re-render replaces, never duplicates")
        self.assertIn("T2", twice)
        self.assertNotIn("T1", twice)
        self.assertIn("## Log", twice)
        self.assertIn(r"a\1", ledger.splice(once, r"a\1"), "backslashes in the table survive")


class LedgerFile(TempLedger):
    def test_save_is_atomic_and_round_trips(self):
        data = ledger.empty()
        ledger.add(data, "x#1", "pr", "waiting", "ünïcode ✓")
        ledger.save(self.path, data)
        self.assertEqual(ledger.load(self.path), data)
        self.assertEqual(list(Path(self.tmp.name).glob(".state-*")), [], "no temp files left behind")
        self.assertNotIn(b"\r\n", self.path.read_bytes())

    def test_load_missing_and_old_files(self):
        self.assertEqual(ledger.load(self.path), ledger.empty())
        self.path.write_text(json.dumps({"version": 1, "items": []}), encoding="utf-8")
        self.assertEqual(ledger.load(self.path)["launches"], [], "missing keys are filled in")

    def test_cli_round_trip(self):
        base = ["--ledger", str(self.path), "--today", "2026-11-24"]
        code, out, _ = run(ledger.main, base + ["add", "x402#4326", "--kind", "pr", "--next", "ping",
                                                "--due", "2026-11-23", "--url", "https://g/1"])
        self.assertEqual(code, 0, out)
        code, out, _ = run(ledger.main, base + ["due"])
        self.assertEqual(code, 1)
        self.assertIn("OVERDUE", out)
        code, out, _ = run(ledger.main, base + ["update", "x402#4326", "--due", "2026-11-27", "--note", "pinged"])
        self.assertEqual(code, 0)
        code, out, _ = run(ledger.main, base + ["due"])
        self.assertEqual(code, 0)
        self.assertIn("nothing due", out)
        code, out, _ = run(ledger.main, base + ["list", "--json"])
        notes = json.loads(out)[0]["notes"]
        self.assertEqual(len(notes), 1)
        self.assertTrue(notes[0].endswith(": pinged"), notes)
        self.assertEqual(json.loads(out)[0]["due"], "2026-11-27")
        code, out, _ = run(ledger.main, base + ["done", "x402#4326"])
        self.assertEqual(code, 0)
        code, out, _ = run(ledger.main, base + ["list"])
        self.assertIn("nothing open", out)
        code, _, err = run(ledger.main, base + ["done", "missing"])
        self.assertEqual(code, 2)
        self.assertIn("missing", err)
        code, _, err = run(ledger.main, base + ["add", "y", "--kind", "pr"])
        self.assertEqual(code, 2, "an open item without --next is refused")


class Launch(TempLedger):
    LIMITS = {"min_free_mb": 1024, "spacing_s": 150, "max_agents": 2}

    def test_decide(self):
        data = ledger.empty()
        self.assertEqual(launch.decide(data, self.LIMITS, NOW, 2000), (True, []))
        ok, why = launch.decide(data, self.LIMITS, NOW, 1007)
        self.assertFalse(ok)
        self.assertIn("1007 MB", why[0])
        ok, why = launch.decide(data, self.LIMITS, NOW, None)
        self.assertFalse(ok, "unknown memory never means go")
        launch.record(data, "foundry", "r2", "", 2000, NOW - timedelta(seconds=60))
        ok, why = launch.decide(data, self.LIMITS, NOW, 2000)
        self.assertFalse(ok)
        self.assertIn("wait 90 s", why[0])
        launch.record(data, "anchor", "r2", "", 2000, NOW - timedelta(seconds=40))
        ok, why = launch.decide(data, self.LIMITS, NOW + timedelta(seconds=600), 2000)
        self.assertFalse(ok)
        self.assertIn("2 agents running", why[0])
        launch.finish(data, 1, "NOTHING", "", NOW)
        self.assertEqual(launch.decide(data, self.LIMITS, NOW + timedelta(seconds=600), 2000), (True, []))

    def test_record_ids_and_finish(self):
        data = ledger.empty()
        a = launch.record(data, "foundry", "x", "p", 1500, NOW)
        b = launch.record(data, "anchor", "y", "p", 1400, NOW)
        self.assertEqual((a["id"], b["id"]), (1, 2))
        self.assertEqual(a["at"], "2026-11-24T18:00:00Z")
        launch.finish(data, 2, "READY", "d.md", NOW)
        self.assertEqual([l["id"] for l in launch.running(data)], [1])
        with self.assertRaises(KeyError):
            launch.finish(data, 9, "READY", "", NOW)

    def test_cli(self):
        base = ["--ledger", str(self.path)]
        kw = {"mem_reader": lambda: 3000, "clock": lambda: NOW}
        self.assertEqual(run(launch.main, base + ["check"], **kw)[0], 0)
        code, out, _ = run(launch.main, base + ["record", "--repo", "foundry", "--desc", "r2"], **kw)
        self.assertEqual(code, 0, out)
        code, out, _ = run(launch.main, base + ["check"], **kw)
        self.assertEqual(code, launch.WAIT)
        self.assertIn("WAIT", out)
        later = {"mem_reader": lambda: 3000, "clock": lambda: NOW + timedelta(seconds=151)}
        self.assertEqual(run(launch.main, base + ["check"], **later)[0], 0)
        self.assertIn("foundry", run(launch.main, base + ["running"], **kw)[1])
        self.assertEqual(run(launch.main, base + ["finish", "1", "--verdict", "NOTHING"], **kw)[0], 0)
        self.assertIn("no agents running", run(launch.main, base + ["running"], **kw)[1])
        self.assertEqual(run(launch.main, base + ["record", "--repo", "nope", "--desc", "x"], **kw)[0], 2)

    def test_smoke(self):
        info = launch.smoke_prompt(Path(self.tmp.name))
        self.assertIn(info["token"], info["prompt"])
        self.assertIn(info["file"], info["prompt"])
        target = Path(info["file"])
        self.assertFalse(launch.smoke_check(target, info["token"])[0], "no file = route not proven")
        target.write_text("something else", encoding="utf-8")
        self.assertFalse(launch.smoke_check(target, info["token"])[0])
        target.write_text(info["token"] + "\n", encoding="utf-8")
        self.assertTrue(launch.smoke_check(target, info["token"])[0])
        self.assertNotEqual(launch.smoke_prompt()["token"], launch.smoke_prompt()["token"])
        code, out, _ = run(launch.main, ["smoke-check", "--file", str(target), "--token", info["token"]])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
