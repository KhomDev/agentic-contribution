#!/usr/bin/env python3
"""What happened to everything we filed: per repo, how often it lands, and how fast.

Use it to choose where the next agent round goes. A repo that fixes our issues
in a day (foundry #18664) earns another round; one that closes them
`not_planned` (viem #5638) calls for more care first.

    python scripts/outcomes.py                    # since 2026-01-01, program repos only
    python scripts/outcomes.py --since 2026-11-01 --all --json

Outcomes: PR merged / closed / open; issue fixed (closed as completed) /
not_planned / duplicate / open. Acceptance = (merged + fixed) / decided items.
One GraphQL search per 50 items (small pages: large ones return HTTP 502).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Gh, load_config, repo_by_upstream  # noqa: E402

QUERY = """query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      __typename
      ... on Issue { number url repository { nameWithOwner } state stateReason createdAt closedAt }
      ... on PullRequest { number url repository { nameWithOwner } state merged createdAt closedAt }
    }
  }
}"""
ACCEPTED = ("merged", "fixed")
REJECTED = ("closed", "not_planned", "duplicate")
MAX_PAGES = 20


def fetch(gh: Gh, author: str, since: str) -> list[dict]:
    nodes, after = [], None
    for _ in range(MAX_PAGES):
        args = ["api", "graphql", "-f", f"query={QUERY}", "-F", f"q=author:{author} created:>={since}"]
        if after:
            args += ["-f", f"after={after}"]
        page = gh.json(*args)["data"]["search"]
        nodes += [n for n in page["nodes"] if n]
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return nodes


def outcome(node: dict) -> str:
    state = node["state"].upper()
    if node["__typename"] == "PullRequest":
        if node.get("merged") or state == "MERGED":
            return "merged"
        return "open" if state == "OPEN" else "closed"
    if state == "OPEN":
        return "open"
    reason = (node.get("stateReason") or "COMPLETED").upper()
    return {"NOT_PLANNED": "not_planned", "DUPLICATE": "duplicate"}.get(reason, "fixed")


def days(a: str, b: str) -> float:
    fmt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    return (fmt(b) - fmt(a)).total_seconds() / 86400


def tally(nodes: list[dict], config: dict, include_all: bool = False) -> list[dict]:
    rows: dict[str, dict] = {}
    for node in nodes:
        upstream = node["repository"]["nameWithOwner"]
        key = repo_by_upstream(config, upstream)
        if key is None and not include_all:
            continue
        name = key or upstream
        row = rows.setdefault(name, {"repo": name, "items": 0, "merged": 0, "fixed": 0, "closed": 0,
                                     "not_planned": 0, "duplicate": 0, "open": 0, "_days": []})
        result = outcome(node)
        row["items"] += 1
        row[result] += 1
        if result in ACCEPTED and node.get("closedAt"):
            row["_days"].append(days(node["createdAt"], node["closedAt"]))
    out = []
    for row in rows.values():
        accepted = sum(row[k] for k in ACCEPTED)
        decided = accepted + sum(row[k] for k in REJECTED)
        row["acceptance"] = round(accepted / decided, 2) if decided else None
        row["median_days_to_land"] = round(statistics.median(row["_days"]), 1) if row["_days"] else None
        del row["_days"]
        out.append(row)
    out.sort(key=lambda r: (-(r["acceptance"] if r["acceptance"] is not None else -1), -r["items"], r["repo"]))
    return out


def render(rows: list[dict], since: str) -> str:
    lines = [f"outcomes since {since}",
             f"{'repo':16} {'items':>5} {'merged':>6} {'fixed':>5} {'rejected':>8} {'open':>4} {'accept':>6} {'days':>5}"]
    for r in rows:
        rejected = r["closed"] + r["not_planned"] + r["duplicate"]
        acc = "-" if r["acceptance"] is None else f"{r['acceptance']:.0%}"
        med = "-" if r["median_days_to_land"] is None else f"{r['median_days_to_land']}"
        lines.append(f"{r['repo']:16} {r['items']:>5} {r['merged']:>6} {r['fixed']:>5} {rejected:>8} "
                     f"{r['open']:>4} {acc:>6} {med:>5}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default="2026-01-01", help="YYYY-MM-DD, by creation date")
    ap.add_argument("--all", action="store_true", help="include repos outside the program")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    config = load_config()
    gh = Gh(min_quota=config["min_rest_quota"])
    rows = tally(fetch(gh, config["author"], args.since), config, args.all)
    print(json.dumps(rows, indent=2) if args.json else render(rows, args.since))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
