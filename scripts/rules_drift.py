#!/usr/bin/env python3
"""Detect changes to each repo's own contributor and agent rules.

Every repo card in repos/ was written from the upstream files listed under
`sources` in config/repos.json. This script re-fetches them from the default
branch and compares their SHA-256 with config/rules-snapshot.json.

    python scripts/rules_drift.py            # report drift, exit 1 if any
    python scripts/rules_drift.py --update   # after re-reading and fixing the cards
    python scripts/rules_drift.py --repo x402

A changed hash means: re-read that file, update repos/<card>.md and
config/repos.json if a rule moved, then run with --update.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SKILL_ROOT, Gh, GhError, load_config  # noqa: E402

SNAPSHOT = SKILL_ROOT / "config" / "rules-snapshot.json"


def sources_for(repo: dict) -> list[tuple[str, str]]:
    pairs = [(repo["upstream"], path) for path in repo["sources"]]
    pairs += [(extra["repo"], extra["path"]) for extra in repo.get("extra_sources", [])]
    return pairs


def fetch(gh: Gh, owner_repo: str, path: str) -> str | None:
    try:
        return gh.run("api", f"repos/{owner_repo}/contents/{path}", "-H", "Accept: application/vnd.github.raw")
    except GhError:
        return None


def digest(text: str | None) -> str | None:
    return None if text is None else hashlib.sha256(text.encode("utf-8")).hexdigest()


def compare(current: dict, snapshot: dict) -> list[str]:
    changes = []
    for key, value in sorted(current.items()):
        old = snapshot.get(key)
        if old is None:
            changes.append(f"NEW      {key}")
        elif value is None:
            changes.append(f"MISSING  {key} (file removed or moved upstream)")
        elif old != value:
            changes.append(f"CHANGED  {key}")
    for key in sorted(set(snapshot) - set(current)):
        changes.append(f"DROPPED  {key} (no longer listed in config)")
    return changes


def main(argv: list[str] | None = None, gh: Gh | None = None) -> int:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--repo", choices=sorted(config["repos"]))
    args = ap.parse_args(argv)
    gh = gh or Gh(min_quota=config["min_rest_quota"])
    gh.guard()

    stored = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {"files": {}}
    keys = [args.repo] if args.repo else list(config["repos"])
    current = {}
    for key in keys:
        for owner_repo, path in sources_for(config["repos"][key]):
            current[f"{owner_repo}:{path}"] = digest(fetch(gh, owner_repo, path))

    scoped = {k: v for k, v in stored["files"].items() if k in current or not args.repo}
    changes = compare(current, scoped)
    for line in changes:
        print(line)
    print(f"{len(changes)} change(s) across {len(current)} file(s)")

    if args.update:
        stored["files"].update({k: v for k, v in current.items() if v is not None})
        stored["checked"] = dt.date.today().isoformat()
        SNAPSHOT.write_text(json.dumps(stored, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"snapshot written: {SNAPSHOT}")
        return 0
    return 1 if changes else 0


if __name__ == "__main__":
    raise SystemExit(main())
