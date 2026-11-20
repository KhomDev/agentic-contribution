# Changelog

## 2026-11-20 (c): code quality and efficiency review

Bugs:
- `ci.py`: `find_run` matched runs by title only. Labels get reused, so re-dispatching the same ref
  and label could report the previous run's id, and the `mpc` path took whatever run was newest.
  Runs must now be created after the dispatch (minus a 15 s clock-skew margin).
- Line endings: two tracked files (`config/rules-snapshot.json`, `scripts/pr_lint.py`) had CRLF.
  `rules_drift.py --update` now writes LF, `.gitattributes` forces `eol=lf`, and
  `tests/test_repo_hygiene.py` fails on any CRLF file.

Quality and efficiency:
- `census.py` builds the upstream-to-key index once instead of scanning per PR.
- `ci.py grep` strips ANSI codes once per line, and the "not listed yet" message names the
  configured CI repo instead of a hard-coded one.
- `signed_check.py main` takes an injectable `gh` (now tested end to end), and computes its commit
  lookup once.
- `pr_lint.py`: a named `COMMIT_SUBJECT_MAX` constant and no redundant list copy. The `Gh`
  docstring now describes `guard()` correctly.
- 79 tests. Each fix is covered by a mutant that the suite catches.
- Repos: added `near-token-rs` and `near-gas-rs` (`NearToken` and `Gas` live there).

## 2026-11-20 (b): discovery lane, public edition

- **Discovery lane.** Agents now look for new, unreported problems as well as picking up filed
  issues. `references/discovery.md` holds the six-technique playbook (docs vs. API, edge inputs,
  test health, sibling bugs, spec conformance, error paths), the novelty and repro rules, and the
  orchestrator's security triage. `brief.py --discover` adds the playbook to the prompt.
- **Public edition.** Every private detail moved to a gitignored overlay, `local/config.json`
  (template: `config/local.example.json`), deep-merged by `scripts/_common.py`. That covers paths,
  the knowledge-search command, per-repo knowledge and held items, extra banned terms and the private
  term list. The brief takes these as placeholders.
- **Leak test.** `tests/test_no_private_leaks.py` fails if a private term, a user home path or an
  email appears in any tracked file.
- **`pr_lint.py --comment`** handles issue bodies, comments and review replies. They skip PR
  template sections, and need an AI disclosure only where the repo's policy covers comments (MCP).

## 2026-11-20 (a): first version

- Process: the orchestrator verifies, and the operator approves every public action in chat (gate
  packets).
- Repo cards for 13 repos, each with an agent rules block in the style of x402's sample prompt. Each
  block was written from the project's own CONTRIBUTING, AGENTS, CLAUDE or PR template, read on
  2026-11-20.
- Scripts: `census`, `brief`, `pr_lint`, `signed_check`, `ci` and `rules_drift`. All are stdlib only,
  and all GitHub access goes through `gh`.
- Agents read the operator's private knowledge for orientation, and never cite it publicly.

## Validation log

### Unit tests and mutation check (2026-11-20)

- All offline tests pass in about 0.1 s (count in the latest commit message).
- 12 hand-made mutants were applied one at a time, and the tests caught every one: footer check
  removed, disclosure check removed, quota floor removed, double trailer allowed, census ignoring
  open PRs, repo rules dropped from the prompt, a leak term removed, title regex ignored, dispatch
  skipping the quota guard, the foundry prose check removed, and a changed hash not reported. The
  rules-dropped mutant first survived; the test now asserts that every rules block appears in the
  prompt.

### Live checks against GitHub (2026-11-20)

- `census.py` matched the state file: intents and mpc 3/3, x402 2/3, nearcore 2/3, docs 1/3,
  outlayer 1/2.
- `signed_check.py` reported OK on x402#4342 and nearcore#16906.
- `ci.py status/grep` read run 44652408954 (`RESULT [PASS]`).
- `rules_drift.py --update` hashed 26 upstream files, and a re-run reported 0 changes.
- Config check: every upstream default branch matched. The cargo-near and near-sdk-rs forks don't
  exist yet (`fork: null`).

### End-to-end Haiku dry run (near/docs, 2026-11-20)

The prompt came from `brief.py --repo docs`. The task was read-only: no push, no CI.

- **Before launch,** reading the generated prompt showed that it didn't tell agents the PR footer,
  the disclosure rule or the lint command. Fixed in the brief, with a test.
- **The agent** read the state file, the docs notes and the knowledge search, and searched prior
  art. It found a real broken snippet: `NEAR.fromDecimal`/`fromUnits` in
  `web3-apps/tutorials/data-types.mdx`. It cited the right source lines, wrote a minimal LF-only
  commit as KhomDev, and linted its drafts (0 errors). It correctly returned **HOLD** because it had
  no red/green proof, and it listed its unverified assumptions.
- **The orchestrator** ran the old and new snippet against `@near-js/tokens@2.5.1` (the old one
  throws `TypeError: NEAR.fromDecimal is not a function`; the new one prints
  `1500000000000000000000000n` and `1.5`). It re-checked prior art, re-signed with its own trailer
  (GitHub verified), added the run output to the body, and linted (0/0).
- **Gate:** the operator clicked "Open PR". Result: near/docs#3191.
- **Lesson applied:** the docs card now tells agents to run JS snippets against the published
  package.

### First live round (2026-11-20)

- foundry, rust-sdk and agave: honest NOTHING. Every verdict was spot-checked against GitHub.
- near-api-js (issue-first): the agent found, unprompted, a suffix-check bug in account creation,
  with a repro it actually ran against the published package. This is the kind of new finding the
  discovery lane now asks for explicitly.
- x402#4342: a review bot's two requests were handled through the gate (push, body edit, reply). The
  review showed our own description was wrong, so the verification step now always re-reads the
  claims in our existing PR text too.
