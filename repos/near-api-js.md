# near-api-js: `near/near-api-js`

Sources: `CONTRIBUTING.md` and `.github/pull_request_template.md` from `master`, read 2026-11-20.

## Agent rules block

```text
You are contributing to near-api-js, the JavaScript/TypeScript client library
for NEAR (signing, RPC, transactions). Applications sign real transactions
with it — correctness is critical.

1. ISSUE FIRST. The team must OK a change before a PR. Your output for a new
   bug is an ISSUE draft (bug template: steps to reproduce, versions, a red
   repro), not a PR.

2. SMALL PRs: one thing, about 300 lines of diff at most.

3. TESTS: unit tests with Vitest (the test files import from 'vitest';
   CONTRIBUTING.md still says Jest) for any public API you touch. A bug fix
   ships with a test that fails without it; use vi.useFakeTimers() rather than
   real waits.

4. CHANGESET: `pnpm changeset` for any change to a published package (patch
   for fixes).

5. TypeDocs must still describe the changed public API.

6. COMMITS AND TITLE: conventional commits (fix:, feat:, docs:, test:, chore:).

7. CHECKS: `pnpm lint`, the package typecheck and tests. NODE_OPTIONS=
   --max-old-space-size=1024 on this host; otherwise CI with toolchain=node.

8. LINE ENDINGS: commit LF only. If git shows CRLF in the diff, stop and fix
   core.autocrlf before committing.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Template | `## Pre-flight checklist` (tick only what is true), `## Motivation`, `## Test Plan`, `## Related issues/PRs`. |
| Claiming | "I'd like to work on this" on an issue means a PR is expected within 7 days. Comment only when the branch is ready. |
| Merges | irondevrel merges, and core-team work dominates. |
| CRLF | A clone made on 19 Nov had 180 CRLF files in one commit (caught before push). Check with `git show \| grep -c $'\r'`. |
