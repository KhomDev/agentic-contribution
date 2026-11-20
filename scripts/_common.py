"""Shared helpers for the oss-contrib scripts.

Everything that talks to GitHub goes through `Gh`, so tests can swap in a fake
runner and no test ever touches the network.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config" / "repos.json"

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]

# Windows consoles default to cp1252, which mangles titles like "spec §10".
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


LOCAL_PATH = SKILL_ROOT / "local" / "config.json"
EXAMPLE_LOCAL_PATH = SKILL_ROOT / "config" / "local.example.json"


def merge(base, overlay):
    """Deep-merge `overlay` into `base`: objects merge, lists append, scalars replace."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        out = dict(base)
        for key, value in overlay.items():
            out[key] = merge(base[key], value) if key in base else value
        return out
    if isinstance(base, list) and isinstance(overlay, list):
        return base + [v for v in overlay if v not in base]
    return overlay


def load_config(path: Path | None = None, local: Path | None = None) -> dict:
    """Public config (config/repos.json) merged with the private overlay.

    The overlay defaults to local/config.json (gitignored) when it exists.
    Tests pass `local=EXAMPLE_LOCAL_PATH` so they never depend on private data.
    """
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        config = json.load(fh)
    overlay_path = local if local is not None else (LOCAL_PATH if LOCAL_PATH.exists() else None)
    if overlay_path is not None:
        with open(overlay_path, encoding="utf-8") as fh:
            overlay = json.load(fh)
        overlay.pop("_comment", None)
        config = merge(config, overlay)
    config.setdefault("private_terms", [])
    for repo in config["repos"].values():
        repo.setdefault("knowledge", [])
        repo.setdefault("private_rules", "")
    return config


def require(config: dict, *keys: str) -> None:
    missing = [k for k in keys if not config.get(k)]
    if missing:
        die(f"missing {', '.join(missing)}: copy config/local.example.json to local/config.json and fill it in")


def repo_by_upstream(config: dict, name_with_owner: str) -> str | None:
    """Return the config key for an upstream `owner/name`, case-insensitively."""
    wanted = name_with_owner.lower()
    for key, repo in config["repos"].items():
        if repo["upstream"].lower() == wanted:
            return key
    return None


def _default_runner(args: Sequence[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        list(args), capture_output=True, text=True, encoding="utf-8", timeout=120
    )


class GhError(RuntimeError):
    pass


class QuotaTooLow(RuntimeError):
    pass


class Gh:
    """Thin wrapper over the `gh` CLI.

    `min_quota` guards every call that the caller marks as `guarded`: the
    REST quota is shared by every session and agent on this account, and an
    exhausted quota blocks all review work for up to an hour.
    """

    def __init__(self, runner: Runner | None = None, min_quota: int = 300):
        self.runner = runner or _default_runner
        self.min_quota = min_quota

    def run(self, *args: str) -> str:
        proc = self.runner(["gh", *args])
        if proc.returncode != 0:
            raise GhError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def json(self, *args: str):
        out = self.run(*args)
        return json.loads(out) if out.strip() else None

    def remaining_quota(self) -> int:
        data = self.json("api", "rate_limit")
        return int(data["resources"]["core"]["remaining"])

    def guard(self) -> int:
        left = self.remaining_quota()
        if left < self.min_quota:
            raise QuotaTooLow(
                f"GitHub REST quota is {left}, below the floor of {self.min_quota}. "
                "Wait for the hourly reset (gh api rate_limit shows the reset time)."
            )
        return left


def die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)
