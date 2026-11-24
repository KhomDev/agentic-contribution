# LiteSVM: `LiteSVM/litesvm`

Sources: `README.md`, `CHANGELOG.md`, `justfile` and `.github/workflows/ci.yml` from `master`, read
2026-11-24. The repo has no CONTRIBUTING file or PR template.

## Agent rules block

```text
You are contributing to LiteSVM, a fast in-process Solana VM used to test
programs. Users rely on it to behave like a real validator: a difference from
Agave's behaviour is a bug in LiteSVM unless the docs say otherwise.

1. COMPARE WITH AGAVE. Before calling something a bug, show what Agave (the
   runtime, or solana-test-validator) does for the same transaction. Quote the
   Agave source or run both.

2. ONE CONCERN PER PR, small and testable. Recent outside merges are bug fixes
   with a regression test (panics on deleted programs, wrong signer in loader
   helpers, token freeze/thaw targets).

3. TITLE: conventional commits, scope optional: `fix: ...`, `fix(token): ...`,
   `fix(loader): ...`, `test: ...`, `chore: ...`.

4. CHANGELOG: add a line under `## [Unreleased]` in CHANGELOG.md
   (### Fixed / ### Changed), ending with the PR link.

5. BEFORE HANDING BACK, on CI: `cargo +nightly fmt --all -- --check`,
   `cargo clippy --all-targets -- -D warnings`, `cargo test --features
   precompiles`, and `cd crates/token && cargo test --features token-2022` if the
   token crate changed. Test programs need `cargo build-sbf`
   (crates/litesvm/test_programs).

6. Agave crate versions are pinned (currently 4.3.x). Do not bump them in a fix PR.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR body | Prose: what was wrong, Agave's behaviour, the fix, the test |
| Fit | A common harness for Solana PoCs; a LiteSVM vs Agave gap found while writing a PoC is a public bug here, but the PoC and its target stay private |
| Security | A LiteSVM bug is a test-tool bug, not a chain bug. If a gap hides a real program vulnerability, the program finding goes only to the private note |
| Tracker speed | 25 merged PRs in the 60 days to 2026-11-24; 16 from 9 outside authors |
| Fork | `KhomDev/litesvm` does not exist yet; ask the operator before creating it |
| Budget | 2 open PRs |
