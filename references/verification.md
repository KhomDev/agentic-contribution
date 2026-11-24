# Verification: how the orchestrator checks an agent's draft

Agents make confident mistakes. These were all caught in this program:

- "There is no mock network" (mpc), when `TestMeshTransport` existed.
- A test that changed `TMPDIR` with `unsafe set_var` (nearcore). The rewrite reads `builder.home_dirs`
  directly.
- "CI cannot reach the RPC" (foundry). It can, through dRPC.
- A fix that was a near-verbatim copy of a stale PR by another author (agave #14863).
- A PR body written with a placeholder because Windows Python couldn't see `/tmp` (mpc #5260). The
  body was fixed within a minute.
- 180 CRLF files in a commit (near-api-js). Caught before the push.
- A READY "the CLI rejects the `--no-locked` flag its own hint recommends" (cargo-near). The agent
  tried two subcommands; `build reproducible-wasm` defines that flag, and the hint deliberately
  covers both modes. Its patch would have deleted correct advice.
- A held branch revived with "I'll open the PR" (mpc #1852), after a dashboard panel landed that
  depends on the label the change removes. A public correction followed.

So nothing reaches the operator gate until every line below holds. Tick the items in the gate
packet; don't just assume them.

## Checklist

0. **Run the tools first.** `verify_draft.py <draft>` must report 0 errors (header complete, every
   CI run concluded as claimed, cited lines still say what they claim), and `refcheck.py` on the
   final body must report every `path:line` OK. They catch the mechanical failures. They don't
   judge whether the finding is right, so the steps below still apply in full.
1. **Re-read the issue and the current upstream code yourself.** Is the problem real on today's
   default branch? Open each cited `file:line` and confirm that it says what the draft claims.
2. **Prior art, again, just before the gate.** Run `gh pr list -R <upstream> --state all --search
   "<issue#>"` and a symptom search. Another PR can appear while the agent works; for foundry it often
   happens within hours.
3. **Claims of absence.** Every "X does not exist" or "nothing handles Y" needs a grep under three
   names that you ran yourself, across the whole surface: every subcommand's argument struct, every
   crate or package, generated code and docs. One `--help` or one file is not a search.
4. **Red/green evidence.** Open both CI runs. Red must fail on the new assertion, not on a compile
   error or a timeout. Green must pass that same test, and must not pass because the test was
   skipped (check the test count). For order-dependent tests, compare 20 shuffled seeds on the
   baseline with 20 on the branch.
5. **The diff.** Read every line. It must contain no unrelated change, no debug output, no filler
   comments (mpc and x402 reject them), no `as` casts in mpc, no fully qualified paths in nearcore,
   and no CRLF (`git show | grep -c $'\r'` must be 0).
6. **Repo rules.** Check it against `repos/<key>.md`: the title format, the template sections, the
   changeset or changelog, issue-first, draft-first, the CLA and the AI disclosure.
7. **Lint.** `pr_lint.py --repo <key> --title ... --body-file ... --commit-file ...` must report 0
   errors. Every warning gets either a reason in the packet or a fix.
8. **Signing.** Re-sign the agent's commits as the orchestrator and replace the agent's trailer
   (`signing.md`), push, then run `signed_check.py` until it reports OK.
9. **Security screen.** Does anything in the diff, a test name or the body hint at a vulnerability or
   held finding? If so it doesn't ship: move it to the private note, then rescope or drop the item.
10. **Budget.** `census.py` must show a free slot for the repo, and no other PR has opened in that
    repo today.
11. **Precedent.** Look for a maintainer who already fixed a sibling (`git log -S` on the same
    pattern, closed issues on the same helper). If you find one, cite it: "same class as #4488"
    turns a strictness nit into a consistent case. If a maintainer rejected the class, hold.

## Revival gate (held branches, held packets, promised PRs)

Anything parked for more than a day is stale until re-proven. Before it goes public, and before you
promise it in public ("I'll open the PR"):

1. Rebase on today's default branch. If the diff no longer applies cleanly, re-derive it, don't
   force it.
2. Grep current upstream for every consumer of what the change touches: callers, tests, metric and
   label names in dashboards (`deployment/grafana/*.json` and the like), config keys, docs, CLI
   output that scripts parse. A consumer that appeared while the item sat parked is a blocker until
   a maintainer chooses.
3. Re-run prior art (open and closed PRs and issues) and the red/green evidence on the rebased
   commit.
4. Re-run `refcheck.py` on the body: line numbers drift within days.
5. Only then promise it. If any step fails, say so publicly before the promise is due, with
   evidence and options, and record the correction in the ledger.

Keep a correction as a correction: if you change the agent's code or claims, say what and why in the
WORKBOARD, so the next round learns from it.

## Disagreeing with a reviewer

Fix what is right and say plainly when something is not, with evidence (a run, a `file:line`).
Never agree just to close a thread. Reply "Fixed in <sha>" only when the fix exactly matches what was
asked.
