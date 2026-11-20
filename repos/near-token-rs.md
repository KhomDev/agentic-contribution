# near-token: `near/near-token-rs`

Sources: `README.md` and `.github/workflows/ci.yml` from `main`, read 2026-11-20. The repo has no
CONTRIBUTING, no PR template and no CLA. near-sdk re-exports `NearToken` from this crate
(`near-sdk-core/src/types/mod.rs`), so bugs reported against `NearToken` in near-sdk are fixed here.

## Agent rules block

```text
You are contributing to near-token, the small Rust crate behind NearToken (the
NEAR amount type used by near-sdk, near-api-rs and near-cli-rs). A wrong
parse or conversion silently changes how much NEAR moves: correctness of
every amount is critical.

1. ONE BEHAVIOUR PER PR. Fix exactly the defect; no API additions, no
   refactors, no new dependencies.

2. TESTS ASSERT EXACT VALUES. Compare against from_yoctonear/from_near with
   the precise expected amount, or against the exact error variant. A fix
   ships with a test that fails without it.

3. CHECKS (CI ci.yml): `cargo fmt -- --check`,
   `cargo clippy --all-features -- -D clippy::all`,
   `cargo test --verbose --all-features`. The toolchain is pinned in
   rust-toolchain.toml (MSRV = rust-version in Cargo.toml); do not raise it.

4. COMMITS AND TITLE: conventional commits (fix:, feat:, ci:, chore:). Never
   bump the version or edit CHANGELOG.md: release-plz does both.

5. SIBLING CRATE. near-gas-rs has the same structure (from_str, utils,
   parse_decimal_number). Check whether the same defect exists there and
   report it; fix each repo in its own PR.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR body | What / Fix / Tests, following the merged precedent #28 (chiliec): the bad inputs and their wrong results, the change in one paragraph, the test names that fail before and pass after. |
| Maintainers | r-near, vsavchyn-dev, frol (release-plz). |
| Budget | 1 open PR. |
| CI | `ci.py dispatch --target KhomDev/near-token-rs --toolchain rust --command 'cargo fmt -- --check && cargo clippy --all-features -- -D clippy::all && cargo test --all-features'`. |
