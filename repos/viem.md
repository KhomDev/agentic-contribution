# Viem: `wevm/viem`

Sources: `AGENTS.md`, `.github/CONTRIBUTING.md` and `.github/pull_request_template.md` from `main`,
read 2026-11-22.

## Agent rules block

```text
You are contributing to Viem (wevm/viem), the TypeScript interface for
Ethereum. Every EVM client and tool built on it depends on exact ABI, encoding
and RPC semantics — correctness is critical.

1. READ AGENTS.md. It is the source of truth for the TypeScript conventions:
   exactOptionalPropertyTypes (`foo?: T | undefined`), no unchecked indexed
   reads, `type` over `interface`, `.js` import extensions, ox helpers over
   hand-rolled conversions, no enums, `options` over `args`, namespace types for
   function params/returns, and no internal-tracking references in code.

2. HUMANS, NOT BOTS. CONTRIBUTING forbids bot accounts and requires a
   non-trivial contribution elsewhere; first contributions must not be
   spelling-only. AI assistance is allowed (AGENTS.md is written for agents),
   but never present the work as fully autonomous.

3. DISCUSS API CHANGES FIRST. Significant API or implementation changes need a
   discussion or feature request before a PR. Bug fixes with a test may go
   directly.

4. TESTS: vitest for unit tests, Foundry/anvil for chain tests. A fix ships
   with a test that fails without it; for encoding changes cover both the
   round-trip and the malformed input.

5. CHANGESETS: a user-visible API or behaviour change needs a changeset
   (`pnpx changeset`, past-tense summary).

6. CHECKS: `pnpm build`, `pnpm test`, and the repo lint. Run what fits locally;
   use CI for the rest.

7. NO PUBLIC ACTION beyond a `verify/*` branch on the fork.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional, lowercase after the colon, at most 72 characters, e.g. `fix: left-pad odd-length raw hex in toPrefixedMessage` |
| PR body | Prose description per the template's single comment block; no required sections |
| Signing | Not required by the repo; we sign anyway |
| AI disclosure | Not required; the footer is enough. Never claim autonomy |
| CI | `pnpm install --frozen-lockfile && pnpm build && pnpm test` (Node 22+, pnpm 9.1+); chain tests use anvil |
| Tracker speed | Very fast: 55 merged PRs and 27 from outside authors in the 30 days to 2026-11-22. Re-check open PRs and discussions immediately before drafting |
| Volume | Budget 2 open PRs; one concern per PR |

Sources: AGENTS.md (TS conventions), CONTRIBUTING (rules, tests, changesets), PR template.
