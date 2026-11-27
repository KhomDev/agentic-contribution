# OpenZeppelin Contracts for Cairo: `OpenZeppelin/cairo-contracts`

Sources: `AGENTS.md`, `CONTRIBUTING.md`, `GUIDELINES.md` and `ARCHITECTURE.md` from `main`, read
2026-11-22.

## Agent rules block

```text
You are contributing to OpenZeppelin Contracts for Cairo (Starknet). Deployed
contracts inherit it; storage layout and ABI compatibility are critical.

1. ISSUE FIRST: open an issue and get agreement before development. Security
   vulnerabilities are the exception and go privately per SECURITY.md — never
   in a public issue or PR.

2. READ GUIDELINES.md and ARCHITECTURE.md before editing, and AGENTS.md for the
   tooling and conventions.

3. COMMITS AND PRS: conventional commits `type(scope): summary`; sign every
   commit. NEVER add a Co-Authored-By trailer or the usual
   'Authored by KhomDev with AI assistance.' line — the repo forbids AI
   commit trailers. The author is accountable under their own name.

4. STORAGE: prefix component storage members with the component name; preserve
   deployed field names and types; assess storage compatibility before changing
   them.

5. NUMERIC LITERALS: prefer literals without type suffixes when the compiler
   can infer the type.

6. COVERAGE AND CHECKS: patch coverage target 80% (codecov, 4-point tolerance).
   Run scarb fmt/lint and snforge as listed in CONTRIBUTING's Verification
   section (including the Falcon checks when touching account, preset or
   generated arithmetic paths).

7. CHANGELOG.md: user-facing changes go under `## Unreleased`, grouped by
   Added/Changed/Fixed, referencing the PR number.

8. AI assistance is welcome; low-effort AI output may be closed without
   explanation.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional commits style; recent maintainer merges are often plain, so title enforcement is a warning |
| Issue | Issue-first: the PR links the maintainer-agreed issue |
| Signing | Required by CONTRIBUTING |
| Commit trailer | **Forbidden**: no `Co-Authored-By` and no `Authored by KhomDev with AI assistance.` (config `commit_trailer: "none"`). The orchestrator must not add either here |
| AI disclosure | Allowed and disclosed in the PR body by the footer; low-effort output is closed |
| CI | `scarb fmt --check --workspace`; `scarb lint --workspace --test --deny-warnings`; `snforge test --workspace --features fuzzing --fuzzer-runs 200 --skip falcon_512`; coverage via `snforge test --workspace --coverage` |
| Changelog | `CHANGELOG.md` under `## Unreleased` |
| Tracker speed | Slower and maintainer-driven: 5 merged PRs and one outside author in the 30 days to 2026-11-22; at most one careful PR at a time |
| Volume | Budget 1 open PR |
