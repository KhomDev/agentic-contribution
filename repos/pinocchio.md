# Pinocchio: `anza-xyz/pinocchio`

Sources: `README.md`, `SECURITY.MD`, `package.json` and `.github/workflows/main.yml` from `main`,
read 2026-11-24. The repo has no CONTRIBUTING file or PR template.

## Agent rules block

```text
You are contributing to Pinocchio, a zero-dependency, no_std library for
writing Solana programs, and its program helper crates (programs/token,
programs/system, ...). Programs holding funds compile against it: correctness
and unsafe-code soundness are critical.

1. SECURITY FIRST. A soundness or account-validation bug is a security issue:
   it goes only to the private note and through GitHub's private advisory
   (SECURITY.MD), never into an issue, PR, branch or test name.

2. PUBLIC CONTRIBUTIONS are the non-security kind: docs that disagree with the
   code, helper APIs that return the wrong error, missing tests, broken links,
   build or feature-flag problems.

3. ONE CONCERN PER PR with a test. Unsafe blocks need a `// SAFETY:` comment.

4. TITLE: `<crate path>: <Capitalized imperative>`, for example
   `programs/token: Return Result from Account::state`,
   `sdk: Use bpf cfg for sol_get_sysvar in impl_sysvar_get`.

5. BEFORE HANDING BACK, on CI, through the pnpm scripts for the member you
   changed: `pnpm format <member>`, `pnpm clippy <member>`, `pnpm test <member>`,
   `pnpm doc <member>`, `pnpm hack <member>`, plus `pnpm spellcheck`
   (members come from scripts/setup/members.mts).
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR body | Prose; release notes are generated from commit titles (git-cliff), so the title matters |
| Security | Speculative reports without a PoC are closed (SECURITY.MD). Program-logic findings stay private |
| Tracker speed | 16 merged PRs in the 60 days to 2026-11-24; 5 from 4 outside authors |
| Fork | `KhomDev/pinocchio` does not exist yet; ask the operator before creating it |
| Budget | 1 open PR |
