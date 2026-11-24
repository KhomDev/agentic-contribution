#!/usr/bin/env python3
"""The structured state ledger: every open item, what happens next, and when.

The WORKBOARD stays the dated log. This ledger is the actionable list, so a
promised follow-up ("ping on 23 Nov", "re-check after the deploy") cannot get
lost in prose. It lives at `ledger_file` from the overlay, else
`<oss_root>/state.json`.

    python scripts/ledger.py add x402#4326 --kind pr --url URL --status waiting \
        --next "ping mikedotexe if still silent" --due 2026-11-27
    python scripts/ledger.py update x402#4326 --due 2026-11-30 --note "pinged"
    python scripts/ledger.py done outlayer#46 --note "fixed by deploy"
    python scripts/ledger.py due              # session start: exit 1 if anything is due
    python scripts/ledger.py list [--all] [--json]
    python scripts/ledger.py render [--write] # table between markers in the state file

Statuses: `open` (we act next), `waiting` (on a maintainer), `held` (parked on
purpose), `done`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, ledger_path, load_config  # noqa: E402

STATUSES = ("open", "waiting", "held", "done")
KINDS = ("pr", "issue", "comment", "branch", "finding", "task")
START = "<!-- ledger:start -->"
END = "<!-- ledger:end -->"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty() -> dict:
    return {"version": 1, "last_sweep": None, "items": [], "launches": []}


def load(path: Path) -> dict:
    if not path.exists():
        return empty()
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, value in empty().items():
        data.setdefault(key, value)
    return data


def save(path: Path, data: dict) -> None:
    """Write atomically: a crash mid-write must never leave a truncated ledger."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".state-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def parse_day(value: str | None) -> str | None:
    if value in (None, "", "none"):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError(f"not a date (YYYY-MM-DD): {value!r}") from None


def find(data: dict, item_id: str) -> dict:
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    raise KeyError(f"no ledger item {item_id!r}")


def add(data: dict, item_id: str, kind: str, status: str, next_action: str, url: str = "",
        due: str | None = None, note: str = "", stamp: str | None = None) -> dict:
    if any(i["id"] == item_id for i in data["items"]):
        raise ValueError(f"ledger item {item_id!r} already exists; use update")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if status != "done" and not next_action.strip():
        raise ValueError("an open item needs --next: what happens next, and who does it")
    stamp = stamp or now_iso()
    item = {"id": item_id, "kind": kind, "url": url, "status": status, "next_action": next_action.strip(),
            "due": parse_day(due), "notes": [], "created": stamp, "updated": stamp}
    if note:
        item["notes"].append(f"{stamp[:10]}: {note}")
    data["items"].append(item)
    return item


def update(data: dict, item_id: str, status: str | None = None, next_action: str | None = None,
           due: str | None = "keep", note: str = "", url: str | None = None, stamp: str | None = None) -> dict:
    item = find(data, item_id)
    stamp = stamp or now_iso()
    if status is not None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        item["status"] = status
    if next_action is not None:
        item["next_action"] = next_action.strip()
    if due != "keep":
        item["due"] = parse_day(due)
    if url is not None:
        item["url"] = url
    if note:
        item["notes"].append(f"{stamp[:10]}: {note}")
    if item["status"] != "done" and not item["next_action"]:
        raise ValueError("an open item needs a next action")
    item["updated"] = stamp
    return item


def due_items(data: dict, today: date) -> tuple[list[dict], list[dict]]:
    """(overdue, due today) among items that are not done."""
    overdue, today_items = [], []
    for item in data["items"]:
        if item["status"] == "done" or not item.get("due"):
            continue
        day = date.fromisoformat(item["due"])
        if day < today:
            overdue.append(item)
        elif day == today:
            today_items.append(item)
    key = lambda i: (i["due"], i["id"])  # noqa: E731
    return sorted(overdue, key=key), sorted(today_items, key=key)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render(data: dict, today: date, include_done: bool = False) -> str:
    rows = [i for i in data["items"] if include_done or i["status"] != "done"]
    order = {s: n for n, s in enumerate(STATUSES)}
    rows.sort(key=lambda i: (order[i["status"]], i.get("due") or "9999-99-99", i["id"]))
    lines = [
        f"_Ledger rendered {today.isoformat()}; last sweep {data.get('last_sweep') or 'never'}. "
        "Edit with `ledger.py`, not by hand._",
        "",
        "| Item | Status | Next action | Due |",
        "|---|---|---|---|",
    ]
    for i in rows:
        due = i.get("due") or "-"
        if i.get("due") and i["status"] != "done" and date.fromisoformat(i["due"]) <= today:
            due = f"**{due} DUE**"
        name = f"[{i['id']}]({i['url']})" if i.get("url") else i["id"]
        lines.append(f"| {_cell(name)} | {i['status']} | {_cell(i['next_action'] or '-')} | {due} |")
    if not rows:
        lines.append("| - | - | nothing open | - |")
    return "\n".join(lines)


def splice(document: str, table: str) -> str:
    """Put `table` between the ledger markers, or insert a marked section after the first heading."""
    block = f"{START}\n{table}\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if pattern.search(document):
        return pattern.sub(lambda _m: block, document, count=1)
    lines = document.split("\n")
    at = next((n + 1 for n, line in enumerate(lines) if line.startswith("# ")), 0)
    section = ["", "## Ledger (actionable items)", "", block, ""]
    return "\n".join(lines[:at] + section + lines[at:])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, help="override the ledger path (tests)")
    ap.add_argument("--today", help="YYYY-MM-DD; defaults to today in UTC")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add")
    p.add_argument("id")
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--status", default="waiting", choices=STATUSES)
    p.add_argument("--next", dest="next_action", default="")
    p.add_argument("--url", default="")
    p.add_argument("--due")
    p.add_argument("--note", default="")

    p = sub.add_parser("update")
    p.add_argument("id")
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--next", dest="next_action")
    p.add_argument("--url")
    p.add_argument("--due", default="keep", help="YYYY-MM-DD, or 'none' to clear")
    p.add_argument("--note", default="")

    p = sub.add_parser("done")
    p.add_argument("id")
    p.add_argument("--note", default="")

    p = sub.add_parser("list")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")

    sub.add_parser("due")

    p = sub.add_parser("render")
    p.add_argument("--write", action="store_true", help="splice the table into the state file")
    p.add_argument("--all", action="store_true")

    args = ap.parse_args(argv)
    config = load_config() if args.ledger is None or args.cmd == "render" else {}
    path = args.ledger or ledger_path(config)
    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    data = load(path)

    try:
        if args.cmd == "add":
            item = add(data, args.id, args.kind, args.status, args.next_action, args.url, args.due, args.note)
            save(path, data)
            print(f"added {item['id']} ({item['status']}, due {item['due'] or '-'})")
        elif args.cmd == "update":
            item = update(data, args.id, args.status, args.next_action, args.due, args.note, args.url)
            save(path, data)
            print(f"updated {item['id']} ({item['status']}, due {item['due'] or '-'})")
        elif args.cmd == "done":
            update(data, args.id, status="done", note=args.note)
            save(path, data)
            print(f"done {args.id}")
        elif args.cmd == "list":
            items = [i for i in data["items"] if args.all or i["status"] != "done"]
            print(json.dumps(items, indent=2, ensure_ascii=False) if args.json else render(data, today, args.all))
        elif args.cmd == "due":
            overdue, today_items = due_items(data, today)
            for label, items in (("OVERDUE", overdue), ("DUE TODAY", today_items)):
                for i in items:
                    print(f"{label:9} {i['due']}  {i['id']}: {i['next_action']}")
            if not overdue and not today_items:
                print(f"nothing due on or before {today.isoformat()}")
                return 0
            return 1
        elif args.cmd == "render":
            table = render(data, today, args.all)
            if args.write:
                state = Path(config["state_file"])
                state.write_text(splice(state.read_text(encoding="utf-8"), table), encoding="utf-8", newline="\n")
                print(f"wrote the ledger table into {state}")
            else:
                print(table)
    except (KeyError, ValueError) as exc:
        die(str(exc).strip("'\""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
