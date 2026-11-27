# cargo-deny: `EmbarkStudios/cargo-deny`

Sources: `CONTRIBUTING.md` and `README.md` from `main`, plus CI (`.github/workflows/ci.yaml`), read 2026-11-27. The KhomDev fork does not exist yet. Create it (`gh repo fork EmbarkStudios/cargo-deny --clone=false`) only once the operator approves the first PR.

## Agent rules block

```text
You are contributing to cargo-deny, the Cargo plugin that lints a crate's
dependencies (advisories, bans, licenses, sources). Teams rely on its
diagnostics — a wrong allow or a missed advisory is a real miss.

1. START FROM A REAL ISSUE when you can. CONTRIBUTING asks contributors to
   look at `help wanted` or `good first issue` and to comment before starting.
   Feature requests and bug reports should include a use case or a
   reproduction (platform, steps, error text).

2. KEEP THE PATCH SMALL. Recent merges are almost all from the maintainer
   (Jake-Shadle). A short, easy-to-review bug fix is more likely to land than
   a large feature. User-facing diagnostic changes usually belong in
   `CHANGELOG.md`.

3. TESTS AND CHECKS: CI (`ci.yaml`) runs typos, `cargo fmt -- --check`,
   `cargo clippy --all-targets --all-features -- -D warnings` (including an
   MSRV job), `cargo test`, a rustsec-compat test
   (`cargo test --release --manifest-path tests/rustsec-compat/Cargo.toml`),
   and `cargo deny --all-features --locked check` as a self-check. Run the
   targeted `cargo test` and fmt/clippy locally; heavy jobs go to oss-ci.

4. AI POLICY (CONTRIBUTING, "AI"): obviously AI-written PRs are likely to be
   closed without a response unless the change is small and easy to review.
   Write a tight, evidence-backed patch. Do not dump generated boilerplate.

5. LICENSING: dual MIT OR Apache-2.0. Follow the Contributor Code of Conduct.
   No CLA and no signed-commit requirement in-repo.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 1 open PR. Title enforcement is a warning: recent titles are plain sentences ("Add `patched` diagnostic"). |
| Fork | None yet. Do not fork until the operator approves the first PR. |
| AI | The maintainer's CONTRIBUTING note is unusually blunt. Only gate small, clearly evidenced fixes; skip wide refactors and generated docs dumps. The skill footer still applies to public text. |
| CI | `cargo fmt -- --check`, `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test`. Self-check: `cargo deny --all-features --locked check`. |
| Starting points (re-check still open) | [#919](https://github.com/EmbarkStudios/cargo-deny/issues/919) (bug: cannot ignore feature-activated dev-dependencies, 2026-11-18). [#908](https://github.com/EmbarkStudios/cargo-deny/issues/908) (wildcard diagnostic points at the wrong span). Reproduce before drafting a fix. |
