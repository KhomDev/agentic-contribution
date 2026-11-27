# RustSec: `rustsec/rustsec`

Sources: `README.md` from `main` (there is no CONTRIBUTING and no PR template), plus CI workflows (`workspace.yml`, `rustsec.yml`, `cargo-audit.yml`), read 2026-11-27. The fork `KhomDev/rustsec` exists (created 2026-11-27 with the operator's approval). Push only `verify/*` branches there for oss-ci; PR branches only after the operator approves the PR.

## Agent rules block

```text
You are contributing to rustsec/rustsec, the Cargo workspace for RustSec
tooling (`cargo-audit`, `cargo-lock`, `cvss`, `platforms`, the `rustsec`
client library, `rustsec-admin`). These tools are how Rust projects learn
about advisories — correctness of audit results is critical.

1. SCOPE: this is a workspace. Touch only the crate your change belongs to
   (`cargo-audit`, `rustsec`, `cargo-lock`, etc.) and the tests for that
   crate. Do not retouch advisory-db (a separate repository).

2. TESTS AND CHECKS: CI formats and lints the workspace (`cargo fmt`,
   `cargo clippy`) and runs per-crate workflows. For `rustsec`: `cargo test`,
   `cargo test --no-default-features`, and
   `cargo test --features=dependency-tree,osv-export,binary-scanning`. For
   `cargo-audit`: `cargo test`, `cargo test --no-default-features`,
   `cargo test --all-features`. Prefer targeted `cargo test -p <crate>`
   locally. Heavy or multi-OS runs go to oss-ci. `cargo doc` must stay
   warning-free on the features CI uses.

3. PR SHAPE: keep the patch small and reviewable. Recent merged titles are
   plain sentences or `crate: description` (`cargo-audit: ...`, `rustsec:
   ...`), not strict conventional commits. Say which crate you changed.

4. SECURITY TOOLING: do not weaken an audit, parse, or version-range check
   to make a test pass. A change that alters how advisories are matched or
   reported needs a test and a clear description of the old vs new behaviour.

5. EXISTING TICKETS: some items still tagged `good first issue` are years
   old (for example #585, last comment 2023). Re-verify on today's `main`
   before spending time on them; prefer a freshly reproduced bug or a docs
   vs CLI mismatch.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 1 open PR. Title enforcement is a warning (max 80, no trailing period). |
| Fork | `KhomDev/rustsec` (created 2026-11-27, operator-approved). `verify/*` branches for oss-ci only; never push to upstream. |
| License | Dual MIT OR Apache-2.0. No CLA or signed-commit requirement in-repo. |
| Starting points (re-verify) | [#740](https://github.com/rustsec/rustsec/issues/740) (configurable max file size when scanning binaries, still open, labeled good first issue, last activity 2026-01-25). [#585](https://github.com/rustsec/rustsec/issues/585) (`cargo audit` creating `./~/.cargo/advisory-db`) is likely stale — confirm before touching. Outside PRs merged the week of 2026-11-26 (trackoor, Mahan-Imanian, atouchet). |
| Adjacent | `rustsec/actions` has open good-first-issues (#2, #3, #4) but is a different repo; out of scope unless the operator adds it. |
