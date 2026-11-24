#!/usr/bin/env python3
"""Check every `path:line` reference in public text against the upstream source.

Line numbers drift: in two days one issue body's refs moved from 66-72 to
66-73, 511 to 512 and 341 to 381. This script resolves each reference on the
upstream ref, prints the cited lines, and fails when a file is missing, a line
is out of range, or (when the expected text is known) the text has moved.

    python scripts/refcheck.py --repo outlayer --file body.md            # default branch
    python scripts/refcheck.py --repo alloy --ref 4ca81a06 --file body.md
    python scripts/refcheck.py --repo mpc --ref main --ref-spec "crates/node/src/network.rs:420-425"

A bare file name (`VAULTS.md:341`) resolves when exactly one file in the tree
has that name or path suffix. Exit 1 on any problem.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Gh, GhError, die, load_config  # noqa: E402

# path with an extension, then :line or :start-end. Not preceded by "/" + "/" (URLs) or a word char.
REF = re.compile(r"(?<![\w/:.])(?P<path>(?:[\w.-]+/)*[\w-][\w.-]*\.[A-Za-z][\w]*):(?P<start>\d+)(?:-(?P<end>\d+))?\b")


@dataclass
class Ref:
    path: str
    start: int
    end: int
    expect: str = ""
    status: str = "OK"
    resolved: str = ""
    lines: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def spec(self) -> str:
        return f"{self.path}:{self.start}" + (f"-{self.end}" if self.end != self.start else "")


def find_refs(text: str) -> list[Ref]:
    seen, out = set(), []
    for m in REF.finditer(text):
        path = m.group("path")
        if re.fullmatch(r"[\d.]+", path) or path.lower().startswith(("http", "www.")):
            continue
        start = int(m.group("start"))
        end = int(m.group("end") or start)
        if end < start:
            start, end = end, start
        key = (path, start, end)
        if key not in seen:
            seen.add(key)
            out.append(Ref(path, start, end))
    return out


class Source:
    """Reads files of one upstream at one ref, with one tree call and a file cache."""

    def __init__(self, gh: Gh, upstream: str, ref: str):
        self.gh, self.upstream, self.ref = gh, upstream, ref
        self._tree: list[str] | None = None
        self._files: dict[str, list[str] | None] = {}

    def tree(self) -> list[str]:
        if self._tree is None:
            data = self.gh.json("api", f"repos/{self.upstream}/git/trees/{self.ref}?recursive=1") or {}
            self._tree = [e["path"] for e in data.get("tree", []) if e.get("type") == "blob"]
        return self._tree

    def resolve(self, path: str) -> tuple[str | None, str]:
        tree = self.tree()
        if path in tree:
            return path, ""
        matches = [p for p in tree if p.endswith("/" + path)]
        if len(matches) == 1:
            return matches[0], ""
        if matches:
            return None, "ambiguous: " + ", ".join(sorted(matches)[:5])
        return None, "no such file at this ref"

    def lines(self, path: str) -> list[str] | None:
        if path not in self._files:
            try:
                text = self.gh.run("api", "-H", "Accept: application/vnd.github.raw",
                                   f"repos/{self.upstream}/contents/{path}?ref={self.ref}")
            except GhError:
                text = None
            self._files[path] = None if text is None else text.splitlines()
        return self._files[path]


def check(source: Source, refs: list[Ref]) -> list[Ref]:
    for ref in refs:
        resolved, why = source.resolve(ref.path)
        if resolved is None:
            ref.status, ref.detail = "MISSING", why
            continue
        ref.resolved = resolved
        lines = source.lines(resolved)
        if lines is None:
            ref.status, ref.detail = "MISSING", "could not read the file"
            continue
        if ref.end > len(lines) or ref.start < 1:
            ref.status, ref.detail = "OUT_OF_RANGE", f"file has {len(lines)} lines"
            continue
        ref.lines = lines[ref.start - 1: ref.end]
        if ref.expect and not any(ref.expect in line for line in ref.lines):
            hits = [n + 1 for n, line in enumerate(lines) if ref.expect in line]
            ref.status = "MOVED"
            ref.detail = (f"expected text is at line(s) {', '.join(map(str, hits[:5]))}" if hits
                          else "expected text not found anywhere in the file")
    return refs


def render(refs: list[Ref], upstream: str, ref_name: str) -> str:
    out = [f"{len(refs)} reference(s) checked against {upstream}@{ref_name}"]
    for r in refs:
        where = f" -> {r.resolved}" if r.resolved and r.resolved != r.path else ""
        out.append(f"{r.status:12} {r.spec}{where}{'  (' + r.detail + ')' if r.detail else ''}")
        for n, line in enumerate(r.lines, start=r.start):
            out.append(f"    {n:>5} | {line}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, choices=sorted(config["repos"]))
    ap.add_argument("--ref", help="branch, tag or sha (default: the repo's default branch)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=Path, help="text to scan for path:line references")
    src.add_argument("--ref-spec", action="append", help="one reference, e.g. src/a.rs:10-12 (repeatable)")
    ap.add_argument("--expect", default="", help="with one --ref-spec: text the cited lines must contain")
    args = ap.parse_args(argv)
    repo = config["repos"][args.repo]
    ref_name = args.ref or repo["default_branch"]
    if args.file:
        refs = find_refs(args.file.read_text(encoding="utf-8"))
    else:
        refs = find_refs(" ".join(args.ref_spec))
        if args.expect:
            if len(refs) != 1:
                die("--expect needs exactly one --ref-spec")
            refs[0].expect = args.expect
    if not refs:
        print("no path:line references found")
        return 0
    checked = check(Source(Gh(min_quota=config["min_rest_quota"]), repo["upstream"], ref_name), refs)
    print(render(checked, repo["upstream"], ref_name))
    return 1 if any(r.status != "OK" for r in checked) else 0


if __name__ == "__main__":
    raise SystemExit(main())
