#!/usr/bin/env python3
"""Count KhomDev's open PRs per repo against each repo's budget.

One `gh search prs` call covers every repo, so a census costs one search
request, not thirteen.

    python scripts/census.py            # table
    python scripts/census.py --json     # machine-readable
    python scripts/census.py --from-file fixture.json   # offline (tests)

A repo with free slots is a candidate for a new agent round. Exit code is 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Gh, load_config  # noqa: E402

FIELDS = "repository,number,title,isDraft,url,updatedAt"


def fetch_open_prs(gh: Gh, author: str) -> list[dict]:
    return gh.json("search", "prs", "--author", author, "--state", "open", "--limit", "200", "--json", FIELDS) or []


def tally(prs: list[dict], config: dict) -> dict:
    rows = {
        key: {"repo": key, "upstream": r["upstream"], "budget": r["budget"], "open": 0, "prs": []}
        for key, r in config["repos"].items()
    }
    by_upstream = {r["upstream"].lower(): key for key, r in config["repos"].items()}
    untracked: list[dict] = []
    for pr in prs:
        key = by_upstream.get(pr["repository"]["nameWithOwner"].lower())
        if key is None:
            untracked.append(pr)
            continue
        row = rows[key]
        row["open"] += 1
        row["prs"].append({"number": pr["number"], "title": pr["title"], "draft": pr.get("isDraft", False)})
    for row in rows.values():
        row["free"] = max(row["budget"] - row["open"], 0)
        row["over"] = max(row["open"] - row["budget"], 0)
    return {"repos": list(rows.values()), "untracked": untracked}


def render(result: dict) -> str:
    lines = [f"{'repo':13} {'open':>4} {'budget':>6} {'free':>4}  PRs"]
    for row in sorted(result["repos"], key=lambda r: (-r["free"], r["repo"])):
        prs = ", ".join(f"#{p['number']}{' (draft)' if p['draft'] else ''}" for p in row["prs"]) or "-"
        flag = "  OVER BUDGET" if row["over"] else ""
        lines.append(f"{row['repo']:13} {row['open']:>4} {row['budget']:>6} {row['free']:>4}  {prs}{flag}")
    if result["untracked"]:
        names = sorted({p["repository"]["nameWithOwner"] for p in result["untracked"]})
        lines.append(f"open PRs in repos outside the program: {', '.join(names)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--from-file", type=Path, help="read `gh search prs --json` output from a file")
    args = ap.parse_args(argv)
    config = load_config()
    if args.from_file:
        prs = json.loads(args.from_file.read_text(encoding="utf-8"))
    else:
        prs = fetch_open_prs(Gh(min_quota=config["min_rest_quota"]), config["author"])
    result = tally(prs, config)
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
