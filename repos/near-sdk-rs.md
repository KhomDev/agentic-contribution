# near-sdk-rs: `near/near-sdk-rs`

Sources: `CONTRIBUTING.md` from `master`, read 2026-11-20. Fork: `KhomDev/near-sdk-rs` (exists since 2026-11-24).

## Agent rules block

```text
You are contributing to near-sdk-rs, the Rust SDK for NEAR smart contracts.
Contracts holding user funds compile against it — correctness and stable APIs
are critical.

1. TITLES: descriptive; conventional commits loosely (fix:, feat:, refactor:,
   test:, chore:).

2. BEFORE A PR: install hooks with ./git-hooks.sh, `cargo fmt`, build the
   example wasm files with ./examples/build_all.sh, then ./run-tests.sh (tests
   and linters). On this host: CI only.

3. New public types or functions get rustdoc documentation.

4. Snapshot tests pinned to a rustc version (e.g. schema_derive_invalids on
   1.95) must not be regenerated with another toolchain.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Red "Audit" check | The repo-wide cargo-audit check is red on unrelated advisories. It isn't ours, so don't try to fix it in a feature PR. |
| #1638 | That PR is Bortlesboat's, not ours. We only commented, so it's not on our PR budget. |
