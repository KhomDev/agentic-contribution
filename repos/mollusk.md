# Mollusk: `anza-xyz/mollusk`

Sources: `README.md`, `Makefile` and `.github/workflows/main.yml` from `main`, read 2026-11-24. The
repo has no CONTRIBUTING file or PR template.

## Agent rules block

```text
You are contributing to Mollusk, Anza's harness for testing Solana programs
instruction by instruction. It must match the Agave runtime's results
(compute units, account changes, errors).

1. COMPARE WITH AGAVE. A harness result that differs from the runtime is the
   bug class maintainers merge. Quote the Agave code the harness should match.

2. ONE CONCERN PER PR with a regression test. Recent outside merges: fixture
   slot recording, failed benches in compute-unit results, a token-2022 ATA
   helper that panicked on every call.

3. TITLE: `<area>: <lower-case summary>` or `fix: ...`, for example
   `harness: serialize sysvars with wincode`, `fix: mark failed benches in
   compute unit results`.

4. BEFORE HANDING BACK, on CI: `make format`, `make clippy`,
   `make build-test-programs` then `make test`, and `make check-features`.
   The nightly toolchain and cargo-build-sbf versions come from
   `make nightly-version` and `make cargo-build-sbf-version`; protobuf-compiler
   is needed.

5. Release-line branches (v4.x) are maintained by backport; target `main`.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR body | Prose: the mismatch, the runtime's behaviour, the fix, the test |
| Fit | A common harness for Solana program PoCs; any program finding it surfaces stays private |
| Tracker speed | 40 merged PRs in the 60 days to 2026-11-24; 19 from 6 outside authors (dependabot excluded) |
| Fork | `KhomDev/mollusk` does not exist yet; ask the operator before creating it |
| Budget | 2 open PRs |
