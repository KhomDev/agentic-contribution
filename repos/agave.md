# Agave (Solana validator): `anza-xyz/agave`

Sources: `AGENTS.md`, `CONTRIBUTING.md` and `.github/PULL_REQUEST_TEMPLATE.md` from `master`, read
2026-11-20.

## Agent rules block

```text
You are contributing to Agave, the Solana validator client. It runs mainnet
validators — correctness and consensus safety are critical.

1. PACKAGE NAMES: the workspace mixes agave-* and solana-* crates. Never infer
   a package name from its directory; read `name` in the crate's [package]
   table before any `cargo -p` command (AGENTS.md).

2. CONSEQUENTIAL CHANGES ONLY. Typo/grammar-only PRs from outside contributors
   are usually closed. Do not mix refactoring with logic changes.

3. TESTS cover at least 90% of added code paths, run fast, never flaky.
   unwrap() only where it provably cannot panic; prefer expect() with a reason.

4. BEFORE HANDING BACK, on CI: ./ci/test-sanity.sh, ./ci/test-checks.sh and the
   smallest crate's tests (`cargo test -p <package> -- <filter>`).

5. NEVER anything consensus-affecting (needs a feature gate and a SIMD). CLI,
   RPC client, tooling and test fixes only.

6. PRIOR ART: search open AND closed PRs for the issue number and the symptom.
   If an earlier PR fixed it, stop and report it — do not rewrite it.

7. PR TITLE: imperative, first word capitalized, no trailing period, from the
   user's point of view ("Fix out-of-memory error in validator"); an area
   prefix like `cli: ` is common in merged PRs.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Template | `#### Problem`, `#### Summary of Changes`, then `Fixes #N`. Write a Problem statement that stands alone, because reviewers decide in 30 seconds. |
| Draft | Open as Draft and mark it Ready only when CI is green. Never add reviewers to a draft; mention them in a comment instead. |
| Review replies | Reply "Fixed in <sha>" and resolve the thread, or "Is this what you had in mind? <sha>". |
| Prior art | Two of our first three agave candidates already had stale PRs (#14863 riba2534, #14185 0xfandom). We credited the authors and asked for a reopen instead of copying. |
| Budget | At most 2 PRs or comments in flight. No more agave comments on a day when we've already posted 2. |
