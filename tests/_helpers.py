"""Test helpers: import path setup and a fake `gh` runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


class FakeGh:
    """Answers `gh` invocations from a list of (argument-prefix, stdout, returncode) rules.

    The first rule whose prefix matches the start of the argument list wins.
    Every call is recorded in `calls` so tests can assert what was (not) run.
    """

    def __init__(self, rules: list[tuple[tuple[str, ...], object, int]] | None = None):
        self.rules = rules or []
        self.calls: list[list[str]] = []

    def add(self, prefix: tuple[str, ...], stdout: object = "", returncode: int = 0) -> "FakeGh":
        self.rules.append((prefix, stdout, returncode))
        return self

    def __call__(self, args):
        args = list(args)
        self.calls.append(args)
        for prefix, stdout, rc in self.rules:
            if tuple(args[: len(prefix)]) == prefix:
                text = stdout if isinstance(stdout, str) else json.dumps(stdout)
                return subprocess.CompletedProcess(args, rc, text, "" if rc == 0 else "fake failure")
        raise AssertionError(f"unexpected gh call: {args}")


def quota(remaining: int) -> dict:
    return {"resources": {"core": {"remaining": remaining, "limit": 5000, "reset": 0}}}
