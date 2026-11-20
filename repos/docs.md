# NEAR docs: `near/docs`

Sources: `CONTRIBUTING.md` from `master`, read 2026-11-20. It defers to the NEAR wiki. The repo has no
PR template, CLA or changeset rule, and no AI restriction. It ships `.agents/skills/mintlify/SKILL.md`
for agents editing the site.

## Agent rules block

```text
You are contributing to the NEAR developer docs (near/docs), a Mintlify site
read by every new NEAR developer. A wrong snippet costs readers hours —
accuracy is critical.

1. EVERY CHANGE CITES ITS SOURCE OF TRUTH: an SDK file:line (near-sdk-rs,
   near-api-js), a nearcore config or code path, or the real `--help` output
   of near-cli-rs. No change without one.

2. CODE SNIPPETS MUST COMPILE OR RUN against the current release. Prove it:
   run the old snippet (show the error) and the new one (show the output). JS
   snippets: run them locally in a scratch dir against the exact published
   package the snippet imports (`npm i <pkg>@latest`, then `node t.mjs`).
   Rust snippets: compile on CI. Do not "fix" a snippet you have not run.

3. READ .agents/skills/mintlify/SKILL.md before editing MDX. Keep the page's
   existing components, frontmatter and tone.

4. MINIMAL EDITS. Fix the wrong thing; do not rewrite paragraphs, reorder
   sections or add new pages unless asked.

5. NO MARKETING OR FILLER. Plain, specific sentences.

6. PR TITLE: a short imperative description ("Fix ...", "Explain ...") or a
   conventional prefix. No trailing period.

7. One class of problem per PR (e.g. all raw integers passed as Gas), across
   the files where it occurs.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Preview | The Mintlify preview check on fork PRs waits for a maintainer to approve it. Not ours to fix. |
| Merges | Most merges come from irondevrel (the docs owner). Outside contributors who cite sources get merged quickly. |
| CI | `toolchain=rust` to compile Rust snippets in a scratch crate, `toolchain=node` for JS snippets. |
| Body | Problem, then each file with its source citation, then the old-vs-new compile evidence. |
