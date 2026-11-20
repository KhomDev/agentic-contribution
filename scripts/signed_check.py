#!/usr/bin/env python3
"""Check that commits are signed, verified by GitHub, and authored as KhomDev.

Local `git log --format=%G?` shows `N` on this host only because no
allowedSignersFile is configured, so GitHub's verdict is the one that counts.

    python scripts/signed_check.py --repo x402 --pr 4342
    python scripts/signed_check.py --repo x402 --sha 4375e869 [--sha ...]

With --sha, the commit is looked up in the fork first, then upstream.
Exit code: 0 all verified, 1 any problem.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Gh, GhError, load_config  # noqa: E402

NOREPLY = "KhomDev@users.noreply.github.com"


def pr_commits(gh: Gh, upstream: str, pr: int) -> list[str]:
    data = gh.json("pr", "view", str(pr), "-R", upstream, "--json", "commits")
    return [c["oid"] for c in data["commits"]]


def commit_info(gh: Gh, repos: list[str], sha: str) -> dict:
    last: Exception | None = None
    for repo in repos:
        try:
            data = gh.json("api", f"repos/{repo}/commits/{sha}")
        except GhError as exc:
            last = exc
            continue
        commit = data["commit"]
        return {
            "sha": data["sha"],
            "repo": repo,
            "verified": bool(commit["verification"]["verified"]),
            "reason": commit["verification"]["reason"],
            "email": commit["author"]["email"],
            "subject": commit["message"].splitlines()[0],
        }
    raise GhError(f"commit {sha} not found in {', '.join(repos)}: {last}")


def problems(info: dict) -> list[str]:
    out = []
    if not info["verified"]:
        out.append(f"not verified ({info['reason']})")
    if info["email"].lower() != NOREPLY.lower():
        out.append(f"author email is {info['email']}, expected {NOREPLY}")
    return out


def main(argv: list[str] | None = None, gh: Gh | None = None) -> int:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, choices=sorted(config["repos"]))
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", type=int)
    group.add_argument("--sha", action="append")
    args = ap.parse_args(argv)

    repo = config["repos"][args.repo]
    gh = gh or Gh(min_quota=config["min_rest_quota"])
    gh.guard()
    if args.pr:
        shas, lookup = pr_commits(gh, repo["upstream"], args.pr), [repo["upstream"]]
    else:
        shas, lookup = args.sha, [r for r in (repo["fork"], repo["upstream"]) if r]

    bad = 0
    for sha in shas:
        info = commit_info(gh, lookup, sha)
        issues = problems(info)
        bad += bool(issues)
        status = "OK " if not issues else "BAD"
        print(f"{status} {info['sha'][:10]} {info['subject'][:60]}" + (f"  <- {'; '.join(issues)}" if issues else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
