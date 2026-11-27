# krates: `EmbarkStudios/krates`

Sources: `CONTRIBUTING.md` and `README.md` from `main`, plus CI (`.github/workflows/ci.yml`), read 2026-11-27. krates builds the crate graph that cargo-deny checks (`Krates`, `Builder`, `krates_filtered`), so a cargo-deny bug can have its root cause here. Example: cargo-deny#919 traced to `Krates::krates_filtered`. The fork `KhomDev/krates` exists (created 2026-11-27 with the operator's approval). Push only `verify/*` branches there for oss-ci. PR branches go there only after the operator approves the PR.

## Agent rules block

```text
You are contributing to krates, the library that turns `cargo metadata` into a
crate graph (crates, features and the edges between them). cargo-deny and
other tools build on it, so a wrong edge or a missed crate shows up as a wrong
diagnostic downstream.

1. START FROM A REAL ISSUE when you can, here or in a downstream repo
   (cargo-deny) whose root cause is in krates. CONTRIBUTING asks for
   reproducible bug reports (platform, steps, error text) and points at
   `help wanted` / `good first issue`.

2. KEEP THE PATCH SMALL AND TESTED. The maintainer (Jake-Shadle) merges outside
   PRs (for example #117, #118 and #119 in 2026). Each fix comes with a test
   fixture under `tests/` (a small path-crate workspace like
   `tests/chained-weak/` or a checked-in metadata JSON) and an assertion that
   fails without the fix.

3. KEEP THE PUBLIC API STABLE. `Node`, `Edge` and `Krates` are public, and
   downstream crates match on them. Prefer private fields and internal
   bookkeeping over new enum variants or changed field sets.

4. TESTS AND CHECKS: CI (`ci.yml`) runs `cargo fmt -- --check`,
   `cargo clippy --all-targets -- -D warnings` (also with `--all-features`),
   `cargo nextest run --release` with and without `--features targets` (after
   `cargo fetch` for tests/bug, features, feature-bug, features-2 and
   feature-bug-2), a cargo-deny check and `cargo publish --dry-run`. The
   test build is small enough to run locally with `-j1`. Use oss-ci for the
   full matrix.

5. LICENSING: dual MIT OR Apache-2.0. Follow the Contributor Code of Conduct.
   No CLA and no signed-commit requirement in-repo.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 1 open PR. Titles are plain sentences ("Fix `PkgSpec` matching"). Enforcement is a warning. |
| Fork | `KhomDev/krates` (created 2026-11-27, operator-approved). `verify/*` branches only. Never push to upstream. |
| Changelog | `CHANGELOG.md` `[Unreleased]`, in the form "[PR#n](...) resolved [#n](...) by ...". Outside PRs sometimes add it; otherwise the maintainer does in an "Update CHANGELOG" commit. Add it once the PR number is known, or leave it to the maintainer and say so. |
| CI | See rule 4. `krates_filtered` must match a graph built with `ignore_kind` (its docs promise this). `tests/kind.rs::filters_after_build` checks it. |
| Downstream check | For a cargo-deny root cause, confirm with cargo-deny built against the branch via `[patch.crates-io] krates = { path = ... }`, and run cargo-deny's own tests with the same patch on oss-ci. |
| Gotcha | On Windows, clone with `core.autocrlf=false` set first (`git -c core.autocrlf=false clone ...`), or every file shows as modified. After restoring a file with `Copy-Item`, touch it: cargo uses mtimes and will run a stale binary. |