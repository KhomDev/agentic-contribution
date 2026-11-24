#!/usr/bin/env python3
"""Launch discipline for agent rounds: memory, spacing, concurrency, and a real route check.

    python scripts/launch.py check                 # exit 0 = launch now, 3 = wait (says why)
    python scripts/launch.py record --repo foundry --desc "discovery r2" --prompt PATH
    python scripts/launch.py finish 3 --verdict NOTHING [--draft PATH]
    python scripts/launch.py running
    python scripts/launch.py smoke-prompt          # prints a prompt + the file it must write
    python scripts/launch.py smoke-check --file F --token T

Limits come from `launch` in config/repos.json (min_free_mb, spacing_s,
max_agents). Launches are recorded in the ledger, so the spacing and the
running count survive a context compaction.

The smoke test exists because an agent that returns no text proves nothing: on
22 Nov launches died with HTTP 402, and on 24 Nov a test agent ran but returned
an empty report. The smoke agent must write a random token to a file; only the
file proves the route works.
"""

from __future__ import annotations

import argparse
import json
import platform
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger  # noqa: E402
from _common import die, ledger_path, load_config  # noqa: E402

WAIT = 3


def free_mb() -> int | None:
    """Free physical memory in MB, or None when this OS is not supported."""
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
                capture_output=True, text=True, timeout=60)
            return int(out.stdout.strip()) // 1024
        if system == "Linux":
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def parse_time(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def running(data: dict) -> list[dict]:
    return [l for l in data["launches"] if not l.get("finished")]


def decide(data: dict, limits: dict, now: datetime, mem: int | None) -> tuple[bool, list[str]]:
    """(launch now?, reasons). Unknown memory is a reason to wait, not to guess."""
    reasons = []
    if mem is None:
        reasons.append("free memory unknown on this OS: check it by hand")
    elif mem < limits["min_free_mb"]:
        reasons.append(f"free memory {mem} MB is under the {limits['min_free_mb']} MB floor")
    live = running(data)
    if len(live) >= limits["max_agents"]:
        reasons.append(f"{len(live)} agents running (cap {limits['max_agents']})")
    if data["launches"]:
        last = max(parse_time(l["at"]) for l in data["launches"])
        gap = (now - last).total_seconds()
        if gap < limits["spacing_s"]:
            reasons.append(f"last launch {int(gap)} s ago; wait {int(limits['spacing_s'] - gap)} s more")
    return (not reasons), reasons


def record(data: dict, repo: str, desc: str, prompt: str, mem: int | None, now: datetime) -> dict:
    entry = {"id": max([l["id"] for l in data["launches"]] + [0]) + 1, "repo": repo, "desc": desc,
             "prompt": prompt, "at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
             "free_mb": mem, "finished": None, "verdict": None, "draft": None}
    data["launches"].append(entry)
    return entry


def finish(data: dict, launch_id: int, verdict: str, draft: str, now: datetime) -> dict:
    for entry in data["launches"]:
        if entry["id"] == launch_id:
            entry["finished"] = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
            entry["verdict"] = verdict
            entry["draft"] = draft or None
            return entry
    raise KeyError(f"no launch {launch_id}")


def smoke_prompt(directory: Path | None = None) -> dict:
    token = secrets.token_hex(8)
    target = (directory or Path(tempfile.gettempdir())) / f"oss-smoke-{token}.txt"
    prompt = (f"Write exactly the text {token} (no newline, nothing else) to the file {target.as_posix()} "
              "using your file-writing tool. Then reply DONE.")
    return {"token": token, "file": target.as_posix(), "prompt": prompt}


def smoke_check(file: Path, token: str) -> tuple[bool, str]:
    if not file.exists():
        return False, "the file was never written: the agent route is NOT working"
    content = file.read_text(encoding="utf-8").strip()
    if content != token:
        return False, f"the file holds {content[:40]!r}, not the token"
    return True, "the agent wrote the token: the route works"


def main(argv: list[str] | None = None, mem_reader: Callable[[], int | None] = free_mb,
         clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, help="override the ledger path (tests)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("record")
    p.add_argument("--repo", required=True)
    p.add_argument("--desc", required=True)
    p.add_argument("--prompt", default="")
    p = sub.add_parser("finish")
    p.add_argument("id", type=int)
    p.add_argument("--verdict", required=True, choices=("READY", "HOLD", "NOTHING", "FAILED"))
    p.add_argument("--draft", default="")
    sub.add_parser("running")
    p = sub.add_parser("smoke-prompt")
    p.add_argument("--dir", type=Path)
    p = sub.add_parser("smoke-check")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--token", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "smoke-prompt":
        print(json.dumps(smoke_prompt(args.dir), indent=2))
        return 0
    if args.cmd == "smoke-check":
        ok, msg = smoke_check(args.file, args.token)
        print(msg)
        return 0 if ok else 1

    config = load_config()
    path = args.ledger or ledger_path(config)
    data = ledger.load(path)
    now = clock()
    if args.cmd == "check":
        ok, reasons = decide(data, config["launch"], now, mem_reader())
        print("LAUNCH OK" if ok else "WAIT: " + "; ".join(reasons))
        return 0 if ok else WAIT
    if args.cmd == "record":
        if args.repo not in config["repos"]:
            die(f"unknown repo {args.repo!r}")
        entry = record(data, args.repo, args.desc, args.prompt, mem_reader(), now)
        ledger.save(path, data)
        print(f"recorded launch {entry['id']}: {entry['repo']} ({entry['free_mb']} MB free)")
        return 0
    if args.cmd == "finish":
        try:
            entry = finish(data, args.id, args.verdict, args.draft, now)
        except KeyError as exc:
            die(str(exc).strip("'\""))
        ledger.save(path, data)
        print(f"launch {entry['id']} finished: {entry['verdict']}")
        return 0
    live = running(data)
    for entry in live:
        print(f"{entry['id']:>3}  {entry['repo']:15} since {entry['at']}  {entry['desc']}")
    if not live:
        print("no agents running")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
