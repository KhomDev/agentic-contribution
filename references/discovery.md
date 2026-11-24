# Discovery lane: finding problems nobody has reported yet

The issue lane picks up bugs that someone else already filed. The discovery lane finds new ones:
broken examples, wrong docs, flaky or order-dependent tests, edge cases the code gets wrong, and
behaviour that contradicts the project's own spec.

New problems are worth more than small fixes. A maintainer has to triage someone else's issue, but a
verified new bug with a minimal repro saves them that work. It's also the strongest signal of skill a
contributor can give.

Both lanes share the rest of the process: verification, the gate and the budgets. Use the discovery
lane when the census shows free slots but the issue tracker has nothing unclaimed, which is common in
fast repos like foundry and rust-sdk.

## How a discovery round runs

1. **Choose a surface** that public work may touch: CLI behaviour, client libraries, examples and
   docs, test infrastructure, tooling, error messages, input parsing, spec conformance.
   Consensus-critical, cryptographic and fund-moving core logic is out of scope for public discovery
   (see "Security triage" below).
2. **Pick one or two techniques** from the playbook below. Don't scan everything shallowly.
3. **Reproduce before you believe.** A candidate counts only with a minimal repro that you ran,
   against the current default branch or the latest published release.
4. **Check that it's new.** Search open and closed issues and PRs for the symptom, the function name
   and the error text, then check the changelog and unreleased commits on the default branch.
5. **Classify** (below), then draft the issue, the PR, or both.

## Playbook (the text agents receive)

```text
DISCOVERY PLAYBOOK. Your task is to find ONE problem that is not yet reported,
prove it, and draft the right artifact. Use one or two of these techniques:

A. EXAMPLES AND DOCS VS. THE REAL API. Extract code snippets from docs,
   READMEs, doc comments and examples/; run or compile them against the
   current release. Compare documented flags, defaults, error names and return
   types with the source and with real `--help` output.
B. BOUNDARY AND EDGE INPUTS. For parsing, validation, naming, amounts, units
   and limits: try empty, maximum, off-by-one, unicode, negative, exponent and
   suffix/prefix inputs. Look for checks done with startsWith/endsWith/contains
   on structured identifiers, unchecked casts, and default values that differ
   between layers.
C. TEST HEALTH. Run a crate's or package's tests under a shuffled order and
   repeated seeds; look for order dependence, shared global state, leaked temp
   dirs, real sleeps and network use. A flaky test proven with 20 seeds is a
   real, welcome finding.
D. SIBLING BUGS (variant analysis). Read the last 30 merged fix PRs. For each
   bug class fixed in one place, search for the same pattern elsewhere in the
   repo that the fix did not touch.
E. SPEC CONFORMANCE. Where the repo has a spec (protocol docs, a standard, an
   RFC-style document), pick one MUST/SHOULD statement and check the code and
   tests actually implement it, including the error path.
F. ERROR PATHS. Find public functions whose failure branches have no test;
   trigger them and check the error that reaches the user is correct and
   actionable (not swallowed, not a panic, not a misleading message).

RULES FOR DISCOVERY
1. A finding needs a minimal repro you RAN, with the real output pasted, on
   the current default branch or the latest release. Reading code is how you
   find candidates, not how you prove them.
2. Novelty: search issues and PRs (open and closed) for the symptom, the
   function name and the exact error text; check unreleased commits on the
   default branch. Report what you searched.
3. Classify the finding:
   - BUG with a small, obvious fix and a test: draft both the issue text and
     the PR (in issue-first repos, the PR waits for a maintainer reply).
   - BUG needing a design decision: draft the issue only, with the repro and
     one or two possible fixes.
   - DOCS/EXAMPLE error: draft the PR (docs repos) or the issue (others).
   - SECURITY-RELEVANT (could let someone take or lock funds or keys, bypass
     a check, or crash a node or service remotely): STOP. Write it only to
     the private note file, with the repro, and tell the orchestrator. No
     public draft at all.
4. One finding per round. Stop when you have one solid finding. "NOTHING
   after techniques X and Y on surfaces P and Q" is a valid, useful result:
   say exactly what you tried, so the next round does not repeat it.
5. In the draft file, add a section "## Discovery" stating the technique, the
   surface and every candidate you rejected and why.
6. Try to refute your own finding before you call it READY. Ask: is this
   behaviour intended somewhere else (another subcommand, mode, feature flag
   or caller that relies on it)? Does a test pin it as correct? Grep the whole
   repo for the flag, function or message, not just the path you entered by.
   A finding that survives this is worth filing; one that does not is a
   rejected candidate for the Discovery section.
7. Precedent: search the history for the same pattern fixed elsewhere
   (git log -S '<pattern>', merged PRs touching the same helper). A maintainer's
   own fix of a sibling bug is the strongest case you can make; a maintainer's
   rejection of the same class means HOLD. Record either in the header.
```

## Security triage (orchestrator)

When a discovery finding might have security impact, the orchestrator decides. The agent never does.

| Question | If yes |
|---|---|
| Could it let an attacker take, lock or misdirect funds or keys, forge or skip a check, or crash a node or service remotely? | Private only. Follow the project's security policy (SECURITY.md, security email or program). Never a public issue, PR, test name or comment. |
| Does it only fail safely, e.g. a transaction the chain rejects, a confusing error, a crash of a local CLI on bad local input? | Public correctness bug. Say plainly in the issue that it fails safely, and why. |
| Unsure? | Treat it as security-relevant until you've checked the on-chain or runtime behaviour. |

The operator still approves every public artifact through the gate. For a security-relevant finding,
the gate packet is the private note plus a recommendation on which disclosure channel to use.

## Choosing surfaces per repo

The repo cards in `repos/` list which areas are open to public work. Good starting surfaces:

| Repo | Surfaces that suit discovery |
|---|---|
| near-api-js | account/transaction builders, unit conversion, error parsing, retry/backoff |
| near docs | snippets vs. near-sdk-rs / near-api-js / near-cli-rs |
| foundry | cast/forge CLI output and flags, config parsing, cheatcode edge inputs |
| rust-sdk | transport edge cases, serde of protocol messages vs. the MCP spec |
| x402 | spec MUST statements vs. the mechanism code and tests |
| nearcore, mpc, intents, agave | test health (C) and tooling/CLI only |
| OpenZeppelin | NatSpec vs. behaviour, missing error-path tests (issue first) |
