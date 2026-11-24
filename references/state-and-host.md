# State, memory and the host

## Where state lives

Paths come from the private overlay (`local/config.json`): `state_file` and `oss_root`.

| File | Role | Who writes |
|---|---|---|
| `ledger_file` (default `<oss_root>/state.json`) | **The actionable state.** One item per PR, issue, held branch or promise: status, next action, due date, dated notes. Also the agent launch log and the last sweep time. Written only through `ledger.py` / `launch.py` / `sweep.py --mark`, atomically | orchestrator |
| `state_file` (a WORKBOARD.md) | **The narrative log.** Dated entries for every round and public action, plus the ledger table (`ledger.py render --write`, between `<!-- ledger:start -->` markers) | orchestrator, after every public action and every round |
| `<oss_root>/<oss_dir>/RESEARCH.md` and `PR-DRAFTS.md` | Per-repo knowledge and drafts | agents and orchestrator |
| `<oss_root>/<oss_dir>/drafts/` | Agent outputs, one file per item | agents |
| `<oss_root>/<oss_dir>/gate/` | Gate packets waiting for the operator; `gate/done/` after posting | orchestrator |
| `<oss_root>/<oss_dir>/PRIVATE-SECURITY-NOTE.md` | Security-class items. Never public | agents and orchestrator |
| The assistant's memory files | Durable program rules for future sessions | orchestrator |
| `config/repos.json` (this skill) | Per-repo public rules as data: titles, budgets, disclosure, sources | orchestrator, when the rules change |
| `local/config.json` (this skill, gitignored) | Private paths, knowledge sources, held items, private terms | operator / orchestrator |

GitHub is the source of truth for PR state. The state file can lag, so run `census.py` before
trusting it.

## Surviving a context compaction

Before a long round, and whenever the conversation grows large:

1. Bring the ledger and the state file up to date: every in-flight agent (`launch.py record`),
   every pending CI run id and gate packet, and every promise as a ledger item with a due date.
2. Note running background tasks there too, with what each will report.
3. After compaction, re-read in this order: `SKILL.md`, `ledger.py due`, `launch.py running`, the
   state file, then `census.py`. Then resume.

A promise made in public ("I'll ping on the 23rd", "re-check after the next deploy") that lives
only in prose gets missed: on 24 Nov two of them were a day late. Put each one in the ledger with a
due date the moment it is made.

## Windows host facts

| Trap | What to do |
|---|---|
| Little free RAM (about 1 GB) | At most 4 agents. Check `Get-CimInstance Win32_OperatingSystem \| % FreePhysicalMemory` (KB) before each launch and wait if it's under about 1,000,000. Builds go to CI. |
| Git Bash has no tz data | `date` prints UTC. Ask the operator for local time when it matters; don't trust the shell clock. |
| Windows Python can't see `/tmp` | Write temp files under the session scratchpad or the repo, and pass Windows paths (`cygpath -w`). |
| CRLF | `git config core.autocrlf false` in every clone, and check `git show \| grep -c $'\r'` before pushing. |
| Long paths | `git config core.longpaths true`. Keep big worktrees (nearcore) close to the drive root. Some repos (mpc's insta `.snap` files) still fail to check out: rebuild a commit without a checkout instead, using a temporary `GIT_INDEX_FILE`, `read-tree <base>`, `git apply --cached`, `write-tree` and `commit-tree -S`. |
| Foundry binaries | `foundryup` installs to `~/.config/.foundry/bin`. |
| Cargo | `~/.cargo/bin`. |
| Killing processes | Only by PID, and only your own. |
| Inline `sed`/`python -c` edits | They mangle Windows backslash paths in docs. Use the Edit/Write tools. |
