# cargo-near: `near/cargo-near`

Sources: the repo `README.md` (it has no CONTRIBUTING and no PR template), CI workflows and the merge
history, read 2026-11-20. The KhomDev fork does not exist yet. Create it (`gh repo fork near/cargo-near
--clone=false`) only once the operator approves the first PR.

## Agent rules block

```text
You are contributing to cargo-near, the cargo extension that builds, ABI-
generates and deploys NEAR Rust contracts. Every NEAR Rust developer's build
goes through it — reproducibility is critical.

1. COMMITS AND TITLE: conventional commits (fix:, feat:, ci:, chore:). Never
   bump versions — release-plz does it.

2. CHECKS (CI test.yml): `cargo fmt -- --check`,
   `cargo clippy --tests -- -Dclippy::all`,
   `RUSTDOCFLAGS="-D warnings" cargo doc -p cargo-near-build`, typos, and
   `cargo nextest run --workspace --profile ci`.

3. PLATFORM: Windows builds of near-sdk ABI fail (LNK1120, near-sdk-rs#1221).
   Platform-specific fixes need tests that run on Linux CI.

4. CREDIT: if a closed PR (e.g. #468) already holds the fix, port it only with
   the original author credited (Co-authored-by) and say so in the PR.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| State | Comments on #188 and #483 are waiting for a maintainer reply, and the branches are ready. No PR until a maintainer responds. |
| Maintainers | r-near, vsavchyn-dev, dj8yfo. |
