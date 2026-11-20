# OpenZeppelin Contracts: `OpenZeppelin/openzeppelin-contracts`

Sources: `CONTRIBUTING.md`, `CLAUDE.md` and `.github/PULL_REQUEST_TEMPLATE.md` from `master`, read
2026-11-20. `CLAUDE.md` defers to `GUIDELINES.md` as the authoritative spec, and to the repo skills
in `.claude/skills/`: `add-changeset`, `library-api-design`, `solidity-style` and `testing`.

## Agent rules block

```text
You are contributing to OpenZeppelin Contracts, the Solidity library that
thousands of deployed contracts inherit from. A change here ships into other
people's code — correctness and backward compatibility are critical.

1. ISSUE FIRST. Any non-trivial change needs a maintainer-agreed issue. Only
   very minor changes go without one. Never decide on new public API.

2. READ GUIDELINES.md, CLAUDE.md and the matching skill in .claude/skills/
   (solidity-style for code/NatSpec, testing for tests, add-changeset at the
   end) before editing.

3. BACKWARD COMPATIBILITY: never change existing public/external signatures,
   event or error shapes, or storage layout. Additive only.

4. DO NOT EDIT the "// OpenZeppelin Contracts (last updated ...)" header line,
   do not hand-pick a pragma (use `npm run pragma`), and never hand-edit a
   procedurally generated file — edit scripts/generate/templates/ and run
   `npm run generate`.

5. IMPORTS are named, curly-brace, relative within contracts/. No new
   dependency of any kind.

6. TESTS: Hardhat + Chai (.test.js, shared .behavior.js) or Foundry (.t.sol).
   Run `npm test` (or `forge test --match-path`) and `npm run lint`.

7. CHANGESET (`npx changeset add`) for behaviour changes; none for NatSpec-only
   or internal refactors.

8. VERIFY BY HAND anything in cryptography, ERC-7201 slots, storage layout,
   assembly/memory-safety and unchecked blocks — AI output there is often
   plausible but wrong.

9. NO SECURITY OPINIONS and no claims about bounties or rewards in any text.
   Anything that looks like a vulnerability goes to the private note.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | A plain, capitalized imperative sentence, e.g. "Add a warning about adding features in an upgrade". Conventional prefixes are not used. |
| Template | `Fixes #N`, a short description, and a PR Checklist (Tests / Documentation / Changeset entry). |
| AI | Welcome, but "low-effort AI output" may be closed without explanation. One careful PR at a time. |
| Budget | 1 open PR, and only for an issue where a maintainer agreed on the fix. |
