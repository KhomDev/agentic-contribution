#!/usr/bin/env python3
"""Run builds and tests on the public CI repo (KhomDev/oss-ci), quota-safely.

    python scripts/ci.py dispatch --target KhomDev/x402 --ref verify/4326-expiry \
        --toolchain node --label red-baseline --command 'cd typescript && pnpm test'
    python scripts/ci.py mpc --ref verify/1852-x --crate mpc-node --test-filter foo
    python scripts/ci.py status 44652408954
    python scripts/ci.py grep 44652408954 'RESULT|test result'

There is deliberately no `watch`: `gh run watch` polls every few seconds and
several of them in parallel drained the shared 5000/hour REST quota on
19 Nov 2026. Check `status` at most once every 5 minutes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Gh, GhError, load_config  # noqa: E402

TOOLCHAINS = ("rust", "node", "rust+node", "none")
# GitHub run logs carry colour codes either as the ESC byte or as the literal text "^[".
ANSI = re.compile(r"(?:\x1b|\^\[)\[[0-9;]*m")


def dispatch_args(ci_repo: str, a: argparse.Namespace) -> list[str]:
    args = [
        "workflow", "run", "fork-branch-verify.yml", "-R", ci_repo,
        "-f", f"repo={a.target}", "-f", f"ref={a.ref}", "-f", f"toolchain={a.toolchain}",
        "-f", f"command={a.command}", "-f", f"label={a.label}",
    ]
    if a.apt:
        args += ["-f", f"apt={a.apt}"]
    if a.node_version:
        args += ["-f", f"node_version={a.node_version}"]
    return args


def mpc_args(ci_repo: str, a: argparse.Namespace) -> list[str]:
    args = ["workflow", "run", "mpc-branch-verify.yml", "-R", ci_repo, "-f", f"ref={a.ref}", "-f", f"crate={a.crate}"]
    if a.test_filter:
        args += ["-f", f"test_filter={a.test_filter}"]
    return args


CLOCK_SKEW = dt.timedelta(seconds=15)


def utc_now() -> str:
    """UTC timestamp (minus a small clock-skew margin) in GitHub's `createdAt` format."""
    return (dt.datetime.now(dt.timezone.utc) - CLOCK_SKEW).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_run(gh: Gh, ci_repo: str, workflow: str, title: str | None, since: str,
             tries: int = 5, delay: float = 4.0) -> dict | None:
    """Find the run of `workflow` created at or after `since` (a UTC ISO timestamp).

    `since` matters: labels are reused (e.g. "ws-red"), so matching on the title
    alone can return the previous run with the same title before the new one is
    listed. `title` narrows further when the workflow sets run-name.
    """
    for attempt in range(tries):
        runs = gh.json("run", "list", "-R", ci_repo, "--workflow", workflow, "--limit", "10",
                       "--json", "databaseId,displayTitle,createdAt,status,url") or []
        for run in runs:
            if run["createdAt"] >= since and (title is None or run["displayTitle"] == title):
                return run
        if attempt < tries - 1:
            time.sleep(delay)
    return None


def cmd_dispatch(gh: Gh, ci_repo: str, a: argparse.Namespace) -> int:
    gh.guard()
    since = utc_now()
    gh.run(*dispatch_args(ci_repo, a))
    run = find_run(gh, ci_repo, "fork-branch-verify.yml", f"{a.target}@{a.ref}: {a.label}", since)
    return _report(run, ci_repo)


def cmd_mpc(gh: Gh, ci_repo: str, a: argparse.Namespace) -> int:
    gh.guard()
    since = utc_now()
    gh.run(*mpc_args(ci_repo, a))
    return _report(find_run(gh, ci_repo, "mpc-branch-verify.yml", None, since), ci_repo)


def _report(run: dict | None, ci_repo: str) -> int:
    if run is None:
        print(f"dispatched, but the run did not appear yet; list it later with: gh run list -R {ci_repo} --limit 5")
        return 0
    print(f"run {run['databaseId']} {run['url']}")
    print("check it with `ci.py status <id>` no sooner than 5 minutes from now")
    return 0


def cmd_status(gh: Gh, ci_repo: str, a: argparse.Namespace) -> int:
    data = gh.json("run", "view", str(a.run_id), "-R", ci_repo, "--json", "status,conclusion,displayTitle,url")
    print(f"{data['status']} {data['conclusion'] or '-'}  {data['displayTitle']}  {data['url']}")
    return 0


def cmd_grep(gh: Gh, ci_repo: str, a: argparse.Namespace) -> int:
    log = gh.run("run", "view", str(a.run_id), "-R", ci_repo, "--log")
    pattern = re.compile(a.pattern)
    hits = [ln for ln in (ANSI.sub("", raw) for raw in log.splitlines()) if pattern.search(ln)]
    for ln in hits[: a.max]:
        print(ln)
    print(f"{len(hits)} matching line(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dispatch", help="run a command on any public repo/ref")
    d.add_argument("--target", required=True, help="owner/name to check out, e.g. KhomDev/x402 or foundry-rs/foundry")
    d.add_argument("--ref", required=True)
    d.add_argument("--toolchain", required=True, choices=TOOLCHAINS)
    d.add_argument("--command", required=True)
    d.add_argument("--label", required=True)
    d.add_argument("--apt", default="")
    d.add_argument("--node-version", default="")

    m = sub.add_parser("mpc", help="fmt + clippy + test one crate of KhomDev/mpc")
    m.add_argument("--ref", required=True)
    m.add_argument("--crate", required=True)
    m.add_argument("--test-filter", default="")

    s = sub.add_parser("status")
    s.add_argument("run_id", type=int)

    g = sub.add_parser("grep")
    g.add_argument("run_id", type=int)
    g.add_argument("pattern")
    g.add_argument("--max", type=int, default=40)
    return ap


def main(argv: list[str] | None = None, gh: Gh | None = None) -> int:
    config = load_config()
    a = build_parser().parse_args(argv)
    gh = gh or Gh(min_quota=config["min_rest_quota"])
    handler = {"dispatch": cmd_dispatch, "mpc": cmd_mpc, "status": cmd_status, "grep": cmd_grep}[a.cmd]
    try:
        return handler(gh, config["ci_repo"], a)
    except GhError as exc:
        if "still in progress" in str(exc):
            print(f"run {getattr(a, 'run_id', '?')} is still in progress; check again in 5 minutes")
            return 3
        raise


if __name__ == "__main__":
    raise SystemExit(main())
