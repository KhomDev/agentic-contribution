# borsh-rs: `near/borsh-rs`

Sources: `README.md` and `CHANGELOG.md` from `master` (there is no CONTRIBUTING and no PR template), plus CI (`.github/workflows/rust.yml` and `.github/test.sh`), read 2026-11-27. The KhomDev fork does not exist yet. Create it (`gh repo fork near/borsh-rs --clone=false`) only once the operator approves the first PR.

## Agent rules block

```text
You are contributing to borsh-rs, the Rust implementation of the Borsh
binary serialization format. It is used in security-critical NEAR (and
other) projects — consistency with the spec and safe decoding are critical.

1. COMMITS AND TITLE: conventional commits (`feat:`, `fix:`, `ci:`,
   `docs:`, `test:`, `chore:`). Never bump crate versions — they are
   managed in the workspace manifest and published by release-plz.

2. CHANGELOG: user-facing changes go in `CHANGELOG.md` under `## Unreleased`.
   Do not empty that section except as part of a release.

3. TESTS: prefer integration tests in `borsh/tests/tests.rs` (see the
   README). CI (`.github/test.sh`) runs `cargo test` across feature
   combinations (default, derive, schema, rc, indexmap, no-default-features,
   unstable__bounded, etc.). A fix should add or extend a targeted
   `cargo test --features ... '<filter>'` and, on oss-ci, the relevant
   slice of test.sh. Also `cargo fmt --check`, `cargo clippy --features
   unstable__schema,unstable__bounded --benches -- -D clippy::all`, and
   `RUSTDOCFLAGS="-D warnings" cargo doc --features derive,unstable__schema,unstable__bounded`.

4. SPEC AND SAFETY: changes to encoding, schema validation or decode
   bounds must stay consistent with the Borsh specification and must not
   relax a check without a documented reason. This is a serialization
   library, not a place for drive-by refactors.

5. MSRV: the crate advertises rustc 1.77+. Do not raise the MSRV or
   unpin the older-toolchain CI job without agreement.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 2 open PRs. Title enforcement is an error (conventional commits, max 72). |
| Fork | None yet. Do not fork until the operator approves the first PR. |
| CI | `.github/test.sh` is the full matrix; run a targeted `cargo test --features ...` locally. rust.yml also has exhaustive-check (`cargo check --features force_exhaustive_checks` on nightly) and manual cargo-semver-checks. |
| Starting points | No current good-first-issue label. Outsiders landed real fixes in Nov 2026 (`feat: add BorshDeserializeBounded`, schema validation hardening, skipped-collection bounds). Discovery: docs vs decode behaviour, schema tests, bounded-decode feature flags. |
| Releases | Do not open a version-bump PR. |
