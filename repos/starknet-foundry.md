# Starknet Foundry: `foundry-rs/starknet-foundry`

Sources: `CONTRIBUTING.md` and `.github/pull_request_template.md` from `master`, read 2026-11-27. The fork `KhomDev/starknet-foundry` exists (created 2026-11-27 with the operator's approval). Push only `verify/*` branches there for oss-ci; PR branches only after the operator approves the PR.

## Agent rules block

```text
You are contributing to Starknet Foundry (snforge, sncast), the Starknet
development toolkit in Rust. Testers rely on its output — correctness of
command results and snapshots is critical.

1. ISSUES: search existing issues before opening a new one. First-time
   contributors should comment on a `good-first-issue` and wait to be assigned.
   More experienced contributors may take `help-wanted` after discussing with
   the core team. This is not a hard issue-first rule, but the PR template
   asks you to link a relevant issue (`Closes #`).

2. ENVIRONMENT: follow the book development guide. Local tests: `cargo test`
   (the supported local runner). `cargo nextest run` can leave an orphan
   `starknet-devnet` process; do not use it on the operator's machine. Some
   e2e tests need the branch pushed to a remote first. Scarb used in tests
   should come from asdf. Heavy runs go to oss-ci.

3. TESTS: features and fixes need automatic tests. Insta snapshot tests for
   older Scarb versions must use a `snap_` name prefix. After adding those,
   run `./scripts/check_snapshots.sh` (and `--fix` if they fail, then review).
   Known flaky tests belong in `.config/nextest.toml` with a justified retry,
   not a silent skip.

4. PR TEMPLATE: use `.github/pull_request_template.md` — `Closes #`,
   Introduced changes, and the Checklist (linked issue, docs, tests,
   self-review, CHANGELOG.md). Keep the PR self-contained and small.

5. NO TYPO-ONLY PRS: spelling or grammar-only contributions are not accepted.

6. SNCAST OUTPUT: imperative tone, concise, `key: value` for config, and a
   hint for the natural next command when there is one (e.g. declare hints
   deploy).
```

## Orchestrator notes

| Item | Rule |
|---|---|
| Volume | Budget 2 open PRs. Title enforcement is a warning: recent merges mix `fix(ci):` with plain sentences. |
| Template | `pr_body: template`. Lint must see Introduced changes and Checklist. User-facing changes go in `CHANGELOG.md`. |
| Fork | `KhomDev/starknet-foundry` (created 2026-11-27, operator-approved). `verify/*` branches for oss-ci only; never push to upstream. |
| CI | Local: `cargo test` for the touched crate. CI (`ci.yml`) also runs `cargo test --profile ci --workspace --exclude sncast --exclude forge --exclude native-api` and partitioned nextest archives for forge integration/e2e. Prefer oss-ci for those. |
| Typo ban | Same as Scarb: no typo-only filings. |
| Starting points (re-check still open) | [#4723](https://github.com/foundry-rs/starknet-foundry/issues/4723) (`snforge --json`, opened 2026-11-27) and related json-support issues (#4719, #4716, #4715, #4714, #4711). Confirm no one is already assigned before picking them up; discovery of a docs-vs-CLI mismatch is equally welcome. |
