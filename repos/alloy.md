# Alloy: `alloy-rs/alloy`

Sources: `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` from `main`, read 2026-11-21.

## Agent rules block

```text
You are contributing to Alloy (alloy-rs/alloy), the Rust Ethereum primitives,
ABI, RPC-type, transport and provider stack that Foundry and much of the Rust
Ethereum ecosystem build on.

1. TEST EVERY CODE CHANGE. Unit or integration tests, table tests where they
   fit; integration tests live in the crate's tests/ directory. Doc examples are
   run by `cargo test --doc`.

2. CONVENTIONAL COMMITS, SIGNED. Subjects like `fix(provider): ...`,
   `chore(primitives): ...`, `test: ...`. Commit signing is a strict project
   standard.

3. RUN THE MATRIX: `cargo check --all-features`, `cargo +nightly fmt --all`,
   `cargo test --all-features`, `cargo test --no-default-features`,
   `cargo +nightly clippy --all-features`. The full test suite needs geth and
   Anvil; targeted crate tests do not.

4. LOCKFILE DISCIPLINE. `Cargo.lock` is committed and CI uses `--locked`. For an
   intentional dependency change use `cargo update -p <package>` and include the
   lockfile diff. A lockfile does not exempt a dependency from security checks.

5. NO SPELLING- OR GRAMMAR-ONLY PRs. No unrequested features. Keep the change
   reviewable and allow edits from maintainers.

6. PR TEMPLATE. Fill `.github/PULL_REQUEST_TEMPLATE.md`.

7. NO PUBLIC ACTION beyond a `verify/*` branch on the fork. Never push to
   alloy-rs/alloy.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional, lowercase after the colon, at most 72 characters. Examples from merged PRs: `fix(rpc-types-mev): serialize full-range U256 numeric string`, `fix(network-primitives): deserialize newtype transactions`. |
| PR body | Template at `.github/PULL_REQUEST_TEMPLATE.md`; fill it. |
| Draft | Not required. |
| Signing | `signed_commits: true` — the project calls commit signing a strict standard. |
| AI disclosure | None required. |
| Volume | 2 open PRs; prefer issues with a stated fix or a clear repro. |
| CI | Per-crate: `cargo test -p <crate> --all-features` and `cargo +nightly clippy -p <crate> --all-features`; full suite needs geth and Anvil, so keep it in CI. |
| Tracker notes | External fixes merge in 0-3 days (Soubhik-10, woniush, stevencartavia, dlr-a). Issue #4485 is claimed in comments by Steven-J-22. #4547 (paste removal) is misfiled and dead: this repo has no `crates/primitives` and no `paste`; the code lives in `alloy-rs/core`, where #897 is CLOSED/NOT_PLANNED and the pastey PR #1086 was closed unmerged. Do not pick it up. |
