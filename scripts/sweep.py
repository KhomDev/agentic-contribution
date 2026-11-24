#!/usr/bin/env python3
"""The review sweep in one command: what moved, and whether a reply is owed.

Covers every open PR by the author, plus every issue or PR the author opened
or commented on that was updated since the last sweep. For each item updated
since then it reads comments and reviews and classifies it:

    OWED   a human other than the author acted after the author's last word
    STATE  closed or merged since the last sweep (record the outcome)
    BOT    only bots acted (read them; usually nothing to answer)
    QUIET  nothing new

For open PRs it also lists failing checks, because a red check is the second
thing a reviewer sees.

    python scripts/sweep.py                    # since the ledger's last sweep (or 72 h)
    python scripts/sweep.py --since 2026-11-22T00:00:00Z
    python scripts/sweep.py --mark             # also record this sweep in the ledger
    python scripts/sweep.py --json --no-ci

Read-only on GitHub. Calls `Gh.guard()` first; cost is about 3 REST calls per
moved item plus one per open PR for checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger  # noqa: E402
from _common import Gh, is_bot, ledger_path, load_config, repo_by_upstream  # noqa: E402

SEARCH_FIELDS = "repository,number,url,updatedAt,title,state,isPullRequest,closedAt"
PR_FIELDS = "repository,number,url,updatedAt,title,state"
VERDICT_ORDER = {"OWED": 0, "STATE": 1, "BOT": 2, "QUIET": 3}
FAILING = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def candidates(gh: Gh, author: str, since: str) -> list[dict]:
    """Open PRs (always) plus anything authored or commented on since `since`, deduplicated."""
    day = since[:10]
    found: dict[tuple[str, int], dict] = {}

    def keep(rows, is_pr=None):
        for row in rows or []:
            repo = row["repository"]["nameWithOwner"]
            item = found.setdefault((repo.lower(), row["number"]), {
                "repo": repo, "number": row["number"], "url": row["url"], "title": row["title"],
                "state": row.get("state", "open").lower(), "updated": row["updatedAt"],
                "is_pr": row.get("isPullRequest", is_pr), "closed_at": row.get("closedAt"),
                "open_pr": False,
            })
            if is_pr:
                item["is_pr"] = True
                item["open_pr"] = item["state"] == "open"

    keep(gh.json("search", "prs", "--author", author, "--state", "open", "--limit", "200",
                 "--json", PR_FIELDS), is_pr=True)
    for role in ("--author", "--commenter"):
        keep(gh.json("search", "issues", role, author, "--include-prs", "--updated", f">={day}",
                     "--limit", "200", "--json", SEARCH_FIELDS))
    return sorted(found.values(), key=lambda i: (i["repo"].lower(), i["number"]))


def events(gh: Gh, item: dict, since: str) -> list[dict]:
    """Comments, reviews and review comments on `item` since `since`, oldest first."""
    base = f"repos/{item['repo']}"
    out = []
    for c in gh.json("api", f"{base}/issues/{item['number']}/comments?since={since}&per_page=100") or []:
        out.append({"login": (c.get("user") or {}).get("login"), "type": (c.get("user") or {}).get("type"),
                    "at": c["created_at"], "what": "comment", "url": c.get("html_url", "")})
    if item["is_pr"]:
        for r in gh.json("api", f"{base}/pulls/{item['number']}/reviews?per_page=100") or []:
            if (r.get("submitted_at") or "") >= since:
                out.append({"login": (r.get("user") or {}).get("login"), "type": (r.get("user") or {}).get("type"),
                            "at": r["submitted_at"], "what": f"review {r.get('state', '').lower()}",
                            "url": r.get("html_url", "")})
        for c in gh.json("api", f"{base}/pulls/{item['number']}/comments?since={since}&per_page=100") or []:
            out.append({"login": (c.get("user") or {}).get("login"), "type": (c.get("user") or {}).get("type"),
                        "at": c["created_at"], "what": "review comment", "url": c.get("html_url", "")})
    return sorted(out, key=lambda e: e["at"])


def classify(item: dict, evts: list[dict], author: str, since: str, config: dict) -> dict:
    ours = [e["at"] for e in evts if (e["login"] or "").lower() == author.lower()]
    cutoff = max([since] + ours)
    after = [e for e in evts if e["at"] > cutoff and (e["login"] or "").lower() != author.lower()]
    humans = [e for e in after if not is_bot(e["login"], config, e.get("type"))]
    bots = [e for e in after if is_bot(e["login"], config, e.get("type"))]
    closed_since = item["state"] in ("closed", "merged") and (item.get("closed_at") or "") >= since
    if humans:
        verdict = "OWED"
    elif closed_since:
        verdict = "STATE"
    elif bots:
        verdict = "BOT"
    else:
        verdict = "QUIET"
    return {**item, "verdict": verdict, "humans": humans, "bots": bots}


def failing_checks(gh: Gh, item: dict) -> dict:
    data = gh.json("pr", "view", str(item["number"]), "-R", item["repo"], "--json",
                   "statusCheckRollup,mergeStateStatus,reviewDecision") or {}
    failed = []
    for check in data.get("statusCheckRollup") or []:
        state = (check.get("conclusion") or check.get("state") or "").upper()
        if state in FAILING:
            failed.append(check.get("name") or check.get("context") or "?")
    return {"failed_checks": sorted(set(failed)), "merge_state": data.get("mergeStateStatus"),
            "review_decision": data.get("reviewDecision")}


def sweep(gh: Gh, config: dict, since: str, with_ci: bool = True) -> list[dict]:
    author = config["author"]
    gh.guard()
    results = []
    for item in candidates(gh, author, since):
        moved = item["updated"] >= since
        row = classify(item, events(gh, item, since) if moved else [], author, since, config)
        row["program"] = repo_by_upstream(config, item["repo"])
        if with_ci and item["open_pr"]:
            row.update(failing_checks(gh, item))
        results.append(row)
    results.sort(key=lambda r: (VERDICT_ORDER[r["verdict"]], r["repo"].lower(), r["number"]))
    return results


def render(results: list[dict], since: str) -> str:
    lines = [f"sweep since {since}: {len(results)} items, "
             f"{sum(r['verdict'] == 'OWED' for r in results)} owed"]
    for r in results:
        ref = f"{r['repo']}#{r['number']}"
        extra = []
        if r["humans"]:
            last = r["humans"][-1]
            extra.append(f"{last['login']} {last['what']} {last['at']}")
        if r["verdict"] == "STATE":
            extra.append(f"now {r['state']}")
        elif r["state"] != "open":
            extra.append(f"({r['state']})")
        if r["bots"] and r["verdict"] != "OWED":
            extra.append("bots: " + ", ".join(sorted({b['login'] for b in r['bots']})))
        if r.get("failed_checks"):
            extra.append("red: " + ", ".join(r["failed_checks"]))
        if r.get("program") is None:
            extra.append("outside the program")
        lines.append(f"{r['verdict']:5}  {ref:40} {' | '.join(extra)}".rstrip())
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="ISO time; default: the ledger's last_sweep, else 72 hours ago")
    ap.add_argument("--mark", action="store_true", help="record this sweep's start time in the ledger")
    ap.add_argument("--no-ci", action="store_true", help="skip the per-PR check lookup")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ledger", type=Path, help="override the ledger path (tests)")
    args = ap.parse_args(argv)
    config = load_config()
    path = args.ledger or ledger_path(config)
    state = ledger.load(path)
    started = iso(datetime.now(timezone.utc))
    since = args.since or state.get("last_sweep") or iso(datetime.now(timezone.utc) - timedelta(hours=72))
    results = sweep(Gh(min_quota=config["min_rest_quota"]), config, since, with_ci=not args.no_ci)
    print(json.dumps(results, indent=2) if args.json else render(results, since))
    if args.mark:
        state["last_sweep"] = started
        ledger.save(path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
