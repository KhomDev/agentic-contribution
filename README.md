# agentic-contribution

A Claude Code skill (`oss-contrib`) for contributing to open source with an AI team, **under human
control**.

A senior model (Opus or Fable) orchestrates. Cheap Haiku agents do the legwork. They pick up
reported issues, and they **discover new, unreported problems**: broken examples, wrong docs, edge
cases, flaky tests, spec gaps. They reproduce, build and run tests on CI. The orchestrator re-checks
everything an agent claims and prepares each public action as a gate packet. **The operator**
approves each one with a click in the chat. Nothing appears on GitHub under the operator's name
without that click.

It's written for one contributor (KhomDev) and the repositories listed in `config/repos.json` (currently 30), but the engine is generic. Swap the
repo cards and `config/repos.json` for your own.

## Why it's built this way

| Problem we hit | What the skill does about it |
|---|---|
| Agents state false things confidently ("no mock network exists") | A 10-point verification checklist the orchestrator runs on every draft |
| One agent nearly re-posted someone else's stale PR | Prior-art search is mandatory twice: by the agent and again right before the gate |
| Maintainers close low-effort AI PRs (x402 and OpenZeppelin say so) | Budgets per repo, one new PR per repo per day, red/green evidence on every fix |
| Fast repos have no unclaimed issues left | A discovery lane with a six-technique playbook for finding new problems, each needing a repro that was actually run |
| A new finding might be a security issue | Security triage by the orchestrator; security-relevant findings go only through the project's security process |
| Each repo has different rules (titles, templates, changesets, CLA, AI disclosure) | A card per repo with an agent rules block from the project's own docs, plus `pr_lint.py` to enforce it |
| Repos change their rules | `rules_drift.py` hashes the upstream rule files and flags changes |
| Parallel `gh run watch` drained the 5000/h GitHub quota | `ci.py` has no watch, refuses to start under 300 remaining, and polls at most every 5 minutes |
| Private knowledge must never leak | Private paths, sources and held items live in a gitignored overlay; `pr_lint.py` and a leak test guard both the PR text and this repo |

## Layout

```
oss-contrib/                      (clone this repo to ~/.claude/skills/oss-contrib)
├── SKILL.md                      entry point Claude loads (orchestrator instructions)
├── README.md                     this file
├── CHANGELOG.md                  changes and the validation log
├── config/
│   ├── repos.json                per-repo public rules as data (single source of truth)
│   ├── local.example.json        template for the private overlay
│   └── rules-snapshot.json       hashes of the upstream rule files the cards were written from
├── local/config.json             YOUR private overlay (gitignored, never committed)
├── repos/<key>.md                one card per repo: agent rules block + orchestrator notes
├── references/
│   ├── discovery.md              discovery lane: playbook and security triage
│   ├── agent-brief.md            the common prompt every Haiku agent gets
│   ├── operator-gate.md          what needs a click, packet format, how the operator is asked
│   ├── verification.md           the orchestrator's checklist for agent drafts
│   ├── ci-and-evidence.md        CI workflows, quota rules, proof standards
│   ├── signing.md                SSH signing, re-signing, trailers, AI disclosure
│   ├── public-text.md            voice, banned terms, body skeleton, review replies
│   ├── knowledge-sources.md      the private overlay and the rules for private knowledge
│   └── state-and-host.md         state file, compaction, Windows traps
├── scripts/                      stdlib-only Python, all GitHub access through `gh`
│   ├── census.py                 open PRs per repo against each budget
│   ├── sweep.py                  review sweep: which PRs and issues owe a reply
│   ├── ledger.py                 actionable state: next action and due date per item
│   ├── launch.py                 agent launch discipline and a real route check
│   ├── brief.py                  builds each agent's prompt
│   ├── verify_draft.py           checks an agent draft against its own evidence
│   ├── refcheck.py               checks every path:line in public text against upstream
│   ├── pr_lint.py                title, template, footer, disclosure, private-term lint
│   ├── signed_check.py           verified signatures and author on every commit
│   ├── outcomes.py               per-repo acceptance rates of what was filed
│   ├── ci.py                     quota-guarded runs on the CI repo
│   └── rules_drift.py            upstream contributor-rule changes
└── tests/                        offline unit tests (python -m unittest)
```

## Setup

```powershell
git clone https://github.com/KhomDev/agentic-contribution "$HOME\.claude\skills\oss-contrib"
cd "$HOME\.claude\skills\oss-contrib"
mkdir local; copy config\local.example.json local\config.json   # then edit it
python -m unittest discover -s tests
```

The overlay holds the private parts:

- the state file and notes root;
- the signing key path;
- a knowledge-search command over your own notes;
- per-repo knowledge paths and held items;
- extra banned terms for PR text;
- the terms that must never appear in this repo.

## Using it

In a Claude Code session, say something like:

- "Keep contributing to the configured repos." This runs the full loop: review sweep, census, agent rounds,
  verification, gate.
- "Find new bugs in near-api-js." This starts the discovery lane.
- "Handle the review comments on our open PRs."
- "Census: which repos have free PR slots?"

### What the operator sees

When items are ready, Claude asks up to four questions at a time, like this one:

> **x402 PR**: Open the x402 PR 'fix(near): evict expired settlement entries' as a draft?
> ○ Open as draft (Recommended): *preview shows the exact title, body, CI evidence and lint result*
> ○ Open ready ○ Revise ○ Hold

**Revise** takes free-text notes; Claude applies them, re-lints and asks again. No answer means
nothing is posted. Each gate packet is also saved under `<oss_root>/<repo>/gate/`.

## Two worked examples

**Issue lane: a flaky test in near/mpc (near/mpc#5260).**

1. The census shows a free slot.
2. `brief.py --repo mpc` combines the common brief, mpc's own rules (`<sut>__should_<assertion>` test
   names, no `as` casts, no filler comments) and the task.
3. The agent proves the test is order-dependent with a 20-seed shuffle on CI: 13/20 fail on main,
   0/20 on its branch.
4. The orchestrator re-checks both runs, re-signs the commit, lints it, and asks the operator, who
   clicks **Open PR**.

**Discovery lane: a broken docs example (near/docs#3191).**

1. A docs agent compared snippets with the real API and found `NEAR.fromDecimal`, a method that
   doesn't exist.
2. The orchestrator ran the old snippet against the published package
   (`TypeError: NEAR.fromDecimal is not a function`) and the fixed one (correct output).
3. It re-signed the commit, linted it, and the operator clicked **Open PR**.

## Maintenance

| When | Do |
|---|---|
| Every session | `ledger.py due`, `census.py`, `sweep.py --mark`, in that order |
| Weekly | `python scripts/rules_drift.py`. On a change, re-read the file, update the card and `config/repos.json`, then `--update`. Also `outcomes.py` to see where the work lands |
| A repo joins or leaves | Edit `config/repos.json` (with `examples` of real merged titles), add or remove `repos/<key>.md`, run the tests |
| A repo's title format changes | Update `title.regex` and `examples`; the tests check each good example matches and each bad one doesn't |
| Before every push of this repo | `python -m unittest discover -s tests` must pass, including the leak test against your real overlay |
| The orchestrator model changes | Nothing to edit: the trailer pattern accepts any `Claude <model>` |

## Testing

```powershell
python -m unittest discover -s tests -v
```

The tests are offline: GitHub calls go through a fake `gh` runner, and the config tests use
`config/local.example.json`, never the private overlay. They cover:

- the linter, with real merged titles as positive and negative cases;
- the census tally and signing checks;
- CI argument building and the quota floor;
- drift detection;
- prompt assembly, with no placeholder left unfilled in the brief, the repo rules or the task, in
  both lanes and for every repo;
- the sweep's OWED / STATE / BOT / QUIET classification, deduplication and quota guard;
- the ledger (atomic writes, due dates, the rendered table) and launch discipline (RAM, spacing,
  cap, and a smoke test that needs a written file);
- the draft verifier (header schema, absence-claim scope, red/green CI conclusions, moved lines),
  the reference checker and the outcome tally;
- the docs: frontmatter, links, and a rules block in every card;
- a **leak test** that fails if any private term from your overlay, or any user path or email,
  appears in a tracked file.

The skill was also run end to end with real Haiku agents (see "Validation log" in `CHANGELOG.md`).

## Limits and honest caveats

- The repo cards summarise each project's rules as of the "read" date in each card. Upstream is the
  authority, which is why `rules_drift.py` exists.
- `pr_lint.py` catches format problems and leaks. It doesn't judge whether a change is correct; the
  verification checklist and the operator's review do that.
- `verify_draft.py` and `refcheck.py` check that the evidence exists and still says what the draft
  claims. They can't tell whether the reasoning is right. On 24 Nov a draft with a real repro was
  still wrong (cargo-near), and only reading the other subcommands caught it.
- `sweep.py` marks a human's comment after ours as OWED even when it's addressed to a bot or needs
  no answer. It decides what to read, not what to say.
- The banned-term lists can't anticipate every leak. Read the preview before you click.
