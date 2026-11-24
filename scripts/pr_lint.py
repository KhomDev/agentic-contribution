#!/usr/bin/env python3
"""Lint a PR title, PR body and commit messages against one repo's rules.

The rules come from config/repos.json, so a repo's conventions live in one place.
The orchestrator runs this on every gate packet before the operator sees it.

    python scripts/pr_lint.py --repo x402 --title "fix(near): ..." \
        --body-file body.md --commit-file msg1.txt --commit-file msg2.txt

Exit code: 0 clean or warnings only, 1 any error, 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_config  # noqa: E402

DISCLOSURE = re.compile(
    r"(?i)(\b(ai|claude|llm)\b[^\n]{0,120}\b(assist\w*|generat\w*|written|wrote|draft\w*|authored|prepared|used|using)\b"
    r"|\b(assist\w*|generat\w*|written|wrote|draft\w*|authored|prepared|used|using)\b[^\n]{0,120}\b(ai|claude|llm)\b)"
)
PROSE_NOISE = re.compile(r"(?im)^\s*([-*+]\s|#{1,6}\s|\d+\.\s)|\b(tested with|validated with)\b")
COMMIT_SUBJECT_MAX = 72  # git convention; every repo in the program uses it
ISSUE_REF = re.compile(r"(#\d+|github\.com/[\w.-]+/[\w.-]+/issues/\d+)")


@dataclass
class Finding:
    level: str  # "error" | "warn"
    where: str  # "title" | "body" | "commit[i]"
    message: str


def _scan_terms(text: str, where: str, public: dict, out: list[Finding]) -> None:
    for pattern in public["error_patterns"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            out.append(Finding("error", where, f"private or internal term in public text: {m.group(0)!r}"))
    for pattern in public["warn_patterns"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            out.append(Finding("warn", where, f"check wording: {m.group(0)!r} (fine only if it is about the code itself)"))


def lint_title(title: str, repo: dict) -> list[Finding]:
    out: list[Finding] = []
    rule = repo["title"]
    if not re.match(rule["regex"], title):
        out.append(Finding(rule["enforcement"], "title", f"does not match the repo's title format: {rule['regex']}"))
    if len(title) > rule["max_len"]:
        out.append(Finding("error", "title", f"{len(title)} chars, limit {rule['max_len']}"))
    elif "warn_len" in rule and len(title) > rule["warn_len"]:
        out.append(Finding("warn", "title", f"{len(title)} chars; repo prefers <= {rule['warn_len']}"))
    if title.rstrip().endswith("."):
        out.append(Finding("error", "title", "ends with a period"))
    return out


def lint_body(body: str, repo: dict, config: dict, comment: bool = False) -> list[Finding]:
    """Lint a PR body, or with `comment=True` a PR/issue comment or review reply.

    Comments skip the PR template sections, the prose check and the issue link,
    and need an AI disclosure only where the repo's policy covers comments
    (`comment_disclosure`, e.g. the MCP org's AI_POLICY.md).
    """
    out: list[Finding] = []
    footer = config["footer"]
    if not body.strip():
        return [Finding("error", "body", "empty body")]
    lines = body.strip().splitlines()
    if footer not in body:
        out.append(Finding("error", "body", f"missing attribution footer: {footer}"))
    elif lines[-1].strip() != footer:
        out.append(Finding("warn", "body", "attribution footer is not the last line"))
    content = body.replace(footer, "")
    _scan_terms(content, "body", config["public_text"], out)

    needs_disclosure = repo.get("comment_disclosure", False) if comment else repo["ai_disclosure"] == "required"
    if needs_disclosure and not DISCLOSURE.search(content):
        out.append(Finding("error", "body", "repo requires an AI-assistance disclosure sentence (the footer alone does not count)"))
    if comment:
        return out

    if repo["pr_body"] == "prose":
        noise = PROSE_NOISE.search(content)
        if noise:
            out.append(Finding("warn", "body", f"repo wants flowing prose, no headings, lists or 'tested with' boilerplate: {noise.group(0).strip()!r}"))

    for section in repo.get("body_sections", []):
        if not re.search(rf"(?im)^#+\s*{re.escape(section)}\s*$", content):
            out.append(Finding("error", "body", f"template section missing: {section}"))

    if repo["process"]["issue_first"] and not ISSUE_REF.search(content):
        out.append(Finding("warn", "body", "issue-first repo: link the issue the maintainers agreed on"))
    return out


def lint_commit(message: str, repo: dict, config: dict, where: str) -> list[Finding]:
    out: list[Finding] = []
    lines = message.rstrip("\n").splitlines()
    if not lines or not lines[0].strip():
        return [Finding("error", where, "empty commit message")]
    subject = lines[0]
    if not re.match(repo["title"]["regex"], subject):
        out.append(Finding(repo["commit_subject_enforcement"], where, "subject does not follow the repo's conventional format"))
    if len(subject) > COMMIT_SUBJECT_MAX:
        out.append(Finding("error", where, f"subject is {len(subject)} chars, limit {COMMIT_SUBJECT_MAX}"))
    if len(lines) > 1 and lines[1].strip():
        out.append(Finding("error", where, "second line must be blank"))
    limit = repo.get("commit_body_max_line")
    if limit:
        long_lines = [i + 1 for i, ln in enumerate(lines[2:], start=2) if len(ln) > limit]
        if long_lines:
            out.append(Finding("error", where, f"body lines over {limit} chars (commitlint): {long_lines}"))
    trailers = [ln for ln in lines if ln.lower().startswith("co-authored-by:") and "anthropic.com" in ln.lower()]
    if repo.get("commit_trailer", "required") == "none":
        # Some upstreams forbid AI co-author trailers outright (OZ Cairo, CONTRIBUTING.md).
        if trailers:
            out.append(Finding("error", where, "this repo forbids Claude co-author trailers; remove it"))
    else:
        good = [ln for ln in trailers if re.match(config["co_author_pattern"], ln.strip())]
        if not good:
            out.append(Finding("error", where, "missing 'Co-Authored-By: Claude <model> <noreply@anthropic.com>' trailer"))
        if len(trailers) > 1:
            out.append(Finding("error", where, f"{len(trailers)} Claude co-author trailers; keep exactly one (the orchestrator's)"))
    body_text = "\n".join(ln for ln in lines if ln not in trailers)
    _scan_terms(body_text, where, config["public_text"], out)
    return out


def lint(repo_key: str, title: str | None, body: str | None, commits: list[str], config: dict,
         comment: bool = False) -> list[Finding]:
    repo = config["repos"][repo_key]
    findings: list[Finding] = []
    if title is not None:
        if comment:
            # An issue title is plain prose: no PR title format, only a sanity limit.
            if len(title) > 120:
                findings.append(Finding("warn", "title", f"{len(title)} chars; keep issue titles under 120"))
        else:
            findings += lint_title(title, repo)
        _scan_terms(title, "title", config["public_text"], findings)
    if body is not None:
        findings += lint_body(body, repo, config, comment=comment)
    for i, msg in enumerate(commits):
        findings += lint_commit(msg, repo, config, f"commit[{i}]")
    return findings


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, choices=sorted(config["repos"]))
    ap.add_argument("--title")
    ap.add_argument("--body-file", type=Path)
    ap.add_argument("--commit-file", type=Path, action="append", default=[])
    ap.add_argument("--comment", action="store_true",
                    help="the body file is a comment or review reply, not a PR body")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.title is None and args.body_file is None and not args.commit_file:
        ap.error("give at least one of --title, --body-file, --commit-file")

    body = args.body_file.read_text(encoding="utf-8") if args.body_file else None
    commits = [p.read_text(encoding="utf-8") for p in args.commit_file]
    findings = lint(args.repo, args.title, body, commits, config, comment=args.comment)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.level.upper():5} {f.where:10} {f.message}")
        errors = sum(f.level == "error" for f in findings)
        print(f"{args.repo}: {errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
