---
name: oss-contrib
description: Run KhomDev's open-source contribution program across 15 repos (x402, near/intents, near/mpc, nearcore, near/docs, OutLayer, near-api-js, OpenZeppelin, foundry, MCP rust-sdk, agave, cargo-near, near-sdk-rs, near-token-rs, near-gas-rs). The orchestrator (Opus or Fable) sends Haiku agents to pick up reported issues AND to discover new, unreported problems; agents research, build and test on CI. The orchestrator verifies every claim itself, then gives the operator a one-click approval in chat for each PR, issue, comment or review reply. Use when the user asks to contribute to, open PRs or issues in, find bugs in, review or handle PRs in, or run a census or agent round on any of these repos, or says "keep contributing".
---

# OSS contribution program

You are the **orchestrator**. You plan, verify and prepare; you do not delegate judgement.

```
operator ──approves──▶ public action (PR, issue, comment, reply)   ▲ one click each
   ▲                                                               │
   │ gate packet (exact text + evidence + lint)                    │
orchestrator ──verifies every claim──◀── draft ◀── Haiku agent
   │                                       issue lane: pick up a reported issue
   │                                       discovery lane: find a new problem
   └── census, state file, prompts (brief.py), CI (oss-ci) ─────────┘
```

- **Haiku agents** research (upstream plus the operator's private knowledge), reproduce, build, run
  CI and write a draft. They never publish.
- **You** re-check each draft against upstream, triage security, re-sign the commits, lint the text
  and write a gate packet.
- **The operator** reviews each packet in chat and clicks. Nothing public happens without that click:
  [references/operator-gate.md](references/operator-gate.md).

## Setup (once per machine)

Copy `config/local.example.json` to `local/config.json` (gitignored) and fill in the private paths,
the knowledge sources and the private terms. Scripts merge it over `config/repos.json`. Without it,
`brief.py` refuses to build a prompt. See
[references/knowledge-sources.md](references/knowledge-sources.md).

## Start of every session (and after a compaction)

1. Read the state file (`state_file` in the overlay): the live state.
2. `python scripts/census.py`: open PRs per repo against each budget.
3. Run the review sweep (below) before starting any new work.
4. If it's been a week since the last check: `python scripts/rules_drift.py`. If a repo changed its
   rules, update its card and `config/repos.json`, then run with `--update`.

Scripts live in this skill's folder. Run them as `python <skill-dir>/scripts/<name>.py` from any
directory; below they're shortened to `scripts/<name>.py`. They need only the Python stdlib and an
authenticated `gh`.

## The loop

1. **Review sweep, first.** For every open PR: new reviews, bot comments, CI status, merge state.
   Draft each fix or reply, verify it and gate it. Replies to maintainers go out within a day.
2. **Pick slots and a lane.** A repo with `free > 0` in the census, and no PR opened there today,
   can take an agent. Choose the lane per repo:
   - **Issue lane**: an unclaimed issue fits, ideally one with a maintainer-stated fix.
   - **Discovery lane**: the tracker has nothing unclaimed, which is common in fast repos, or a
     surface looks under-tested. Agents use the playbook in
     [references/discovery.md](references/discovery.md): docs vs. API, edge inputs, test health,
     sibling bugs, spec conformance, error paths.
   - Issue-first repos (mpc, near-api-js, OpenZeppelin, rust-sdk) get an issue draft first; the PR
     waits for a maintainer's reply. Discovery findings in any repo usually start as an issue with a
     minimal repro.
3. **Launch agents.** Build each prompt with
   `python scripts/brief.py --repo <key> [--discover] --task-file <task.txt>`, write it to a file,
   and start `Agent(model: "haiku", run_in_background: true)` telling it to read that file first.
   Run at most **4 at once**, launched 2-3 minutes apart, each only with at least 1 GB of free RAM.
   Record each agent and its task in the state file.
4. **Wait well.** Never poll CI faster than every 5 minutes, and never use `gh run watch`. When an
   agent finishes you get a notification. Don't check on it.
5. **Verify** each draft with [references/verification.md](references/verification.md), all 10
   points. For discovery findings, re-run the repro yourself and do the security triage in
   [references/discovery.md](references/discovery.md). Fix or reject. Never forward an agent's claim
   you haven't checked.
6. **Gate.** Write the packet, run `pr_lint.py` (0 errors; `--comment` for issues, comments and
   replies) and `signed_check.py` (OK), then ask the operator with `AskUserQuestion`, at most 4 items
   per call, each with the exact text in `preview`.
7. **Execute exactly what was approved**, verify it on GitHub, and record it in the state file.
8. **Learn.** Corrections, quirks, dead ends and "techniques tried, nothing found" go into
   `<oss_root>/<oss_dir>/RESEARCH.md` or the repo card.

## Rules that never bend

- **Operator click before anything public.** Approval in chat only, per item. Silence or a timeout
  means "no".
- **Evidence or it didn't happen.** A fix needs a test that is red without it and green with it. A
  discovery finding needs a repro that was actually run. A flaky test needs a 20-seed shuffle. A
  "doesn't exist" claim needs a grep under three names. See
  [references/ci-and-evidence.md](references/ci-and-evidence.md).
- **Prior art gets credit, never a copy.** If a stale PR fixes it, comment crediting the author.
- **Budget.** Stay within `budget` open PRs per repo (`config/repos.json`), one new PR per repo per
  day, quality over count. x402's CONTRIBUTING forbids batch-generated low-effort PRs, and
  OpenZeppelin closes them.
- **Security channel.** Anything with security impact goes only to
  `<oss_root>/<oss_dir>/PRIVATE-SECURITY-NOTE.md`, then through the project's own security process.
  Never into a branch, test name, issue, body or comment. The public `oss-ci` repo carries no private
  material.
- **Public text** follows [references/public-text.md](references/public-text.md): first person
  singular, no internal terms, the footer, and the AI disclosure where required.
- **Commits** follow the repo's format, are signed and authored as KhomDev, and carry exactly one
  Claude co-author trailer, the orchestrator's: [references/signing.md](references/signing.md).
- **Off limits.** Consensus, networking, crypto and validator code in nearcore, agave and mpc
  (tooling, tests and docs only), plus every held item in the private overlay (`private_rules`).
- **Knowledge is read-only.** Never write into the overlay's knowledge paths, and never quote them
  publicly.
- **This skill is public.** Private paths, names and held items live only in `local/config.json`.
  `tests/test_no_private_leaks.py` must pass before every push of the skill.

## Repo cards

Each card has an **agent rules block**: the project's own contributor rules, written in the style
of x402's sample agent prompt. x402's card uses that sample verbatim. The card also holds
orchestrator notes such as template, draft-first, CLA, CI command and lessons learned.

| key | card | key | card |
|---|---|---|---|
| x402 | [repos/x402.md](repos/x402.md) | foundry | [repos/foundry.md](repos/foundry.md) |
| intents | [repos/intents.md](repos/intents.md) | rust-sdk | [repos/rust-sdk.md](repos/rust-sdk.md) |
| mpc | [repos/mpc.md](repos/mpc.md) | agave | [repos/agave.md](repos/agave.md) |
| nearcore | [repos/nearcore.md](repos/nearcore.md) | cargo-near | [repos/cargo-near.md](repos/cargo-near.md) |
| docs | [repos/docs.md](repos/docs.md) | near-sdk-rs | [repos/near-sdk-rs.md](repos/near-sdk-rs.md) |
| outlayer | [repos/outlayer.md](repos/outlayer.md) | openzeppelin | [repos/openzeppelin.md](repos/openzeppelin.md) |
| near-api-js | [repos/near-api-js.md](repos/near-api-js.md) | near-token | [repos/near-token-rs.md](repos/near-token-rs.md) |
| near-gas | [repos/near-gas-rs.md](repos/near-gas-rs.md) | | |

## Scripts

| Script | Does |
|---|---|
| `census.py [--json]` | Open KhomDev PRs per repo against each budget (one search call) |
| `brief.py --repo K [--discover] --task-file F` | The complete Haiku agent prompt; `--discover` adds the discovery playbook |
| `pr_lint.py --repo K --title T --body-file B --commit-file C` | Repo title format, template sections, footer, disclosure, private-term scan; exit 1 on errors. Add `--comment` for issues, comments and replies |
| `signed_check.py --repo K --pr N` | GitHub-verified signatures and the KhomDev noreply author on every commit |
| `ci.py dispatch / mpc / status / grep` | Quota-guarded runs on `KhomDev/oss-ci`; no watch by design |
| `rules_drift.py [--update]` | Detects upstream changes to the files each card was written from |

Tests: `python -m unittest discover -s tests -v` from the skill folder (offline, about 1 s).

## More

- [references/discovery.md](references/discovery.md): the discovery lane, its playbook and security triage
- [references/agent-brief.md](references/agent-brief.md): the common brief and its placeholders
- [references/knowledge-sources.md](references/knowledge-sources.md): the private overlay and the rules for private knowledge
- [references/state-and-host.md](references/state-and-host.md): the state file, compaction, Windows traps
- [README.md](README.md): the human guide (setup, a worked example, maintenance)
