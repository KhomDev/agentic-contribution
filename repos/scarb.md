# Scarb: `software-mansion/scarb`

Sources: `CONTRIBUTING.md` and `AGENTS.md` (`CLAUDE.md` is the same text) from `main`, read 2026-11-27. The fork `KhomDev/scarb` exists (created 2026-11-27 with the operator's approval). Push only `verify/*` branches there for oss-ci; PR branches only after the operator approves the PR.

## Agent rules block

```text
You are contributing to Scarb, the Cairo package manager (Rust). Cairo
developers' builds go through it — reproducibility of resolution and
documentation output is critical.

1. SEARCH FIRST: before opening a pull request, search existing issues. A
   feature request is appreciated before you start work, so the change can be
   discussed. This is not a hard issue-first rule for bug fixes.

2. TESTS AND CHECKS: features and fixes need automatic tests. Before a PR,
   CONTRIBUTING requires `cargo fmt`, `cargo clippy` and `cargo test`. CI
   (`ci.yml`, 27 Nov) runs `cargo fmt --check`, `cargo clippy --all-targets
   --all-features --workspace --exclude scarb-prove --exclude scarb-verify`,
   `cargo test --doc --workspace` with the same excludes, and `cargo nextest`
   on a workspace archive. Prefer targeted `cargo test -p <crate>` locally;
   AGENTS.md says never run the full suite without asking first. Heavy runs go
   to oss-ci.

3. PR SHAPE: keep PRs small and squashable to one commit. For larger work,
   small self-contained commits that each pass lint and tests, then a stack of
   PRs. The project uses stacked PRs (`git spr` / `git spice`) internally;
   outside contributors should not invent a stack unless the operator asks.

4. DEPENDENCIES: do not add, remove, or run a broad `cargo update`. Do not
   delete `Cargo.lock`. Cairo upgrades use `cargo xtask upgrade cairo` only
   when that is the task.

5. NO TYPO-ONLY PRS: CONTRIBUTING rejects pull requests that only fix typos in
   documentation or code. Hunt for behavioural bugs, broken docs-vs-code, or
   missing tests instead.

6. BREAKING CHANGES must be called out in the PR description.
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 2 open PRs. Title and commit-subject enforcement are warnings: recent merges mix `ci:` conventional titles, `[nightly-fix]` prefixes and plain sentences. |
| Fork | `KhomDev/scarb` (created 2026-11-27, operator-approved). `verify/*` branches for oss-ci only; never push to upstream. |
| Typo ban | Discovery agents must not file typo-only PRs or issues. |
| CI | Local: `cargo fmt --check`, `cargo clippy --all-targets --all-features --workspace --exclude scarb-prove --exclude scarb-verify`, targeted `cargo test -p <crate>`. Full nextest archive runs belong on oss-ci. |
| Starting points (re-check still open and unclaimed) | [#1206](https://github.com/software-mansion/scarb/issues/1206) (`good first issue`, missing files in Scarb manifest metadata, last activity 2026-05-17). Also [#1441](https://github.com/software-mansion/scarb/issues/1441), [#1152](https://github.com/software-mansion/scarb/issues/1152), [#698](https://github.com/software-mansion/scarb/issues/698). Outsiders do land docs fixes ([#3309](https://github.com/software-mansion/scarb/pull/3309), 2026-11-10). |
| Maintainers | software-mansion/scarb-maintainers; project lead @maciektr (MAINTAINING.md). |
