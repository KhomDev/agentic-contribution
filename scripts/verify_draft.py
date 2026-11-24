#!/usr/bin/env python3
"""Check an agent's draft against its own evidence before the orchestrator reads it.

Every draft starts with a machine-readable header in an HTML comment:

    <!-- oss-draft
    {"repo": "alloy", "verdict": "READY", "kind": "pr",
     "base": {"ref": "main", "sha": "4ca81a06"},
     "claims": [{"id": "C1", "kind": "behaviour", "text": "...", "evidence": ["cmd -> output"]},
                {"id": "C2", "kind": "absence", "text": "no other flag", "evidence": ["grep ..."],
                 "searched": ["cargo-near/src/commands/*/mod.rs", "--help of every subcommand"]}],
     "ci_runs": [{"id": 45454613093, "role": "red", "expect": "failure"},
                 {"id": 45454640913, "role": "green", "expect": "success"}],
     "prior_art": {"queries": ["...", "...", "..."], "related": ["#4488 merged"]},
     "precedent": ["#4488: same guard for BlockNumberOrTag"],
     "line_refs": [{"path": "crates/x/src/index.rs", "line": 69, "text": "from_str_radix"}],
     "not_run": ["full feature matrix"]}
    -->

What it checks (errors fail, warnings are for the gate packet):
- the header exists, parses, and has every field; the repo is in the program;
- READY/HOLD drafts carry claims with evidence; an absence claim lists where
  it searched (at least two places: one `--help` is not a search);
- a READY PR has a red run that must fail and a green run that must pass;
- unless --offline: each CI run exists on the CI repo, has completed, and its
  conclusion matches; each line_ref still says the expected text at `base.sha`;
- refs in the draft body that are not listed in line_refs (warning).

    python scripts/verify_draft.py <draft.md> [--offline] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refcheck  # noqa: E402
from _common import Gh, GhError, load_config  # noqa: E402

HEADER = re.compile(r"<!--\s*oss-draft\s*(\{.*?\})\s*-->", re.DOTALL)
VERDICTS = ("READY", "HOLD", "NOTHING")
DRAFT_KINDS = ("pr", "issue", "comment", "none")
CLAIM_KINDS = ("behaviour", "absence", "line", "cause", "novelty")
ROLES = ("red", "green", "baseline", "other")
REQUIRED = ("repo", "verdict", "kind", "base", "claims", "ci_runs", "prior_art", "precedent", "not_run")
SHA = re.compile(r"^[0-9a-f]{7,40}$")


def parse(text: str) -> dict:
    m = HEADER.search(text)
    if not m:
        raise ValueError("no `<!-- oss-draft {...} -->` header: the draft predates the schema or skipped it")
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"the oss-draft header is not valid JSON: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError("the oss-draft header must be a JSON object")
    return data


def body_section(text: str) -> str:
    m = re.search(r"^## Draft body\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def static_checks(header: dict, config: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    missing = [k for k in REQUIRED if k not in header]
    if missing:
        errors.append(f"header is missing: {', '.join(missing)}")
        return errors, warnings
    if header["repo"] not in config["repos"]:
        errors.append(f"unknown repo {header['repo']!r}")
    verdict, kind = header["verdict"], header["kind"]
    if verdict not in VERDICTS:
        errors.append(f"verdict must be one of {VERDICTS}")
    if kind not in DRAFT_KINDS:
        errors.append(f"kind must be one of {DRAFT_KINDS}")
    base = header["base"] if isinstance(header["base"], dict) else {}
    if not SHA.match(str(base.get("sha", ""))):
        errors.append("base.sha must be the 7-40 hex commit that was examined (not a branch name)")
    claims = header["claims"] if isinstance(header["claims"], list) else []
    if verdict in ("READY", "HOLD") and not claims:
        errors.append(f"a {verdict} draft needs at least one claim")
    for n, claim in enumerate(claims, 1):
        cid = claim.get("id", f"#{n}")
        if claim.get("kind") not in CLAIM_KINDS:
            errors.append(f"claim {cid}: kind must be one of {CLAIM_KINDS}")
        if not str(claim.get("text", "")).strip():
            errors.append(f"claim {cid}: empty text")
        if not claim.get("evidence"):
            errors.append(f"claim {cid}: no evidence (the command and the output line that shows it)")
        if claim.get("kind") == "absence" and len(claim.get("searched") or []) < 2:
            errors.append(f"claim {cid}: an absence claim must list at least two places searched "
                          "(every subcommand, every crate, three names); one --help is not a search")
    runs = header["ci_runs"] if isinstance(header["ci_runs"], list) else []
    for run in runs:
        if not isinstance(run.get("id"), int):
            errors.append(f"ci run {run.get('id')!r}: id must be an integer run id")
        if run.get("role") not in ROLES:
            errors.append(f"ci run {run.get('id')}: role must be one of {ROLES}")
        if run.get("expect") not in ("success", "failure"):
            errors.append(f"ci run {run.get('id')}: expect must be success or failure")
    if verdict == "READY" and kind == "pr":
        if not any(r.get("role") == "red" and r.get("expect") == "failure" for r in runs):
            errors.append("a READY PR needs a red run that is expected to fail")
        if not any(r.get("role") == "green" and r.get("expect") == "success" for r in runs):
            errors.append("a READY PR needs a green run that is expected to pass")
    prior = header["prior_art"] if isinstance(header["prior_art"], dict) else {}
    queries = prior.get("queries") or []
    if verdict != "NOTHING" and len(queries) < 3:
        errors.append("prior_art.queries needs at least three searches (symptom, names, exact error text)")
    if verdict == "READY" and not header["precedent"]:
        warnings.append("no precedent: say whether a maintainer already fixed a sibling of this bug "
                        "(git log -S on the same pattern); a precedent makes the case")
    if not isinstance(header["not_run"], list):
        errors.append("not_run must be a list (empty only if everything relevant ran)")
    return errors, warnings


def network_checks(header: dict, body: str, config: dict, gh: Gh) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for run in header.get("ci_runs") or []:
        if not isinstance(run.get("id"), int):
            continue
        try:
            data = gh.json("run", "view", str(run["id"]), "-R", config["ci_repo"], "--json",
                           "status,conclusion,displayTitle") or {}
        except GhError:
            errors.append(f"ci run {run['id']}: not found on {config['ci_repo']}")
            continue
        if data.get("status") != "completed":
            errors.append(f"ci run {run['id']} ({run.get('role')}): still {data.get('status')}")
        elif data.get("conclusion") != run.get("expect"):
            errors.append(f"ci run {run['id']} ({run.get('role')}): concluded {data.get('conclusion')}, "
                          f"the draft says {run.get('expect')}")
    repo = config["repos"].get(header.get("repo"), {})
    sha = (header.get("base") or {}).get("sha", "")
    declared = []
    for lr in header.get("line_refs") or []:
        start = int(lr.get("line", 0))
        declared.append(refcheck.Ref(lr.get("path", ""), start, int(lr.get("end", start)), expect=lr.get("text", "")))
    found = refcheck.find_refs(body)
    listed = {(r.path, r.start, r.end) for r in declared}
    extra = [r for r in found if (r.path, r.start, r.end) not in listed]
    if (declared or extra) and repo:
        source = refcheck.Source(gh, repo["upstream"], sha or repo["default_branch"])
        for r in refcheck.check(source, declared):
            if r.status != "OK":
                errors.append(f"line_ref {r.spec}: {r.status} ({r.detail})")
        for r in refcheck.check(source, extra):
            if r.status != "OK":
                errors.append(f"body ref {r.spec}: {r.status} ({r.detail})")
            else:
                warnings.append(f"body ref {r.spec} is not in line_refs, so its text is unchecked")
    return errors, warnings


def verify(text: str, config: dict, gh: Gh | None) -> dict:
    try:
        header = parse(text)
    except ValueError as exc:
        return {"errors": [str(exc)], "warnings": [], "header": None}
    errors, warnings = static_checks(header, config)
    if gh is not None and not errors:
        e2, w2 = network_checks(header, body_section(text), config, gh)
        errors += e2
        warnings += w2
    return {"errors": errors, "warnings": warnings, "header": header}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", type=Path)
    ap.add_argument("--offline", action="store_true", help="skip CI and line checks")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    config = load_config()
    gh = None if args.offline else Gh(min_quota=config["min_rest_quota"])
    result = verify(args.draft.read_text(encoding="utf-8"), config, gh)
    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "header"}, indent=2))
    else:
        h = result["header"] or {}
        print(f"{args.draft.name}: {h.get('verdict', '?')} {h.get('kind', '?')} in {h.get('repo', '?')}")
        for e in result["errors"]:
            print(f"ERROR   {e}")
        for w in result["warnings"]:
            print(f"warning {w}")
        print(f"{len(result['errors'])} error(s), {len(result['warnings'])} warning(s)")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
