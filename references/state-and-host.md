# State, memory and the host

## Where state lives

Paths come from the private overlay (`local/config.json`): `state_file` and `oss_root`.

| File | Role | Who writes |
|---|---|---|
| `state_file` (a WORKBOARD.md) | **The live state.** Open PRs and their last action, issues waiting on maintainers, holds, dated log, plan | orchestrator, after every public action and every round |
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

1. Bring the state file up to date: every in-flight agent with its task, every pending CI run id,
   every pending gate packet.
2. Note running background tasks there too, with what each will report.
3. After compaction, re-read in this order: `SKILL.md`, the state file, then `census.py`. Then
   resume.

## Windows host facts

| Trap | What to do |
|---|---|
| Little free RAM (about 1 GB) | At most 4 agents. Check `Get-CimInstance Win32_OperatingSystem \| % FreePhysicalMemory` (KB) before each launch and wait if it's under about 1,000,000. Builds go to CI. |
| Git Bash has no tz data | `date` prints UTC. Ask the operator for local time when it matters; don't trust the shell clock. |
| Windows Python can't see `/tmp` | Write temp files under the session scratchpad or the repo, and pass Windows paths (`cygpath -w`). |
| CRLF | `git config core.autocrlf false` in every clone, and check `git show \| grep -c $'\r'` before pushing. |
| Long paths | `git config core.longpaths true`. Keep big worktrees (nearcore) close to the drive root. |
| Foundry binaries | `foundryup` installs to `~/.config/.foundry/bin`. |
| Cargo | `~/.cargo/bin`. |
| Killing processes | Only by PID, and only your own. |
| Inline `sed`/`python -c` edits | They mangle Windows backslash paths in docs. Use the Edit/Write tools. |
