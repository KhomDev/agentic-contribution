# Private knowledge sources

An operator who has worked on these codebases before has notes, research files and indexes that let
an agent orient in minutes instead of hours. This skill lets agents read that knowledge for
orientation. It never appears in public text, and every fact is re-verified against current upstream.

The skill itself names no private source. They're configured in the gitignored overlay
`local/config.json` (template: `config/local.example.json`):

| Key | What it holds | How agents use it |
|---|---|---|
| `state_file` | The live program state (open PRs, holds, plan) | Read first; never duplicate in-flight work |
| `oss_root/<oss_dir>/` | Per-repo research, drafts, round notes | Read before choosing work |
| `knowledge_search` | A command that searches the operator's notes (e.g. a local index or `rg` over a notes folder); `<topic words>` is replaced by the agent | 2-4 focused queries |
| `knowledge_general` | Folders or files useful for every repo | Read what matches the task |
| `repos.<key>.knowledge` | Code-reading notes or read-only checkouts for that codebase | Read for orientation |
| `repos.<key>.private_rules` | Held items and exclusions that must not be named publicly | Pasted into the prompt as private notes |

## Rules

1. **Read-only.** Agents never write into knowledge paths. They write only to their own `drafts/`,
   the repo's `RESEARCH.md` (durable learnings), and the private security note.
2. **Private.** Nothing from these sources is quoted, linked or named in public text: no paths, file
   names, internal ids or wording. `pr_lint.py` blocks the overlay's `public_text.error_patterns`,
   and `tests/test_no_private_leaks.py` blocks `private_terms` from the skill's own tracked files.
3. **Possibly stale.** Notes describe the code as it was. Verify every fact on current upstream and
   cite only the upstream `file:line`.
4. **Security topics are off limits.** If a note discusses a vulnerability or a held finding, public
   work must not touch that area.
5. **Useful finds go back** into `oss/<oss_dir>/RESEARCH.md`, so the next round starts ahead.

## Why this is safe

The sources inform which problem to pick and how the code works. The public artifact is still the
agent's own change, proven on current upstream, verified by the orchestrator and approved by the
operator.
