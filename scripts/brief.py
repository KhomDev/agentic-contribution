#!/usr/bin/env python3
"""Assemble the full prompt for one Haiku agent.

    python scripts/brief.py --repo mpc --task-file task.txt > prompt.txt
    python scripts/brief.py --repo docs --discover --task "Surface: snippets in tools/"

Order: the common brief (references/agent-brief.md) with placeholders filled
from the merged config (config/repos.json + local/config.json), the private
per-repo rules from the local overlay (if any), the repo's agent rules block(s)
verbatim from repos/<key>.md, the discovery playbook with --discover, then the
task. Fails loudly if any placeholder stays unfilled.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SKILL_ROOT, die, load_config, require  # noqa: E402

FENCE = re.compile(r"```text\n(.*?)```", re.DOTALL)
PLACEHOLDER = re.compile(r"<[A-Z][A-Z_]+>")


def section(markdown: str, heading: str) -> str:
    """Return the text under `## heading` up to the next `## ` heading."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", markdown, re.MULTILINE | re.DOTALL)
    if not m:
        raise ValueError(f"section '## {heading}' not found")
    return m.group(1)


def text_blocks(markdown: str, heading: str) -> list[str]:
    blocks = FENCE.findall(section(markdown, heading))
    if not blocks:
        raise ValueError(f"no ```text block under '## {heading}'")
    return [b.rstrip() for b in blocks]


def fill(template: str, values: dict[str, str]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace(f"<{key}>", value)
    return out


def _paths(root: str, paths: list[str]) -> str:
    return ", ".join(p if re.match(r"^[A-Za-z]:|^/", p) else f"{root}/{p}" for p in paths) or "none"


def build(repo_key: str, task: str, config: dict, discover: bool = False) -> str:
    repo = config["repos"][repo_key]
    brief_md = (SKILL_ROOT / "references" / "agent-brief.md").read_text(encoding="utf-8")
    card_md = (SKILL_ROOT / repo["card"]).read_text(encoding="utf-8")
    root = config["workspace_root"]
    values = {
        "UPSTREAM": repo["upstream"],
        "FORK": repo["fork"] or f"(none yet: keep the branch local and tell the orchestrator; it forks {repo['upstream']} on operator approval)",
        "DEFAULT_BRANCH": repo["default_branch"],
        "OSS_ROOT": config["oss_root"],
        "OSS_DIR": repo["oss_dir"],
        "STATE_FILE": config["state_file"],
        "SKILL_ROOT": SKILL_ROOT.as_posix(),
        "KNOWLEDGE_SEARCH": config["knowledge_search"],
        "KNOWLEDGE_GENERAL": _paths(root, config.get("knowledge_general", [])),
        "KNOWLEDGE_PATHS": _paths(root, repo["knowledge"]),
        "REPO_KEY": repo_key,
        "FOOTER": config["footer"],
        "DISCLOSURE_RULE": (
            "REQUIRED. Add one plain sentence before the footer saying how AI was used, e.g. "
            "\"Most of this change was written with Claude Code; I reviewed every line.\""
            if repo["ai_disclosure"] == "required"
            else "the footer line below is enough."
        ),
    }
    common = fill(text_blocks(brief_md, "Common brief")[0], values)
    left = sorted(set(PLACEHOLDER.findall(common)))
    if left:
        raise ValueError(f"unfilled placeholders in the brief: {left}")
    parts = [common]
    if repo["private_rules"]:
        parts.append(f"PRIVATE REPO NOTES (never repeat these publicly)\n\n{repo['private_rules'].strip()}")
    rules = "\n\n".join(text_blocks(card_md, "Agent rules block"))
    parts.append(f"REPO RULES ({repo['upstream']}, from the project's own contributor docs)\n\n{rules}")
    if discover:
        playbook = text_blocks((SKILL_ROOT / "references" / "discovery.md").read_text(encoding="utf-8"),
                               "Playbook (the text agents receive)")[0]
        parts.append(playbook)
    parts.append(f"TASK\n\n{task.strip()}")
    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, choices=sorted(config["repos"]))
    ap.add_argument("--discover", action="store_true", help="append the discovery playbook (find new problems)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--task")
    group.add_argument("--task-file", type=Path)
    args = ap.parse_args(argv)
    require(config, "workspace_root", "oss_root", "state_file", "knowledge_search")
    task = args.task if args.task is not None else args.task_file.read_text(encoding="utf-8")
    if not task.strip():
        die("the task is empty")
    print(build(args.repo, task, config, discover=args.discover))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
