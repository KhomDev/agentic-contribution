# NEAR CLI: `near/near-cli-rs`

Sources: `README.md`, `release-plz.toml`, `CODEOWNERS` from `main`, read 2026-11-21.

## Agent rules block

```text
You are contributing to NEAR CLI (near/near-cli-rs), the official human-friendly
command-line tool for NEAR Protocol.

1. HUMAN-FACING UX. The CLI is interactive: prompts, wording and transaction
   previews are part of the product. Preserve stdout/stderr separation, quiet
   mode and scriptable output. Explain any change to user-visible text.

2. CONVENTIONAL COMMITS. release-plz generates CHANGELOG.md and releases from
   commit subjects, so use `fix: ...`, `feat: ...`, `chore: ...`,
   `fix(deps): ...`.

3. RUST CHECKS. `cargo fmt --check`, `cargo clippy --all-targets`,
   `cargo test`. The workspace depends on nearcore crates (near-primitives,
   near-jsonrpc-client), so full builds are heavy: use CI for full matrices.

4. ONE CONCERN PER PR. No unrequested features or refactors. Keep offline mode
   and scripted usage working.

5. NO PUBLIC ACTION beyond a `verify/*` branch on the fork. Never push to
   near/near-cli-rs.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| PR title | Conventional, lowercase after the colon, at most 72 characters. Examples from merged PRs: `fix: report recipient warnings without a TTY`, `fix: staking validator-list network-config mainnet`. |
| PR body | No template in the repo: prose with the problem, the fix and the verification. |
| Draft | Not required. |
| Signing | Not required. |
| AI disclosure | None required. |
| Volume | 1 open PR; small repo, small reviewer pool. CODEOWNERS is `@near/devex`. |
| CI | Upstream: `cargo fmt --all -- --check`, `cargo clippy -- -D warnings`, `cargo test --all-features`; both workflows install `libudev-dev`. On oss-ci, dispatch Rust runs with `--apt libudev-dev` (hidapi fails to build otherwise). Full workspace builds are heavy, so use CI. |
| Tracker notes | Many issues are maintainer-authored from Slack threads; check cross-references and assignments first. #691 had a maintainer PR (#694) closed on 2026-11-09 — do not revive it without new information. #714 depends on the still-open #704. #713 is taken by draft PRs #626/#627. |
