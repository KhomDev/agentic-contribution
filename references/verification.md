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

So nothing reaches the operator gate until every line below holds. Tick the items in the gate
packet; don't just assume them.

## Checklist

1. **Re-read the issue and the current upstream code yourself.** Is the problem real on today's
   default branch? Open each cited `file:line` and confirm that it says what the draft claims.
2. **Prior art, again, just before the gate.** Run `gh pr list -R <upstream> --state all --search
   "<issue#>"` and a symptom search. Another PR can appear while the agent works; for foundry it often
   happens within hours.
3. **Claims of absence.** Every "X does not exist" or "nothing handles Y" needs a grep under three
   names that you ran yourself.
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

Keep a correction as a correction: if you change the agent's code or claims, say what and why in the
WORKBOARD, so the next round learns from it.

## Disagreeing with a reviewer

Fix what is right and say plainly when something is not, with evidence (a run, a `file:line`).
Never agree just to close a thread. Reply "Fixed in <sha>" only when the fix exactly matches what was
asked.
