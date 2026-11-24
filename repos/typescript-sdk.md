# TypeScript SDK: `modelcontextprotocol/typescript-sdk`

Sources: `CONTRIBUTING.md`, `CLAUDE.md`, `REVIEW.md` from `main`, read 2026-11-21.

## Agent rules block

```text
You are contributing to the TypeScript SDK for the Model Context Protocol
(modelcontextprotocol/typescript-sdk), the reference TypeScript implementation.
The SDK is the contract every MCP client and server depends on; spec conformance
and compatibility matter more than novelty.

1. SMALL CHANGES. A smaller change that lands beats a bigger one that does not.
   Split independent work into separate PRs. Dozens of lines get reviewed in
   minutes; hundreds sit in the queue.

2. DISCUSS BEFORE FEATURES. New public APIs, architectural changes, multi-module
   refactors and anything needing a spec change (SEP) need an issue first.
   Straightforward bug fixes with a test may skip that step.

3. SPEC IS THE ANCHOR. Read the MCP spec and the other official SDKs (Python,
   Rust, Go) before choosing behaviour. Add no invented fields and no leniency
   for peers that break the spec.

4. MINIMALISM AND BACKWARDS COMPATIBILITY. Add no API or option unless
   justified. Keep changes backwards compatible; when a bug or spec violation
   forces a break, say what breaks in the PR (and in a changeset if the repo
   uses one).

5. BRANCHES. `main` is v2 (the stable line, monorepo). v1 bug fixes target
   `v1.x`. Base v2 work on `main`.

6. TEST AND LINT. From the repository root run `pnpm build:all`, `pnpm
   lint:all` and `pnpm test:all`; paste the real output. Add a test that fails
   before the fix and passes after it.

7. COMMITS AND TITLES. Conventional commits, subject under 72 characters,
   lowercase after the colon, no trailing period: `fix(server): ...`,
   `docs: ...`, `test(e2e): ...`.

8. DISCLOSE AI ASSISTANCE. The modelcontextprotocol AI Contribution Policy
   applies org-wide: any AI assistance must be disclosed in the PR or issue,
   with the extent (docs vs code generation). If a comment is AI-generated,
   say so. Trivial typo fixes are exempt.

9. NO PUBLIC ACTION beyond a `verify/*` branch on the fork. Never push to
   modelcontextprotocol/typescript-sdk.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional, lowercase after the colon, at most 72 characters. Examples from merged PRs: `fix(server): set Allow: POST on stateless legacy 405 responses`, `docs: publish the Skills over MCP guides as an agent skill`. |
| PR body | No template in the repo: prose with the problem, the spec reference, the fix and the tests. |
| Draft | Not required by CONTRIBUTING; bug fixes can go ready once CI is green. |
| Signing | Not required by the repo; our commits are signed anyway. |
| AI disclosure | **Required** by the org-wide AI Contribution Policy (`modelcontextprotocol/modelcontextprotocol/AI_POLICY.md`): disclose in the PR or issue and say the extent; disclose AI-generated comments too. |
| Volume | 2 open PRs; bug fixes and small spec-conformance fixes only, one concern each. |
| Branches | `main` = v2; `v1.x` = v1 fixes. |
| CI | `pnpm install --frozen-lockfile && pnpm build:all && pnpm lint:all && pnpm test:all` from the repository root (node toolchain in oss-ci); targeted local run with `pnpm vitest run <path>`. |
| Tracker speed | Fast. Hot issues usually have a PR within days; check cross-references and open PRs before building. |
